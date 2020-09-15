# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import pandas as pd, json
# from functools import lru_cache
from gateway.asset.assets import Asset
from gateway.driver.tools import _parse_url
from gateway.driver.client import tsclient
from gateway.driver.resample import Sample
from gateway.driver.bar_reader import AssetSessionReader
from gateway.driver.bcolz_reader import BcolzMinuteReader
from gateway.driver.adjustment_reader import SQLiteAdjustmentReader
from gateway.driver.history_loader import (
    HistoryDailyLoader,
    HistoryMinuteLoader
)
from gateway.asset.assets import Equity, Fund, Convertible


class DataPortal(object):
    """Interface to all of the data that a nakedquant needs.

    This is used by the nakedquant runner to answer questions about the data,
    like getting the prices of asset on a given day or to service history
    calls.

    Parameters
    ----------
    rule --- resample rule
    asset_finder : assets.assets.AssetFinder
        The AssetFinder instance used to resolve asset.
    """
    OHLCV_FIELDS = frozenset(["open", "high", "low", "close", "volume"])

    def __init__(self):

        self.resize_rule = Sample()
        self._adjustment_reader = SQLiteAdjustmentReader()
        _minute_reader = BcolzMinuteReader()
        _session_reader = AssetSessionReader()

        _history_daily_loader = HistoryDailyLoader(
            _session_reader,
            self._adjustment_reader,
        )
        _history_minute_loader = HistoryMinuteLoader(
            _minute_reader,
            self._adjustment_reader,

        )
        self._history_loader = {
            'daily': _history_daily_loader,
            'minute': _history_minute_loader,
        }
        self._extra_source = None

    @property
    def adjustment_reader(self):
        return self._adjustment_reader

    def get_dividends_for_asset(self, asset, trading_day):
        """
        splits --- divdends

        Returns all the stock dividends for a specific sid that occur
        in the given trading range.

        Parameters
        ----------
        asset: Asset
            The asset whose stock dividends should be returned.

        trading_day: pd.DatetimeIndex
            The trading day.

        Returns
        -------
            equity divdends or cash divdends
        """
        dividends = self._adjustment_reader.load_divdends_for_sid(asset.sid, trading_day)
        return dividends

    def get_rights_for_asset(self, asset, trading_day):
        """
        Returns all the stock dividends for a specific sid that occur
        in the given trading range.

        Parameters
        ----------
        asset: Asset
            The asset whose stock dividends should be returned.

        trading_day: pd.DatetimeIndex
            The trading dt.

        Returns
        -------
            equity rights
        """
        rights = self._adjustment_reader.load_rights_for_sid(asset.sid, trading_day)
        return rights

    def get_open_pct(self, assets, dts):
        # pre_close 经过qfq --- close
        open_pctchange, pre_close = self._history_loader['daily'].get_open_pct(assets, dts)
        return open_pctchange, pre_close

    def get_spot_value(self, asset, dts, frequency, field):
        spot_value = self._history_loader[frequency].get_spot_value(dts, asset, field)
        return spot_value

    def get_stack_value(self, tbl, session):
        stack = self._history_loader.get_stack_value(tbl, session)
        return stack

    # @lru_cache(maxsize=32)
    def get_window_data(self,
                        assets,
                        dt,
                        days_in_window,
                        field,
                        data_frequency):
        """
        Internal method that gets a window of raw daily data for a sid
        and specified date range.  Used to support the history API method for
        daily bars.

        Parameters
        ----------
        assets : list --- element is Asset
            The asset whose data is desired.

        dt: pandas.Timestamp
            The end of the desired window of data.

        field: string or list
            The specific field to return.  "open", "high", "close_price", etc.

        days_in_window: int
            The number of days of data to return.

        data_frequency : minute or daily

        Returns
        -------
        A numpy array with requested values.  Any missing slots filled with
        nan.
        """
        history_reader = self._history_loader[data_frequency]
        window_array = history_reader.window(assets, field, dt, days_in_window)
        return window_array

    # @lru_cache(maxsize=32)
    def get_history_window(self,
                           assets,
                           end_date,
                           bar_count,
                           field,
                           data_frequency):
        """
        Public API method that returns a dataframe containing the requested
        history window.  Data is fully adjusted.

        Parameters
        ----------
        assets : list of zipline.data.Asset objects
            The asset whose data is desired.

        end_date : history date(not include)

        bar_count: int
            The number of bars desired.

        frequency: string
            "1d" or "1m"

        field: string
            The desired field of the asset.

        data_frequency: string
            The frequency of the data to query; i.e. whether the data is
            'daily' or 'minute' bars.

        ex: boolean
            raw or adjusted array

        Returns
        -------
        A dataframe containing the requested data.
        """
        fields = field if isinstance(field, (set, list)) else [field]
        if not set(field).issubset(self.OHLCV_FIELDS):
            raise ValueError("Invalid field: {0}".format(field))

        if bar_count < 1:
            raise ValueError(
                "bar_count must be >= 1, but got {}".format(bar_count)
            )
        history = self._history_loader[data_frequency]
        history_window_arrays = history.history(assets, fields, end_date, bar_count)
        return history_window_arrays

    def freq_by_minute(self, kwargs):
        """
        :param kwargs: hour,minute
        :return: minute ticker list
        """
        minutes = self.resize_rule.minute_rule(kwargs)
        return minutes

    def freq_by_week(self, delta):
        """
        :param delta: int , the number day of week (1-7) which is trading_day
        :return: trading list
        """
        week_days = self.resize_rule.week_rules(delta)
        return week_days

    def freq_by_month(self, delta):
        """
        :param delta: int ,the number day of month (max -- 31) which is trading_day
        :return: trading list
        """
        month_days = self.resize_rule.month_rules(delta)
        return month_days

    @staticmethod
    def get_current_minutes(sid):
        """
            return current live tickers data
        """
        _url = 'http://push2.eastmoney.com/api/qt/stock/trends2/get?fields1=f1&' \
               'fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&secid={}'
        # 处理数据
        req_sid = '0.' + sid if sid.startswith('6') else '1.' + sid
        req_url = _url.format(req_sid)
        obj = _parse_url(req_url, bs=False)
        d = json.loads(obj)
        raw_array = [item.split(',') for item in d['data']['trends']]
        minutes = pd.DataFrame(raw_array, columns=['ticker', 'open', 'close', 'high',
                                                   'low', 'volume', 'turnover', 'avg'])
        return minutes

    @staticmethod
    def get_equities_pledge(symbol):
        frame = tsclient.to_ts_pledge(symbol)
        return frame


