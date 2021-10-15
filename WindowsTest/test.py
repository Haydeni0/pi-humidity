import csv
import datetime
import os
from collections import deque
from typing import Counter, Tuple
from itertools import count
import time

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.signal
from utils import timing



# check deque maxlength feature: when using .extend with data 
# longer than maxlength, will it remove the right or left bit?

d = deque(["a", "b", "c"])
a = deque([1,2,3,4,5,6,7])
print(a)
a = deque(a, maxlen=4)

print(a)

