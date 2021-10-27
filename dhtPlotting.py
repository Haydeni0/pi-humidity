from Sensors import DHTSensorData
from DHT_MySQL_interface import DHTConnection, ObsDHT
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import textwrap
import time
from collections import deque
from itertools import count

import matplotlib
matplotlib.use('Qt5Agg')

def plotDHT(connection_config: dict):

    DHT_db = DHTConnection(connection_config, True)

    t = time.time()
    inside_sensor = DHTSensorData(DHT_db, "dht_inside")
    outside_sensor = DHTSensorData(DHT_db, "dht_outside")
    print(f"Set up DHTSensorData: {time.time()-t: 2.4f}")

    # Initial plot
    t = time.time()
    fig = plt.figure()
    ax_H = fig.add_subplot(2, 1, 1)
    plt.grid()
    ax_T = fig.add_subplot(2, 1, 2)
    plt.grid()
    # fig.tight_layout()
    line_H_inside, = ax_H.plot(
        inside_sensor.D_grid_centres, inside_sensor.H, label="Inside")
    line_T_inside, = ax_T.plot(
        inside_sensor.D_grid_centres, inside_sensor.T, label="Inside")
    line_H_outside, = ax_H.plot(
        outside_sensor.D_grid_centres, outside_sensor.H, label="Outside")
    line_T_outside, = ax_T.plot(
        outside_sensor.D_grid_centres, outside_sensor.T, label="Outside")
    print(f"Set up initial figure: {time.time()-t: 2.4f}")

    # Maximise the window (QT5Agg specific)
    # figManager = plt.get_current_fig_manager()
    # figManager.window.showMaximized()

    # Make the frametime text object
    t = time.time()
    avg_looptime_text = ax_H.text(inside_sensor.D_grid_centres[0], 66, "")
    # Set x and y axes limits
    # Set these using only the dates from the inside sensor
    ax_H.set_xlim(
        inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
    ax_T.set_xlim(
        inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
    ax_H.set_ylim(DHTSensorData.ylim_H)
    ax_T.set_ylim(DHTSensorData.ylim_T)

    ax_H.set_ylabel("Humidity (%RH)")
    ax_T.set_ylabel("Temperature ($^\circ$C)")
    ax_T.set_xlabel("Time (s)")
    print(f"Set additional plot attributes: {time.time()-t: 2.4f}")


    # Draw the initial figure
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
    print(f"Draw the initial figure: {time.time()-t: 2.4f}")

    # Loop intervals
    # The time (seconds) to wait between each event loop cycle
    event_loop_interval = 0.1
    update_interval = 2  # The time (seconds) to wait between each update
    num_update_loop_cycles = update_interval / event_loop_interval

    loop_counter = count()
    decay_counter = count()  # Initialise counter for use with the y limit decay
    # Store a few of the most recent loop times to keep a running average
    looptimes_draw = deque([0], maxlen=20)
    looptimes_update = deque([0], maxlen=20)
    looptimes_loop = deque([0], maxlen=20)

    while True:
        loop_start_time = time.time()

        # To keep the plot responsive, only attempt to update every few loop cycles
        if next(loop_counter) >= num_update_loop_cycles:
            loop_counter = count()  # Reset loop counter
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

                # Set looptime text
                txt = f"""
                Average loop time (s): {np.mean(looptimes_loop): 0.3f}
                Average query time (s): {np.mean(looptimes_update): 0.3f}
                Average draw time (s): {np.mean(looptimes_draw): 0.3f}"""
                avg_looptime_text.set_text(textwrap.dedent(txt))
                # Make sure the frametime counter stays in the axis limits
                avg_looptime_text.set_x(inside_sensor.D_grid_centres[0])
                # Make sure the frametime counter stays in the axis limits
                avg_looptime_text.set_y(DHTSensorData.ylim_H[1] + 1)

                # Set new data
                line_H_inside.set_data(
                    inside_sensor.D_grid_centres, inside_sensor.H)
                line_T_inside.set_data(
                    inside_sensor.D_grid_centres, inside_sensor.T)
                line_H_outside.set_data(
                    outside_sensor.D_grid_centres, outside_sensor.H)
                line_T_outside.set_data(
                    outside_sensor.D_grid_centres, outside_sensor.T)

                # Redraw everything, as we need changing x ticks as well as the line and frametimes
                fig.canvas.draw()

                # Every once in a while, check if the y limits have become too large
                # And if so, slowly decay them
                decay_interval = 5
                if next(decay_counter) == int(decay_interval/event_loop_interval):
                    decay_counter = count()  # Reset counter
                    DHTSensorData.decayLimits(
                        DHTSensorData.ylim_H, DHTSensorData.ylim_H_buffer, inside_sensor.H, outside_sensor.H)
                    DHTSensorData.decayLimits(
                        DHTSensorData.ylim_T, DHTSensorData.ylim_T_buffer, inside_sensor.T, outside_sensor.T)

                looptimes_draw.append(time.time() - loop_start_time)
            else:
                looptimes_update.append(time.time() - loop_start_time)
        else:
            looptimes_loop.append(time.time() - loop_start_time)

        fig.canvas.flush_events()  # Always flush events to keep the gui responsive
        time.sleep(event_loop_interval)


# Raspberry pi zero WH MySQL server 
raspi_connection_config = {
    "host": '192.168.1.46',
    "database": "pi_humidity",
    "user": "haydeni0",
    "password": "raspizeroWH_SQL",
    'raise_on_warnings': True
}

HaydensPC_connection_config = {
    "host": 'localhost',
    "database": "pi_humidity",
    "user": "Haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}


if __name__ == "__main__":
    # Server connection details
    # plotDHT(HaydensPC_connection_config)
    plotDHT(raspi_connection_config)




