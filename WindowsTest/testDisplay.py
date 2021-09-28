# %matplotlib notebook
import csv
import datetime
import os
import time
from collections import deque
from itertools import count
from typing import Tuple

import dask.dataframe as dd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from utils import binSearchDatetime, reversed_lines, decayLimits

# filepath = "data/DHT22_data.csv"
filepath = "WindowsTest/TestData_inside.csv"

# Use a dask dataframe for better & faster memory management when reading the whole csv
data = dd.read_csv(filepath)
data["Datetime"] = dd.to_datetime(data["Datetime"])

# The amount of time history shown in the graph
history_timedelta = datetime.timedelta(hours=1)

current_time = datetime.datetime.now()
window_start = current_time - history_timedelta
if data["Datetime"].loc[0].compute().item() < window_start:
    # Use a binary search to find the initial start window indices
    window_start_idx = binSearchDatetime(data["Datetime"], window_start)
else:
    # If there is not enough history, start at the latest recorded date
    window_start_idx = 0

window_end_idx = len(data) - 1
assert window_start_idx < window_end_idx

# Use a deque for fast append/pop
D = deque(data["Datetime"].loc[window_start_idx:window_end_idx].compute())
H = deque(data["Humidity"].loc[window_start_idx:window_end_idx].compute())
T = deque(data["Temperature"].loc[window_start_idx:window_end_idx].compute())

def updateQueues(history_timedelta: datetime.timedelta) -> Tuple[deque, deque, deque]:
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
    return D_end, H_end, T_end # Return the newly added deques


# Initial plot
fig = plt.figure()
ax_H = fig.add_subplot(2, 1, 1)
ax_T = fig.add_subplot(2, 1, 2)
# fig.tight_layout()
line_H, = ax_H.plot(D, H)
line_T, = ax_T.plot(D, T)

# Set x and y axes limits
ylim_H_buffer = 5 # The amount to add on to the top and bottom of the limits
ylim_T_buffer = 3 
ax_H.set_xlim(D[0], D[-1])
ax_T.set_xlim(D[0], D[-1])
ylim_H = [np.min(H) - ylim_H_buffer, np.max(H) + ylim_H_buffer] # Store ylim in a list to do efficiently (don't repeatedly call max/min on the whole deque)
ylim_T = [np.min(T) - ylim_T_buffer, np.max(T) + ylim_T_buffer] 
ax_H.set_ylim(ylim_H)
ax_T.set_ylim(ylim_T)

# Draw the initial plots
fig.canvas.draw()

blit = True # Whether to use blit or not (True means faster plotting)
if blit:
    ax_H_background = fig.canvas.copy_from_bbox(ax_H.bbox)
    ax_T_background = fig.canvas.copy_from_bbox(ax_T.bbox)

plt.show(block=False)

frame_counter = count()
old_time = int(time.time())
decay_counter = count() # Initialise counter for use with the y limit decay
update_interval = 2 # The time (seconds) to wait before each update

while True:
    D_end, H_end, T_end = updateQueues(history_timedelta)

    # Find new y limits
    if D_end: # If not empty
        min_H_end = np.min(np.array(H_end).astype(np.float))
        max_H_end = np.max(np.array(H_end).astype(np.float))
        if min_H_end < ylim_H[0]:
            ylim_H[0] = min_H_end - ylim_H_buffer
        if max_H_end > ylim_H[1]:
            ylim_H[1] = max_H_end + ylim_H_buffer

    # Every once in a while, check if the y limits have become too large
    # And if so, slowly decay them
    decay_interval = 20 # Probably have this large ish so that we dont have to run np.max/min on the whole deque too often
    ylim_decay = 0.1 # Proportion to decay each time
    if next(decay_counter) == int(decay_interval/update_interval):
        decay_counter = count() # Reset counter
        decayLimits(H, ylim_H, ylim_decay, ylim_H_buffer)
        decayLimits(T, ylim_T, ylim_decay, ylim_T_buffer)

    # Set new y limits
    ax_H.set_xlim(D[0], D[-1])
    ax_T.set_xlim(D[0], D[-1])
    ax_H.set_ylim(ylim_H)
    ax_T.set_ylim(ylim_T)

    # These are the costly lines, runs at about 10 fps maybe
    #########
    # Set new data
    line_H.set_data(D, H)
    line_T.set_data(D, T)

    if blit:
        fig.canvas.restore_region(ax_H_background)
        fig.canvas.restore_region(ax_T_background)

        ax_H.draw_artist(line_H)
        ax_T.draw_artist(line_T)

        fig.canvas.blit(ax_H.bbox)
        fig.canvas.blit(ax_T.bbox)
    else:
        fig.canvas.draw()

    fig.canvas.flush_events()
    #########

    # Check FPS
    
    if old_time < int(time.time()):
        old_time = int(time.time())
        print(f"FPS: {next(frame_counter)}")
        frame_counter = count()
    else:
        next(frame_counter)

    # time.sleep(update_interval)





