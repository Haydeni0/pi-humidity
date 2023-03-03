from dash_extensions.enrich import register_page, html

register_page(__name__, path="/")

layout = html.Div(
    children=[
        html.H1("aosihdoaishd")
        # html.Img(src="assets.fig_humidity.png")
    ]
)
