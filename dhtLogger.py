import datetime
import logging
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
    "user": "haydeni0",
    "password": "raspizeroWH_SQL",
    'raise_on_warnings': True
}
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"

log_interval = 2 # in seconds

# Try to connect to the server, and retry if fail
for j in range(10):
    try:
        pi_humidity_SQL = DHTConnection(connection_config)
        break
    except:
        time.sleep(5)
        continue

# If we need to create a new table
# pi_humidity_SQL.createTable(TABLE_NAME_inside)
# pi_humidity_SQL.createTable(TABLE_NAME_outside)

# Set up error logging
logger = logging.getLogger("dhtLoggerErrorLogger")
logging_format = '%(name)s:%(levelname)s %(message)s'
logging.basicConfig(filename='dhtLogger.log', filemode='w',
                    format=logging_format, level=logging.WARNING)


while True:

    # Read from the sensor
    H_inside, T_inside, H_outside, T_outside = DHTutils.read_retry_inout(DHT_SENSOR, DHT_PIN_INSIDE, DHT_PIN_OUTSIDE)

    # Put observations into an ObsDHT struct 
    current_time = datetime.datetime.now()
    inside_obs = ObsDHT(
        D=current_time,
        H=H_inside,
        T=T_inside
    )
    outside_obs = ObsDHT(
        D=current_time,
        H=H_outside,
        T=T_outside
    )

    # Send the observations to the server
    try:
        pi_humidity_SQL.sendObservation(TABLE_NAME_inside, inside_obs, ignore_insert_error=True)
        pi_humidity_SQL.sendObservation(TABLE_NAME_outside, outside_obs, ignore_insert_error=True)
    except Exception as e:
        logger.exception("Failed to send dht observation to MySQL server")

    # Wait between sensor readings
    time.sleep(log_interval)
