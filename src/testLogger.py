import datetime
import math
import os
import time

import numpy as np

from DHT_MySQL_interface import DHTConnection, ObsDHT

SCHEMA_NAME = "test"
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"

TABLE_NAME_inside = f"{SCHEMA_NAME}.{TABLE_NAME_inside}"
TABLE_NAME_outside = f"{SCHEMA_NAME}.{TABLE_NAME_outside}"

# Data generation parameters
# Use same AR parameters for both inside and outside
log_interval = 1  # in seconds
AR_time_constant = 60 * 60  # Time constant of the AR(1) processes (in seconds)
C = math.exp(-log_interval / AR_time_constant)
sigma_H = 6
sigma_T = 3
mean_H_inside = 82
mean_T_inside = 23
mean_H_outside = 66
mean_T_outside = 22

inside_obs = ObsDHT(D=datetime.datetime.now(), H=80, T=20)
outside_obs = ObsDHT(D=datetime.datetime.now(), H=60, T=20)


def updateAR(x0: float, sigma: float, C: float, mean: float) -> float:
    # Simulate an AR(1) process
    x1 = C * (x0 - mean) + np.random.normal(0, sigma * math.sqrt(1 - C * C)) + mean

    return x1


# ---- MySQL functions and connection ----

pi_humidity_SQL = DHTConnection()

pi_humidity_SQL.createSchema(SCHEMA_NAME)
pi_humidity_SQL.createTable(TABLE_NAME_inside)
pi_humidity_SQL.createTable(TABLE_NAME_outside)


while True:
    # Update DHT observations (using an AR(1))
    inside_obs = ObsDHT(
        D=datetime.datetime.now(),
        H=updateAR(inside_obs.H, sigma_H, C, mean_H_inside),
        T=updateAR(inside_obs.T, sigma_T, C, mean_T_inside),
    )
    outside_obs = ObsDHT(
        D=datetime.datetime.now(),
        H=updateAR(outside_obs.H, sigma_H, C, mean_H_outside),
        T=updateAR(outside_obs.T, sigma_T, C, mean_T_outside),
    )

    # Send the observation to the server
    pi_humidity_SQL.sendObservation(TABLE_NAME_inside, inside_obs)
    pi_humidity_SQL.sendObservation(TABLE_NAME_outside, outside_obs)

    time.sleep(log_interval)