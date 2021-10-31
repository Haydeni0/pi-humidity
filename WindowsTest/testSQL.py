import datetime
import inspect
import os
import sys
from typing import Tuple

import numpy as np

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from DHT_MySQL_interface import DHTConnection, ObsDHT

HaydensPC_connection_config = {
    "host": 'localhost',
    "database": "test_pi_humidity",
    "user": "haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

DHT_db = DHTConnection(HaydensPC_connection_config, True)

# obs = ObsDHT(datetime.datetime.now(), None, None)
# # obs = ObsDHT(datetime.datetime.now(), 80, 20)

# DHT_db.sendObservation("dht_inside", obs)

queried_obs = DHT_db.getObservations("dht_inside", datetime.datetime.now()-datetime.timedelta(hours=1), datetime.datetime.now())

print(queried_obs)