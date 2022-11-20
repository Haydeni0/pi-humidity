from database_api import DatabaseDHT
from sensors import SensorData
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import sys


GREEN_HEX = "#74A122"
RED_HEX = "#D3042F"

conn = DatabaseDHT()

# Update interval in seconds
update_interval = 5

sensor_history = timedelta(minutes=2)

# There are still some major problems with 
# stability when num_grid is too big or small...
num_grid = 800
# Define num_grid by the desired update interval
# num_grid = int(sensor_history / timedelta(seconds=update_interval))
# print(num_grid)
# sys.exit()

inside_sensor = SensorData(conn, "test.dht_inside", sensor_history=sensor_history, num_grid=num_grid)
outside_sensor = SensorData(conn, "test.dht_outside", sensor_history=sensor_history, num_grid=num_grid)


fig_H = go.Figure()
fig_T = go.Figure()


app = Dash(name=__name__, update_title="asdohg")
app.layout = html.Div(
    children=[
        dcc.Graph(id="humidity-graph", figure=fig_H, animate=False),
        dcc.Graph(id="temperature-graph", figure=fig_T, animate=False),
        dcc.Interval(id="update-tick", interval=update_interval * 1000, n_intervals=0),
    ]
)

@app.callback(
    [Output("humidity-graph", "figure"), Output("temperature-graph", "figure")],
    Input("update-tick", "n_intervals"),
)
def updateGraph(n: int) -> tuple[dict, dict]:

    H_traces = []
    T_traces = []

    for sensor, name, colour in zip(
        [inside_sensor, outside_sensor], ["Inside", "Outside"], [GREEN_HEX, RED_HEX]
    ):
        inside_sensor.update()
        outside_sensor.update()

        D = np.array(sensor.D_grid_centres)
        H = np.array(sensor.H)
        T = np.array(sensor.T)

        H_traces.append(go.Scatter(x=D, y=H, marker_color=colour, name=name))
        T_traces.append(go.Scatter(x=D, y=T, marker_color=colour, name=name))

    H_layout = go.Layout(yaxis=go.layout.YAxis(title = "Humidity (%RH)"), font=go.layout.Font(size=18))
    T_layout = go.Layout(yaxis=go.layout.YAxis(title = "Temperature (<sup>o</sup>C)"), font=go.layout.Font(size=18))

    # Only update elements of the figure, rather than returning a whole new figure. This is much faster.
    return {"data": H_traces, "layout": H_layout}, {"data": T_traces, "layout": T_layout}


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port = "8080", debug=True)
