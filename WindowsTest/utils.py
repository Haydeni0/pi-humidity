import csv
import datetime
import os
from collections import deque
from typing import Tuple

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.signal


def binSearchDatetime(
    Datetime: dd.core.Series, target_datetime: datetime.datetime
) -> int:
    # Searches the dask list for the index of the greatest time smaller than target_datetime
    # Inputs:
    # - Datetime (Sorted list of datetime.datetime objects, in dask series format)
    # - target_datetime (datetime.datetime)
    #
    # Outputs:
    # - L_idx (int) - Index of the greatest datetime in the list smaller than target_datetime

    #  Assume that Datetime is already sorted
    L_idx = 0
    R_idx = len(Datetime) - 1
    L = Datetime.loc[L_idx].compute().item()
    R = Datetime.loc[R_idx].compute().item()

    idx_width = R_idx - L_idx

    # The date we are searching for must be within the left and right limits
    assert L < target_datetime < R

    # Binary search
    while idx_width > 1:
        M_idx = np.ceil(np.mean([L_idx, R_idx]))
        M = Datetime.loc[M_idx].compute().item()

        if M > target_datetime:
            R_idx = M_idx
        elif M < target_datetime:
            L_idx = M_idx
        elif M == target_datetime:
            R_idx = M_idx
            L_idx = M_idx
        elif Datetime.loc[L_idx].compute().item() == target_datetime:
            R_idx = L_idx

        idx_width = R_idx - L_idx

    return int(L_idx)


# Based on SO post https://stackoverflow.com/questions/10933838/how-to-read-a-csv-file-in-reverse-order-in-python
#################################################################################################################
def reversed_lines(f):
    # Generate the lines of file in reverse order
    part = ""
    for block in reversed_blocks(f):
        for c in reversed(block):
            if c == "\n" and part:
                yield part[::-1]
                part = ""
            part += c
    if part:
        yield part[::-1]


def reversed_blocks(f, blocksize=4096):
    # Generate blocks of file's contents in reverse order
    f.seek(0, os.SEEK_END)
    here = f.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        f.seek(here, os.SEEK_SET)
        yield f.read(delta)
#################################################################################################################


def decayLimits(timeseries: deque, ylim: list, ylim_decay: float, ylim_buffer: float):
    # Decays ylim (mutate)
    ideal_ymin = np.min(np.array(timeseries).astype(np.float)) - ylim_buffer
    ideal_ymax = np.max(np.array(timeseries).astype(np.float)) + ylim_buffer
    if ideal_ymin > ylim[0]:
        ylim[0] = ylim[0] + ylim_decay*abs(ylim[0] - ideal_ymin)

    if ideal_ymax < ylim[1]:
        ylim[1] = ylim[1] - ylim_decay*abs(ylim[1] - ideal_ymax)


def updateQueues(D: deque, H: deque, T: deque, filepath: str, history_timedelta: datetime.timedelta) -> Tuple[deque, deque, deque]:
    # Update D, H and T (passed by reference) from the csv file
    # Also return the new additions to D, H and T (e.g. if we want to use them to update ylim)
    with open(filepath, "r") as textfile:
        # Open and read the file in reverse order
        f_end = csv.DictReader(reversed_lines(textfile), fieldnames=[
                               "Datetime", "Temperature", "Humidity"])
        D_end = deque()
        H_end = deque()
        T_end = deque()
        while True:
            # Read line by line (from the end backwards) until we reach the date we have at the end of D
            line = next(f_end)
            D_proposed = pd.Timestamp(datetime.datetime.strptime(
                line["Datetime"], "%Y-%m-%d %H:%M:%S"))
            H_proposed = float(line["Humidity"])
            T_proposed = float(line["Temperature"])
            if D_proposed <= D[-1]:
                D.extend(D_end)
                H.extend(H_end)
                T.extend(T_end)
                break
            else:
                D_end.appendleft(D_proposed)
                H_end.appendleft(H_proposed)
                T_end.appendleft(T_proposed)

    # Remove old values from D
    old_time = datetime.datetime.now() - history_timedelta
    while D[0] < old_time and len(D) > 1:
        D.popleft()
        H.popleft()
        T.popleft()
    return D_end, H_end, T_end  # Return the new deques


def smoothInterp(t: np.array, x: np.array, n: int, window_halflength: int) -> Tuple[deque, deque]:
    # Given values x occurring at times t, interpolate regularly between the start and end times and smooth to give a deque of length n
    # Use moving average smoothing (median)
    # The window_halflength is the half length of the window used for the moving average
    assert(len(t) == len(x))
    N = len(t)
    assert(N >= n)

    # Subset the indices evenly
    idx = np.linspace(0, N-1, n, dtype=int)
    T = deque(pd.to_datetime(t[idx]))
    X = deque(scipy.signal.medfilt(x, 2*window_halflength+1)[idx])

    return T, X
