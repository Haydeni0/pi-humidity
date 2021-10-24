import csv
import datetime
from logging import error
import os
from collections import deque
from typing import Counter, Tuple
from itertools import count
import time
import sys

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.signal
from utils import timing


# Based on examples
# https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

from DHT_MySQL_interface import ConnectDHTSQL, ObsDHT

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

pi_humidity_SQL = ConnectDHTSQL(connection_config)



def getLatestObservations():

    current_time = datetime.datetime.now()
    history_timedelta = datetime.timedelta(seconds=3)

    start_dtime = current_time - history_timedelta
    end_dtime = current_time

    return pi_humidity_SQL.getObservations("dht_outside", start_dtime, end_dtime)


print(getLatestObservations())


pass
