import time
from functools import wraps
import numpy as np
from collections import deque
from itertools import count

# Timing decorator for a function
# https://stackoverflow.com/questions/1622943/timeit-versus-timing-decorator
def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        # print('func:%r args:[%r, %r] took: %2.4f sec' %
        #       (f.__name__, args, kw, te-ts))
        print(f"func:{f.__name__} took: {te-ts: 2.4f} sec")
        return result
    return wrap


def noneToNan(x):
    if x is None:
        return np.nan
    else:
        return x

def getDequeLast(data: deque, n: int) -> deque:
    # Gets the last values of the deque in reverse order
    # This is faster than using itertools.islice
    assert(n>0)
    k = count()
    last = deque()
    for d in reversed(data):
        if next(k) < n:
            last.append(d)
        else:
            break
    return last