# Import packages
from typing import Optional
from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, ctx
import fabio.readbytestream
import pandas as pd
import numpy as np
import plotly.express as px, plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from pyFAI.detectors import _detector_class_names
from pyFAI.calibrant import ALL_CALIBRANTS
from pyFAI.io.ponifile import PoniFile
from pyFAI.detectors import Detector, detector_factory
import fabio
from svg.path import parse_path
import os
import base64
import io
import json
import scipy.constants as sc
import datetime

from XSUI.webapp.dash.models import (
    ImageCalibrant,
    DetectorMask,
    CustomMask,
    CompositeMask,
)
from XSUI.webapp.dash.main import db


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


def pixel_beamcentre(poni: PoniFile, detector: Detector):
    psize = detector.pixel1, detector.pixel2
    detect_coords = np.array([0, 0, 0])  # Beam centre
    pix_coords = np.array([1 / psize[0], 1 / psize[1], 0]) * (
        detect_coords - np.array([-poni.poni1, -poni.poni2, poni.dist])
    ) - np.array([0.5, 0.5, 0])
    """The pixel coordinates (y,x) of the beam centre in the image"""
    return pix_coords


#################################################
#### CALLBACKS
#################################################


### Poni File
@callback(
    Output("calibration_tab-poni_file", "data"),
    Output("poni-filename", "children"),
    Input("calibration_tab-upload_poni", "filename"),
    Input("calibration_tab-upload_poni", "contents"),
    prevent_initial_call=True,
    running=[(Output("calibration_tab-upload_poni", "disabled"), True, False)],
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
            "rot1": np.deg2rad(rot1) if rot1 is not None else 0.0,
            "rot2": np.deg2rad(rot2) if rot2 is not None else 0.0,
            "rot3": np.deg2rad(rot3) if rot3 is not None else 0.0,
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
            return np.rad2deg(float(rotation1))
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
            return np.rad2deg(float(rotation2))
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
            return np.rad2deg(float(rotation3))
    raise PreventUpdate


## Figure Generation


@callback(
    # Output("calibration_tab-image_data", "data"),
    Output("calibration_tab-image_plot", "figure"),
    Output("calibration_tab-uploaded_filename", "children"),
    Input("calibration_tab-upload_calibration_data", "contents"),
    Input("calibration_tab-upload_calibration_data", "filename"),
    Input("calibration_tab-poni_file", "data"),
    Input("calibration_tab-image_plot_mask", "data"),
    State("calibration_tab-image_plot", "figure"),
    State("calibration_tab-input-detector_dropdown", "value"),
    # State("calibration_tab-image_data", "data"),
    running=[
        (Output("calibration_tab-upload_calibration_data", "disabled"), True, False),
    ],
    prevent_initial_call=True,
)
def figure_callback(
    img_upload_contents: str,
    filename: str,
    poni_file: str,
    mask_data: np.ndarray | None,
    # figure: go.Figure, detector: str, fig_data: np.ndarray | None) -> tuple[np.ndarray | None, go.Figure, str]:
    figure: go.Figure,
    detector: str,
) -> tuple[np.ndarray | None, go.Figure, str]:
    # Get the ID name of the trigger
    trigger_id, trigger_sig = ctx.triggered[0]["prop_id"].split(".")

    print("Trigger ID:", trigger_id)
    # Whether to create a new figure or not from uploaded data:
    if trigger_id == "calibration_tab-upload_calibration_data":
        fig, fig_data = upload_calibration_data(img_upload_contents, filename)
    else:
        fig = figure
        query = db.session.query(ImageCalibrant)
        calibrant_image = query.filter_by(filename=filename)
        print("The Query is :", calibrant_image)
        calibrant_image = calibrant_image.first()
        if calibrant_image:
            fig_data = calibrant_image.image_data
        else:
            fig_data = None
            print(f"Image data for {filename} not found in database.")

    # Add beam centre scatter if PONI file is available
    if trigger_id == "calibration_tab-poni_file":
        # Update or add the beam centre scatter trace
        fig = update_image_figure_beamcentre(poni_file, fig, detector)

    if trigger_id == "calibration_tab-image_plot_mask":
        # Update or add the mask heatmap trace
        fig = update_image_figure_mask(mask_data, fig)

    return (fig_data, fig, filename)


### Calibration Data Upload
def upload_calibration_data(
    contents: str,
    filename: str,
) -> tuple[go.Figure, np.ndarray | None]:
    """
    Process the uploaded calibration data and return a plot.

    Parameters
    ----------
    contents : str
        The base64 encoded contents of the uploaded file.
    filename : str
        The name of the uploaded file.
    Returns
    -------
    fig : go.Figure
        The figure containing the calibration data.
    data : np.ndarray | None
        The image data from the uploaded file, or None if no data is available.
    """
    # A figure:
    fig: go.Figure | None = None
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

        fabio_data = fabio.open(byte_buffer_data)
        # fabio_data = fabio.openimage._openimage(byte_buffer_data)

        data = fabio_data.data

        # Place the image data into the database.
        db_img = ImageCalibrant(filename, data)
        db.session.add(db_img)
        db.session.commit()
        print("Image data added to database.")

        fig = px.imshow(
            np.log10(fabio_data.data),
            color_continuous_scale="inferno",
            title="Calibrant Image (Draw Pixel Mask)",
            labels={"color": "Intensity (log10)"},
        )
    else:
        fig = go.Figure(
            layout={
                "title": "Calibrant Image (Draw Pixel Mask)",
            }
        )
        data = None

    return fig, data


def update_image_figure_beamcentre(
    poni_file: str, figure: go.Figure, detector: str
) -> go.Figure:
    # Check if figure already has a heatmap trace
    has_beamcentre_scatter = False
    bc_obj = None
    if "data" in figure:
        for ax_obj in figure["data"]:
            if ax_obj["type"] == "scatter" and ax_obj["name"] == "Beam Centre":
                bc_obj = ax_obj
                has_beamcentre_scatter = True
                break

    bc_coords = None
    if poni_file:
        poni_dict: dict = json.loads(poni_file)
        poni = PoniFile(**poni_dict)
        det = detector_factory(detector) if detector else poni.detector
        if det:
            bc_coords = pixel_beamcentre(poni, det)

    if bc_coords is not None:
        if bc_obj:
            # Update the existing scatter trace with new beam centre coordinates
            bc_obj["x"] = [bc_coords[1]]
            bc_obj["y"] = [bc_coords[0]]
        else:
            # Create new tracefigure.add_trace(
            go.Scatter(
                x=[bc_coords[1]],
                y=[bc_coords[0]],
                mode="markers",
                marker=dict(color="red", size=10, symbol="x"),
                name="Beam Centre",
            )
    elif has_beamcentre_scatter and bc_obj:
        # If no beam centre coordinates, remove the scatter trace
        figure["data"] = [
            ax_obj
            for ax_obj in figure["data"]
            if not (ax_obj["type"] == "scatter" and ax_obj["name"] == "Beam Centre")
        ]
    return figure


def update_image_figure_mask(
    mask_data: np.ndarray | None, figure: dict | go.Figure
) -> go.Figure:
    # Check if figure already has a heatmap trace
    if isinstance(figure, dict):
        figure = go.Figure(**figure)
    has_mask_heatmap = False
    heatmap = None
    if "data" in figure:
        for ax_obj in figure["data"]:
            if ax_obj["type"] == "heatmap" and ax_obj["name"] == "Mask":
                heatmap = ax_obj
                has_mask_heatmap = True
                break

    if mask_data:
        mask_data = np.asarray(mask_data)
        # If mask data is provided, apply it to the image
        mask_shape = np.shape(mask_data)
        x, y = np.indices(mask_shape)
        colorscale = [[0, "rgba(0,0,0,0)"], [1, "rgba(0,222,256,1)"]]
        no_hover_mask_data = mask_data.astype(object)
        no_hover_mask_data[no_hover_mask_data == 0] = (
            None  # Set non-masked pixels to None
        )

        if has_mask_heatmap and heatmap:
            # Update the existing heatmap trace
            heatmap["z"] = no_hover_mask_data

        if not has_mask_heatmap:
            figure.add_heatmap(
                z=no_hover_mask_data,
                colorscale=colorscale,
                hoverongaps=False,
                colorbar=None,
                showscale=False,
                # hovertemplate="Mask",
                name="Mask",
            )
    elif has_mask_heatmap:
        # If no mask data is provided, remove the heatmap trace
        figure["data"] = [
            ax_obj
            for ax_obj in figure["data"]
            if not (ax_obj["type"] == "heatmap" and ax_obj["name"] == "Mask")
        ]
    return figure


@callback(
    Output("calibration_tab-image_plot_mask", "data"),
    Input("calibration_tab-image_plot", "relayoutData"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-input-use_detector_mask", "value"),
    # State("calibration_tab-image_data", "data"),
    State("calibration_tab-image_plot_mask", "data"),
    prevent_initial_call=True,
    running=[
        (Output("calibration_tab-upload_calibration_data", "disabled"), True, False),
        (Output("calibration_tab-upload_poni", "disabled"), True, False),
        (Output("calibration_tab-image_plot", "interactive"), False, True),
    ],
)
# def update_mask(relayoutData: dict, detector: str | None, use_mask:bool, img_data: np.ndarray, existing_mask: np.ndarray) -> np.ndarray | None:
def update_mask(
    relayoutData: dict, detector: str | None, use_mask: bool, existing_mask: np.ndarray
) -> np.ndarray | None:
    """Reconstruct the masking based on the relayout data."""

    trigger_id, trigger_sig = ctx.triggered[0]["prop_id"].split(".")

    # Query the database for the image data
    query = db.session.query(ImageCalibrant)
    if query:
        img_data = query.first().image_data
    else:
        img_data = None

    masks = []
    img_data_shape = None
    if img_data is not None:
        img_data = np.asarray(img_data)
        img_data_shape = np.shape(img_data)
        masks.append(img_data <= 0)  # Add a mask for zero values in the image data

    if detector and use_mask:
        mask = detector_factory(detector).mask
        if img_data is not None and np.shape(img_data) == mask.shape:
            masks.append(mask)
        elif img_data is None:
            img_data_shape = mask.shape
            masks.append(mask)
        else:
            print(
                f"Detector mask shape {mask.shape} does not match image data shape {np.shape(img_data)}. Skipping detector mask."
            )

    if relayoutData and "shapes" in relayoutData:
        # Process the shapes to update the mask
        shapes = relayoutData["shapes"]
        # Create numpy coordinate array
        coords = np.indices(np.asarray(img_data).shape)
        # Check each pixel is contained in any of the shapes
        for shape in shapes:
            if shape["type"] == "rect":
                mask = (
                    (coords[:, 0] >= shape["y0"])
                    & (coords[:, 0] <= shape["y1"])
                    & (coords[:, 1] >= shape["x0"])
                    & (coords[:, 1] <= shape["x1"])
                )
            elif shape["type"] == "circle":
                # Circle mask
                center_x = (shape["x0"] + shape["x1"]) / 2
                center_y = (shape["y0"] + shape["y1"]) / 2
                radius = (shape["x1"] - shape["x0"]) / 2
                mask = (
                    (coords[1] - center_x) ** 2 + (coords[0] - center_y) ** 2
                ) <= radius**2
            elif shape["type"] == "path":
                # Get the trace points
                descrption = shape["path"]
                path = parse_path(descrption)
                x_min, y_min, x_max, y_max = path.boundingbox()

                # Use ray tracing method to see if point is contained or not
                # i.e. from the point of interest, does a line intersect odd or even?
                mask = np.zeros(img_data_shape, dtype=bool)
                for y in range(img_data_shape[0]):
                    for x in range(img_data_shape[1]):
                        # Check if point (x, y) is inside the path
                        if x_min < x and x < x_max and y_min < y and y < y_max:
                            # Could be inside the path
                            intersections = 0
                            for segment in path:
                                # Check if the segment intersects with a horizontal line from (x, y)
                                # Substitute x value of point into the segment equation:
                                x0, y0 = segment.start.real, segment.start.imag
                                x1, y1 = segment.end.real, segment.end.imag
                                if (x0 < x and x < x1) or (x1 < x and x < x0):
                                    # X within the segment
                                    point = (x - x0) / (x1 - x0)
                                    if np.isclose(
                                        y, segment.point(point).imag, atol=1e-3
                                    ):
                                        # Point is on the segment
                                        intersections += 1
                            if intersections % 2 == 1:
                                mask[y, x] = True
            else:
                continue
            masks.append(mask)

    if len(masks) > 0:
        # Create a new mask
        mask = np.bitwise_or.reduce([*masks])
        return mask
    return None
