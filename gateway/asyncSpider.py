# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import asyncio
from gateway.spider.asset_router import AssetRouterWriter
from gateway.spider.bundle import BundlesWriter
from gateway.spider.divdend_rights import AdjustmentsWriter
from gateway.spider.ownership import OwnershipWriter
from gateway.spider.events import EventWriter


# 初始化各个spider module
router_writer = AssetRouterWriter()
adjust_writer = AdjustmentsWriter()
ownership_writer = OwnershipWriter()
event_writer = EventWriter()


async def router_spider():
    router_writer.writer()


async def kline_spider(flag):
    bundle_writer = BundlesWriter(None if flag else 1)
    bundle_writer.writer()


async def splits_spider():
    adjust_writer.writer()


async def event_spider(flag):
    date = '2000-01-01' if flag else None
    await asyncio.sleep(10)
    event_writer.writer(date)


async def main(initialization=True):

    await router_spider()
    await kline_spider(initialization)
    await splits_spider()
    await event_spider(initialization)
    # from gateway.driver._ext_mkt import MarketValue
    # mcap_writer = MarketValue(initialization)
    # mcap_writer.calculate_mcap()


if __name__ == '__main__':

    # asyncio.run(main(None))
    # event_loop 导致cannot start new thread
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(False))
    loop.close()
