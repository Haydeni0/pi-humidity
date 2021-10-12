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

from utils import SensorData

# filepath = "data/DHT22_inside.csv"
filepath = "WindowsTest/TestData/inside.csv"
# filepath = "WindowsTest/TestData/inside_old.csv"
# filepath = "WindowsTest/TestData/nonexistent.csv"


if not os.path.exists(filepath):
    raise FileNotFoundError(filepath)

inside_sensor = SensorData(filepath)

# Initial plot
fig = plt.figure()
ax_H = fig.add_subplot(2, 1, 1)
ax_T = fig.add_subplot(2, 1, 2)
# fig.tight_layout()
line_H, = ax_H.plot([], [])
line_T, = ax_T.plot([], [])

# Make the frametime text object
frametime_text = ax_H.text(inside_sensor.D[0], 66, "")

# Set x and y axes limits

ax_H.set_xlim(inside_sensor.D[0], inside_sensor.D[-1])
ax_T.set_xlim(inside_sensor.D[0], inside_sensor.D[-1])

ax_H.set_ylim(SensorData.ylim_H)
ax_T.set_ylim(SensorData.ylim_T)


# Draw the initial figure before setting the data
fig.canvas.draw()
plt.show(block=False)

decay_counter = count()  # Initialise counter for use with the y limit decay
update_interval = 2  # The time (seconds) to wait before each update
frametime_old = ""
while True:
    frame_start_time = time.time()

    # Update the sensor data
    inside_sensor.update()

    # Set new y limits
    ax_H.set_xlim(inside_sensor.D[0], inside_sensor.D[-1])
    ax_T.set_xlim(inside_sensor.D[0], inside_sensor.D[-1])
    ax_H.set_ylim(SensorData.ylim_H)
    ax_T.set_ylim(SensorData.ylim_T)

    # Set frametime text
    frametime_text.set_text(frametime_old)
    # Make sure the frametime counter stays in the axis limits
    frametime_text.set_x(inside_sensor.D[0])
    # Make sure the frametime counter stays in the axis limits
    frametime_text.set_y(SensorData.ylim_H[1] + 1)

    # Set new data
    line_H.set_data(inside_sensor.D, inside_sensor.H)
    line_T.set_data(inside_sensor.D, inside_sensor.T)

    # Redraw everything, as we need changing x ticks as well as the line and frametimes
    fig.canvas.draw()

    fig.canvas.flush_events()

    # Every once in a while, check if the y limits have become too large
    # And if so, slowly decay them
    # Probably have this large ish so that we dont have to run np.max/min on the whole deque too often
    decay_interval = 20
    if next(decay_counter) == int(decay_interval/update_interval):
        decay_counter = count()  # Reset counter
        SensorData.decayLimits(SensorData.ylim_H, SensorData.ylim_H_buffer, inside_sensor.H)
        SensorData.decayLimits(SensorData.ylim_T, SensorData.ylim_T_buffer, inside_sensor.T)

    # Get current frametime to display on the next frame
    frametime_old = f"Frame time (s): {time.time() - frame_start_time: 0.3f}"

    time.sleep(update_interval)
