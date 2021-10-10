import csv
import datetime
import os
from collections import deque
from typing import Tuple

import dask.dataframe as dd
import numpy as np
import pandas as pd
import scipy.signal


class SensorData:
    history_timedelta = datetime.timedelta(minutes=6)
    # Y axes limits are also contained within this class as a static variable
    ylim_H_buffer = 5  # The amount to add on to the top and bottom of the limits
    ylim_T_buffer = 3
    # Store ylim in a list to do efficiently (don't repeatedly call max/min on the whole deque)
    ylim_H = []
    ylim_T = []
    # What length should the data be, after thinning
    ideal_length = 1000
    # Median smoothing window halfwidth 
    bulk_smooth_window_halfwidth = 10
    buffer_smooth_window_halfwidth = 3
    # New data smoothing buffer size
    smooth_buffer_size = buffer_smooth_window_halfwidth + 1

    def __init__(self, filepath: str):
        self.filepath = filepath
        # Load D, H and T from file, also keep track of the length of these data
        self.D, self.H, self.T, self.length = self.loadInitialData()
        # Initialise deques to hold unsmoothed new data
        self.D_buffer = deque()
        self.H_buffer = deque()
        self.T_buffer = deque()

        SensorData.updateYlim(
            SensorData.ylim_H, SensorData.ylim_H_buffer, self.H)
        SensorData.updateYlim(
            SensorData.ylim_T, SensorData.ylim_T_buffer, self.T)

    def loadInitialData(self) -> Tuple[deque, deque, deque, int]:
        # Inputs:
        #   num_thin - Number of data points after thinning (this increases the resolution
        #       of the line)
        #   window_halflength - Number of array elements to use as the window halflength for moving
        #       median smoothing (this increases the smoothness of the line)
        #
        # Outputs:
        #   (D, H, T) - Datetime, humidity and temperature deques

        data = dd.read_csv(self.filepath)
        data["Datetime"] = dd.to_datetime(data["Datetime"])

        current_time = datetime.datetime.now()
        window_start = current_time - SensorData.history_timedelta

        window_end_idx = len(data) - 1

        if data["Datetime"].loc[0].compute().item() < window_start:
            # Check if the desired start time
            if window_start > data["Datetime"].loc[len(data)-1].compute().item():
                window_start_idx = window_end_idx
            else:
                # Use a binary search to find the initial start window indices
                window_start_idx = binSearchDatetime(
                    data["Datetime"], window_start)
        else:
            # If there is not enough history, start at the latest recorded date
            window_start_idx = 0

        assert window_start_idx <= window_end_idx

        # Use an np.array before smoothing and thinning
        D_bulk = np.array(
            data["Datetime"].loc[window_start_idx:window_end_idx].compute())
        H_bulk = np.array(
            data["Humidity"].loc[window_start_idx:window_end_idx].compute())
        T_bulk = np.array(
            data["Temperature"].loc[window_start_idx:window_end_idx].compute())

        # Smooth and thin data, for better and faster plotting
        # Just in case there are fewer data than num_thin
        num_thin = np.min([SensorData.ideal_length, len(D_bulk)])
        D, H = smoothThin(D_bulk, H_bulk, num_thin, SensorData.bulk_smooth_window_halfwidth)
        T = smoothThin(D_bulk, T_bulk, num_thin, SensorData.bulk_smooth_window_halfwidth)[1]
        # D, H and T are deques for fast append/pop

        length = num_thin  # Length of the deques

        return D, H, T, length

    def update(self):
        # Update D, H and T (passed by reference) from the csv file
        # Also return the new additions to D, H and T (e.g. if we want to use them to update ylim)
        with open(self.filepath, "r") as textfile:
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
                if D_proposed <= self.D[-1]:
                    break
                else:
                    D_end.appendleft(D_proposed)
                    H_end.appendleft(H_proposed)
                    T_end.appendleft(T_proposed)

        # Remove old values from D
        old_time = datetime.datetime.now() - SensorData.history_timedelta
        while self.D[0] < old_time and self.length > 1:
            self.D.popleft()
            self.H.popleft()
            self.T.popleft()
            self.length -= 1

        # self.D_buffer.extend(D_end)
        # self.H_buffer.extend(H_end)
        # self.T_buffer.extend(T_end)

        if len(D_end) >= 1:
            # Update deques (once smoothed)
            self.D.extend(D_end)
            self.H.extend(H_end)
            self.T.extend(T_end)
            self.length += len(D_end)

            # Update y limits, using the smaller ._end deques
            SensorData.updateYlim(
                SensorData.ylim_H, SensorData.ylim_H_buffer, H_end)
            SensorData.updateYlim(
                SensorData.ylim_T, SensorData.ylim_T_buffer, T_end)

    @staticmethod
    def decayLimits(ylim: list, buffer: float, *data: deque):
        # Decays ylim (mutate)
        # Allows input of multiple sets of data, eg. decayLimits(ylim, buffer, H_inside, H_outside, ...)
        ylim_decay = 0.1  # Proportion to decay each time

        assert(len(data) >= 1)
        ymin = min(data[0])
        ymax = max(data[0])
        if len(data) >= 2:
            for d in data[1:]:
                ymin = max(ymin, max(d))
                ymax = max(ymax, max(d))

        ymin -= buffer
        ymax += buffer
        if ymin > ylim[0]:
            ylim[0] = ylim[0] + ylim_decay*abs(ylim[0] - ymin)
        if ymax < ylim[1]:
            ylim[1] = ylim[1] - ylim_decay*abs(ylim[1] - ymax)

    @staticmethod
    def updateYlim(ylim: list, buffer: int, data: deque):
        # data is a deque of floats
        # Since ylim is a list, it is mutated within this function
        data_min = min(data)
        data_max = max(data)
        if len(ylim) == 0:
            ylim.clear()
            ylim.append(data_min - buffer)
            ylim.append(data_max + buffer)
        else:
            if data_min < ylim[0]:
                ylim[0] = data_min - buffer
            if data_max > ylim[1]:
                ylim[1] = data_max + buffer





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


def smoothThin(t: np.array, x: np.array, num_thin: int, window_halflength: int, *, start: int = 0) -> Tuple[deque, deque]:
    # Given values x occurring at times t, thinning regularly between the start and end times and
    # smooth to give a deque of length num_thin
    # Use moving average smoothing (median), as the data can have spikes
    # The window_halflength is the half length of the window used for the moving average
    N = len(t)
    assert(0 <= start < N)
    assert(N == len(x))
    assert(N-start >= num_thin)

    # Subset the indices evenly
    idx = np.linspace(start, N-1, num_thin, dtype=int)
    T = deque(pd.to_datetime(t[idx]))
    X = deque(scipy.signal.medfilt(x, 2*window_halflength+1)[idx])

    return T, X
