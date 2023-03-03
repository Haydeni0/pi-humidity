import copy
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from time import time

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from dash import no_update
from dash_extensions.enrich import (
    DashProxy,
    FileSystemStore,
    Input,
    Output,
    ServersideOutput,
    ServersideOutputTransform,
    State,
)

import layouts
from database_api import DatabaseApi
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

backend_dir = "/dash_filesystemstore"
my_backend = FileSystemStore(cache_dir=backend_dir)


def deleteOldCache(since: timedelta = timedelta(hours=1)):
    """Delete old dash cached files"""
    path = Path(backend_dir)
    for f in path.iterdir():
        is_file = f.is_file()
        last_modified = datetime.fromtimestamp(f.lstat().st_mtime)
        if is_file and last_modified < (datetime.now() - since):
            os.remove(f)


app = DashProxy(
    name=__name__,
    update_title="",
    title="pi-humidity",
    transforms=[ServersideOutputTransform(backend=my_backend)],
    use_pages=True
)
server = app.server
app.layout = layouts.app()
# Flask requires a secret key, just use the postgres password
app.server.secret_key = os.getenv("POSTGRES_PASSWORD")  # type:ignore


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
    sensor_data: SensorData | None,
    new_history_value: int,
    update_button_clicks: int,
    n_intervals: int,
):
    t = time()
    if sensor_data is None:
        sensor_data = SensorData(table_name=FULL_TABLE_NAME, max_buckets=800)

    history = timedelta(days=new_history_value)
    if history != sensor_data.history:
        # Setting a new history value updates the sensor data
        sensor_data.history = history
    else:
        sensor_data.update()

    deleteOldCache()

    logger.info(f"Sensor data updated in {time() - t:.2g} seconds")
    return sensor_data


def makeFigures(sensor_data: SensorData) -> tuple[go.Figure, go.Figure]:
    t = time()

    fig_H = go.Figure()
    fig_T = go.Figure()

    colour_idx = 0
    # STOP USING _sensors, use sensors instead
    for sensor_name, data in sensor_data._sensors.items():
        df = pd.DataFrame(data)
        dtime = np.array(df.iloc[:, 0])
        humidity = np.array(df.iloc[:, 1])
        temperature = np.array(df.iloc[:, 2])

        colour_idx = colour_idx % len(colourmap)
        colour = colourmap[colour_idx]

        fig_H.add_trace(
            go.Scattergl(x=dtime, y=humidity, marker_color=colour, name=sensor_name)
        )
        fig_T.add_trace(
            go.Scattergl(x=dtime, y=temperature, marker_color=colour, name=sensor_name)
        )

        colour_idx += 1

    xaxis_range = [sensor_data._last_bucket - sensor_data.history, sensor_data._last_bucket]

    for fig in [fig_H, fig_T]:
        fig.layout = go.Layout(
            xaxis=go.layout.XAxis(range=xaxis_range),
            font=go.layout.Font(size=18),
            margin={"t": 0},  # https://plotly.com/javascript/reference/#layout-margin
            height=400,
            plot_bgcolor="rgba(100,149,237,0)",
        )
        fig.update_xaxes(range=xaxis_range, gridcolor="rgba(86,95,110,0.2)")
    fig_H.update_yaxes(
        title="Humidity (%RH)", side="right", gridcolor="rgba(86,95,110,0.2)"
    )
    fig_T.update_yaxes(
        title="Temperature (<sup>o</sup>C)",
        side="right",
        gridcolor="rgba(86,95,110,0.2)",
    )

    logger.info(f"Created figures in {time() - t: .2g} seconds")

    return fig_H, fig_T

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

    fig_H, fig_T = makeFigures(sensor_data)

    # Fully regenerate an image of each figure to disk every 10 minutes
    filepath_H = Path(__file__).parent.joinpath("assets/fig_humidity.png")
    filepath_T = Path(__file__).parent.joinpath("assets/fig_temperature.png")
    if not filepath_H.exists() or (
        datetime.fromtimestamp(filepath_H.lstat().st_mtime)
        > datetime.now() - timedelta(minutes=10)
    ):  
        temp_sensor_data = SensorData(table_name=FULL_TABLE_NAME)
        temp_sensor_data.history = timedelta(days=2)
        temp_fig_H, temp_fig_T = makeFigures(temp_sensor_data)
        temp_fig_H.write_image(filepath_H)
        temp_fig_T.write_image(filepath_T)

    current_time = datetime.now()
    return (
        fig_H,
        fig_T,
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
        level=logging.INFO,
    )

    from webserver import startWebserver

    startWebserver(dev=True)
