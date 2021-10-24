import time
from collections import deque
from itertools import count

import dask.dataframe as dd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from utils import SensorData

from DHT_MySQL_interface import DHTConnection, ObsDHT

connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

DHT_db = DHTConnection(connection_config)

inside_sensor = SensorData(DHT_db, "dht_inside")
outside_sensor = SensorData(DHT_db, "dht_outside")

# Initial plot
fig = plt.figure()
ax_H = fig.add_subplot(2, 1, 1)
ax_T = fig.add_subplot(2, 1, 2)
# fig.tight_layout()
line_H_inside, = ax_H.plot([], [], label="Inside")
line_T_inside, = ax_T.plot([], [], label="Inside")
line_H_outside, = ax_H.plot([], [], label="Outside")
line_T_outside, = ax_T.plot([], [], label="Outside")

# Make the frametime text object
frametime_text = ax_H.text(inside_sensor.D_grid_centres[0], 66, "")

# Set x and y axes limits
# Set these using only the dates from the inside sensor
ax_H.set_xlim(
    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
ax_T.set_xlim(
    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
ax_H.set_ylim(SensorData.ylim_H)
ax_T.set_ylim(SensorData.ylim_T)

# Set labels
ax_H.set_ylabel("Humidity (%RH)")
ax_T.set_ylabel("Temperature ($^\circ$C)")
ax_T.set_xlabel("Time (s)")


# Draw the initial figure before setting the data
fig.canvas.draw()
plt.show(block=False)

decay_counter = count()  # Initialise counter for use with the y limit decay
update_interval = 2  # The time (seconds) to wait before each update
frametime_old = ""
while True:
    frame_start_time = time.time()

    # Update the sensor data
    inside_updated = inside_sensor.update()
    outside_updated = outside_sensor.update()

    if inside_updated or outside_updated:
        # Set new y limits
        ax_H.set_xlim(
            inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
        ax_T.set_xlim(
            inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
        ax_H.set_ylim(SensorData.ylim_H)
        ax_T.set_ylim(SensorData.ylim_T)

        # Set frametime text
        frametime_text.set_text(frametime_old)
        # Make sure the frametime counter stays in the axis limits
        frametime_text.set_x(inside_sensor.D_grid_centres[0])
        # Make sure the frametime counter stays in the axis limits
        frametime_text.set_y(SensorData.ylim_H[1] + 1)

        # Set new data
        line_H_inside.set_data(inside_sensor.D_grid_centres, inside_sensor.H)
        line_T_inside.set_data(inside_sensor.D_grid_centres, inside_sensor.T)
        line_H_outside.set_data(
            outside_sensor.D_grid_centres, outside_sensor.H)
        line_T_outside.set_data(
            outside_sensor.D_grid_centres, outside_sensor.T)

        # Redraw everything, as we need changing x ticks as well as the line and frametimes
        fig.canvas.draw()

        fig.canvas.flush_events()

        # Every once in a while, check if the y limits have become too large
        # And if so, slowly decay them
        decay_interval = 5
        if next(decay_counter) == int(decay_interval/update_interval):
            decay_counter = count()  # Reset counter
            SensorData.decayLimits(
                SensorData.ylim_H, SensorData.ylim_H_buffer, inside_sensor.H, outside_sensor.H)
            SensorData.decayLimits(
                SensorData.ylim_T, SensorData.ylim_T_buffer, inside_sensor.T, outside_sensor.H)

        # Get current frametime to display on the next frame
        frametime_old = f"Frame time (s): {time.time() - frame_start_time: 0.3f}"

    time.sleep(update_interval)
