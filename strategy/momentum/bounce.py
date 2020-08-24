# -*- coding : utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import numpy as np
from toolz import keyfilter, valmap
from strategy import Strategy


class Bound(Strategy):
    """
        参数： backPeriod --- 回测度量周期
              withdraw --- 回调比例
              retPeriod --- 预期时间段的收益率
              注意 backPeriod >= retPeriod ,关键点下一个迭代从哪一个时间点开始，时间交叉的比例（如果比例太大，产生的结果过度产生偏差，但是比例
              如果太小，影响样本同时分析不具有连续性
        逻辑：
            1、筛选出backPeriod的区间收益率最高的top1%
            2、计算top1%股票集的回撤幅度
            3、根据回撤幅度进行label，并计算未来的一段时间的收益率
            4、将时间推导retPeriod之后的，重复
            5、将分类结果收集，统计出最佳的回撤幅度
            6、修改backPeriod、returnPeriod进行迭代
        分析：
            1 回撤比例达到什么范围，股价在给定时间内反弹的可能性最大，由于时间越长，变数越大导致历史分析参考的依据性急剧下降
            2 回补缺口，如果短期内缺口回补了，说明向上的概率增大，惯性越大
            3 剔除上市不满半年，退市日期不足一个月--- 如果一个股票即将退市，将有公告，避免的存活偏差
            4 借鉴斐波那契数列性质
    """
    def __init__(self, params):
        # fields ,window, threshold
        self.params = params

    def _compute(self, data, kwargs):
        """
        :param data: frame
        :param kwargs:
        :return:
        """
        window_data = data.iloc[-kwargs['window', :]]
        ret = window_data['close'] - window_data['close'].shift(1)
        peak = np.argmax(data['close'])
        withdraw = (ret[-1] - ret[peak]) / ret[peak]
        return withdraw

    def compute(self, feed, mask):
        # 过滤
        data = keyfilter(lambda x: x in mask, feed)
        kwargs = self.params.copy()
        out = dict()
        for sid, frame in data.items():
            out[sid] = self._compute(frame, kwargs.pop('fields'))
        # filter threshold
        output = valmap(lambda x: x >= self.params['threshold'], out)
        # assets list
        _mask = list(output.keys())
        return _mask
