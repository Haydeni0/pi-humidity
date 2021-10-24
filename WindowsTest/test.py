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

a = ConnectDHTSQL(connection_config)
# a.createTable("dht_outside")
# a.sendObservation("dht_outside", ObsDHT(datetime.datetime.now(), 60, 22))
pass
