#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import urllib.request

DB_FILENAME = 'ticker.db'
TABLE_NAME = 'ticker'


def setup_database(cursor):
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS {0} (epoch_time INT, bid INT, ask INT)'.format(TABLE_NAME))
    except sqlite3.Error as error:
        print(error.msg)
        exit(1)

if __name__ == '__main__':
    connect = sqlite3.connect('{0}/{1}'.format(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME))
    cursor = connect.cursor()
    setup_database(cursor)

    with urllib.request.urlopen('https://coincheck.jp/api/ticker') as response:
        ticker = json.loads(response.read().decode('utf-8'))
        epoch_time = ticker['timestamp']
        bid = ticker['bid']
        ask = ticker['ask']
        cursor.execute('INSERT INTO {0} (epoch_time, bid, ask) VALUES ({1}, {2}, {3})'.format(TABLE_NAME, epoch_time, bid, ask))
        connect.commit()

    cursor.close()
    connect.close()
