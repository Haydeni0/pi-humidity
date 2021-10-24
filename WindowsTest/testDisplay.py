import time
from itertools import count

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from DHT_MySQL_interface import DHTConnection, ObsDHT
from Sensors import DHTSensorData

# MySQL server connection details
connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}

DHT_db = DHTConnection(connection_config)

t = time.time()
inside_sensor = DHTSensorData(DHT_db, "dht_inside")
outside_sensor = DHTSensorData(DHT_db, "dht_outside")
print(f"Set up DHTSensorData: {time.time()-t: 2.4f}")

# Initial plot
t = time.time()
fig = plt.figure()
ax_H = fig.add_subplot(2, 1, 1)
ax_T = fig.add_subplot(2, 1, 2)
# fig.tight_layout()
line_H_inside, = ax_H.plot(
    inside_sensor.D_grid_centres, inside_sensor.H, label="Inside")
line_T_inside, = ax_T.plot(
    inside_sensor.D_grid_centres, inside_sensor.T, label="Inside")
line_H_outside, = ax_H.plot(
    outside_sensor.D_grid_centres, outside_sensor.H, label="Outside")
line_T_outside, = ax_T.plot(
    outside_sensor.D_grid_centres, outside_sensor.T, label="Outside")
print(f"Initial plot: {time.time()-t: 2.4f}")

# Make the frametime text object
t = time.time()
frametime_text = ax_H.text(inside_sensor.D_grid_centres[0], 66, "")

# Set x and y axes limits
# Set these using only the dates from the inside sensor
ax_H.set_xlim(
    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
ax_T.set_xlim(
    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
ax_H.set_ylim(DHTSensorData.ylim_H)
ax_T.set_ylim(DHTSensorData.ylim_T)
print(f"Frametime text and set axis limits: {time.time()-t: 2.4f}")

# Set labels
t = time.time()
ax_H.set_ylabel("Humidity (%RH)")
ax_T.set_ylabel("Temperature ($^\circ$C)")
ax_T.set_xlabel("Time (s)")
print(f"Set labels: {time.time()-t: 2.4f}")


# Draw the initial figure before setting the data
t = time.time()
fig.canvas.draw()
fig.canvas.flush_events()
# Use block=False so that we have control of the figure event loop
plt.show(block=False)
# Draw and flush the plot twice more, not sure why this has to happen,
# but otherwise we have to wait for two successful iterations of the while loop
fig.canvas.draw()
fig.canvas.flush_events()
fig.canvas.draw()
fig.canvas.flush_events()

print(
    f"Draw the initial figure before setting the data: {time.time()-t: 2.4f}")

decay_counter = count()  # Initialise counter for use with the y limit decay
update_interval = 0.5  # The time (seconds) to wait before each update
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
        ax_H.set_ylim(DHTSensorData.ylim_H)
        ax_T.set_ylim(DHTSensorData.ylim_T)

        # Set frametime text
        frametime_text.set_text(frametime_old)
        # Make sure the frametime counter stays in the axis limits
        frametime_text.set_x(inside_sensor.D_grid_centres[0])
        # Make sure the frametime counter stays in the axis limits
        frametime_text.set_y(DHTSensorData.ylim_H[1] + 1)

        # Set new data
        line_H_inside.set_data(inside_sensor.D_grid_centres, inside_sensor.H)
        line_T_inside.set_data(inside_sensor.D_grid_centres, inside_sensor.T)
        line_H_outside.set_data(
            outside_sensor.D_grid_centres, outside_sensor.H)
        line_T_outside.set_data(
            outside_sensor.D_grid_centres, outside_sensor.T)

        # Redraw everything, as we need changing x ticks as well as the line and frametimes
        fig.canvas.draw()

        # Every once in a while, check if the y limits have become too large
        # And if so, slowly decay them
        decay_interval = 5
        if next(decay_counter) == int(decay_interval/update_interval):
            decay_counter = count()  # Reset counter
            DHTSensorData.decayLimits(
                DHTSensorData.ylim_H, DHTSensorData.ylim_H_buffer, inside_sensor.H, outside_sensor.H)
            DHTSensorData.decayLimits(
                DHTSensorData.ylim_T, DHTSensorData.ylim_T_buffer, inside_sensor.T, outside_sensor.T)

        # Get current frametime to display on the next frame
        frametime_old = f"Frame time (s): {time.time() - frame_start_time: 0.3f}"
        # print(f"[updated]")

    print(f"Loop time: {time.time() - frame_start_time: 0.3f}")
    fig.canvas.flush_events()  # Always flush events to keep the gui responsive
    time.sleep(update_interval)
