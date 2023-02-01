import copy
import logging
import os
import sys
from collections import deque
from datetime import datetime, timedelta
from time import time

from app_layout import app_layout

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from dash_extensions.enrich import (
    DashProxy,
    ServersideOutputTransform,
    ServersideOutput,
    Input,
    Output,
    State,
    FileSystemStore
)
from dash import no_update
from flask_caching import Cache
from plotly.subplots import make_subplots
from werkzeug.middleware.profiler import ProfilerMiddleware

from database_api import DatabaseApi, MyConnectionPool
from my_certbot import Cert, createCertificate
from sensors import SensorData

logger = logging.getLogger("__name__")

# Make colourmap for line plots https://plotly.com/python/discrete-color/
GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"
colourmap = [GREEN_HEX, RED_HEX] + px.colors.qualitative.G10

# Set up logging
start_time = datetime.now()

with open("/shared/config.yaml", "r") as f:
    config: dict = yaml.load(f, yaml.Loader)
SCHEMA_NAME = config["schema_name"]
TABLE_NAME = config["table_name"]
FULL_TABLE_NAME = DatabaseApi.joinNames(SCHEMA_NAME, TABLE_NAME)

# Find a way of choosing num_bins optimally based on the length of sensor history and the update interval
# Num bins shouldn't be too big such that the time it takes to draw > the update interval
# Num bins shouldn't be too small such that every time we update, nothing happens.
# Also update interval should be longer than the sensor retry seconds, send a logger warning message about this?
max_buckets = 800
# db_pool = MyConnectionPool()

my_backend = FileSystemStore(cache_dir="/dash_filesystemstore")

app = DashProxy(
    name=__name__,
    update_title="",
    title="pi-humidity",
    transforms=[ServersideOutputTransform(backend=my_backend)],
)
server = app.server
app.layout = app_layout


# @app.callback(
#     [Output("manual-data-update", "n_clicks"), Output("numinput:history", "value")],
#     [Input("numinput:history", "value"), State("store:sensor-data", "data")],
#     prevent_initial_call=False,
# )
# def changeHistory(value: float, sensor_data: SensorData | None):
#     if sensor_data is not None:
#         sensor_data.history = timedelta(days=value)
#         return "please update data", no_update
#     else:
#         # Try to update history again
#         return no_update, no_update, value


@app.callback(
    ServersideOutput("store:sensor-data", "data"),
    [
        State("store:sensor-data", "data"),
        Input("numinput:history", "value"),
        Input("button:update", "n_clicks"),
        Input("interval:graph-update-tick", "n_intervals"),
    ],
)
def updateSensorData(
    sensor_data: SensorData | None, new_history_value: int, update_button_clicks: int, n_intervals: int
):
    t = time()
    if sensor_data is None:
        sensor_data = SensorData(table_name=FULL_TABLE_NAME, max_buckets=max_buckets)

    history = timedelta(days=new_history_value)
    if history != sensor_data.history:
        # Setting a new history value updates the sensor data
        sensor_data.history = history
    else:
        sensor_data.update()

    logger.debug(f"Sensor data updated in {time() - t:.2g} seconds")
    return sensor_data


@app.callback(
    [
        Output("graph:humidity", "figure"),
        Output("graph:temperature", "figure"),
        Output("graph-update-time", "data"),
    ],
    Input("store:sensor-data", "data"),
    prevent_initial_call=True,
)
def updateGraphs(sensor_data: SensorData | None):

    if sensor_data is None:
        return no_update

    t = time()
    H_traces = []
    T_traces = []

    colour_idx = 0
    # STOP USING _sensors, use sensors instead
    for sensor_name, data in sensor_data._sensors.items():
        df = pd.DataFrame(data)
        dtime = np.array(df.iloc[:, 0])
        humidity = np.array(df.iloc[:, 1])
        temperature = np.array(df.iloc[:, 2])

        colour_idx = colour_idx % len(colourmap)
        colour = colourmap[colour_idx]

        H_traces.append(
            go.Scatter(x=dtime, y=humidity, marker_color=colour, name=sensor_name)
        )
        T_traces.append(
            go.Scatter(x=dtime, y=temperature, marker_color=colour, name=sensor_name)
        )

        colour_idx += 1

    current_time = datetime.now()
    xaxis_range = [current_time - sensor_data.history, current_time]
    H_layout = go.Layout(
        xaxis=go.layout.XAxis(range=xaxis_range),
        font=go.layout.Font(size=18),
        margin={"t": 0},  # https://plotly.com/javascript/reference/#layout-margin
        height=400,
    )
    T_layout = copy.deepcopy(H_layout)
    H_layout.yaxis = go.layout.YAxis(title="Humidity (%RH)", side="right")
    T_layout.yaxis = go.layout.YAxis(title="Temperature (<sup>o</sup>C)", side="right")

    logger.debug(f"Updated figure in {time() - t: .2g} seconds")

    # Only update elements of the figure, rather than returning a whole new figure. This is much faster.
    return (
        {"data": H_traces, "layout": H_layout},
        {
            "data": T_traces,
            "layout": T_layout,
        },
        current_time,
    )


@app.callback(
    [
        Output("time", "children"),
        Output("time", "dateTime"),
        Output("debug-text", "children"),
    ],
    [
        Input("interval:time-update-tick", "n_intervals"),
        Input("graph-update-time", "data"),
    ],
)
def updateTimeDisplay(n: int, graph_last_updated: str) -> tuple[str, datetime, str]:

    current_time = datetime.now()
    rounded_time = datetime.strftime(current_time, "%H:%M:%S")
    if graph_last_updated is not None:
        time_passed = current_time - datetime.strptime(
            graph_last_updated, "%Y-%m-%dT%H:%M:%S.%f"
        )
    else:
        time_passed = current_time - start_time

    # Some text for debugging
    debug_text = f"Worker pid: {os.getpid()}"

    return (
        f"""
    {current_time.date()} {rounded_time}.{str(current_time.microsecond)[0]} (last updated {time_passed.seconds} seconds ago)
    """,
        current_time,
        debug_text,
    )


if __name__ == "__main__":
    """
    Dash webserver for development
    Only runs on a single process
    """

    start_time_formatted = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # Worry about this potentially clogging up the device storage
    # if the container keeps restarting or too many things are logged...
    logging.basicConfig(
        filename=f"/shared/logs/dhtPlotter_{start_time_formatted}.log",
        filemode="w",
        format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
        level=logging.DEBUG,
    )

    from webserver import startWebserver

    startWebserver(dev=True)
