from database_api import DatabaseApi
from sensors import SensorData
from dash import Dash, dcc, html
from dash_daq.NumericInput import NumericInput
from dash_daq.BooleanSwitch import BooleanSwitch
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
from my_certbot import Cert, createCertificate
import os
import pandas as pd
from time import time

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
max_buckets = 800
history = timedelta(days=2)
sensor_data = SensorData(db, full_table_name, max_buckets=max_buckets, history=history)


fig_H = go.Figure()
fig_T = go.Figure()


app = Dash(name=__name__, update_title="", title="pi-humidity")
server = app.server

app.layout = html.Div(
    children=[
        # Graphs
        html.Div(
            children=[
                dcc.Graph(id="graph:humidity", figure=fig_H, animate=False),
                dcc.Graph(id="graph:temperature", figure=fig_T, animate=False),
            ],
        ),
        # Display info and buttons
        html.Div(
            children=[
                html.Time(id="time"),
                # html.Button("Pause updates", id="btn:toggle-pause", n_clicks=0), # Allow pause to be able to investigate data manually using the graph
            ],
            style={"width:": "30%", "display": "inline-block"},
        ),
        html.Div(),
        # Config
        html.Div(
            children=[
                NumericInput(
                    id="numinput:history",
                    min=1,
                    max=100,
                    label="History (days)",
                    labelPosition="right",
                    value=history.days,
                    persistence=True,
                )
            ],
            id="div:config",
            style={"display": "inline-block"},
        ),
        # Other
        html.Div(
            children=[
                dcc.Interval(
                    id="interval:graph-update-tick",
                    interval=figure_update_interval_seconds * 1000,
                    n_intervals=0,
                ),
                dcc.Interval(
                    id="interval:time-update-tick", interval=800, n_intervals=0
                ),
                dcc.Store(id="graph-update-time"),
                html.Div(id="manual-graph-update", n_clicks=0)
            ],
        ),
    ]
)

@app.callback(Output("manual-graph-update", "n_clicks"), Input("numinput:history", "value"), prevent_initial_call=True)
def changeHistory(value: float):
    sensor_data.history = timedelta(days=value)
    # Return something so that graphs are updated
    return 0

@app.callback(
    [
        Output("graph:humidity", "figure"),
        Output("graph:temperature", "figure"),
        Output("graph-update-time", "data"),
    ],
    [Input("interval:graph-update-tick", "n_intervals"), Input("manual-graph-update", "n_clicks")],
)
def updateGraphs(n: int, manual_update_clicks: int) -> tuple[dict, dict, datetime]:
    t = time()
    H_traces = []
    T_traces = []

    logger.debug(f"Updating sensor data from database...")
    sensor_data.update()
    t_update = time() - t

    logger.debug(f"Plotting...")
    colour_idx = 0
    # STOP USING _sensors, use sensors instead
    for sensor_name, data in sensor_data._sensors.items():
        df = pd.DataFrame(data)
        dtime = np.array(df["Index"])
        humidity = np.array(df["humidity"])
        temperature = np.array(df["temperature"])

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
    t_plotting = time() - (t + t_update)
    logger.debug(f"Done [{t_update:2g}, {t_plotting:2g}]")

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
    [Output("time", "children"), Output("time", "dateTime")],
    [
        Input("interval:time-update-tick", "n_intervals"),
        Input("graph-update-time", "data"),
    ],
)
def updateTimeDisplay(n: int, graph_last_updated: str) -> tuple[str, datetime]:

    current_time = datetime.now()
    rounded_time = datetime.strftime(current_time, "%H:%M:%S")
    if graph_last_updated is not None:
        time_passed = current_time - datetime.strptime(
            graph_last_updated, "%Y-%m-%dT%H:%M:%S.%f"
        )
    else:
        time_passed = current_time - start_time

    return (
        f"""
    {current_time.date()} {rounded_time}.{str(current_time.microsecond)[0]} (last updated {time_passed.seconds} seconds ago)
    """,
        current_time,
    )


if __name__ == "__main__":
    # Set up a cronjob to renew the certificate every day at 0230
    # os.system("crontab -l > my_cron")
    os.system(r"echo 30 2 \* \* \* python /src/my_certbot.py  >> /tmp/my_cron")
    os.system("crontab /tmp/my_cron")
    os.system("rm /tmp/my_cron")

    cert = Cert()

    # Create a certificate if one doesn't already exist and a hostname is given
    if not cert and cert.getHostname():
        createCertificate()
        cert = Cert()

    if cert:
        # Certificate exists, use https
        port = 443
    else:
        # Certificate doesn't exist, use http
        port = 80

    # Use Dash instead of gunicorn for the webserver
    ssl_context = cert.getSslContext()
    app.run_server(host="0.0.0.0", port=port, debug=True, ssl_context=ssl_context)
