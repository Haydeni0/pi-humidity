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



a = np.array([1,2,3, None, 4, None])
a[a == np.array(None)] = np.nan

print(a)
pass
