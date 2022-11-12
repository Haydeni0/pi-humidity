import datetime

import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

from DHT_MySQL_interface import DHTConnection, ObsDHT

SCHEMA_NAME = "test"
TABLE_NAME_inside = "dht_inside"
TABLE_NAME_outside = "dht_outside"

TABLE_NAME_inside = f"{SCHEMA_NAME}.{TABLE_NAME_inside}"
TABLE_NAME_outside = f"{SCHEMA_NAME}.{TABLE_NAME_outside}"

GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DHTConnection()


app = Dash(name=__name__)

# Update interval in seconds
update_interval = 2

app.layout = html.Div(
    children=[
        html.H1(children="pi-humidity"),
        html.Div(
            children="""
        Humidity and temperature monitoring
    """
        ),
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

    end_dtime = datetime.datetime.now()
    start_dtime = end_dtime - datetime.timedelta(seconds = 20)

    # Inside
    D, H, T = conn.getObservations(
        TABLE_NAME_inside, start_dtime=start_dtime, end_dtime=end_dtime
    )
    fig_H.add_trace(go.Scatter(x=D, y=H, marker_color=GREEN_HEX, name = "Inside"))
    fig_T.add_trace(go.Scatter(x=D, y=T, marker_color=GREEN_HEX, name = "Inside"))

    # Outside
    D, H, T = conn.getObservations(
        TABLE_NAME_outside, start_dtime=start_dtime, end_dtime=end_dtime
    )
    fig_H.add_trace(go.Scatter(x=D, y=H, marker_color=RED_HEX, name = "Outside"))
    fig_T.add_trace(go.Scatter(x=D, y=T, marker_color=RED_HEX, name = "Outside"))

    return fig_H, fig_T


if __name__ == "__main__":
    app.run_server(debug=True)
