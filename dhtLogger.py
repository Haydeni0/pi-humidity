import datetime
import os
import time

import Adafruit_DHT

import DHTutils
import utils
from DHT_MySQL_interface import DHTConnection, ObsDHT

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN_INSIDE = 4
DHT_PIN_OUTSIDE = 27

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "root",
    "password": "raspizeroWH_SQL",
    'raise_on_warnings': True
}
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"

log_interval = 2 # in seconds

pi_humidity_SQL = DHTConnection(connection_config)

pi_humidity_SQL.createTable(TABLE_NAME_inside)
pi_humidity_SQL.createTable(TABLE_NAME_outside)


while True:

    # Read from the sensor
    H_inside, T_inside, H_outside, T_outside = DHTutils.read_retry_inout(DHT_SENSOR, DHT_PIN_INSIDE, DHT_PIN_OUTSIDE)

    # Put observations into an ObsDHT struct 
    current_time = datetime.datetime.now()
    inside_obs = ObsDHT(
        D=current_time,
        H=utils.noneToNan(H_inside),
        T=utils.noneToNan(T_inside)
    )
    outside_obs = ObsDHT(
        D=current_time,
        H=utils.noneToNan(H_outside),
        T=utils.noneToNan(T_outside)
    )

    # Send the observations to the server
    pi_humidity_SQL.sendObservation(TABLE_NAME_inside, inside_obs)
    pi_humidity_SQL.sendObservation(TABLE_NAME_outside, outside_obs)

    # Wait between sensor readings
    time.sleep(log_interval)
