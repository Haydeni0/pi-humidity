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
history_timedelta = datetime.timedelta(minutes=10)

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
    return D_end, H_end, T_end  # Return the newly added deques


# Initial plot
fig = plt.figure()
ax_H = fig.add_subplot(2, 1, 1)
ax_T = fig.add_subplot(2, 1, 2)
# fig.tight_layout()
line_H, = ax_H.plot([], [])
line_T, = ax_T.plot([], [])

# Make the frametime text object
frametime_text = ax_H.text(D[0], 66, "")

# Set x and y axes limits
ylim_H_buffer = 5  # The amount to add on to the top and bottom of the limits
ylim_T_buffer = 3
ax_H.set_xlim(D[0], D[-1])
ax_T.set_xlim(D[0], D[-1])
# Store ylim in a list to do efficiently (don't repeatedly call max/min on the whole deque)
ylim_H = [np.min(H) - ylim_H_buffer, np.max(H) + ylim_H_buffer]
ylim_T = [np.min(T) - ylim_T_buffer, np.max(T) + ylim_T_buffer]
ax_H.set_ylim(ylim_H)
ax_T.set_ylim(ylim_T)


# Draw the initial figure before setting the data
fig.canvas.draw()
plt.show(block=False)

decay_counter = count()  # Initialise counter for use with the y limit decay
update_interval = 2  # The time (seconds) to wait before each update
frametime_old = ""
while True:
    frame_start_time = time.time()

    # Get new data from the csvs if there are any
    D_end, H_end, T_end = updateQueues(history_timedelta)

    # Find new y limits
    if D_end:  # If not empty
        min_H_end = np.min(np.array(H_end).astype(np.float))
        max_H_end = np.max(np.array(H_end).astype(np.float))
        if min_H_end < ylim_H[0]:
            ylim_H[0] = min_H_end - ylim_H_buffer
        if max_H_end > ylim_H[1]:
            ylim_H[1] = max_H_end + ylim_H_buffer

    # Set new y limits
    ax_H.set_xlim(D[0], D[-1])
    ax_T.set_xlim(D[0], D[-1])
    ax_H.set_ylim(ylim_H)
    ax_T.set_ylim(ylim_T)

    # Set frametime text
    frametime_text.set_text(frametime_old)
    # Make sure the frametime counter stays in the axis limits
    frametime_text.set_x(D[0])
    # Make sure the frametime counter stays in the axis limits
    frametime_text.set_y(ylim_H[1] + 1)

    # Set new data
    line_H.set_data(D, H)
    line_T.set_data(D, T)

    # Redraw just the points
    # ax_H.draw_artist(line_H)
    # ax_T.draw_artist(line_T)
    # ax_H.draw_artist(frametime_text)

    # Redraw everything, as we need changing x ticks as well as the line and frametimes
    fig.canvas.draw()

    fig.canvas.flush_events()

    # Every once in a while, check if the y limits have become too large
    # And if so, slowly decay them
    # Probably have this large ish so that we dont have to run np.max/min on the whole deque too often
    decay_interval = 20
    ylim_decay = 0.1  # Proportion to decay each time
    if next(decay_counter) == int(decay_interval/update_interval):
        decay_counter = count()  # Reset counter
        decayLimits(H, ylim_H, ylim_decay, ylim_H_buffer)
        decayLimits(T, ylim_T, ylim_decay, ylim_T_buffer)

    # Get current frametime to display on the next frame
    frametime_old = f"Frame time (s): {time.time() - frame_start_time: 0.3f}"

    # time.sleep(update_interval)
