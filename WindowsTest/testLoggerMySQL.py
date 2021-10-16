import datetime
import os
import time
import math
from typing import Tuple

import numpy as np
from numpy.lib.twodim_base import _trilu_indices_form_dispatcher
import pandas as pd


# Based on examples
# https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

# MySQL server connection config
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

# Data generation parameters
# Use same AR parameters for both inside and outside
log_interval = 4  # in seconds
AR_time_constant = 60*60  # Time constant of the AR(1) processes (in seconds)
C = math.exp(-log_interval/AR_time_constant)
sigma_H = 6
sigma_T = 3
mean_H_inside = 82
mean_T_inside = 23
mean_H_outside = 66
mean_T_outside = 22


class ObsDHT:
    def __init__(self, *, D, H, T):
        self.D = D
        self.H = H
        self.T = T


inside_obs = ObsDHT(D=datetime.datetime.now().replace(
    microsecond=0), H=80, T=20)
outside_obs = ObsDHT(
    D=datetime.datetime.now().replace(microsecond=0), H=60, T=20)


def updateAR(x0: float, sigma: float, C: float, mean: float) -> float:
    # Simulate an AR(1) process
    x1 = C*(x0 - mean) + np.random.normal(0, sigma*math.sqrt(1-C*C)) + mean

    return x1


# ---- MySQL functions and connection ----

def createTableDHT(cursor, TABLE_NAME):
    # Function to create a table in DHT format if it doesn't already exist
    try:
        cursor.execute(
            f"CREATE TABLE {TABLE_NAME} (`id` INT NOT NULL AUTO_INCREMENT UNIQUE \
                PRIMARY KEY, dtime DATETIME, humidity FLOAT, temperature FLOAT);"
        )
    except Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print(f"Table {TABLE_NAME} exists")
        else:
            print(err)


def sendObservationDHT(cursor, TABLE_NAME, DHT: ObsDHT):
    try:
        date_formatted = datetime.datetime.strftime(DHT.D, "%Y-%m-%d %H:%M:%S")
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} (dtime, humidity, temperature)\
                VALUES ('{date_formatted}', {DHT.H:0.1f}, {DHT.T: 0.1f});"
        )
    except Error as err:
        print(err)


# Start connection
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

    while True:
        inside_obs = ObsDHT(
            D=datetime.datetime.now().replace(microsecond=0),
            H=updateAR(inside_obs.H, sigma_H, C, mean_H_inside),
            T=updateAR(inside_obs.T, sigma_T, C, mean_T_inside)
        )
        outside_obs = ObsDHT(
            D=datetime.datetime.now().replace(microsecond=0),
            H=updateAR(outside_obs.H, sigma_H, C, mean_H_outside),
            T=updateAR(outside_obs.T, sigma_T, C, mean_T_outside)
        )

        cursor.execute("START TRANSACTION;")
        sendObservationDHT(cursor, TABLE_NAME_inside, inside_obs)
        sendObservationDHT(cursor, TABLE_NAME_outside, outside_obs)
        cursor.execute("COMMIT;")

        # break
        time.sleep(log_interval)

except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
finally:
    if 'cnx' in locals():
        cnx.close()
        print("_"*100)
        print("MySQL connection closed")


# f.write(f"{current_time},{ctemperature:0.2f},{chumidity:0.2f}\n")
