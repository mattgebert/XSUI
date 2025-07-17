# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

from XSUI.webapp.dash.tabs import CalibrationTab
from XSUI.webapp.dash.tabs import GIWAXSTab
from XSUI.webapp.dash.tabs import WAXSTab

# Initialize the app - incorporate a Dash Bootstrap theme
external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=external_stylesheets)

calibrant_tab = CalibrationTab()
giwaxs_tab = GIWAXSTab()
waxs_tab = WAXSTab()

# App layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                html.Div(
                    "WAXS / GI-WAXS Viewer", className="text-primary text-center fs-1"
                )
            ]
        ),
        dbc.Row(
            [
                html.Div(
                    "Powered by pyFAI / Dash / Plotly",
                    className="text-secondary text-center fs-5",
                )
            ]
        ),
        dcc.Tabs([calibrant_tab, giwaxs_tab, waxs_tab]),
    ],
    fluid=True,
)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
