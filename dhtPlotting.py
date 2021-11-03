import datetime
import textwrap
import time
from collections import deque
from itertools import count

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from DHT_MySQL_interface import DHTConnection
from Sensors import DHTSensorData

matplotlib.use('Qt5Agg')

font = {'size': 19}

matplotlib.rc('font', **font)


def setUpFigure(inside_sensor: DHTSensorData, outside_sensor: DHTSensorData):
    # Set up figure
    fig = plt.figure()
    # Make subplots for separate temp/humidity
    ax_H = fig.add_subplot(2, 1, 1)
    ax_T = fig.add_subplot(2, 1, 2)
    # Set tight layout
    fig.tight_layout()
    # Maximise the window (Qt5Agg specific)
    if matplotlib.get_backend() == "Qt5Agg":
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()

    def setUpAxes(ax, xlim: list, ylim: list):
        # Show grid
        ax.grid(True)
        # Set xtick locations and formats
        minor_tick_interval = max(1, int(DHTSensorData.history_timedelta.days))
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0]))
        ax.xaxis.set_minor_locator(mdates.HourLocator(
            byhour=range(0, 23, minor_tick_interval)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a"))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter("%Hh"))
        # Set major tick font size
        ax.xaxis.set_tick_params(labelsize=30)
        # Set yaxis ticks on left and right
        ax.tick_params(labelright=True)
        # Set x and y axes limits
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    xlim = [inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1]]
    setUpAxes(ax_H, xlim, DHTSensorData.ylim_H)
    setUpAxes(ax_T, xlim, DHTSensorData.ylim_T)

    line_H_inside, = ax_H.plot(
        inside_sensor.D_grid_centres, inside_sensor.H, label="Inside")
    line_T_inside, = ax_T.plot(
        inside_sensor.D_grid_centres, inside_sensor.T, label="Inside")
    line_H_outside, = ax_H.plot(
        outside_sensor.D_grid_centres, outside_sensor.H, label="Outside")
    line_T_outside, = ax_T.plot(
        outside_sensor.D_grid_centres, outside_sensor.T, label="Outside")
    # Set line colours
    line_H_inside.set_color("#74A122")  # Green
    line_T_inside.set_color("#74A122")  # Green
    line_H_outside.set_color("#D3042F")  # Red
    line_T_outside.set_color("#D3042F")  # Green
    # Set linewidths
    line_H_inside.set_linewidth(3)
    line_T_inside.set_linewidth(3)
    line_H_outside.set_linewidth(3)
    line_T_outside.set_linewidth(3)
    # Make legend
    ax_H.legend(loc="upper left")

    # Set axis labels
    ax_H.set_ylabel("Humidity (%RH)")
    ax_T.set_ylabel("Temperature ($^\circ$C)")
    ax_T.set_xlabel("waiting for diagnostic info", fontsize=15)

    # Draw the initial figure
    fig.canvas.draw()
    fig.canvas.flush_events()
    # Use block=False so that we have control of the figure event loop
    plt.show(block=False)
    # Draw and flush the plot twice more, not sure why this has to happen,
    # but otherwise we have to wait for two successful iterations of the while loop
    # before we actually see the plot
    fig.canvas.draw()
    fig.canvas.flush_events()
    fig.canvas.draw()
    fig.canvas.flush_events()

    return fig, ax_H, ax_T, line_H_inside, line_T_inside, line_H_outside, line_T_outside

# Set up figure and run the event loop for reading from the database and plotting DHT data


def plotDHT(connection_config: dict, *, event_loop_interval: float = 0.5,
            update_interval: float = 5, fig_save_path: str = "DHT_graph.png"):
    # Connect to the database
    DHT_db = DHTConnection(connection_config, True)

    # Set up SensorData classes (get data from database and organise)
    t = time.time()
    inside_sensor = DHTSensorData(DHT_db, "dht_inside")
    outside_sensor = DHTSensorData(DHT_db, "dht_outside")
    print(f"Set up DHTSensorData: {time.time()-t: 2.4f}")

    # Set up figure
    t = time.time()
    fig, ax_H, ax_T, line_H_inside, line_T_inside, line_H_outside, line_T_outside = \
        setUpFigure(inside_sensor, outside_sensor)
    print(f"Set up the initial figure: {time.time()-t: 2.4f}")

    # Loop intervals
    # event_loop_interval# The time (seconds) to wait between each event loop cycle
    # update_interval  # The time (seconds) to wait between each update
    num_update_loop_cycles = update_interval / event_loop_interval

    loop_counter = count()
    decay_counter = count()  # Initialise counter for use with the y limit decay
    # Store a few of the most recent loop times to keep a running average
    looptimes_draw = deque([0], maxlen=20)
    looptimes_update = deque([0], maxlen=20)
    looptimes_loop = deque([0], maxlen=20)
    looptimes_save = deque([0], maxlen=20)

    while True:
        loop_start_time = time.time()

        # To keep the plot responsive, only attempt to update every few loop cycles
        if next(loop_counter) >= num_update_loop_cycles:
            loop_counter = count()  # Reset loop counter
            # Update the sensor data
            inside_updated = inside_sensor.update()
            outside_updated = outside_sensor.update()

            # Store the time it takes to do an update
            looptimes_update.append(time.time() - loop_start_time)
            draw_start_time = time.time()
            if inside_updated or outside_updated:
                # Set new y limits
                ax_H.set_xlim(
                    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
                ax_T.set_xlim(
                    inside_sensor.D_grid_centres[0], inside_sensor.D_grid_centres[-1])
                ax_H.set_ylim(DHTSensorData.ylim_H)
                ax_T.set_ylim(DHTSensorData.ylim_T)

                # Set looptime text
                diagnostic_txt = f"""
                Average loop|query|save|draw time (s): {np.mean(looptimes_loop): 0.3f} | {np.mean(looptimes_update): 0.3f} | {np.mean(looptimes_save): 0.3f} | {np.mean(looptimes_draw): 0.3f}
                Last updated: {inside_sensor.last_queried_time.strftime("%a %H:%M:%S")}
                """

                ax_T.set_xlabel(textwrap.dedent(diagnostic_txt), fontsize=15)

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

                # Store the time it takes to draw
                looptimes_draw.append(time.time() - draw_start_time)

                # Save the figure to the local directory (this takes a while)
                save_start_time = time.time()
                plt.savefig(fig_save_path)
                looptimes_save.append(time.time() - save_start_time)

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
    "user": "haydeni0",
    "password": "OSzP34,@H0.I2m$sZpI<",
    'raise_on_warnings': True
}


if __name__ == "__main__":
    # Server connection details
    # Use the local server when run from the windows pc, for faster queries
    plotDHT(HaydensPC_connection_config,
            event_loop_interval=0.05, update_interval=2)
    plotDHT(raspi_connection_config)
