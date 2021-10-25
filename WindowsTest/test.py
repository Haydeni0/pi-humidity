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
import scipy.signal
from utils import timing


a = np.searchsorted([1,5,10], [], side="right")



print(a)
print(a[0])
pass
