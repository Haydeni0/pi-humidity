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

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

DB_NAME = "pi_humidity"
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"


def createTableDHT(cursor, TABLE_NAME):
    try:
        cursor.execute(
            f"CREATE TABLE {TABLE_NAME} (`id` INT NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY, dtime DATETIME, humidity FLOAT, temperature FLOAT);"
        )
    except Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("Table exists")
        else:
            print(err)


try:
    # Connect to server and database
    cnx = mysql.connector.connect(**connection_config)

    db_Info = cnx.get_server_info()
    print("Connected to MySQL Server version ", db_Info)
    cursor = cnx.cursor()
    cursor.execute("select database();")
    record = cursor.fetchone()
    print("Connected to database: ", record[0])
    print("="*100)

    createTableDHT(cursor, TABLE_NAME_inside)
    createTableDHT(cursor, TABLE_NAME_outside)

except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    cnx.close()
    print("_"*100)
    print("MySQL connection closed")
