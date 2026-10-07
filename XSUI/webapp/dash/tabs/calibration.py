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
            dcc.Store(id="calibration_tab-poni_file", data=None),
            dcc.Store(id="calibration_tab-image_path", data=None),
            dcc.Store(id="calibration_tab-image_data", data=None),
            dcc.Store(id="calibration_tab-image_plot_mask", data=None),
            dcc.Store(id="calibration_tab-cache", data={}, storage_type="local"),
            dcc.Store(id="calibration_tab-selected_label", data=None),
            dcc.Store(id="calibration_tab-ready", data=False),
            dcc.Store(id="calibration_tab-display_mode", data="pixel"),
            dcc.Store(id="calibration_tab-ring_q_values", data=[]),
            dcc.Store(id="calibration_tab-qspace_cache", data=None),
            dcc.Store(id="calibration_tab-suppress_invalidate", data=False),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div("PONI File", className="text-secondary text-left fs-4"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Button(
                                            "Select PONI File",
                                            id="calibration_tab-btn-select_poni",
                                            className="btn btn-primary",
                                        ),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Button(
                                                "Download PONI",
                                                id="calibration_tab-btn-download_poni",
                                                className="btn btn-outline-secondary",
                                            ),
                                            dcc.Download(
                                                id="calibration_tab-download-poni"
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(id="poni-filename", className="text-secondary text-left fs-7 mb-3"),
                            html.Div(
                                "Not calibrated",
                                id="calibration_tab-calibrated_indicator",
                                className="fw-bold mb-2",
                                style={
                                    "color": "#721c24",
                                    "backgroundColor": "#f8d7da",
                                    "border": "1px solid #f5c6cb",
                                    "padding": "0.25rem 0.5rem",
                                    "borderRadius": "0.25rem",
                                    "display": "inline-block",
                                },
                            ),
                            html.Div("Detector", className="text-secondary text-left fs-5"),
                            dcc.Dropdown(
                                id="calibration_tab-input-detector_dropdown",
                                options=[{"label": name, "value": name} for name in _detector_class_names],
                                value=None,
                                className="mb-2",
                            ),
                            dbc.Checkbox(
                                id="calibration_tab-input-use_detector_mask",
                                label="Use Detector Mask",
                                value=True,
                                className="mb-3",
                            ),
                            html.Div("PONI Properties", className="text-secondary text-left fs-5"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div("Wavelength (meters)", className="text-secondary text-left fs-9"),
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
                                            html.Div("Energy (eV)", className="text-secondary text-left fs-9"),
                                            dcc.Input(
                                                id="calibration_tab-input-energy",
                                                type="number",
                                                placeholder="Energy (eV)",
                                                className="form-control",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div("Sample-Detector Distance (meters)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-sdd", type="number", className="form-control mb-2"),
                            html.Div("PONI-1 (meters)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-poni1", type="number", className="form-control mb-2"),
                            html.Div("PONI-2 (meters)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-poni2", type="number", className="form-control mb-2"),
                            html.Div("Rotation 1 (degrees)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-rot1", type="number", className="form-control mb-2"),
                            html.Div("Rotation 2 (degrees)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-rot2", type="number", className="form-control mb-2"),
                            html.Div("Rotation 3 (degrees)", className="text-secondary text-left fs-9"),
                            dcc.Input(id="calibration_tab-input-rot3", type="number", className="form-control mb-2"),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.Div("Calibration Data", className="text-secondary text-left fs-5"),
                            html.Div("Select Calibrant", className="text-secondary text-left fs-6"),
                            dcc.Dropdown(
                                id="calibration_tab-calibrant_dropdown",
                                options=[{"label": cal, "value": cal} for cal in ALL_CALIBRANTS.keys()],
                                value="AgBeh",
                                className="mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Button(
                                            "Select Calibration Image",
                                            id="calibration_tab-btn-select_calibration_data",
                                            className="btn btn-primary",
                                        ),
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div("Rings:", className="text-secondary text-left fs-7"),
                                            dcc.Input(
                                                id="calibration_tab-input-max_rings",
                                                type="number",
                                                value=5,
                                                min=1,
                                                step=1,
                                                className="form-control",
                                                placeholder="Max rings",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            dcc.RadioItems(
                                id="calibration_tab-display_mode_toggle",
                                options=[
                                    {"label": "Pixel", "value": "pixel"},
                                    {"label": "Q-space", "value": "qspace"},
                                ],
                                value="pixel",
                                inline=True,
                                style={"pointerEvents": "none", "opacity": 0.5},
                                className="mb-2",
                            ),
                            html.Div(id="calibration_tab-uploaded_filename", className="text-secondary text-left fs-7 mb-2"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Input(
                                            id="calibration_tab-input-label",
                                            type="text",
                                            placeholder="Calibration label",
                                            className="form-control",
                                        ),
                                        width=7,
                                    ),
                                    dbc.Col(
                                        html.Button(
                                            "Run Calibration",
                                            id="calibration_tab-btn-run_calibration",
                                            className="btn btn-success w-100",
                                        ),
                                        width=5,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            dcc.Dropdown(id="calibration_tab-cache_dropdown", placeholder="Cached calibrations", className="mb-2"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Button(
                                            "Load Selected",
                                            id="calibration_tab-btn-load_cache",
                                            className="btn btn-outline-secondary w-100",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        html.Button(
                                            "Delete Selected",
                                            id="calibration_tab-btn-delete_cache",
                                            className="btn btn-outline-warning w-100",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        html.Button(
                                            "Clear All",
                                            id="calibration_tab-btn-clear_cache",
                                            className="btn btn-outline-danger w-100",
                                        ),
                                        width=4,
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(id="calibration_tab-status", className="text-secondary text-left fs-7 mb-2"),
                            dcc.Graph(
                                figure={"layout": {"title": "Calibrant Image (Draw Pixel Mask)"}},
                                id="calibration_tab-image_plot",
                                config={
                                    "modeBarButtonsToAdd": [
                                        "drawclosedpath",
                                        "drawcircle",
                                        "drawrect",
                                        "eraseshape",
                                    ]
                                },
                            ),
                        ],
                        width=9,
                    ),
                ]
            ),
        ]
        super().__init__(layout, **kwargs)
