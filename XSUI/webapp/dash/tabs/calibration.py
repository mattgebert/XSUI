# Import packages
from typing import Optional
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

from pyFAI.detectors import _detector_class_names
from pyFAI.calibrant import ALL_CALIBRANTS
from pyFAI.io.ponifile import PoniFile

import os
import base64
import io
import json
import scipy.constants as sc

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
                            dcc.Store(id='calibration_tab-poni_file', data=''),
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
                                        className="text-secondary text-left fs-5",
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
                                        className="text-secondary text-left fs-5",
                                    ),
                                ]
                            ),
                            ## Edit for wavelength
                            dbc.Row([
                                dbc.Col([
                                    dbc.Row([html.Div("Wavelength (meters):", className="text-secondary text-left fs-9")]),
                                    dcc.Input(
                                        id="wavelength-input",
                                        type="number",
                                        placeholder="Wavelength (meters)",
                                        className="form-control",
                                    )], width=6),
                                dbc.Col([
                                    dbc.Row([html.Div("Energy (eV):", className="text-secondary text-left fs-9")]),
                                    dcc.Input(
                                        id="energy-input",
                                        type="number",
                                        placeholder="Energy (eV)",
                                        className="form-control",
                                    )], width=6),
                            ]),
                            
                            ## Edit for sample-detector distance
                            dbc.Row([html.Div("Sample-Detector Distance (meters):", className="text-secondary text-left fs-9")]),
                            dcc.Input(
                                id="sample-detector-distance-input",
                                type="number",
                                placeholder="Sample-Detector Distance (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 1
                            
                            dbc.Row([html.Div("PONI-1 (meters):", className="text-secondary text-left fs-9")]),
                            dcc.Input(
                                id="poni1-input",
                                type="number",
                                placeholder="PONI 1 (meters)",
                                className="form-control",
                            ),
                            ## Edit for PONI 2
                            dbc.Row([html.Div("PONI-2 (meters)", className="text-secondary text-left fs-9")]),
                            dcc.Input(
                                id="poni2-input",
                                type="number",
                                placeholder="PONI 2 (meters)",
                                className="form-control",
                            ),
                            ## Edit for rotation 1
                            dbc.Row([html.Div("Rotation 1 (degrees):", className="text-secondary text-left fs-9")]),
                            dcc.Input(
                                id="rotation1-input",
                                type="number",
                                placeholder="Rotation 1 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 2
                            dbc.Row([html.Div("Rotation 2 (degrees):", className="text-secondary text-left fs-9")]),
                            dcc.Input(
                                id="rotation2-input",
                                type="number",
                                placeholder="Rotation 2 (degrees)",
                                className="form-control",
                            ),
                            ## Edit for rotation 3
                            dbc.Row([html.Div("Rotation 3 (degrees):", className="text-secondary text-left fs-9")]),
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
                                    # Upload File Button 
                                    dcc.Upload(
                                        id="upload-calibration-data",
                                        children=html.Button(
                                            "Upload Calibration Data File"
                                        ),
                                        multiple=False,
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
@callback(Output("calibration_tab-poni_file", "data"),
            Output("poni-file-path", "children"),
            Input("upload-poni", "filename"), 
            Input("upload-poni", "contents"))
def update_poni_file(filename: str, contents: str) -> tuple[PoniFile | None, str]:
    """Update the PONI file path display."""
    if filename:
        # Decode the base64 contents
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        print("Decode:", decoded)
        # perform a second decode from bytes to string
        decoded = decoded.decode('utf-8') 
        
        try: 
            poni_file = decode_PONI_file(decoded)
            return json.dumps(poni_file.as_dict()), filename
        except Exception as e:
            return None, f"Error loading PONI file `{filename}`:\n{str(e)}"
    return None, "No PONI file uploaded."

# Propagate PONI file data
@callback(Output("detector-dropdown", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_detector_dropdown(poni_file: str) -> Optional[str]:
    """Update the detector dropdown based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        detector = poni_dict.get("detector")
        if detector in _detector_class_names:
            return detector
        else:
            print(f"Detector {detector} not found in known detector classes.")
    return None

@callback(Output("wavelength-input", "value"),
          Output("energy-input", "value"),
          Input("calibration_tab-poni_file", "data"))
def update_wavelength_energy_input(poni_file: str) -> tuple[Optional[float], Optional[float]]:
    """Update the wavelength input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        wavelength = poni_dict.get("wavelength")
        if wavelength is not None:
            wavelength = float(wavelength)
            energy = wavelength_to_energy(wavelength)
            return wavelength, energy
    return None, None

@callback(Output("sample-detector-distance-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_sample_detector_distance_input(poni_file: str) -> Optional[float]:
    """Update the sample-detector distance input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        distance = poni_dict.get("dist")
        if distance is not None:
            return float(distance)
    return None

@callback(Output("poni1-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_poni1_input(poni_file: str) -> Optional[float]:
    """Update the PONI 1 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        poni1 = poni_dict.get("poni1")
        if poni1 is not None:
            return float(poni1)
    return None

@callback(Output("poni2-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_poni2_input(poni_file: str) -> Optional[float]:
    """Update the PONI 2 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        poni2 = poni_dict.get("poni2")
        if poni2 is not None:
            return float(poni2)
    return None
@callback(Output("rotation1-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_rotation1_input(poni_file: str) -> Optional[float]:
    """Update the rotation 1 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation1 = poni_dict.get("rot1")
        if rotation1 is not None:
            return float(rotation1)
    return None
@callback(Output("rotation2-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_rotation2_input(poni_file: str) -> Optional[float]:
    """Update the rotation 2 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation2 = poni_dict.get("rot2")
        if rotation2 is not None:
            return float(rotation2)
    return None
@callback(Output("rotation3-input", "value"),
            Input("calibration_tab-poni_file", "data"))
def update_rotation3_input(poni_file: str) -> Optional[float]:
    """Update the rotation 3 input based on the PONI file."""
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        rotation3 = poni_dict.get("rot3")
        if rotation3 is not None:
            return float(rotation3)
    return None