# Import packages
from typing import Optional
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import fabio.readbytestream
import pandas as pd
import numpy as np
import plotly.express as px, plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from pyFAI.detectors import _detector_class_names
from pyFAI.calibrant import ALL_CALIBRANTS
from pyFAI.io.ponifile import PoniFile
import fabio

import os
import base64
import io
import json
import scipy.constants as sc
import datetime

# Define editable elements
# poni_file = dcc.Store(id='calibration_tab-poni_file', data='')
# poni_filename = html.Div(id="poni-filename", className="text-secondary text-left fs-7",)
# poni_wavelength = dcc.Input(id="calibration_tab-input-wavelength", type="number", placeholder="Wavelength (meters)", className="form-control")
# poni_energy = dcc.Input(id="calibration_tab-input-energy", type="number", placeholder="Energy (eV)", className="form-control",)
# poni_sdd = dcc.Input(id="calibration_tab-input-sdd", type="number", placeholder="Sample-Detector Distance (meters)", className="form-control",)
# poni_poni1 = dcc.Input(id="calibration_tab-input-poni1", type="number", placeholder="PONI1 (meters)", className="form-control",)
# poni_poni2 = dcc.Input(id="calibration_tab-input-poni2", type="number", placeholder="PONI2 (meters)", className="form-control",)
# poni_rot1 = dcc.Input(id="calibration_tab-input-rot1", type="number", placeholder="Rotation 1 (degrees)", className="form-control",)
# poni_rot2 = dcc.Input(id="calibration_tab-input-rot2", type="number", placeholder="Rotation 2 (degrees)", className="form-control",)
# poni_rot3 = dcc.Input(id="calibration_tab-input-rot3", type="number", placeholder="Rotation 3 (degrees)", className="form-control",)
# poni_detector_dropdown = dcc.Dropdown(
#     id="calibration_tab-input-detector_dropdown",
#     options=[
#         {"label": name, "value": name}
#         for name in _detector_class_names
#     ],
#     value=None,
# ),


