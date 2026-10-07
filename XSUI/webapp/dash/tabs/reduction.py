"""Reduction tab layout for image and lineprofile workflows."""

from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc


class ReductionTab(dcc.Tab):
    """Top-level reduction workflow tab."""

    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Reduction")
        kwargs.setdefault("className", "text-secondary text-left fs-3")
        kwargs.setdefault("id", "tab-reduction")
        if "children" in kwargs:
            raise ValueError("ReductionTab should not have children defined.")

        layout = [
            dcc.Store(id="reduction_tab-image_files", data=[]),
            dcc.Store(id="reduction_tab-selected_files", data=[]),
            dcc.Store(id="reduction_tab-input_dir", data=None),
            dcc.Store(id="reduction_tab-output_dir", data=None),
            dcc.Store(id="reduction_tab-images_cache", data={}),
            dcc.Store(id="reduction_tab-lines_cache", data={}),
            dcc.Store(id="reduction_tab-images_preview_payload", data=None),
            dcc.Store(id="reduction_tab-lines_preview_payload", data=None),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div("Input Selection", className="text-secondary text-left fs-4"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Button(
                                                    "Select Image Directory",
                                                    id="reduction_tab-btn-select_dir",
                                                    className="btn btn-primary w-100",
                                                ),
                                                width=6,
                                            ),
                                            dbc.Col(
                                                html.Div(
                                                    id="reduction_tab-selected_dir",
                                                    className="text-secondary fs-7",
                                                ),
                                                width=6,
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    dbc.Checkbox(
                                        id="reduction_tab-input-grazing",
                                        label="Grazing Incidence (Fiber Integrator)",
                                        value=True,
                                        className="mb-2",
                                    ),
                                    html.Div("AOI Selection", className="text-secondary text-left fs-5 mt-2"),
                                    dcc.Tabs(
                                        id="reduction_tab-incidence-tabs",
                                        value="fixed",
                                        children=[
                                            dcc.Tab(
                                                label="Fixed AOI",
                                                value="fixed",
                                                children=[
                                                    html.Div(
                                                        "Angle of incidence (degrees)",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Input(
                                                        id="reduction_tab-input-fixed_aoi",
                                                        type="number",
                                                        value=0.1,
                                                        className="form-control mb-2",
                                                    ),
                                                ],
                                            ),
                                            dcc.Tab(
                                                label="AOI Regex",
                                                value="regex",
                                                children=[
                                                    html.Div(
                                                        "Regex must contain a named group (?P<aoi>...)",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Input(
                                                        id="reduction_tab-input-aoi_regex",
                                                        type="text",
                                                        placeholder=r"(?P<sample>[^_]+)_(?P<aoi>\d+p\d+)_.*",
                                                        className="form-control mb-2",
                                                    ),
                                                    html.Button(
                                                        "Show Regex Hint",
                                                        id="reduction_tab-btn-regex_hint",
                                                        className="btn btn-outline-secondary btn-sm mb-2",
                                                    ),
                                                    html.Div(id="reduction_tab-regex_hint", className="text-secondary fs-7 mb-2"),
                                                    html.Div(id="reduction_tab-regex_status", className="text-secondary fs-7"),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div("Files", className="text-secondary text-left fs-5 mt-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Button(
                                                    "Select All",
                                                    id="reduction_tab-btn-select_all",
                                                    className="btn btn-outline-primary btn-sm w-100",
                                                ),
                                                width=4,
                                            ),
                                            dbc.Col(
                                                html.Button(
                                                    "Clear Selection",
                                                    id="reduction_tab-btn-clear_selection",
                                                    className="btn btn-outline-secondary btn-sm w-100",
                                                ),
                                                width=4,
                                            ),
                                            dbc.Col(
                                                html.Div(
                                                    id="reduction_tab-file_count",
                                                    className="text-secondary fs-7",
                                                ),
                                                width=4,
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        dcc.Checklist(
                                            id="reduction_tab-file_dropdown",
                                            options=[],
                                            value=[],
                                            labelStyle={"display": "block"},
                                        ),
                                        style={
                                            "maxHeight": "18rem",
                                            "overflowY": "auto",
                                            "border": "1px solid #ced4da",
                                            "padding": "0.5rem",
                                        },
                                    ),
                                    html.Div("Output Directory", className="text-secondary text-left fs-5 mt-3"),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.Button(
                                                    "Select Output Directory",
                                                    id="reduction_tab-btn-select_output_dir",
                                                    className="btn btn-primary btn-sm w-100",
                                                ),
                                                width=5,
                                            ),
                                            dbc.Col(
                                                html.Button(
                                                    "View Output Directory",
                                                    id="reduction_tab-btn-view_output_dir",
                                                    className="btn btn-outline-secondary btn-sm w-100",
                                                ),
                                                width=3,
                                            ),
                                            dbc.Col(
                                                html.Div(
                                                    id="reduction_tab-output_dir_label",
                                                    className="text-secondary fs-7",
                                                ),
                                                width=4,
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(id="reduction_tab-output_dir_action_status", className="text-secondary fs-7"),
                                ],
                                width=5,
                            ),
                            dbc.Col(
                                [
                                    html.Div("Reduction", className="text-secondary text-left fs-4"),
                                    dcc.Tabs(
                                        id="reduction_tab-subtabs",
                                        value="images",
                                        children=[
                                            dcc.Tab(
                                                label="Images",
                                                value="images",
                                                children=[
                                                    html.Div("2D Reduction", className="text-secondary text-left fs-5 mt-2"),
                                                    dbc.Checkbox(
                                                        id="reduction_tab-input-cache_images",
                                                        label="Cache reduced images in memory",
                                                        value=True,
                                                        className="mb-2",
                                                    ),
                                                    html.Div(
                                                        "Image output mode",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="reduction_tab-output_mode",
                                                        options=[
                                                            {"label": "Cake", "value": "cake"},
                                                            {"label": "Qip Qoop", "value": "qip_qoop"},
                                                            {"label": "Qx Qy", "value": "qx_qy"},
                                                        ],
                                                        value="qip_qoop",
                                                        className="mb-2",
                                                    ),
                                                    html.Div(
                                                        "Image output regex/template",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Input(
                                                        id="reduction_tab-input-image_name_regex",
                                                        type="text",
                                                        placeholder=r"(?P<sample>[^_]+)_(?P<aoi>\d+p\d+)_.*_(?P<index>\d+)\.tif",
                                                        className="form-control mb-2",
                                                    ),
                                                    html.Div(
                                                        id="reduction_tab-image_name_example",
                                                        className="text-secondary fs-7 mb-2",
                                                    ),
                                                    html.Button(
                                                        "Run 2D Reduction",
                                                        id="reduction_tab-btn-run_images",
                                                        className="btn btn-success",
                                                    ),
                                                    dbc.Progress(
                                                        id="reduction_tab-images_progress",
                                                        value=0,
                                                        label="0%",
                                                        className="my-2",
                                                    ),
                                                    html.Div(
                                                        id="reduction_tab-images_status",
                                                        className="text-secondary fs-7 mt-2",
                                                    ),
                                                    html.Div("Image Preview", className="text-secondary text-left fs-6 mt-3"),
                                                    dcc.Dropdown(
                                                        id="reduction_tab-images_preview_dropdown",
                                                        options=[],
                                                        value=None,
                                                        placeholder="Choose a reduced image preview",
                                                        className="mb-2",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dcc.Dropdown(
                                                                    id="reduction_tab-images_zscale",
                                                                    options=[
                                                                        {"label": "Z Linear", "value": "linear"},
                                                                        {"label": "Z Log", "value": "log"},
                                                                    ],
                                                                    value="linear",
                                                                    clearable=False,
                                                                ),
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                dcc.RangeSlider(
                                                                    id="reduction_tab-images_zrange",
                                                                    min=0.0,
                                                                    max=1.0,
                                                                    value=[0.0, 1.0],
                                                                    allowCross=False,
                                                                    tooltip={"always_visible": False},
                                                                ),
                                                                width=8,
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    ),
                                                    dcc.Graph(
                                                        id="reduction_tab-images_preview_plot",
                                                        figure={"layout": {"title": "Image Reduction Preview"}},
                                                    ),
                                                ],
                                            ),
                                            dcc.Tab(
                                                label="Lineprofiles",
                                                value="lineprofiles",
                                                children=[
                                                    html.Div("1D Lineprofile Reduction", className="text-secondary text-left fs-5 mt-2"),
                                                    dbc.Checkbox(
                                                        id="reduction_tab-input-cache_lines",
                                                        label="Cache lineprofiles in memory",
                                                        value=True,
                                                        className="mb-2",
                                                    ),
                                                    html.Div(
                                                        "Lineprofile output regex/template",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Input(
                                                        id="reduction_tab-input-lineprofile_name_regex",
                                                        type="text",
                                                        placeholder=r"(?P<sample>[^_]+)_(?P<aoi>\d+p\d+)_(?P<arc1>-?\d+)_(?P<arc2>-?\d+)\.tif",
                                                        className="form-control mb-2",
                                                    ),
                                                    html.Div(
                                                        id="reduction_tab-lineprofile_regex_status",
                                                        className="text-secondary fs-7 mb-2",
                                                    ),
                                                    html.Div(
                                                        id="reduction_tab-lineprofile_name_example",
                                                        className="text-secondary fs-7 mb-2",
                                                    ),
                                                    html.Div(
                                                        "Angle arcs (degrees, one pair per line: start,end)",
                                                        className="text-secondary text-left fs-7",
                                                    ),
                                                    dcc.Textarea(
                                                        id="reduction_tab-input-arcs",
                                                        value="-90,-80\n-5,5",
                                                        className="form-control mb-2",
                                                        style={"height": "140px"},
                                                    ),
                                                    html.Button(
                                                        "Run 1D Reduction",
                                                        id="reduction_tab-btn-run_lines",
                                                        className="btn btn-success",
                                                    ),
                                                    dbc.Progress(
                                                        id="reduction_tab-lines_progress",
                                                        value=0,
                                                        label="0%",
                                                        className="my-2",
                                                    ),
                                                    html.Div(
                                                        id="reduction_tab-lines_status",
                                                        className="text-secondary fs-7 mt-2",
                                                    ),
                                                    html.Div("Lineprofile Preview", className="text-secondary text-left fs-6 mt-3"),
                                                    dcc.Dropdown(
                                                        id="reduction_tab-lines_preview_dropdown",
                                                        options=[],
                                                        value=None,
                                                        placeholder="Choose a reduced lineprofile preview",
                                                        className="mb-2",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dcc.Dropdown(
                                                                    id="reduction_tab-lines_xscale",
                                                                    options=[
                                                                        {"label": "X Linear", "value": "linear"},
                                                                        {"label": "X Log", "value": "log"},
                                                                    ],
                                                                    value="linear",
                                                                    clearable=False,
                                                                ),
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                dcc.Dropdown(
                                                                    id="reduction_tab-lines_yscale",
                                                                    options=[
                                                                        {"label": "Y Linear", "value": "linear"},
                                                                        {"label": "Y Log", "value": "log"},
                                                                    ],
                                                                    value="linear",
                                                                    clearable=False,
                                                                ),
                                                                width=6,
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    ),
                                                    dcc.Graph(
                                                        id="reduction_tab-lines_preview_plot",
                                                        figure={"layout": {"title": "Lineprofile Reduction Preview"}},
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                                width=7,
                            ),
                        ]
                    )
                ]
            ),
        ]

        super().__init__(layout, **kwargs)
