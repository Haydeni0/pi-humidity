import datetime
import logging
import time

import Adafruit_DHT

import DHTutils
import utils
from database_api import DatabaseDHT, ObsDHT
import asyncio

# Set up error logging
logging.basicConfig(
    filename="/logs/dhtLogger.log",
    filemode="w",
    format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN_INSIDE = 4
DHT_PIN_OUTSIDE = 27

TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"


log_interval = 2  # in seconds

# Try to connect to the server, and retry if fail
for j in range(10):
    try:
        pi_humidity_SQL = DatabaseDHT()
        break
    except:
        time.sleep(5)
        continue
else:
    logger.error("Could not connect to server")
    raise

# Create table if it doesn't exist
pi_humidity_SQL.createTable(TABLE_NAME_inside)
pi_humidity_SQL.createTable(TABLE_NAME_outside)


try:
    while True:

        # Read from the sensor
        H_inside, T_inside, H_outside, T_outside = DHTutils.read_retry_inout(
            DHT_SENSOR, DHT_PIN_INSIDE, DHT_PIN_OUTSIDE
        )

        # Put observations into an ObsDHT struct
        current_time = datetime.datetime.now()
        inside_obs = ObsDHT(D=current_time, H=H_inside, T=T_inside)
        outside_obs = ObsDHT(D=current_time, H=H_outside, T=T_outside)

        # Send the observations to the server
        try:
            pi_humidity_SQL.sendObservation(
                TABLE_NAME_inside, inside_obs, ignore_insert_error=True
            )
            pi_humidity_SQL.sendObservation(
                TABLE_NAME_outside, outside_obs, ignore_insert_error=True
            )
        except Exception as e:
            logger.exception("Failed to send dht observation to MySQL server")

        # Wait between sensor readings
        time.sleep(log_interval)
except Exception as e:
    logger.exception("Something went wrong.........")
