from dash_extensions.enrich import register_page, html
import layouts

# Use this page as the default one (path "/")
register_page(__name__, path="/")

layout = layouts.dhtPlotter()