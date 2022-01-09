import csv
import datetime
import logging
import os
from collections import deque
from typing import Counter, Tuple
from itertools import count
import time
import sys

import dask.dataframe as dd
import numpy as np
import pandas as pd

logger = logging.getLogger("testLogger")

logging_format = '%(name)s:%(levelname)s %(message)s'
logging.basicConfig(filename='asd.log', filemode='w',
                    format=logging_format, level=logging.INFO)
logger.info("aeae")
logger.warning("warning help")
a = 5
b = 0
try:
    c = a / b
except Exception as e:
    logger.exception("Exception occurred")
