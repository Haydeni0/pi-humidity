import csv
import datetime
from logging import error
import os
from collections import deque
from typing import Counter, Tuple
from itertools import count
import itertools
import time
import sys

import numpy as np
import scipy.ndimage

N = 10000

a = deque(range(1000))
t = time.time()
for j in range(N):
    b = getDequeLast(a, 3)
t1 = time.time()-t
t = time.time()
for j in range(N):
    c = deque(itertools.islice(a, len(a)-3, len(a)))
    c.reverse()
t2 = time.time()-t
print(b)
print(c)
print(t1)
print(t2)
pass
