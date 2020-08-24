# -*- coding : utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
from strategy import Strategy


class SLTrading(Strategy):
    """
        主要针对于ETF或者其他的自定义指数
        度量动量配对交易策略凸优化(Convex Optimization)
        1、etf 国内可以卖空
        2、构建一个协整关系的组合与etf 进行多空交易
        逻辑：
        1、以ETF50为例，找出成分股中与指数具备有协整关系的成分股
        2、买入具备协整关系的股票集，并卖出ETF50指数
        3、如果考虑到交易成本，微弱的价差刚好覆盖成本，没有利润空间
        筛选etf成分股中与指数具备有协整关系的成分股
        将具备协整关系的成分股组合买入，同时卖出对应ETF
        计算固定周期内对冲收益率，定期去更新_coint_test

        ---- 缺少对应的ETF对应的标的集
    """

