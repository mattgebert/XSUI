# Import packages
from typing import Optional
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

from pyFAI.detectors import _detector_class_names
from pyFAI.calibrant import ALL_CALIBRANTS


class CalibrationTab(dcc.Tab):
    #################################################
    #### LAYOUT / INITIALIZATION
    #################################################
    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Calibration")
        kwargs.setdefault("id", "tab-calibration")
        if "children" in kwargs:
            raise ValueError("CalibrationTab should not have children defined.")

        # Define the class layout
        layout = [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # PONI title
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "PONI File",
                                                className="text-secondary text-left fs-5",
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Upload(
                                                id="upload-poni",
                                                children=html.Button(
                                                    "Upload PONI File"
                                                ),
                                                multiple=False,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ]
                            ),
                            ## Div for uploaded PONI file path.
                            dbc.Row(
                                [
                                    html.Div(
                                        id="poni-file-path",
                                        className="text-secondary text-left fs-7",
                                    ),
                                ]
                            ),
                            # TODO: Do I need store?
                            # dcc.Store(id='calibration_tab-poni_file_path', data=''),
                            # dcc.Store(id='calibration_tab-detector', data=''),
                            # dcc.Store(id='calibration_tab-calibrant', data=''),
                            # dcc.Store(id='calibration_tab-calibration_data', data=''),
                            # dcc.Store(id='calibration_tab-wavelength', data=''),
                            # dcc.Store(id='calibration_tab-sample_detector_distance', data=''),
                            # dcc.Store(id='calibration_tab-poni1', data=''),
                            # dcc.Store(id='calibration_tab-poni2', data=''),
                            # dcc.Store(id='calibration_tab-rotation1', data=''),
                            # dcc.Store(id='calibration_tab-rotation2', data=''),
                            # dcc.Store(id='calibration_tab-rotation3', data=''),
                            # Detector Properties
                            dbc.Row(
                                [
                                    html.Div(
                                        "Detector",
                                        className="text-secondary text-left fs-7",
                                    ),
                                ]
                            ),
                            ## Dropdown for detector type
                            dcc.Dropdown(
                                id="detector-dropdown",
                                options=[
                                    {"label": name, "value": name}
                                    for name in _detector_class_names
                                ],
                                value="detector",
                            ),
                            # PONI Properties
                            dbc.Row(
                                [
                                    html.Div(
                                        "PONI Properties",
                                        className="text-secondary text-left fs-7",
                                    ),
                                ]
                            ),
                            ## Edit for wavelength
                            dcc.Input(
                                id="wavelength-input",
                                type="number",
                                placeholder="Wavelength (nm)",
                                className="form-control",
                            ),
                            ## Edit for sample-detector distance
                            dcc.Input(
                                id="sample-detector-distance-input",
                                type="number",
                                placeholder="Sample-Detector Distance (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 1
                            dcc.Input(
                                id="poni1-input",
                                type="number",
                                placeholder="PONI 1 (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 2
                            dcc.Input(
                                id="poni2-input",
                                type="number",
                                placeholder="PONI 2 (meters)",
                                className="form-control",
                            ),
                            ## Edit for rotation 1
                            dcc.Input(
                                id="rotation1-input",
                                type="number",
                                placeholder="Rotation 1 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 2
                            dcc.Input(
                                id="rotation2-input",
                                type="number",
                                placeholder="Rotation 2 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 3
                            dcc.Input(
                                id="rotation3-input",
                                type="number",
                                placeholder="Rotation 3 (degrees)",
                                className="form-control",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            # Calibratant Selection
                            dbc.Row(
                                [
                                    html.Div(
                                        "Calibration Data",
                                        className="text-secondary text-left fs-5",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    html.Div(
                                        "Select Calibrant:",
                                        className="text-secondary text-left fs-6",
                                    ),
                                    dcc.Dropdown(
                                        id="calibrant-dropdown",
                                        options=[
                                            # {'label': 'AgBeh', 'value': 'AgBh'},
                                        ]
                                        + [
                                            {"label": cal, "value": cal}
                                            for cal in ALL_CALIBRANTS.keys()
                                            if cal != "AgBeh"
                                        ],
                                        value="calibrant",
                                    ),
                                ]
                            ),
                            # Calibration Data Selection
                            dbc.Row(
                                [
                                    html.Div(
                                        "Select Calibration Data:",
                                        className="text-secondary text-left fs-6",
                                    ),
                                    dcc.Dropdown(
                                        id="calibration-data-dropdown",
                                        options=[
                                            # {'label': 'Data1', 'value': 'data1'},
                                        ],
                                        value="calibration_data",
                                    ),
                                ]
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(figure={}, id="calibration-plot"),
                        ]
                    ),
                ]
            ),
        ]
        super().__init__(layout, **kwargs)

    #################################################
    #### CALLBACKS
    #################################################
    @callback(Output("poni-file-path", "children"), Input("upload-poni", "filename"))
    def update_poni_file_path(filename: str) -> str:
        """Update the PONI file path display."""
        if filename:
            self.poni_file_path = filename
            return f"PONI File Path: {filename}"
        return "No PONI file uploaded."
