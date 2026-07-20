#This file creates the Dash app that is used throughout the project.
#I kept it in a separate file so every part of the project uses the same app instance.

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
app.title = "UK Job Market Platform"
server = app.server
