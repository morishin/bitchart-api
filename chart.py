#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import time
from enum import Enum

from bottle import request, response, route, run, static_file

DB_FILENAME = 'data.db'
IMAGE_TABLE_NAME = 'images'
IMAGE_DIR = 'images'


class Scale(Enum):
    five_min = 0
    fifteen_min = 1
    one_hour = 2
    one_day = 3


def parse_scale_param(scale_param):
    if scale_param == '15m':
        return Scale.fifteen_min
    elif scale_param == '1h':
        return Scale.one_hour
    elif scale_param == '1d':
        return Scale.one_day
    else:
        return Scale.five_min


def make_absolute_path(relative_path):
    return '{0}/{1}'.format(os.path.dirname(os.path.abspath(__file__)), relative_path)


@route('/', method='GET')
def index():
    scale_param = request.query.get('scale')
    scale = parse_scale_param(scale_param)

    connect = sqlite3.connect(make_absolute_path(DB_FILENAME))
    cursor = connect.cursor()

    try:
        cursor.execute('SELECT {0}, {1}, {2}, {3} FROM {4} \
                        ORDER BY epoch_time DESC LIMIT 1'.format(Scale.five_min.name,
                                                                 Scale.fifteen_min.name,
                                                                 Scale.one_hour.name,
                                                                 Scale.one_day.name,
                                                                 IMAGE_TABLE_NAME))
    except sqlite3.OperationalError as error:
        print(error.msg)
        abort(500, "Gomen.")

    row = cursor.fetchone()
    image_name = row[scale.value] + '.png'
    return static_file(image_name, root=make_absolute_path(IMAGE_DIR), mimetype='image/png')

if __name__ == '__main__':
    if os.environ.get('PRODUCTION') == 'true':
        run(host='0.0.0.0', port=(os.environ.get('PORT', 8080)))
    else:
        run(host='localhost', port=(os.environ.get('PORT', 8080)), debug=True, reloader=True)
