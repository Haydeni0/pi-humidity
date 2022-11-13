from DHT_MySQL_interface import DHTConnection
from Sensors import DHTSensorData
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from flask import Flask
import numpy as np


GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DHTConnection()

server = Flask(__name__)
app = Dash(name=__name__)

inside_sensor = DHTSensorData(conn, "test.dht_inside")
outside_sensor = DHTSensorData(conn, "test.dht_outside")

# Update interval in seconds
update_interval = 2

app = Dash(name=__name__)
app.layout = html.Div(
    children=[
        dcc.Graph(id="humidity-graph"),
        dcc.Graph(id="temperature-graph"),
        dcc.Interval(id="update-tick", interval=update_interval * 1000, n_intervals=0),
    ]
)


@app.callback(
    [Output("humidity-graph", "figure"), Output("temperature-graph", "figure")],
    Input("update-tick", "n_intervals"),
)
def updateGraph(n: int) -> tuple[go.Figure, go.Figure]:

    fig_T = go.Figure()
    fig_H = go.Figure()

    fig_T.update_yaxes(title_text="Temperature (<sup>o</sup>C)")
    fig_H.update_yaxes(title_text="Humidity (%RH)")

    for sensor, name, colour in zip(
        [inside_sensor, outside_sensor], ["Inside", "Outside"], [GREEN_HEX, RED_HEX]
    ):
        inside_sensor.update()
        outside_sensor.update()

        D = np.array(sensor.D_grid_centres)
        H = np.array(sensor.H)
        T = np.array(sensor.T)

        fig_H.add_trace(
            go.Scatter(
                x=D, y=H, marker_color=colour, name=name
            )
        )
        fig_T.add_trace(
            go.Scatter(
                x=D, y=T, marker_color=colour, name=name
            )
        )

    return fig_H, fig_T


if __name__ == "__main__":
    app.run_server(port = 8050,debug=True)
