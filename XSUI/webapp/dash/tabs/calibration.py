# Import packages
from dash import html, dcc
import dash_bootstrap_components as dbc
from pyFAI.detectors import _detector_class_names
from pyFAI.calibrant import ALL_CALIBRANTS


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
                                                id="calibration_tab-upload_poni",
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
                            dbc.Row(
                                html.Div(
                                    # Use detector mask toggle
                                    dbc.Checkbox(
                                        id="calibration_tab-input-use_detector_mask",
                                        label="Use Detector Mask",
                                        value=True,
                                    ),
                                ),
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
                                        id="calibration_tab-calibrant_dropdown",
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
                            dbc.Row(
                                [
                                    dcc.Graph(
                                        figure={
                                            "layout": {
                                                "title": "Calibrant Image (Draw Pixel Mask)"
                                            }
                                        },
                                        id="calibration_tab-image_plot",
                                        config={
                                            "modeBarButtonsToAdd": [
                                                # "drawline",
                                                # "drawopenpath",
                                                "drawclosedpath",
                                                "drawcircle",
                                                "drawrect",
                                                "eraseshape",
                                            ]
                                        },
                                    ),
                                    dcc.Store(
                                        id="calibration_tab-image_data", data=None
                                    ),
                                    dcc.Store(
                                        id="calibration_tab-image_plot_mask", data=None
                                    ),
                                ]
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(figure={}, id="calibration_tab-calibration_plot"),
                        ]
                    ),
                ]
            ),
        ]
        super().__init__(layout, **kwargs)