if __name__ == '__main__':

    data_portal = DataPortal()
    sessions = ['2017-03-01', '2020-09-07']
    assets = [Equity('000002'), Equity('300360')]
    fields = ['open', 'close']
    # window_data = data_portal.get_window_data(assets, sessions[1],
    #                                           days_in_window=300, field=fields, data_frequency='daily')
    # print('window_data', window_data)
    # history_data = data_portal.get_history_window(assets, sessions[1],
    #                                               bar_count=300, field=fields, data_frequency='daily')
    # print('history_data', history_data)
    # spot_value = data_portal.get_spot_value(assets[0], '2020-09-03', 'daily', ['close', 'low'])
    # print('spot_value', spot_value)
    # divdends = data_portal.get_dividends_for_asset(assets[1], '2017-05-25')
    # print('divdends', divdends)
    # rights = data_portal.get_rights_for_asset(assets[0], '2000-01-24')
    # print('rights', rights)
    # open_pct = data_portal.get_open_pct(assets, '2020-09-03')
    # print('open_pct', open_pct)
    window_data = data_portal.get_window_data(assets, sessions[1],
                                              days_in_window=300, field=fields, data_frequency='minute')
    print('minute_window_data', window_data)
    history_data = data_portal.get_history_window(assets, sessions[1],
                                                  bar_count=300, field=fields, data_frequency='minute')
    print('minute_history_data', history_data)
