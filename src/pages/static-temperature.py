from dash_extensions.enrich import register_page, html
import layouts
register_page(__name__, title="Temperature")

layout = layouts.static_temperature()
