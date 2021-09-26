# %matplotlib notebook
import dask.dataframe as dd
import pandas as pd
import csv
from collections import deque
import numpy as np

import os
import time
import datetime
from itertools import count

from typing import Tuple

from utils import binSearchDatetime, reversed_lines

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# filepath = "data/DHT22_data.csv"
filepath = "WindowsTest/TestData.csv"

# Use a dask dataframe for better & faster memory management when reading the whole csv
data = dd.read_csv(filepath)
data["Datetime"] = dd.to_datetime(data["Datetime"])

# The amount of time history shown in the graph
history_window = datetime.timedelta(seconds=20)

current_time = datetime.datetime.now()
window_end = current_time
window_start = window_end - history_window
# Use a binary search to find the initial start window indices
window_start_idx = binSearchDatetime(data["Datetime"], window_start)
window_end_idx = len(data) - 1
assert window_start_idx < window_end_idx

# Use a deque for fast append/pop
D = deque(data["Datetime"].loc[window_start_idx:window_end_idx].compute())
H = deque(data["Humidity"].loc[window_start_idx:window_end_idx].compute())
T = deque(data["Temperature"].loc[window_start_idx:window_end_idx].compute())

# Initial plot
fig, ax = plt.subplots()
(l,) = ax.plot(D, H)

# Set x and y axes limits
ax.set_xlim(D[0], D[-1])
ylim = [np.min(H), np.max(H)] # Store ylim in a list to do efficiently (don't repeatedly call max/min)
ax.set_ylim(ylim)


def updateQueues() -> Tuple[deque, deque, deque]:
    # Update D, H and T from the csv file
    # Also return the new additions to D, H and T (e.g. if we want to use them to update ylim)
    with open(filepath, "r") as textfile:
        # Open and read the file in reverse order
        f_end = csv.DictReader(reversed_lines(textfile), fieldnames=["Datetime", "Temperature", "Humidity"])
        D_end = deque()
        H_end = deque()
        T_end = deque()
        while True:
            # Read line by line (from the end backwards) until we reach the date we have at the end of D
            line = next(f_end)
            D_proposed = pd.Timestamp(datetime.datetime.strptime(line["Datetime"], "%Y-%m-%d %H:%M:%S"))
            H_proposed = line["Humidity"]
            T_proposed = line["Temperature"]
            if D_proposed <= D[-1]:
                D.extend(D_end)
                H.extend(H_end)
                T.extend(T_end)
                return D_end, H_end, T_end # Return the newly added deques
            else:
                D_end.appendleft(D_proposed)
                H_end.appendleft(H_proposed)
                T_end.appendleft(T_proposed)
                

# plt.show()
while True:
    D_end, H_end, T_end = updateQueues()
    l.set_data(D, H) # Can I append to l instead of setting?

    # Set new limits
    if D_end: # If not empty
        ax.set_xlim(D[0], D[-1])
        min_H_end = np.min(np.array(H_end).astype(np.float))
        max_H_end = np.max(np.array(H_end).astype(np.float))
        if min_H_end < ylim[0]:
            ylim[0] = min_H_end
        if max_H_end > ylim[1]:
            ylim[1] = max_H_end
        ax.set_ylim(ylim)

    plt.pause(0.5)
    



# plt.axis([0, 10, 0, 1])

# for i in range(10000):
#     updatePlot(i)
#     plt.pause(0.01)

# plt.show()
# updatePlot(data)

