from datetime import timedelta

import plotly.graph_objects as go
from dash_daq.NumericInput import NumericInput
from dash_extensions.enrich import dcc, html, page_container, page_registry

default_history = timedelta(days=2)
default_figure_update_interval_seconds = 30


def app() -> html.Div:
    """
    Base app layout that shows on the main page
    """
    return html.Div(
        children=[
            html.Div(
                [
                    html.Div(
                        dcc.Link(
                            f"{page['name']} - {page['path']}",
                            href=page["relative_path"],
                        )
                    )
                    for page in page_registry.values()
                ]
            ),
            page_container,
        ]
    )


def dhtPlotter() -> html.Div:
    """
    Graphs for DHT plotting
    """
    return html.Div(
        children=[
            # Graphs
            html.Div(
                children=[
                    dcc.Graph(id="graph:humidity", animate=False),
                    dcc.Graph(id="graph:temperature", animate=False),
                ],
            ),
            # Display info and buttons
            html.Div(
                children=[
                    html.Time(id="time"),
                    html.Div(id="debug-text"),
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


def static_humidity() -> html.Div:
    return html.Div(
        children=[
            html.Img(src="assets/fig_humidity.png"),
        ]
    )


def static_temperature() -> html.Div:
    return html.Div(
        children=[
            html.Img(src="assets/fig_temperature.png"),
        ]
    )