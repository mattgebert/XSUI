"""Dash callbacks for calibration and shared calibration state."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Optional

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, no_update
from dash.exceptions import PreventUpdate
from pyFAI.io.ponifile import PoniFile

from XSUI.webapp.services.calibration_service import (
    build_calibration_figure,
    build_qspace_overlay_figure,
    compute_qspace_image_data,
    deserialize_poni,
    read_calibration_image,
    read_poni_file,
    run_geometry_refinement,
    serialize_poni,
    wavelength_to_energy,
)
from XSUI.webapp.services.file_dialogs import select_file


def _status_message(message: str, *, is_error: bool = False) -> str:
    """Return formatted status message text."""
    prefix: str = "ERROR" if is_error else "INFO"
    return f"{prefix}: {message}"


def _indicator_text(calibrated: bool) -> str:
    """Return indicator label for calibration state."""
    return "Calibrated" if calibrated else "Not calibrated"


def _indicator_style(calibrated: bool) -> dict[str, str]:
    """Return style map for calibration state indicator."""
    if calibrated:
        return {
            "color": "#155724",
            "backgroundColor": "#d4edda",
            "border": "1px solid #c3e6cb",
            "padding": "0.25rem 0.5rem",
            "borderRadius": "0.25rem",
            "display": "inline-block",
        }
    return {
        "color": "#721c24",
        "backgroundColor": "#f8d7da",
        "border": "1px solid #f5c6cb",
        "padding": "0.25rem 0.5rem",
        "borderRadius": "0.25rem",
        "display": "inline-block",
    }


def _build_effective_poni(
    poni_payload: Optional[str],
    detector_name: Optional[str],
    wavelength: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
) -> Optional[PoniFile]:
    """Build the effective geometry from payload and current editor fields."""
    if poni_payload is None:
        if all(
            value is not None
            for value in [wavelength, sdd, poni1, poni2, rot1, rot2, rot3]
        ):
            return PoniFile(
                wavelength=float(wavelength),
                dist=float(sdd),
                poni1=float(poni1),
                poni2=float(poni2),
                rot1=float(np.deg2rad(rot1)),
                rot2=float(np.deg2rad(rot2)),
                rot3=float(np.deg2rad(rot3)),
                detector=detector_name,
            )
        return None

    base = deserialize_poni(poni_payload)
    effective_wavelength = wavelength
    if effective_wavelength is None and getattr(base, "wavelength", None):
        effective_wavelength = float(base.wavelength)

    if all(
        value is not None
        for value in [effective_wavelength, sdd, poni1, poni2, rot1, rot2, rot3]
    ):
        return PoniFile(
            wavelength=float(effective_wavelength),
            dist=float(sdd),
            poni1=float(poni1),
            poni2=float(poni2),
            rot1=float(np.deg2rad(rot1)),
            rot2=float(np.deg2rad(rot2)),
            rot3=float(np.deg2rad(rot3)),
            detector=detector_name or str(base.detector.__class__.__name__),
        )

    # Keep mutable fields aligned with editor values without trying to set wavelength.
    if detector_name and base.detector is None:
        base.detector = detector_name
    if sdd is not None:
        base.dist = float(sdd)
    if poni1 is not None:
        base.poni1 = float(poni1)
    if poni2 is not None:
        base.poni2 = float(poni2)
    if rot1 is not None:
        base.rot1 = float(np.deg2rad(rot1))
    if rot2 is not None:
        base.rot2 = float(np.deg2rad(rot2))
    if rot3 is not None:
        base.rot3 = float(np.deg2rad(rot3))
    return base


def _build_qspace_figure_from_cache(
    qspace_cache: dict[str, list],
    calibrant_name: str,
    ring_q_values: list[float],
) -> go.Figure:
    """Build q-space overlay figure from precomputed cache payload."""
    transformed = np.asarray(qspace_cache["z"])
    axis_x = np.asarray(qspace_cache["x"])
    axis_y = np.asarray(qspace_cache["y"])

    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            x=axis_x,
            y=axis_y,
            z=transformed,
            colorscale="Inferno",
            colorbar={"title": "log10(I)"},
            name="Q-space",
        )
    )

    for index, q_value in enumerate(ring_q_values):
        if q_value <= 0:
            continue
        theta = np.linspace(0, 2 * np.pi, 361)
        x_coords = q_value * np.cos(theta)
        y_coords = q_value * np.sin(theta)
        in_bounds = (
            (x_coords >= float(np.min(axis_x)))
            & (x_coords <= float(np.max(axis_x)))
            & (y_coords >= float(np.min(axis_y)))
            & (y_coords <= float(np.max(axis_y)))
        )
        if not np.any(in_bounds):
            continue
        figure.add_trace(
            go.Scatter(
                x=x_coords[in_bounds],
                y=y_coords[in_bounds],
                mode="lines",
                line={"color": "cyan", "width": 1, "dash": "dash"},
                name=f"{calibrant_name} ring {index + 1}",
                showlegend=index == 0,
            )
        )

    figure.update_layout(
        title="Calibrated Q-space with Calibrant Rings",
        xaxis_title="Qx (nm^-1)",
        yaxis_title="Qy (nm^-1)",
    )
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return figure


@callback(
    Output("calibration_tab-poni_file", "data"),
    Output("poni-filename", "children"),
    Output("calibration_tab-ready", "data", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "children", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "style", allow_duplicate=True),
    Output("calibration_tab-display_mode", "data", allow_duplicate=True),
    Output("calibration_tab-ring_q_values", "data", allow_duplicate=True),
    Output("calibration_tab-selected_label", "data", allow_duplicate=True),
    Output("calibration_tab-suppress_invalidate", "data", allow_duplicate=True),
    Input("calibration_tab-btn-select_poni", "n_clicks"),
    prevent_initial_call=True,
)
def select_poni_file(
    _: int,
) -> tuple[
    Optional[str],
    str,
    bool,
    str,
    dict[str, str],
    str,
    list[float],
    Optional[str],
    bool,
]:
    """Select and load a local PONI file via PyQt dialog."""
    try:
        selected_path = select_file("Select a PONI file", "PONI Files (*.poni)")
    except Exception as exc:
        return (
            None,
            _status_message(f"File dialog failed: {exc}", is_error=True),
            False,
            _indicator_text(False),
            _indicator_style(False),
            "pixel",
            [],
            None,
            False,
        )

    if not selected_path:
        return (
            no_update,
            _status_message("No PONI file selected.", is_error=True),
            False,
            _indicator_text(False),
            _indicator_style(False),
            "pixel",
            [],
            None,
            False,
        )

    try:
        poni = read_poni_file(selected_path)
    except Exception as exc:
        return (
            None,
            _status_message(f"Failed to load PONI: {exc}", is_error=True),
            False,
            _indicator_text(False),
            _indicator_style(False),
            "pixel",
            [],
            None,
            False,
        )

    return (
        serialize_poni(poni),
        f"Loaded PONI: {selected_path}",
        False,
        _indicator_text(False),
        _indicator_style(False),
        "pixel",
        [],
        None,
        True,
    )


@callback(
    Output("calibration_tab-cache_dropdown", "options"),
    Input("calibration_tab-cache", "data"),
)
def sync_cache_dropdown_options(cache_payload: Optional[dict]) -> list[dict[str, str]]:
    """Hydrate cache dropdown options from persistent local storage."""
    cache = cache_payload or {}
    return [{"label": key, "value": key} for key in sorted(cache.keys())]


@callback(
    Output("calibration_tab-ready", "data", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "children", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "style", allow_duplicate=True),
    Output("calibration_tab-display_mode", "data", allow_duplicate=True),
    Output("calibration_tab-ring_q_values", "data", allow_duplicate=True),
    Input("calibration_tab-input-wavelength", "value"),
    Input("calibration_tab-input-energy", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    State("calibration_tab-suppress_invalidate", "data"),
    prevent_initial_call=True,
)
def invalidate_calibration_on_edit(
    wavelength: Optional[float],
    energy: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
    detector_name: Optional[str],
    suppress_invalidate: Optional[bool],
) -> tuple[object, object, object, object, object]:
    """Clear calibrated state whenever the PONI editor is manually changed."""
    _ = wavelength, energy, sdd, poni1, poni2, rot1, rot2, rot3, detector_name
    if bool(suppress_invalidate):
        return no_update, no_update, no_update, no_update, no_update
    return False, _indicator_text(False), _indicator_style(False), "pixel", []


@callback(
    Output("calibration_tab-display_mode_toggle", "style"),
    Input("calibration_tab-ready", "data"),
    Input("calibration_tab-image_data", "data"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-input-energy", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
)
def update_display_toggle_style(
    calibration_ready: Optional[bool],
    image_data_payload: Optional[list],
    detector_name: Optional[str],
    energy: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
) -> dict[str, float | str]:
    """Enable the pixel/q-space toggle only once calibration is ready."""
    has_complete_poni = all(
        value is not None for value in [detector_name, energy, sdd, poni1, poni2, rot1, rot2, rot3]
    )
    can_toggle = bool(calibration_ready) or (image_data_payload is not None and has_complete_poni)
    if can_toggle:
        return {"pointerEvents": "auto", "opacity": 1.0}
    return {"pointerEvents": "none", "opacity": 0.5}


@callback(
    Output("calibration_tab-btn-run_calibration", "disabled"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-input-energy", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
)
def toggle_run_calibration_button(
    detector_name: Optional[str],
    energy: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
) -> bool:
    """Enable Run Calibration only when all required PONI fields are populated."""
    required_fields = [detector_name, energy, sdd, poni1, poni2, rot1, rot2, rot3]
    return not all(field is not None for field in required_fields)


@callback(
    Output("calibration_tab-input-energy", "value", allow_duplicate=True),
    Input("calibration_tab-input-wavelength", "value"),
    prevent_initial_call=True,
)
def sync_energy_from_wavelength(wavelength: Optional[float]) -> Optional[float]:
    """Infer energy from wavelength edits instead of mutating PONI wavelength in-place."""
    if wavelength in (None, 0):
        return no_update
    return float(wavelength_to_energy(float(wavelength)))


@callback(
    Output("calibration_tab-qspace_cache", "data"),
    Input("calibration_tab-image_data", "data"),
    Input("calibration_tab-poni_file", "data"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-input-wavelength", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
    State("calibration_tab-image_plot_mask", "data"),
    prevent_initial_call=True,
)
def precompute_qspace_cache(
    image_data_payload: Optional[list],
    poni_payload: Optional[str],
    detector_name: Optional[str],
    wavelength: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
    mask_data: Optional[list],
) -> Optional[dict[str, list]]:
    """Precompute q-space map data to make display-mode switches responsive."""
    if image_data_payload is None:
        return None

    effective_poni = _build_effective_poni(
        poni_payload=poni_payload,
        detector_name=detector_name,
        wavelength=wavelength,
        sdd=sdd,
        poni1=poni1,
        poni2=poni2,
        rot1=rot1,
        rot2=rot2,
        rot3=rot3,
    )
    if effective_poni is None:
        return None

    image_data = np.asarray(image_data_payload)
    mask = np.asarray(mask_data) if mask_data is not None else None
    transformed, axis_x, axis_y = compute_qspace_image_data(
        image_data=image_data,
        poni=effective_poni,
        mask=mask,
        npt=800,
    )
    return {
        "z": transformed.tolist(),
        "x": axis_x.tolist(),
        "y": axis_y.tolist(),
    }


@callback(
    Output("calibration_tab-image_plot", "figure", allow_duplicate=True),
    Input("calibration_tab-image_data", "data"),
    Input("calibration_tab-poni_file", "data"),
    Input("calibration_tab-display_mode_toggle", "value"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-calibrant_dropdown", "value"),
    Input("calibration_tab-input-wavelength", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
    Input("calibration_tab-qspace_cache", "data"),
    State("calibration_tab-image_plot_mask", "data"),
    State("calibration_tab-ring_q_values", "data"),
    prevent_initial_call=True,
)
def update_calibration_preview(
    image_data_payload: Optional[list],
    poni_payload: Optional[str],
    display_mode: Optional[str],
    detector_name: Optional[str],
    calibrant_name: Optional[str],
    wavelength: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
    qspace_cache: Optional[dict[str, list]],
    mask_data: Optional[list],
    ring_q_values: Optional[list[float]],
) -> go.Figure:
    """Render calibration preview in pixel or q-space using current editor geometry."""
    if image_data_payload is None:
        raise PreventUpdate

    image_data = np.asarray(image_data_payload)
    mask = np.asarray(mask_data) if mask_data is not None else None
    effective_poni = _build_effective_poni(
        poni_payload=poni_payload,
        detector_name=detector_name,
        wavelength=wavelength,
        sdd=sdd,
        poni1=poni1,
        poni2=poni2,
        rot1=rot1,
        rot2=rot2,
        rot3=rot3,
    )

    if display_mode == "qspace" and qspace_cache is not None:
        return _build_qspace_figure_from_cache(
            qspace_cache=qspace_cache,
            calibrant_name=calibrant_name or "Calibrant",
            ring_q_values=ring_q_values or [],
        )

    return build_calibration_figure(
        image_data,
        poni=effective_poni,
        detector_name=detector_name,
        calibrant_name=calibrant_name,
    )


@callback(
    Output("calibration_tab-image_path", "data"),
    Output("calibration_tab-image_data", "data"),
    Output("calibration_tab-uploaded_filename", "children"),
    Output("calibration_tab-image_plot", "figure"),
    Input("calibration_tab-btn-select_calibration_data", "n_clicks"),
    State("calibration_tab-poni_file", "data"),
    State("calibration_tab-input-detector_dropdown", "value"),
    State("calibration_tab-calibrant_dropdown", "value"),
    prevent_initial_call=True,
)
def select_calibration_image(
    _: int,
    poni_payload: Optional[str],
    detector_name: Optional[str],
    calibrant_name: Optional[str],
) -> tuple[Optional[str], Optional[list], str, go.Figure]:
    """Select local calibration image and update figure."""
    try:
        selected_path = select_file(
            "Select calibration image",
            "Detector Images (*.tif *.tiff *.edf *.cbf);;All Files (*)",
        )
    except Exception as exc:
        figure = go.Figure(layout={"title": "Calibrant Image (Draw Pixel Mask)"})
        return (
            no_update,
            no_update,
            _status_message(f"File dialog failed: {exc}", is_error=True),
            figure,
        )

    if not selected_path:
        return no_update, no_update, _status_message("No calibration image selected.", is_error=True), no_update

    try:
        image_data = read_calibration_image(selected_path)
    except Exception as exc:
        figure = go.Figure(layout={"title": "Calibrant Image (Draw Pixel Mask)"})
        return None, None, _status_message(f"Failed to load image: {exc}", is_error=True), figure

    poni = deserialize_poni(poni_payload) if poni_payload else None
    figure = build_calibration_figure(
        image_data,
        poni=poni,
        detector_name=detector_name,
        calibrant_name=calibrant_name,
    )
    return selected_path, image_data.tolist(), f"Calibration image: {selected_path}", figure


@callback(
    Output("calibration_tab-input-detector_dropdown", "value"),
    Output("calibration_tab-input-wavelength", "value"),
    Output("calibration_tab-input-energy", "value"),
    Output("calibration_tab-input-sdd", "value"),
    Output("calibration_tab-input-poni1", "value"),
    Output("calibration_tab-input-poni2", "value"),
    Output("calibration_tab-input-rot1", "value"),
    Output("calibration_tab-input-rot2", "value"),
    Output("calibration_tab-input-rot3", "value"),
    Output("calibration_tab-suppress_invalidate", "data", allow_duplicate=True),
    Input("calibration_tab-poni_file", "data"),
    prevent_initial_call=True,
)
def update_poni_inputs(poni_payload: Optional[str]) -> tuple[Any, ...]:
    """Hydrate form fields from selected or loaded PONI data."""
    if not poni_payload:
        raise PreventUpdate

    poni = deserialize_poni(poni_payload)
    wavelength = float(poni.wavelength) if poni.wavelength else None
    energy = wavelength_to_energy(wavelength) if wavelength else None
    return (
        str(poni.detector.__class__.__name__) if poni.detector else None,
        wavelength,
        energy,
        float(poni.dist),
        float(poni.poni1),
        float(poni.poni2),
        float(np.rad2deg(poni.rot1)),
        float(np.rad2deg(poni.rot2)),
        float(np.rad2deg(poni.rot3)),
        False,
    )


@callback(
    Output("calibration_tab-download-poni", "data"),
    Input("calibration_tab-btn-download_poni", "n_clicks"),
    State("calibration_tab-poni_file", "data"),
    State("calibration_tab-selected_label", "data"),
    prevent_initial_call=True,
)
def save_poni_file(
    _: int,
    poni_payload: Optional[str],
    selected_label: Optional[str],
) -> dict:
    """Download the currently selected calibration PONI."""
    if not poni_payload:
        raise PreventUpdate

    poni = deserialize_poni(poni_payload)
    file_name = f"{selected_label or 'calibration'}.poni"
    buffer = io.StringIO()
    poni.write(buffer)
    file_bytes = buffer.getvalue().encode("utf-8")
    return dcc.send_bytes(file_bytes, file_name, None)


@callback(
    Output("calibration_tab-image_plot_mask", "data"),
    Input("calibration_tab-image_plot", "relayoutData"),
    State("calibration_tab-image_data", "data"),
    prevent_initial_call=True,
)
def update_mask_from_drawing(
    relayout_data: Optional[dict],
    image_data_payload: Optional[list],
) -> Optional[list]:
    """Update binary mask from user drawing operations."""
    if image_data_payload is None:
        raise PreventUpdate

    image_data = np.asarray(image_data_payload)
    mask = np.zeros_like(image_data, dtype=bool)

    if not relayout_data or "shapes" not in relayout_data:
        return mask.tolist()

    y_coords, x_coords = np.indices(image_data.shape)
    for shape in relayout_data.get("shapes", []):
        shape_type = shape.get("type")
        if shape_type == "rect":
            x0, x1 = sorted([shape.get("x0", 0), shape.get("x1", 0)])
            y0, y1 = sorted([shape.get("y0", 0), shape.get("y1", 0)])
            mask |= (x_coords >= x0) & (x_coords <= x1) & (y_coords >= y0) & (y_coords <= y1)
        elif shape_type == "circle":
            x0, x1 = shape.get("x0", 0), shape.get("x1", 0)
            y0, y1 = shape.get("y0", 0), shape.get("y1", 0)
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            radius = abs(x1 - x0) / 2
            mask |= (x_coords - center_x) ** 2 + (y_coords - center_y) ** 2 <= radius**2

    return mask.tolist()


@callback(
    Output("calibration_tab-image_plot", "figure", allow_duplicate=True),
    Output("calibration_tab-cache", "data"),
    Output("calibration_tab-status", "children"),
    Output("calibration_tab-poni_file", "data", allow_duplicate=True),
    Output("calibration_tab-selected_label", "data"),
    Output("calibration_tab-ready", "data"),
    Output("calibration_tab-calibrated_indicator", "children", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "style", allow_duplicate=True),
    Output("calibration_tab-display_mode", "data", allow_duplicate=True),
    Output("calibration_tab-ring_q_values", "data", allow_duplicate=True),
    Output("calibration_tab-suppress_invalidate", "data", allow_duplicate=True),
    Input("calibration_tab-btn-run_calibration", "n_clicks"),
    State("calibration_tab-image_data", "data"),
    State("calibration_tab-poni_file", "data"),
    State("calibration_tab-calibrant_dropdown", "value"),
    State("calibration_tab-input-max_rings", "value"),
    State("calibration_tab-input-label", "value"),
    State("calibration_tab-input-detector_dropdown", "value"),
    State("calibration_tab-cache", "data"),
    prevent_initial_call=True,
)
def run_calibration(
    _: int,
    image_data_payload: Optional[list],
    poni_payload: Optional[str],
    calibrant_name: Optional[str],
    max_rings: Optional[int],
    calibration_label: Optional[str],
    detector_name: Optional[str],
    cache_payload: Optional[dict],
) -> tuple[go.Figure, dict, str, Optional[str], Optional[str], bool, str, dict[str, str], str, list[float], bool]:
    """Run calibration refinement and cache the labelled result."""
    if image_data_payload is None or not poni_payload or not calibrant_name:
        raise PreventUpdate

    image_data = np.asarray(image_data_payload)
    initial_poni = deserialize_poni(poni_payload)
    ring_count = int(max_rings) if max_rings else 5
    label = (calibration_label or "calibration").strip()

    cache_data: dict[str, Any] = dict(cache_payload or {})

    try:
        refined_poni, metadata = run_geometry_refinement(
            image_data=image_data,
            poni=initial_poni,
            calibrant_name=calibrant_name,
            max_rings=ring_count,
        )
    except Exception as exc:
        return (
            go.Figure(layout={"title": "Calibrated Overlay"}),
            cache_data,
            _status_message(f"Calibration failed: {exc}", is_error=True),
            no_update,
            no_update,
            False,
            _indicator_text(False),
            _indicator_style(False),
            "pixel",
            [],
            False,
        )

    refined_payload = serialize_poni(refined_poni)
    cache_data[label] = {
        "poni": refined_payload,
        "calibrant": calibrant_name,
        "max_rings": ring_count,
        "detector": detector_name,
        "metrics": metadata,
    }
    overlay = build_qspace_overlay_figure(
        image_data,
        calibrant_name=calibrant_name,
        poni=refined_poni,
        ring_q_values=metadata.get("ring_q_values", []),
    )
    status = (
        f"Calibration '{label}' saved. "
        f"chi2: {metadata['initial_chi2']:.4g} -> {metadata['final_chi2']:.4g}."
    )
    return (
        overlay,
        cache_data,
        status,
        refined_payload,
        label,
        True,
        _indicator_text(True),
        _indicator_style(True),
        "qspace",
        metadata.get("ring_q_values", []),
        True,
    )


@callback(
    Output("calibration_tab-image_plot", "figure", allow_duplicate=True),
    Output("calibration_tab-poni_file", "data", allow_duplicate=True),
    Output("calibration_tab-selected_label", "data", allow_duplicate=True),
    Output("calibration_tab-status", "children", allow_duplicate=True),
    Output("calibration_tab-ready", "data", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "children", allow_duplicate=True),
    Output("calibration_tab-calibrated_indicator", "style", allow_duplicate=True),
    Output("calibration_tab-display_mode", "data", allow_duplicate=True),
    Output("calibration_tab-ring_q_values", "data", allow_duplicate=True),
    Output("calibration_tab-suppress_invalidate", "data", allow_duplicate=True),
    Input("calibration_tab-btn-load_cache", "n_clicks"),
    State("calibration_tab-cache", "data"),
    State("calibration_tab-cache_dropdown", "value"),
    State("calibration_tab-image_data", "data"),
    prevent_initial_call=True,
)
def load_cached_calibration(
    _: int,
    cache_payload: Optional[dict],
    selected_label: Optional[str],
    image_data_payload: Optional[list],
) -> tuple[go.Figure, Optional[str], Optional[str], str, bool, str, dict[str, str], str, list[float], bool]:
    """Load previously cached calibration by label."""
    cache = cache_payload or {}
    if not selected_label or selected_label not in cache:
        raise PreventUpdate

    item = cache[selected_label]
    poni_payload = item.get("poni")
    if not poni_payload:
        raise PreventUpdate

    image_data = np.asarray(image_data_payload) if image_data_payload is not None else None
    if image_data is None:
        figure = go.Figure(layout={"title": f"Loaded calibration: {selected_label}"})
    else:
        figure = build_qspace_overlay_figure(
            image_data,
            poni=deserialize_poni(poni_payload),
            calibrant_name=item.get("calibrant"),
            ring_q_values=item.get("metrics", {}).get("ring_q_values", []),
        )
    ring_q_values = item.get("metrics", {}).get("ring_q_values", [])
    return (
        figure,
        poni_payload,
        selected_label,
        f"Loaded cached calibration '{selected_label}'.",
        True,
        _indicator_text(True),
        _indicator_style(True),
        "qspace",
        ring_q_values,
        True,
    )


@callback(
    Output("calibration_tab-cache", "data", allow_duplicate=True),
    Output("calibration_tab-cache_dropdown", "value", allow_duplicate=True),
    Output("calibration_tab-status", "children", allow_duplicate=True),
    Input("calibration_tab-btn-delete_cache", "n_clicks"),
    State("calibration_tab-cache", "data"),
    State("calibration_tab-cache_dropdown", "value"),
    prevent_initial_call=True,
)
def delete_cached_calibration(
    _: int,
    cache_payload: Optional[dict],
    selected_label: Optional[str],
) -> tuple[dict, Optional[str], str]:
    """Delete one cached calibration entry."""
    cache_data: dict[str, Any] = dict(cache_payload or {})
    if not selected_label or selected_label not in cache_data:
        return (
            cache_data,
            selected_label,
            _status_message("No cached calibration selected for deletion.", is_error=True),
        )

    cache_data.pop(selected_label, None)
    return cache_data, None, _status_message(f"Deleted cached calibration '{selected_label}'.")


@callback(
    Output("calibration_tab-cache", "data", allow_duplicate=True),
    Output("calibration_tab-cache_dropdown", "value", allow_duplicate=True),
    Output("calibration_tab-status", "children", allow_duplicate=True),
    Input("calibration_tab-btn-clear_cache", "n_clicks"),
    prevent_initial_call=True,
)
def clear_cached_calibrations(_: int) -> tuple[dict, Optional[str], str]:
    """Clear all cached calibrations from local storage."""
    return {}, None, _status_message("Cleared all cached calibrations.")


@callback(
    Output("tab-reduction", "disabled"),
    Input("calibration_tab-ready", "data"),
    Input("calibration_tab-input-detector_dropdown", "value"),
    Input("calibration_tab-input-energy", "value"),
    Input("calibration_tab-input-sdd", "value"),
    Input("calibration_tab-input-poni1", "value"),
    Input("calibration_tab-input-poni2", "value"),
    Input("calibration_tab-input-rot1", "value"),
    Input("calibration_tab-input-rot2", "value"),
    Input("calibration_tab-input-rot3", "value"),
)
def enable_reduction_tab(
    calibration_ready: Optional[bool],
    detector_name: Optional[str],
    energy: Optional[float],
    sdd: Optional[float],
    poni1: Optional[float],
    poni2: Optional[float],
    rot1: Optional[float],
    rot2: Optional[float],
    rot3: Optional[float],
) -> bool:
    """Enable Reduction tab after calibration is ready or full PONI fields are populated."""
    has_poni_fields = all(
        value is not None
        for value in [detector_name, energy, sdd, poni1, poni2, rot1, rot2, rot3]
    )
    return not (bool(calibration_ready) or has_poni_fields)
