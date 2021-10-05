import csv
import datetime
import os
import time
from collections import deque
from itertools import count

import dask.dataframe as dd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from utils import binSearchDatetime, decayLimits, updateQueues, smoothInterp

# filepath = "data/DHT22_data.csv"
filepath = "WindowsTest/TestData/inside.csv"
# filepath = "data/DHT22_inside.csv"

# Use a dask dataframe for better & faster memory management when reading the whole csv
data = dd.read_csv(filepath)
data["Datetime"] = dd.to_datetime(data["Datetime"])

# The amount of time history shown in the graph
history_timedelta = datetime.timedelta(minutes=6)

current_time = datetime.datetime.now()
window_start = current_time - history_timedelta

window_end_idx = len(data) - 1

if data["Datetime"].loc[0].compute().item() < window_start: 
    # Check if the desired start time 
    if window_start > data["Datetime"].loc[len(data)-1].compute().item():
        window_start_idx = window_end_idx
    else:
        # Use a binary search to find the initial start window indices
        window_start_idx = binSearchDatetime(data["Datetime"], window_start)
else:
    # If there is not enough history, start at the latest recorded date
    window_start_idx = 0

assert window_start_idx <= window_end_idx

# Use an np.array before smoothing and interpolation
D_bulk = np.array(data["Datetime"].loc[window_start_idx:window_end_idx].compute())
H_bulk = np.array(data["Humidity"].loc[window_start_idx:window_end_idx].compute())
T_bulk = np.array(data["Temperature"].loc[window_start_idx:window_end_idx].compute())

# Smooth and interpolate data, for better and faster plotting
num_interp = 1000 # Number of data points after interpolation (this increases the resolution of the line)
window_halflength = 10 # Number of array elements to use as the window halflength for moving median smoothing (this increases the smoothness of the line)
num_interp = np.min([num_interp, len(D_bulk)]) # Just in case there are fewer data than num_interp
D, H = smoothInterp(D_bulk, H_bulk, num_interp, window_halflength)
T = smoothInterp(D_bulk, T_bulk, num_interp, window_halflength)[1]
# D, H and T are deques for fast append/pop

# Remove bulk arrays from memory, otherwise they will persist for no reason
del D_bulk, H_bulk, T_bulk

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
    D_end, H_end, T_end = updateQueues(D, H, T, filepath, history_timedelta)

    # Find new y limits
    if D_end:  # If not empty
        min_H_end = np.min(np.array(H_end).astype(np.float))
        max_H_end = np.max(np.array(H_end).astype(np.float))
        if min_H_end < ylim_H[0]:
            ylim_H[0] = min_H_end - ylim_H_buffer
        if max_H_end > ylim_H[1]:
            ylim_H[1] = max_H_end + ylim_H_buffer
        min_T_end = np.min(np.array(T_end).astype(np.float))
        max_T_end = np.max(np.array(T_end).astype(np.float))
        if min_T_end < ylim_T[0]:
            ylim_T[0] = min_T_end - ylim_T_buffer
        if max_T_end > ylim_T[1]:
            ylim_T[1] = max_T_end + ylim_T_buffer

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

    time.sleep(update_interval)
