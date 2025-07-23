# Import packages
import tempfile, os
import flask, sqlite3
from flask import g
from flask_sqlalchemy import SQLAlchemy
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# temp_dir = tempfile.gettempdir()
# temp_sqlite_db = os.path.join(temp_dir, "XSUI_sqlite.db")

# Initialize Flask server
server = flask.Flask(__name__)
server.app_context().push()
# server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + temp_sqlite_db
# server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)

# Initialize the app - incorporate a Dash Bootstrap theme
external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, server=server, external_stylesheets=external_stylesheets)
# db = SQLAlchemy(server)
# # db.init_app(server)
# # db = SQLAlchemy(server)
# import XSUI.webapp.dash.models
# # Setup the database
# db.create_all()

# print("Tables created: ", db.Model.metadata.tables.keys())

# print("Database initialized at:", temp_sqlite_db)


# Create the tabs
from XSUI.webapp.dash.tabs import CalibrationTab
from XSUI.webapp.dash.tabs import GIWAXSTab
from XSUI.webapp.dash.tabs import WAXSTab

calibrant_tab = CalibrationTab()
giwaxs_tab = GIWAXSTab()
waxs_tab = WAXSTab()

# App layout
app.layout = dbc.Container(
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
        dcc.Tabs([calibrant_tab, giwaxs_tab, waxs_tab]),
    ],
    fluid=True,
)

# Run the app
if __name__ == "__main__":
    # import the call backs
    from XSUI.webapp.dash.callbacks import *

    app.run(debug=True)
