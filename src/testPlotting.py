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

conn = DHTConnection()



app = Dash(name=__name__)

# Update interval in seconds
update_interval = 2

app.layout = html.Div(
    children=[
        html.H1(children="Pi "),
        html.Div(
            children="""
        Dash: A web application framework for your data.
    """
        ),
        dcc.Graph(id="dht_inside"),
        dcc.Interval(id="update-tick", interval=update_interval*1000, n_intervals=0)
    ]
)

@app.callback(Output("dht_inside", "figure"),Input("update-tick", "n_intervals"))
def updateGraph(n:int) -> go.Figure:
    
    fig_T = go.Figure()
    end_dtime = datetime.datetime.now()
    start_dtime = end_dtime - datetime.timedelta(minutes=10)

    D, H, T = conn.getObservations(
        TABLE_NAME_inside, start_dtime=start_dtime, end_dtime=end_dtime
    )
    fig_T.add_trace(go.Scatter(x=D, y=T))
    D, H, T = conn.getObservations(
        TABLE_NAME_outside, start_dtime=start_dtime, end_dtime=end_dtime
    )
    fig_T.add_trace(go.Scatter(x=D, y=T))

    return fig_T

if __name__ == "__main__":
    app.run_server(debug=True)
