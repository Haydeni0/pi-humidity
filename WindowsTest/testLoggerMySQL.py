import datetime
import os
import time
import math
from typing import Tuple

import numpy as np
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
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"

# Data generation parameters
# Use same AR parameters for both inside and outside
log_interval = 1  # in seconds
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


inside_obs = ObsDHT(D=datetime.datetime.now(), H=80, T=20)
outside_obs = ObsDHT(
    D=datetime.datetime.now(), H=60, T=20)


def updateAR(x0: float, sigma: float, C: float, mean: float) -> float:
    # Simulate an AR(1) process
    x1 = C*(x0 - mean) + np.random.normal(0, sigma*math.sqrt(1-C*C)) + mean

    return x1


# ---- MySQL functions and connection ----

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

from DHT_MySQL_interface import ConnectDHTSQL, ObsDHT
pi_humidity_SQL = ConnectDHTSQL(connection_config)

pi_humidity_SQL.createTable(TABLE_NAME_inside)
pi_humidity_SQL.createTable(TABLE_NAME_outside)


while True:
    # Update DHT observations (using an AR(1))
    inside_obs = ObsDHT(
        D=datetime.datetime.now(),
        H=updateAR(inside_obs.H, sigma_H, C, mean_H_inside),
        T=updateAR(inside_obs.T, sigma_T, C, mean_T_inside)
    )
    outside_obs = ObsDHT(
        D=datetime.datetime.now(),
        H=updateAR(outside_obs.H, sigma_H, C, mean_H_outside),
        T=updateAR(outside_obs.T, sigma_T, C, mean_T_outside)
    )


    # Send the observation to the server
    pi_humidity_SQL.sendObservation(TABLE_NAME_inside, inside_obs)
    pi_humidity_SQL.sendObservation(TABLE_NAME_outside, outside_obs)

    time.sleep(log_interval)

