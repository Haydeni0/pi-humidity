from datetime import timedelta

import plotly.graph_objects as go
from dash_daq.NumericInput import NumericInput
from dash_extensions.enrich import dcc, html

default_history = timedelta(days=2)
default_figure_update_interval_seconds = 30

fig_H = go.Figure()
fig_T = go.Figure()

app_layout = html.Div(
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
                html.Div(id="debug-text"),
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
                    value=default_history.days,
                    persistence=True,
                ),
                html.Button("Update", id="button:update", n_clicks=0),
            ],
            id="div:config",
            style={"display": "inline-block"},
        ),
        # Other
        html.Div(
            children=[
                dcc.Interval(
                    id="interval:graph-update-tick",
                    interval=default_figure_update_interval_seconds * 1000,
                    n_intervals=0,
                ),
                dcc.Interval(
                    id="interval:time-update-tick", interval=800, n_intervals=0
                ),
                dcc.Store(id="graph-update-time"),
                dcc.Store(id="store:fig-humidity"),
                dcc.Store(id="store:fig-temperature"),
                dcc.Store(id="store:sensor-data"),
                html.Div(id="manual-data-update", n_clicks=0),
            ],
        ),
    ]
)
