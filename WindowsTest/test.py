import csv
import datetime
import os
from collections import deque
from typing import Tuple

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.signal


history_timedelta = datetime.timedelta(minutes=6)

current_time = datetime.datetime.now()
before_time = current_time - history_timedelta

start = pd.Timestamp(current_time)
end = pd.Timestamp(before_time)
t = np.linspace(start.value, end.value, 10)
t = pd.to_datetime(t)

print(t)