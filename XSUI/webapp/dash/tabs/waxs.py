# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc


class WAXSTab(dcc.Tab):
    def __init__(self, **kwargs):
        kwargs.setdefault("label", "WAXS")
        kwargs.setdefault("id", "tab-waxs")
        if "children" in kwargs:
            raise ValueError("WAXSTab should not have children defined.")

        # Define the class layout
        layout = [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                "WAXS Data", className="text-secondary text-left fs-5"
                            ),
                            dash_table.DataTable(
                                data=None,
                                page_size=12,
                                style_table={"overflowX": "auto"},
                            ),
                        ],
                    )
                ]
            ),
            dbc.Row(
                [
                    ### Placeholder for Point of normal incidence data.
                ]
            ),
            dcc.Graph(figure={}, id="waxs-plot"),
        ]
        super().__init__(layout, **kwargs)
