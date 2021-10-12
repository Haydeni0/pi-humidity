import csv
import datetime
import time
import os
from collections import deque
from itertools import count
from typing import Tuple

import dask.dataframe as dd
import numpy as np
from numpy.lib.function_base import median
import pandas as pd
import scipy.signal


class SensorData:
    history_timedelta = datetime.timedelta(minutes=6)
    # assert(history_timedelta < datetime.timedelta(days=7)) # Should there be a maximum?
    # Y axes limits are also contained within this class as a static variable
    ylim_H_buffer = 5  # The amount to add on to the top and bottom of the limits
    ylim_T_buffer = 3
    # Store ylim in a list to do efficiently (don't repeatedly call max/min on the whole deque)
    ylim_H = []
    ylim_T = []
    # How many bins should there be in the datetime grid
    num_grid = 1000
    grid_resolution = history_timedelta/num_grid  # Width of one grid bin
    # Median smoothing window halfwidth
    bulk_smooth_window_halfwidth = 10
    buffer_smooth_window_halfwidth = 3
    # New data smoothing buffer size
    smooth_buffer_size = buffer_smooth_window_halfwidth + 1

    def __init__(self, filepath: str):
        self.filepath = filepath
        # These datetime grid variables are initialised in self.loadInitialData()
        # self.D_grid_edges
        # self.D_grid_centres

        # Load H and T from file
        self.H, self.T = self.loadInitialData()
        # Initialise deques to hold new data from the next bin in the future
        self.D_buffer = deque()
        self.H_buffer = deque()
        self.T_buffer = deque()

        SensorData.updateYlim(
            SensorData.ylim_H, SensorData.ylim_H_buffer, self.H)
        SensorData.updateYlim(
            SensorData.ylim_T, SensorData.ylim_T_buffer, self.T)

        # For testing purposes:
        time.sleep(2)
        self.update()

    def loadInitialData(self) -> Tuple[deque, deque]:
        # Inputs:
        #   num_thin - Number of data points after thinning (this increases the resolution
        #       of the line)
        #   window_halflength - Number of array elements to use as the window halflength for moving
        #       median smoothing (this increases the smoothness of the line)
        #
        # Outputs:
        #   (D, H, T) - Datetime, humidity and temperature deques

        current_time = datetime.datetime.now()
        window_start_time = pd.Timestamp(
            current_time - SensorData.history_timedelta)
        window_end_time = pd.Timestamp(current_time)

        # Define regular (1-dimensional) grid edges and bin centres (for datetime)
        # Leave this as an array for now, convert to deque later
        self.D_grid_edges = np.linspace(
            window_start_time.value, window_end_time.value, SensorData.num_grid + 1)
        self.D_grid_centres = 0.5 * \
            (self.D_grid_edges[:-1] + self.D_grid_edges[1:])
        # Edges of each bin in the grid
        self.D_grid_edges = pd.to_datetime(self.D_grid_edges)
        # Centre of each bin in the grid
        self.D_grid_centres = pd.to_datetime(self.D_grid_centres)

        # Find and load the data from the csv into arrays
        D_bulk, H_bulk, T_bulk = self.loadBulkData(window_start_time)

        # Allocate the correct data to each bin
        # Take the median within each bin to decide on their final values
        H, T = self.allocateToGrid(self.D_grid_edges, D_bulk, H_bulk, T_bulk)

        # Finally, convert the grid values to deques for fast pop/append
        self.D_grid_edges = deque(self.D_grid_edges)
        self.D_grid_centres = deque(self.D_grid_centres)

        return H, T

    def update(self):
        # Get new data from the csv file
        D_new, H_new, T_new = self.loadNewData()
        # Add to the buffer
        self.D_buffer.extend(D_new)
        self.H_buffer.extend(H_new)
        self.T_buffer.extend(T_new)

        current_time = datetime.datetime.now()
        new_time_elapsed = current_time - self.D_grid_edges[-1]
        num_new_bins = int(np.floor(new_time_elapsed / self.grid_resolution))
        num_new_edges = num_new_bins + 1

        # Return if no new bins need to be added
        if num_new_bins < 1:
            return

        # Remove old bins from the grid
        for _ in range(num_new_bins):
            self.D_grid_centres.popleft()
            self.D_grid_edges.popleft()
            self.H.popleft()
            self.T.popleft()

        # Calculate new grid edges (including the existing final grid edge == first grid edge here)
        new_grid_edges = np.array(
            [self.D_grid_edges[-1] + _*self.grid_resolution for _ in range(num_new_edges)])
        new_grid_centres = new_grid_edges[:-1] + 0.5*self.grid_resolution

        # Remove values to be added to the grid from the buffer
        D_add = deque()
        H_add = deque()
        T_add = deque()

        while len(self.D_buffer) >= 1 and self.D_buffer[0] < new_grid_edges[-1]:
            D_add.append(self.D_buffer.popleft())
            H_add.append(self.H_buffer.popleft())
            T_add.append(self.T_buffer.popleft())

        # Allocate new data into the new grid
        H_new_grid, T_new_grid = self.allocateToGrid(
            new_grid_edges, np.array(D_add), np.array(H_add), np.array(T_add))

        # Add these new values to the grid, and update the grid edges & centres
        self.H.extend(H_new_grid)
        self.T.extend(T_new_grid)
        self.D_grid_edges.extend(deque(new_grid_edges[1:]))
        self.D_grid_centres.extend(deque(new_grid_centres))

        # Update y limits, using the new bins
        SensorData.updateYlim(
            SensorData.ylim_H, SensorData.ylim_H_buffer, H_new_grid)
        SensorData.updateYlim(
            SensorData.ylim_T, SensorData.ylim_T_buffer, T_new_grid)

    def loadNewData(self) -> Tuple[deque, deque, deque]:
        # Load new values of D, H and T from the csv
        D_new = deque()
        H_new = deque()
        T_new = deque()
        with open(self.filepath, "r") as textfile:
            # Open and read the file in reverse order
            f_end = csv.DictReader(reversed_lines(textfile), fieldnames=[
                "Datetime", "Temperature", "Humidity"])
            while True:
                # Read line by line (from the end backwards) until we reach the date we have at the end of D
                line = next(f_end)
                D_proposed = pd.Timestamp(datetime.datetime.strptime(
                    line["Datetime"], "%Y-%m-%d %H:%M:%S"))
                H_proposed = float(line["Humidity"])
                T_proposed = float(line["Temperature"])
                if D_proposed <= self.D_grid_edges[-1]:
                    break
                else:
                    D_new.appendleft(D_proposed)
                    H_new.appendleft(H_proposed)
                    T_new.appendleft(T_proposed)

        return D_new, H_new, T_new

    def allocateToGrid(self, grid_edges: pd.DatetimeIndex, D_bulk: np.array, H_bulk: np.array, T_bulk: np.array) -> Tuple[deque, deque]:
        # By construction, D_bulk should all be greater than grid_edges[0]
        # Throw an error otherwise
        # Add a small timedelta to compare these float values approximately
        assert(D_bulk[0] >= grid_edges[0] -
               datetime.timedelta(seconds=0.01))

        num_grid = len(grid_edges) - 1

        # Find indices of the data that fall in each bin
        bin_data_idx = []
        for bin_idx in range(num_grid):
            data_indices_above = grid_edges[bin_idx] <= D_bulk
            if bin_idx < num_grid-1:
                data_indices_below = D_bulk < grid_edges[bin_idx+1]
            else:
                data_indices_below = D_bulk <= grid_edges[bin_idx+1]

            bin_data_idx.append(np.where(np.logical_and(
                data_indices_above, data_indices_below))[0])

        # Fill in each bin with one value, by using the median within each bin
        def fillGrid(bin_data_idx: list, data: np.array) -> deque:
            grid = deque()
            for bin_idx in range(num_grid):
                bin_input = data[bin_data_idx[bin_idx]]
                bin_input = np.median(bin_input)
                grid.append(bin_input)

            return grid

        H = fillGrid(bin_data_idx, H_bulk)
        T = fillGrid(bin_data_idx, T_bulk)

        return H, T

    def loadBulkData(self, window_start_time: pd.Timestamp) -> Tuple[np.array, np.array, np.array]:
        # Load the bulk data from file after a specified time
        data = dd.read_csv(self.filepath)
        data["Datetime"] = dd.to_datetime(data["Datetime"])

        within_window_end_idx = len(data) - 1
        if data["Datetime"].loc[0].compute().item() < window_start_time:
            # Check if the desired start time
            if window_start_time > data["Datetime"].loc[len(data)-1].compute().item():
                within_window_start_idx = within_window_end_idx
            else:
                # Use a binary search to find the initial start window indices
                within_window_start_idx = binSearchDatetime(
                    data["Datetime"], window_start_time)
        else:
            # If there is not enough history, start at the latest recorded date
            within_window_start_idx = 0

        assert within_window_start_idx <= within_window_end_idx

        # Return as an np.array
        D_bulk = np.array(
            data["Datetime"].loc[within_window_start_idx:within_window_end_idx].compute())
        H_bulk = np.array(
            data["Humidity"].loc[within_window_start_idx:within_window_end_idx].compute())
        T_bulk = np.array(
            data["Temperature"].loc[within_window_start_idx:within_window_end_idx].compute())

        return D_bulk, H_bulk, T_bulk

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
        data_min = np.nanmin(data)
        data_max = np.nanmax(data)
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
            L_idx = R_idx

        idx_width = R_idx - L_idx

    return int(R_idx)


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
