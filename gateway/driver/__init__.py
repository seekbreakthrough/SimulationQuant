# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:37:47 2019

@author: python
"""
import sqlalchemy as sa

ASSET_DB_VERSION = 8
# A frozenset of the names of all tables in the asset db
# NOTE: When modifying this schema, update the ASSET_DB_VERSION value
engine_path = 'mysql+pymysql://root:macpython@localhost:3306/test01'

engine = sa.create_engine(engine_path)

metadata = sa.MetaData(bind=engine)

# 解析通达信数据存储位置
TdxDir = ''

# seconds
Seconds_Per_Day = 24 * 60 * 60

# 外围指数对应关系
lookup_benchmark = {
                '道琼斯': 'us.DJI',
                '纳斯达克': 'us.IXIC',
                '标普500': 'us.INX',
                '香港恒生指数': 'hkHSI',
                '香港国企指数': 'hkHSCEI',
                '香港红筹指数': 'hkHSCCI'
}

# h5 -- scale factor
# Retain 3 decimal places for prices.
# Volume is expected to be a whole integer.
DEFAULT_SCALING_FACTORS = {
    'open': 1000,
    'high': 1000,
    'low': 1000,
    'close': 1000,
    'volume': 1,
}
