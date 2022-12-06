from database_api import DatabaseDHT
from sensors import SensorData
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta, datetime
import sys
import logging

# Set up logging
logging.basicConfig(
    filename="/logs/dhtPlotter.log",
    filemode="w",
    format="[%(asctime)s - %(levelname)s] %(funcName)20s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("__name__")

GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DatabaseDHT()

# Update interval in seconds
update_interval = 5

sensor_history = timedelta(days=2)

# There are still some major problems with
# stability when num_grid is too big or small...
num_grid = 800
# Define num_grid by the desired update interval
# num_grid = int(sensor_history / timedelta(seconds=update_interval))
# print(num_grid)
# sys.exit()

inside_sensor = SensorData(
    conn, "test.dht_inside", sensor_history=sensor_history, num_grid=num_grid
)
outside_sensor = SensorData(
    conn, "test.dht_outside", sensor_history=sensor_history, num_grid=num_grid
)


fig_H = go.Figure()
fig_T = go.Figure()


app = Dash(name=__name__, update_title="", title="pi-humidity")

app.layout = html.Div(
    children=[
        dcc.Graph(id="humidity-graph", figure=fig_H, animate=True),
        dcc.Graph(id="temperature-graph", figure=fig_T, animate=True),
        html.Time(id="time"),
        dcc.Interval(id="graph-update-tick", interval=update_interval * 1000, n_intervals=0),
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

    for sensor, name, colour in zip(
        [inside_sensor, outside_sensor], ["Inside", "Outside"], [GREEN_HEX, RED_HEX]
    ):
        inside_sensor.update()
        logger.debug("Updated inside sensor")
        outside_sensor.update()
        logger.debug("Updated outside sensor")

        D = np.array(sensor.D_grid_centres)
        H = np.array(sensor.H)
        T = np.array(sensor.T)

        H_traces.append(go.Scatter(x=D, y=H, marker_color=colour, name=name))
        T_traces.append(go.Scatter(x=D, y=T, marker_color=colour, name=name))

    current_time = datetime.now()
    xaxis_range = [current_time - sensor_history, current_time]
    H_layout = T_layout = go.Layout(
        xaxis=go.layout.XAxis(range=xaxis_range),
        yaxis=go.layout.YAxis(title="Humidity (%RH)"),
        font=go.layout.Font(size=18),
        margin={"t": 0},  # https://plotly.com/javascript/reference/#layout-margin
        height=400,
    )
    H_layout.yaxis = go.layout.YAxis(title="Humidity (%RH)")
    T_layout.yaxis = go.layout.YAxis(title="Temperature (<sup>o</sup>C)")

    # Only update elements of the figure, rather than returning a whole new figure. This is much faster.
    return {"data": H_traces, "layout": H_layout}, {
        "data": T_traces,
        "layout": T_layout,
    }, current_time


@app.callback([Output("time", "children"), Output("time", "dateTime")], [Input("time-update-tick", "n_intervals"), Input("graph-update-time", "data")])
def updateTimeDisplay(n, graph_last_updated):
    current_time = datetime.now()
    time_passed = current_time - datetime.strptime(graph_last_updated, "%Y-%m-%dT%H:%M:%S.%f")
    
    # rounded_time = current_time - timedelta(microseconds=current_time.microsecond)
    rounded_time = datetime.strftime(current_time, "%H:%M:%S")

    return f"""
    {rounded_time}.{str(current_time.microsecond)[0]} (last updated {time_passed.seconds} seconds ago)
    """, current_time

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port="8080", debug=True)
