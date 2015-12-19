#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sqlite3
import time
from io import BytesIO

import matplotlib.dates as dt
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import pandas.io.sql as psql
import pytz
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.finance import candlestick_ohlc
from matplotlib.ticker import MultipleLocator

from bottle import request, response, route, run

DB_FILENAME = 'ticker.db'
TABLE_NAME = 'ticker'


def setup_database(cursor):
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS {0} (epoch_time INT, bid INT, ask INT)'.format(TABLE_NAME))
    except sqlite3.Error as error:
        print(error.msg)


def get_scale_in_minute(scale_param):
    default_scale = 5
    default_scale_text = '5min'
    scale_in_minute = default_scale
    scale_text = default_scale_text

    if scale_param is not None:
        minute_match = re.compile('(\d+)m').match(scale_param)
        hour_match = re.compile('(\d+)h').match(scale_param)
        day_match = re.compile('(\d+)d').match(scale_param)
        if minute_match is not None:
            minutes = int(minute_match.group(1))
            scale_in_minute = minutes
            scale_text = '{0}min'.format(minutes)
        elif hour_match is not None:
            hours = int(hour_match.group(1))
            scale_in_minute = hours * 60
            scale_text = '{0}min'.format(hours)
        elif day_match is not None:
            days = int(day_match.group(1))
            scale_in_minute = days * 24 * 60
            scale_text = '{0}day'.format(days)

    return (scale_in_minute, scale_text)


@route('/', method='GET')
def index():
    scale_param = request.query.get('scale')
    scale_in_minute, scale_text = get_scale_in_minute(scale_param)

    connect = sqlite3.connect('{0}/{1}'.format(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME))
    cursor = connect.cursor()
    setup_database(cursor)

    current_time = (int)(time.time())
    time_range_min = current_time - scale_in_minute * 60 * 150
    df = psql.read_sql('SELECT epoch_time, bid FROM {0} WHERE epoch_time > {1}'.format(TABLE_NAME, time_range_min), connect)
    connect.close()
    df.epoch_time = pd.to_datetime(df.epoch_time, unit='s')
    df.set_index('epoch_time', inplace=True)

    ohlc = df.bid.resample('{0}Min'.format(scale_in_minute), how='ohlc')
    ohlc['date_num'] = ohlc.index.map(dt.date2num)

    fig, ax = plt.subplots()
    fig.set_size_inches(12, 4)
    fig.patch.set_facecolor('white')
    plt.subplots_adjust(left=0.02, top=0.9, right=0.85, bottom=0.15)
    ax.set_title(scale_text)
    timezone_name = os.environ.get('TIME_ZONE', 'UTC')
    timezone = pytz.timezone(timezone_name)
    ax.xaxis.set_minor_formatter(dt.DateFormatter('%H:%M', timezone))
    ax.xaxis.set_minor_locator(dt.MinuteLocator(interval=scale_in_minute*10))
    ax.xaxis.set_major_formatter(dt.DateFormatter('\n%m/%d', timezone))
    ax.xaxis.set_major_locator(dt.DayLocator(interval=1))
    ax.yaxis.set_ticks_position('right')
    candlestick_ohlc(ax, ohlc[['date_num', 'open', 'high', 'low', 'close']].values, width=1.0/24/60*scale_in_minute, colorup='g', alpha =0.4)

    canvas = FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    response.content_type = 'image/png'
    return png_output.getvalue()

if __name__ == '__main__':
    if os.environ.get('PRODUCTION') == 'true':
        run(host='0.0.0.0', port=(os.environ.get('PORT', 8080)))
    else:
        run(host='localhost', port=(os.environ.get('PORT', 8080)), debug=True, reloader=True)
