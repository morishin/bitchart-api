#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import sqlite3
import time
import urllib.request

import pytz

import matplotlib.dates as dt
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import pandas.io.sql as psql
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.finance import candlestick_ohlc
from matplotlib.ticker import MultipleLocator

DB_FILENAME = 'data.db'
TICKER_TABLE_NAME = 'ticker'
IMAGE_TABLE_NAME = 'images'
IMAGE_DIR = 'images'


def setup_database(cursor):
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS {0} (epoch_time INT, bid INT, ask INT)'
                        .format(TICKER_TABLE_NAME))
        cursor.execute('CREATE TABLE IF NOT EXISTS {0} (epoch_time INT, five_min CHAR(32), \
                        fifteen_min CHAR(32), one_hour CHAR(32), one_day CHAR(32))'
                        .format(IMAGE_TABLE_NAME))
    except sqlite3.Error as error:
        print(error.msg)
        exit(1)

if __name__ == '__main__':
    connect = sqlite3.connect('{0}/{1}'.format(os.path.dirname(os.path.abspath(__file__))
                                , DB_FILENAME))
    cursor = connect.cursor()
    setup_database(cursor)

    with urllib.request.urlopen('https://coincheck.jp/api/ticker') as response:
        ticker = json.loads(response.read().decode('utf-8'))
        epoch_time = ticker['timestamp']
        bid = ticker['bid']
        ask = ticker['ask']
        cursor.execute('INSERT INTO {0} (epoch_time, bid, ask) VALUES ({1}, {2}, {3})'
                        .format(TICKER_TABLE_NAME, epoch_time, bid, ask))
        connect.commit()

        image_names = []
        for scale_min, scale_name in [(5, '5min'), (15, '15min'), (60, '1hour'), (60 * 24, '1day')]:
            current_time = (int)(time.time())
            time_range_sec = current_time - scale_min * 60 * 150
            df = psql.read_sql('SELECT epoch_time, bid FROM {0} WHERE epoch_time > {1}'
                                .format(TICKER_TABLE_NAME, time_range_sec), connect)
            df.epoch_time = pd.to_datetime(df.epoch_time, unit='s')
            df.set_index('epoch_time', inplace=True)

            ohlc = df.bid.resample('{0}Min'.format(scale_min), how='ohlc')
            ohlc['date_num'] = ohlc.index.map(dt.date2num)

            fig, ax = plt.subplots()
            fig.set_size_inches(12, 4)
            fig.patch.set_facecolor('white')
            plt.subplots_adjust(left=0.02, top=0.9, right=0.85, bottom=0.15)
            ax.set_title(scale_name)
            timezone_name = os.environ.get('TIME_ZONE', 'UTC')
            timezone = pytz.timezone(timezone_name)
            ax.xaxis.set_minor_formatter(dt.DateFormatter('%H:%M', timezone))
            ax.xaxis.set_minor_locator(dt.MinuteLocator(interval=scale_min*10))
            ax.xaxis.set_major_formatter(dt.DateFormatter('\n%m/%d', timezone))
            ax.xaxis.set_major_locator(dt.DayLocator(interval=1))
            ax.yaxis.set_ticks_position('right')
            candlestick_ohlc(ax, ohlc[['date_num', 'open', 'high', 'low', 'close']].values,
                             width=1.0/24/60*scale_min, colorup='g', alpha=0.4)

            digest = hashlib.md5(str(current_time + scale_min).encode()).hexdigest()
            image_names.append(digest)
            fig.savefig(IMAGE_DIR + '/' + digest + '.png')

        timestamp = (int)(time.time())
        cursor.execute('INSERT INTO {0} (epoch_time, five_min, fifteen_min, one_hour, one_day) \
                        VALUES (?, ?, ?, ?, ?)'
                        .format(IMAGE_TABLE_NAME), tuple([timestamp] + image_names))
        connect.commit()

    cursor.close()
    connect.close()
