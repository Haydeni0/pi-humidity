from database_api import DatabaseApi
from sensors import SensorData
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import timedelta, datetime
import sys
import logging
import copy
import yaml
from collections import deque

# Make colourmap for line plots https://plotly.com/python/discrete-color/
GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"
colourmap = [GREEN_HEX, RED_HEX] + px.colors.qualitative.G10

# Set up logging
start_time = datetime.now()
start_time_formatted = datetime.now().strftime("%Y-%m-%d_%H%M%S")
# Worry about this potentially clogging up the device storage
# if the container keeps restarting or too many things are logged...
logging.basicConfig(
    filename=f"/shared/logs/dhtPlotter_{start_time_formatted}.log",
    filemode="w",
    format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("__name__")

db = DatabaseApi()

with open("/shared/config.yaml", "r") as f:
    config: dict = yaml.load(f, yaml.Loader)

figure_update_interval_seconds = config["figure_update_interval_seconds"]
sensor_retry_seconds = config["sensor_retry_seconds"]
schema_name = config["schema_name"]
table_name = config["table_name"]
full_table_name = db.joinNames(schema_name, table_name)

# Find a way of choosing num_bins optimally based on the length of sensor history and the update interval
# Num bins shouldn't be too big such that the time it takes to draw > the update interval 
# Num bins shouldn't be too small such that every time we update, nothing happens.
# Also update interval should be longer than the sensor retry seconds, send a logger warning message about this?
num_bins = 800
sensor_history=timedelta(days=2)
sensor_data = SensorData(db, full_table_name, num_bins = num_bins, sensor_history=sensor_history)


fig_H = go.Figure()
fig_T = go.Figure()


app = Dash(name=__name__, update_title="", title="pi-humidity")

app.layout = html.Div(
    children=[
        dcc.Graph(id="humidity-graph", figure=fig_H, animate=True),
        dcc.Graph(id="temperature-graph", figure=fig_T, animate=True),
        html.Time(id="time"),
        dcc.Interval(id="graph-update-tick", interval=figure_update_interval_seconds * 1000, n_intervals=0),
        dcc.Interval(id="time-update-tick", interval=100, n_intervals=0),

        dcc.Store(id="graph-update-time")
    ]
)

@app.callback(
    [Output("humidity-graph", "figure"), Output("temperature-graph", "figure"), Output("graph-update-time", "data")],
    Input("graph-update-tick", "n_intervals"),
)
def updateGraph(n: int) -> tuple[dict, dict, datetime]:
    logger.debug("Started graph update")
    H_traces = []
    T_traces = []

    sensor_data.update()
    logger.debug(f"Updated sensor data")

    colour_idx = 0
    for sensor in sensor_data.sensors:
        dtime = np.array(sensor.data.index)
        humidity = np.array(sensor.data["humidity"])
        temperature = np.array(sensor.data["temperature"])

        colour_idx = colour_idx % len(colourmap)
        colour = colourmap[colour_idx]
        
        H_traces.append(go.Scatter(x=dtime, y=humidity, marker_color=colour, name=sensor.name))
        T_traces.append(go.Scatter(x=dtime, y=temperature, marker_color=colour, name=sensor.name))

        
        colour_idx += 1

    current_time = datetime.now()
    xaxis_range = [current_time - sensor_history, current_time]
    H_layout = go.Layout(
        xaxis=go.layout.XAxis(range=xaxis_range),
        font=go.layout.Font(size=18),
        margin={"t": 0},  # https://plotly.com/javascript/reference/#layout-margin
        height=400,
    )
    T_layout = copy.deepcopy(H_layout)
    H_layout.yaxis = go.layout.YAxis(title="Humidity (%RH)")
    T_layout.yaxis = go.layout.YAxis(title="Temperature (<sup>o</sup>C)")

    # Only update elements of the figure, rather than returning a whole new figure. This is much faster.
    return {"data": H_traces, "layout": H_layout}, {
        "data": T_traces,
        "layout": T_layout,
    }, current_time


@app.callback([Output("time", "children"), Output("time", "dateTime")], [Input("time-update-tick", "n_intervals"), Input("graph-update-time", "data")])
def updateTimeDisplay(n: int, graph_last_updated: str) -> tuple[str, datetime]:

    current_time = datetime.now()
    rounded_time = datetime.strftime(current_time, "%H:%M:%S")
    if graph_last_updated is not None:
        time_passed = current_time - datetime.strptime(graph_last_updated, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        time_passed = current_time - start_time
        

    return f"""
    {rounded_time}.{str(current_time.microsecond)[0]} (last updated {time_passed.seconds} seconds ago)
    """, current_time

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="8080", debug=True)
