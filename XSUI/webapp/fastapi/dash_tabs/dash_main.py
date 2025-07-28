# Import packages
import tempfile, os
import flask, sqlite3
from flask import g
from flask_sqlalchemy import SQLAlchemy
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# server = flask.Flask(__name__)
# server.app_context().push()
external_stylesheets = [dbc.themes.CERULEAN]
dash_app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    requests_pathname_prefix="/dashboard1/",
)

from XSUI.webapp.fastapi.dash_tabs.calibration import CalibrationTab

calibrant_tab = CalibrationTab()
# giwaxs_tab = GIWAXSTab()
# waxs_tab = WAXSTab()

# App layout
dash_app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            "WAXS / GI-WAXS Viewer",
                            className="text-primary text-center fs-1",
                        )
                    ],
                    width=8,
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                "Powered by ",
                                html.A("pyFAI", href="https://pyfai.readthedocs.io/"),
                                " / ",
                                html.A("Dash", href="https://dash.plotly.com/"),
                                " / ",
                                html.A(
                                    "Plotly",
                                    href="https://plotly.com/graphing-libraries/",
                                ),
                            ],
                            className="text-secondary text-center fs-5",
                        )
                    ],
                    width=4,
                ),
            ]
        ),
        dcc.Tabs(
            [
                calibrant_tab,
                # giwaxs_tab,
                # waxs_tab
            ]
        ),
    ],
    fluid=True,
)

# Run the app
if __name__ == "__main__":
    # import the call backs
    from XSUI.webapp.dash.callbacks import *

    dash_app.run(debug=True)
