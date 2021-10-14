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


print(len(np.array([])))

# check deque maxlength feature: when using .extend with data 
# longer than maxlength, will it remove the right or left bit?