class CalibrationTab(dcc.Tab):
    #################################################
    #### LAYOUT / INITIALIZATION
    #################################################
    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Calibration")
        kwargs.setdefault("className", "text-secondary text-left fs-3")
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
                                                className="text-secondary text-left fs-4",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Button(
                                                "Download PONI",
                                                id="calibration_tab-btn-download_poni",
                                            ),
                                            dcc.Download(
                                                id="calibration_tab-download-poni"
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Upload(
                                                id="calibration_tab-upload-poni",
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
                                        id="poni-filename",
                                        className="text-secondary text-left fs-7",
                                    ),
                                ]
                            ),
                            # TODO: Do I need store?
                            dcc.Store(id="calibration_tab-poni_file", data=""),
                            # Detector Properties
                            dbc.Row(
                                [
                                    html.Div(
                                        "Detector",
                                        className="text-secondary text-left fs-5",
                                    ),
                                ]
                            ),
                            ## Dropdown for detector type
                            dcc.Dropdown(
                                id="calibration_tab-input-detector_dropdown",
                                options=[
                                    {"label": name, "value": name}
                                    for name in _detector_class_names
                                ],
                                value=None,
                            ),
                            # PONI Properties
                            dbc.Row(
                                [
                                    html.Div(
                                        "PONI Properties",
                                        className="text-secondary text-left fs-5",
                                    ),
                                ]
                            ),
                            ## Edit for wavelength
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Row(
                                                [
                                                    html.Div(
                                                        "Wavelength (meters):",
                                                        className="text-secondary text-left fs-9",
                                                    )
                                                ]
                                            ),
                                            dcc.Input(
                                                id="calibration_tab-input-wavelength",
                                                type="number",
                                                placeholder="Wavelength (meters)",
                                                className="form-control",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Row(
                                                [
                                                    html.Div(
                                                        "Energy (eV):",
                                                        className="text-secondary text-left fs-9",
                                                    )
                                                ]
                                            ),
                                            dcc.Input(
                                                id="calibration_tab-input-energy",
                                                type="number",
                                                placeholder="Energy (eV)",
                                                className="form-control",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ]
                            ),
                            ## Edit for sample-detector distance
                            dbc.Row(
                                [
                                    html.Div(
                                        "Sample-Detector Distance (meters):",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-sdd",
                                type="number",
                                placeholder="Sample-Detector Distance (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 1
                            dbc.Row(
                                [
                                    html.Div(
                                        "PONI-1 (meters):",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-poni1",
                                type="number",
                                placeholder="PONI1 (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 2
                            dbc.Row(
                                [
                                    html.Div(
                                        "PONI-2 (meters)",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-poni2",
                                type="number",
                                placeholder="PONI2 (meters)",
                                className="form-control",
                            ),
                            ## Edit for rotation 1
                            dbc.Row(
                                [
                                    html.Div(
                                        "Rotation 1 (degrees):",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-rot1",
                                type="number",
                                placeholder="Rotation 1 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 2
                            dbc.Row(
                                [
                                    html.Div(
                                        "Rotation 2 (degrees):",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-rot2",
                                type="number",
                                placeholder="Rotation 2 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 3
                            dbc.Row(
                                [
                                    html.Div(
                                        "Rotation 3 (degrees):",
                                        className="text-secondary text-left fs-9",
                                    )
                                ]
                            ),
                            dcc.Input(
                                id="calibration_tab-input-rot3",
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
                                            {"label": cal, "value": cal}
                                            for cal in ALL_CALIBRANTS.keys()
                                            # if cal != "AgBeh"
                                        ],
                                        value="AgBeh",
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
                                    # Upload File Button
                                    dcc.Upload(
                                        id="calibration_tab-upload_calibration_data",
                                        children=html.Button(
                                            "Upload Calibration Data File"
                                        ),
                                        multiple=False,
                                    ),
                                    html.Div(id="calibration_tab-uploaded_filename"),
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
#### Functions
#################################################
def decode_PONI_file(contents: str) -> PoniFile:
    """

    Copied from pyFAI.io.ponifile.PoniFile.read_from_string
    TODO: Have a method that can read from a string IO buffer instead of a file path.
    """
    # First split by sub dict groups, then by lines
    import collections

    data = collections.OrderedDict()
    poni = PoniFile()
    for line in contents.splitlines():
        if line.startswith("#") or (":" not in line):
            continue
        words = line.split(":", 1)

        key = words[0].strip().lower()
        try:
            value = words[1].strip()
        except Exception as error:  # IGNORE:W0703:
            print("Error %s with line: %s", error, line)
        data[key] = value
    poni.read_from_dict(data)
    return poni


def wavelength_to_energy(wavelength: float) -> float:
    """
    Convert wavelength in m to energy in eV.
    Uses the formula E = hc / λ, where h is Planck's constant and c is the speed of light.
    """
    if wavelength <= 0:
        wavelength = abs(wavelength)
    return sc.h * sc.c / (wavelength) / sc.e


#################################################
#### CALLBACKS
#################################################


### Poni File
@callback(
    Output("calibration_tab-poni_file", "data"),
    Output("poni-filename", "children"),
    Input("calibration_tab-upload-poni", "filename"),
    Input("calibration_tab-upload-poni", "contents"),
    prevent_initial_call=True,
    running=[(Output("calibration_tab-upload-poni", "disabled"), True, False)],
)
def upload_poni_file(filename: str, contents: str) -> tuple[PoniFile | None, str]:
    """Process the uploaded PONI file and return its contents."""
    if filename:
        # Decode the base64 contents
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        # perform a second decode from bytes to string
        decoded = decoded.decode("utf-8")

        try:
            poni_file = decode_PONI_file(decoded)
            return json.dumps(poni_file.as_dict()), filename
        except Exception as e:
            return None, f"Error loading PONI file `{filename}`:\n{str(e)}"
    return None, "No PONI file uploaded."


@callback(
    Output("calibration_tab-download-poni", "data"),
    Input("calibration_tab-btn-download_poni", "n_clicks_timestamp"),
    State("calibration_tab-input-wavelength", "value"),
    State("calibration_tab-input-sdd", "value"),
    State("calibration_tab-input-poni1", "value"),
    State("calibration_tab-input-poni2", "value"),
    State("calibration_tab-input-rot1", "value"),
    State("calibration_tab-input-rot2", "value"),
    State("calibration_tab-input-rot3", "value"),
    State("calibration_tab-input-detector_dropdown", "value"),
    prevent_initial_call=True,
)
def save_poni_file(
    n_clicks_timestamp: int,
    wavelength: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
    detector: Optional[str],
) -> dict:
    """Save the PONI file to a specific location."""
    file = PoniFile(
        **{
            "dist": sdd,
            "poni1": poni1,
            "poni2": poni2,
            "rot1": rot1,
            "rot2": rot2,
            "rot3": rot3,
            "wavelength": wavelength,
            "detector": detector,
        }
    )
    # Get file output as string
    f = io.StringIO()
    file.write(f)
    f.seek(0)
    # Convert string to bytes
    file_bytes = f.read().encode("utf-8")
    return dcc.send_bytes(
        file_bytes,
        f"{datetime.datetime.today().strftime('%Y-%m-%d')}-{detector}.poni",
        None,
    )


# Propagate PONI file data
@callback(
    Output("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_detector_dropdown(poni_file: str) -> Optional[str]:
    """Update the detector dropdown based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        detector = poni_dict.get("detector")
        if detector in _detector_class_names:
            return detector
        else:
            print(f"Detector {detector} not found in known detector classes.")
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-wavelength", "value"),
    Output("calibration_tab-input-energy", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_wavelength_energy_input(
    poni_file: str,
) -> tuple[Optional[float], Optional[float]]:
    """Update the wavelength input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        wavelength = poni_dict.get("wavelength")
        if wavelength is not None:
            wavelength = float(wavelength)
            energy = wavelength_to_energy(wavelength)
            return wavelength, energy
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_sample_detector_distance_input(poni_file: str) -> Optional[float]:
    """Update the sample-detector distance input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        distance = poni_dict.get("dist")
        if distance is not None:
            return float(distance)
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_poni1_input(poni_file: str) -> Optional[float]:
    """Update the PONI 1 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        poni1 = poni_dict.get("poni1")
        if poni1 is not None:
            return float(poni1)
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_poni2_input(poni_file: str) -> Optional[float]:
    """Update the PONI 2 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        poni2 = poni_dict.get("poni2")
        if poni2 is not None:
            return float(poni2)
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_rotation1_input(poni_file: str) -> Optional[float]:
    """Update the rotation 1 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation1 = poni_dict.get("rot1")
        if rotation1 is not None:
            return float(rotation1)
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_rotation2_input(poni_file: str) -> Optional[float]:
    """Update the rotation 2 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation2 = poni_dict.get("rot2")
        if rotation2 is not None:
            return float(rotation2)
    raise PreventUpdate


@callback(
    Output("calibration_tab-input-rot3", "value"),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_rotation3_input(poni_file: str) -> Optional[float]:
    """Update the rotation 3 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation3 = poni_dict.get("rot3")
        if rotation3 is not None:
            return float(rotation3)
    raise PreventUpdate


## Calibration Data Upload
@callback(
    Output("calibration-plot", "figure"),
    Output("calibration_tab-uploaded_filename", "children"),
    Input("calibration_tab-upload_calibration_data", "contents"),
    Input("calibration_tab-upload_calibration_data", "filename"),
    State("calibrant-dropdown", "value"),
    prevent_initial_call=True,
    running=[
        (Output("calibration_tab-upload_calibration_data", "disabled"), True, False)
    ],
)
def upload_calibration_data(
    contents: str, filename: str, calibrant: str
) -> tuple[go.Figure, str]:
    """Process the uploaded calibration data and return a plot."""
    if contents:
        # Decode the base64 contents
        content_type, content_string = contents.split(",")
        print("Got content type:", content_type, "for filename:", filename)
        decoded = base64.b64decode(content_string)
        byte_buffer_data = io.BytesIO(
            decoded
        )  # Use BytesIO to read the bytes as a file-like object
        byte_buffer_data.name = filename
        byte_buffer_data.seek(0)
        head = byte_buffer_data.read(50)
        print(head)
        byte_buffer_data.seek(0)

        # # Convert bytes to string
        # str_data = decoded.decode('utf-8')
        # # Read the data into a StringIO buffer
        # str_buffer_data = io.StringIO(str_data)  # Use StringIO to read the string as a file-like object
        fabio_data = fabio.openimage._openimage(byte_buffer_data)

        data = fabio_data.data
        print("Got data:", data.shape)

        fig = px.imshow(
            fabio_data.data,
            color_continuous_scale="inferno",
            title=f"Calibration Data for {calibrant}",
            labels={"color": "Intensity"},
        )
        return fig, filename

    raise PreventUpdate
