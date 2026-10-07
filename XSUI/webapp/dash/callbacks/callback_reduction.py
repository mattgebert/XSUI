"""Dash callbacks for reduction workflows."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate

from XSUI.webapp.services.calibration_service import deserialize_poni
from XSUI.webapp.services.file_dialogs import select_directory
from XSUI.webapp.services.reduction_service import (
    example_output_name,
    list_image_files,
    parse_angle_arcs,
    parse_incident_angle_from_filename,
    reduce_image_2d,
    reduce_lineprofile_1d,
    summarise_regex_match,
)


def _downsample_image(
    intensity: np.ndarray,
    axis_x: np.ndarray,
    axis_y: np.ndarray,
    max_points: int = 600,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Downsample 2D image arrays for responsive Plotly rendering."""
    y_stride = max(1, int(np.ceil(intensity.shape[0] / max_points)))
    x_stride = max(1, int(np.ceil(intensity.shape[1] / max_points)))
    return (
        intensity[::y_stride, ::x_stride],
        axis_x[::x_stride],
        axis_y[::y_stride],
    )


def _prepare_image_display_data(
    intensity: np.ndarray,
    zscale: str,
) -> np.ndarray:
    """Apply selected z-scale transform for image display."""
    if zscale == "log":
        positive = intensity[intensity > 0]
        floor = float(np.nanmin(positive)) if positive.size else 1.0
        safe_floor = max(floor, 1e-12)
        return np.log10(np.where(intensity > 0, intensity, safe_floor))
    return intensity


def _build_image_preview_figure(
    payload: dict[str, object],
    zscale: str,
    zrange: Optional[list[float]],
) -> go.Figure:
    """Build image preview figure from prepared payload."""
    z_data = _prepare_image_display_data(np.asarray(payload["intensity"]), zscale)
    zmin = None
    zmax = None
    if zrange and len(zrange) == 2:
        zmin, zmax = float(zrange[0]), float(zrange[1])

    figure = go.Figure()
    figure.add_trace(
        go.Heatmap(
            x=np.asarray(payload["x"]),
            y=np.asarray(payload["y"]),
            z=z_data,
            zmin=zmin,
            zmax=zmax,
            colorscale="Inferno",
            colorbar={"title": "log10(I)" if zscale == "log" else "I"},
        )
    )
    figure.update_layout(title=str(payload.get("title", "Image Reduction Preview")))
    return figure


def _build_line_preview_figure(
    payload: dict[str, object],
    xscale: str,
    yscale: str,
) -> go.Figure:
    """Build lineprofile preview figure from prepared payload."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=np.asarray(payload["q"]),
            y=np.asarray(payload["intensity"]),
            mode="lines",
            name=str(payload.get("title", "Lineprofile Preview")),
        )
    )
    figure.update_layout(
        title=str(payload.get("title", "Lineprofile Preview")),
        xaxis_title="q",
        yaxis_title="Intensity",
    )
    figure.update_xaxes(type=xscale)
    figure.update_yaxes(type=yscale)
    return figure


def _list_disk_image_outputs(output_dir: Optional[str]) -> list[str]:
    """List non-lineprofile reduction outputs on disk."""
    if not output_dir:
        return []
    folder = Path(output_dir)
    if not folder.is_dir():
        return []
    paths = sorted(folder.glob("*.npz"))
    return [str(path) for path in paths if not path.name.endswith(".lineprofile.npz")]


def _list_disk_line_outputs(output_dir: Optional[str]) -> list[str]:
    """List lineprofile reduction outputs on disk."""
    if not output_dir:
        return []
    folder = Path(output_dir)
    if not folder.is_dir():
        return []
    return [str(path) for path in sorted(folder.glob("*.lineprofile.npz"))]


def _load_image_preview_payload(
    selected_value: str,
    image_cache: dict,
) -> Optional[dict[str, object]]:
    """Load an image preview payload from cache or disk and downsample it."""
    if selected_value.startswith("cache::"):
        key = selected_value.replace("cache::", "", 1)
        entry = image_cache.get(key)
        if entry is None:
            return None
        intensity, axis_x, axis_y = _downsample_image(
            np.asarray(entry["intensity"]),
            np.asarray(entry["x"]),
            np.asarray(entry["y"]),
        )
        return {
            "intensity": intensity.tolist(),
            "x": axis_x.tolist(),
            "y": axis_y.tolist(),
            "title": str(entry.get("label", key)),
        }

    if selected_value.startswith("disk::"):
        path = Path(selected_value.replace("disk::", "", 1))
        if not path.exists():
            return None
        payload = np.load(path, mmap_mode="r", allow_pickle=False)
        intensity, axis_x, axis_y = _downsample_image(
            np.asarray(payload["intensity"]),
            np.asarray(payload["x"]),
            np.asarray(payload["y"]),
        )
        return {
            "intensity": intensity.tolist(),
            "x": axis_x.tolist(),
            "y": axis_y.tolist(),
            "title": f"Disk: {path.name}",
        }

    return None


def _load_line_preview_payload(
    selected_value: str,
    line_cache: dict,
) -> Optional[dict[str, object]]:
    """Load a lineprofile preview payload from cache or disk."""
    if selected_value.startswith("cache::"):
        key = selected_value.replace("cache::", "", 1)
        entry = line_cache.get(key)
        if entry is None:
            return None
        return {
            "q": entry["q"],
            "intensity": entry["intensity"],
            "title": str(entry.get("label", key)),
        }

    if selected_value.startswith("disk::"):
        path = Path(selected_value.replace("disk::", "", 1))
        if not path.exists():
            return None
        payload = np.load(path, mmap_mode="r", allow_pickle=False)
        return {
            "q": np.asarray(payload["q"]).tolist(),
            "intensity": np.asarray(payload["intensity"]).tolist(),
            "title": f"Disk: {path.name}",
        }

    return None


@callback(
    Output("reduction_tab-image_files", "data"),
    Output("reduction_tab-selected_files", "data"),
    Output("reduction_tab-input_dir", "data"),
    Output("reduction_tab-file_dropdown", "options"),
    Output("reduction_tab-file_dropdown", "value"),
    Output("reduction_tab-selected_dir", "children"),
    Output("reduction_tab-file_count", "children"),
    Output("reduction_tab-output_dir", "data"),
    Output("reduction_tab-output_dir_label", "children"),
    Input("reduction_tab-btn-select_dir", "n_clicks"),
    prevent_initial_call=True,
)
def select_image_directory(_: int) -> tuple[list[str], list[str], str, list[dict[str, str]], list[str], str, str, str, str]:
    """Select a local directory and populate the reduction file list."""
    directory = select_directory("Select image directory")
    if not directory:
        raise PreventUpdate

    files = list_image_files(directory)
    options = [{"label": Path(path).name, "value": path} for path in files]
    selected = list(files)
    output_dir = directory
    return files, selected, directory, options, selected, directory, f"{len(files)} files", output_dir, output_dir


@callback(
    Output("reduction_tab-output_dir", "data", allow_duplicate=True),
    Output("reduction_tab-output_dir_label", "children", allow_duplicate=True),
    Input("reduction_tab-btn-select_output_dir", "n_clicks"),
    State("reduction_tab-input_dir", "data"),
    prevent_initial_call=True,
)
def select_output_directory(_: int, input_dir: Optional[str]) -> tuple[str, str]:
    """Select a separate output directory for reduced data."""
    directory = select_directory("Select output directory", start_dir=input_dir or "")
    if not directory:
        raise PreventUpdate
    return directory, directory


@callback(
    Output("reduction_tab-output_dir_action_status", "children"),
    Input("reduction_tab-btn-view_output_dir", "n_clicks"),
    State("reduction_tab-output_dir", "data"),
    State("reduction_tab-input_dir", "data"),
    prevent_initial_call=True,
)
def view_output_directory(
    _: int,
    output_dir: Optional[str],
    input_dir: Optional[str],
) -> str:
    """Open the output directory in the platform file viewer."""
    target = output_dir or input_dir
    if not target:
        return "No output directory selected."

    path = Path(target)
    if not path.exists() or not path.is_dir():
        return f"Output directory is not available: {target}"

    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        return f"Failed to open output directory: {exc}"

    return f"Opened output directory: {path}"


@callback(
    Output("reduction_tab-file_dropdown", "value", allow_duplicate=True),
    Input("reduction_tab-btn-select_all", "n_clicks"),
    Input("reduction_tab-btn-clear_selection", "n_clicks"),
    State("reduction_tab-image_files", "data"),
    prevent_initial_call=True,
)
def update_file_selection(
    _: Optional[int],
    __: Optional[int],
    file_paths: Optional[list[str]],
) -> list[str]:
    """Select all files or clear the current selection."""
    if not file_paths:
        return []

    trigger = ctx.triggered_id
    if trigger == "reduction_tab-btn-select_all":
        return list(file_paths)
    if trigger == "reduction_tab-btn-clear_selection":
        return []
    return no_update


@callback(
    Output("reduction_tab-regex_hint", "children"),
    Input("reduction_tab-btn-regex_hint", "n_clicks"),
    prevent_initial_call=True,
)
def show_regex_hint(_: int) -> str:
    """Display a simple AOI regex hint."""
    return "Use a named group (?P<aoi>...) like: .*_(?P<aoi>\\d+p\\d+)_.* to parse 0p10 as 0.10 deg."


@callback(
    Output("reduction_tab-regex_status", "children"),
    Input("reduction_tab-input-aoi_regex", "value"),
    Input("reduction_tab-image_files", "data"),
)
def validate_aoi_regex(regex_pattern: Optional[str], file_paths: Optional[list[str]]) -> str:
    """Validate AOI regex and show an example match when possible."""
    if not regex_pattern:
        return "Regex not set."

    summary = summarise_regex_match(file_paths or [], regex_pattern)
    if summary.get("example"):
        return f"{summary['message']} Example: {summary['example']}"
    return summary["message"]


@callback(
    Output("reduction_tab-lineprofile_name_example", "children"),
    Input("reduction_tab-input-lineprofile_name_regex", "value"),
    Input("reduction_tab-file_dropdown", "value"),
)
def update_lineprofile_name_example(
    regex_pattern: Optional[str],
    selected_files: Optional[list[str]],
) -> str:
    """Show an example lineprofile output name."""
    if not selected_files:
        return "Lineprofile example unavailable until files are selected."
    return f"Example output: {example_output_name(selected_files[0], regex_pattern or '', 'lineprofile')}"


@callback(
    Output("reduction_tab-image_name_example", "children"),
    Input("reduction_tab-input-image_name_regex", "value"),
    Input("reduction_tab-file_dropdown", "value"),
    Input("reduction_tab-output_mode", "value"),
)
def update_output_name_example(
    regex_pattern: Optional[str],
    selected_files: Optional[list[str]],
    output_mode: Optional[str],
) -> str:
    """Show an example 2D output name."""
    if not selected_files:
        return "Output example unavailable until files are selected."
    return f"Example output: {example_output_name(selected_files[0], regex_pattern or '', output_mode or 'qip_qoop')}"


@callback(
    Output("reduction_tab-lineprofile_regex_status", "children"),
    Input("reduction_tab-input-lineprofile_name_regex", "value"),
    Input("reduction_tab-input-image_name_regex", "value"),
    Input("reduction_tab-input-aoi_regex", "value"),
)
def validate_lineprofile_regex(
    lineprofile_regex: Optional[str],
    image_regex: Optional[str],
    aoi_regex: Optional[str],
) -> str:
    """Validate lineprofile naming compatibility with image naming and AOI groups."""
    if not lineprofile_regex:
        return "Lineprofile regex not set."

    try:
        compiled_line = re.compile(lineprofile_regex)
    except re.error as exc:
        return f"Lineprofile regex error: {exc}"

    line_groups = set(compiled_line.groupindex)
    if "aoi" not in line_groups:
        return "Lineprofile regex must contain a named group: (?P<aoi>...)."
    if "arc1" not in line_groups or "arc2" not in line_groups:
        return "Lineprofile regex must contain named groups: (?P<arc1>...) and (?P<arc2>...)."

    if image_regex:
        try:
            compiled_image = re.compile(image_regex)
        except re.error as exc:
            return f"Image regex error: {exc}"
        image_groups = set(compiled_image.groupindex)
        missing = sorted(image_groups - line_groups)
        if missing:
            return f"Lineprofile regex must include the image groups: {', '.join(missing)}."

    if aoi_regex:
        try:
            compiled_aoi = re.compile(aoi_regex)
        except re.error as exc:
            return f"AOI regex error: {exc}"
        if "aoi" not in compiled_aoi.groupindex:
            return "AOI regex must contain a named group: (?P<aoi>...)."

    return "Lineprofile regex is compatible with the image output template."


@callback(
    Output("reduction_tab-output_mode", "options"),
    Output("reduction_tab-output_mode", "value"),
    Input("reduction_tab-input-grazing", "value"),
)
def update_output_mode_options(grazing: bool) -> tuple[list[dict[str, str]], str]:
    """Adjust 2D output mode defaults for grazing and non-grazing workflows."""
    if grazing:
        options = [
            {"label": "Cake", "value": "cake"},
            {"label": "Qip Qoop", "value": "qip_qoop"},
        ]
        return options, "qip_qoop"

    options = [
        {"label": "Qx Qy", "value": "qx_qy"},
        {"label": "Cake", "value": "cake"},
    ]
    return options, "qx_qy"


@callback(
    Output("reduction_tab-images_cache", "data"),
    Output("reduction_tab-images_status", "children"),
    Output("reduction_tab-images_progress", "value"),
    Output("reduction_tab-images_progress", "label"),
    Input("reduction_tab-btn-run_images", "n_clicks"),
    State("reduction_tab-file_dropdown", "value"),
    State("reduction_tab-input_dir", "data"),
    State("reduction_tab-output_dir", "data"),
    State("calibration_tab-poni_file", "data"),
    State("reduction_tab-input-grazing", "value"),
    State("reduction_tab-incidence-tabs", "value"),
    State("reduction_tab-input-fixed_aoi", "value"),
    State("reduction_tab-input-aoi_regex", "value"),
    State("reduction_tab-output_mode", "value"),
    State("reduction_tab-input-cache_images", "value"),
    State("reduction_tab-images_cache", "data"),
    prevent_initial_call=True,
)
def run_image_reduction(
    _: int,
    selected_files: Optional[list[str]],
    input_dir: Optional[str],
    output_dir: Optional[str],
    poni_payload: Optional[str],
    grazing: bool,
    incidence_mode: str,
    fixed_aoi: Optional[float],
    aoi_regex: Optional[str],
    output_mode: Optional[str],
    cache_images: bool,
    existing_cache: Optional[dict],
) -> tuple[dict, str, int, str]:
    """Run 2D reduction and update the image cache."""
    if not selected_files or not poni_payload:
        raise PreventUpdate

    if incidence_mode == "regex" and not aoi_regex:
        return existing_cache or {}, "AOI regex mode is selected but regex is empty.", 0, "0%"

    poni = deserialize_poni(poni_payload)
    reduced_count = 0
    image_cache: dict[str, dict[str, object]] = dict(existing_cache or {})
    total = max(len(selected_files), 1)
    output_folder = Path(output_dir or input_dir or Path(selected_files[0]).parent)
    output_folder.mkdir(parents=True, exist_ok=True)

    for image_path in selected_files:
        if incidence_mode == "regex":
            try:
                angle_of_incidence = parse_incident_angle_from_filename(image_path, aoi_regex or "")
            except Exception as exc:
                percent_error = int(100 * reduced_count / total)
                return image_cache, f"Failed to parse AOI from {Path(image_path).name}: {exc}", percent_error, f"{percent_error}%"
        else:
            angle_of_incidence = float(fixed_aoi or 0.1)

        intensity, axis_x, axis_y = reduce_image_2d(
            image_path=image_path,
            poni=poni,
            grazing=bool(grazing),
            output_mode=output_mode or "qip_qoop",
            angle_of_incidence_deg=angle_of_incidence,
        )

        output_path = output_folder / f"{Path(image_path).stem}.{output_mode or 'qip_qoop'}.npz"
        np.savez_compressed(output_path, intensity=intensity, x=axis_x, y=axis_y)

        if cache_images:
            cache_key = f"image:{Path(image_path).name}"
            image_cache[cache_key] = {
                "kind": "image",
                "label": f"{Path(image_path).name} -> {output_path.name}",
                "intensity": intensity.tolist(),
                "x": axis_x.tolist(),
                "y": axis_y.tolist(),
            }

        reduced_count += 1

    percent = int(100 * reduced_count / total)
    return image_cache, f"Reduced {reduced_count} image(s) into {output_folder}.", percent, f"{percent}%"


@callback(
    Output("reduction_tab-lines_cache", "data"),
    Output("reduction_tab-lines_status", "children"),
    Output("reduction_tab-lines_progress", "value"),
    Output("reduction_tab-lines_progress", "label"),
    Input("reduction_tab-btn-run_lines", "n_clicks"),
    State("reduction_tab-file_dropdown", "value"),
    State("reduction_tab-input_dir", "data"),
    State("reduction_tab-output_dir", "data"),
    State("calibration_tab-poni_file", "data"),
    State("reduction_tab-input-fixed_aoi", "value"),
    State("reduction_tab-input-arcs", "value"),
    State("reduction_tab-input-cache_lines", "value"),
    State("reduction_tab-lines_cache", "data"),
    prevent_initial_call=True,
)
def run_lineprofile_reduction(
    _: int,
    selected_files: Optional[list[str]],
    input_dir: Optional[str],
    output_dir: Optional[str],
    poni_payload: Optional[str],
    fixed_aoi: Optional[float],
    arcs_payload: str,
    cache_lines: bool,
    existing_cache: Optional[dict],
) -> tuple[dict, str, int, str]:
    """Run 1D reduction and update the lineprofile cache."""
    if not selected_files or not poni_payload:
        raise PreventUpdate

    poni = deserialize_poni(poni_payload)
    angle_arcs = parse_angle_arcs(arcs_payload)
    produced = 0
    line_cache: dict[str, dict[str, object]] = dict(existing_cache or {})
    output_folder = Path(output_dir or input_dir or Path(selected_files[0]).parent)
    output_folder.mkdir(parents=True, exist_ok=True)
    total = max(len(selected_files) * max(len(angle_arcs), 1), 1)

    for image_path in selected_files:
        for angle_arc in angle_arcs:
            q_vals, intensity_vals = reduce_lineprofile_1d(
                image_path=image_path,
                poni=poni,
                angle_arc=angle_arc,
                angle_of_incidence_deg=float(fixed_aoi or 0.1),
            )
            output_path = output_folder / f"{Path(image_path).stem}.{angle_arc[0]}_{angle_arc[1]}.lineprofile.npz"
            np.savez_compressed(output_path, q=q_vals, intensity=intensity_vals)

            if cache_lines:
                cache_key = f"line:{Path(image_path).name}|{angle_arc[0]}_{angle_arc[1]}"
                line_cache[cache_key] = {
                    "kind": "lineprofile",
                    "label": f"{Path(image_path).name} [{angle_arc[0]}, {angle_arc[1]}]",
                    "q": q_vals.tolist(),
                    "intensity": intensity_vals.tolist(),
                }
            produced += 1

    percent = int(100 * produced / total)
    return line_cache, f"Generated {produced} lineprofile dataset(s) into {output_folder}.", percent, f"{percent}%"


@callback(
    Output("reduction_tab-images_preview_dropdown", "options"),
    Output("reduction_tab-images_preview_dropdown", "value"),
    Input("reduction_tab-images_cache", "data"),
    Input("reduction_tab-output_dir", "data"),
)
def refresh_image_preview_options(
    image_cache: Optional[dict],
    output_dir: Optional[str],
) -> tuple[list[dict[str, str]], Optional[str]]:
    """Refresh image preview selector from cache and output-directory files."""
    options: list[dict[str, str]] = []
    for key, entry in sorted((image_cache or {}).items()):
        options.append({"label": str(entry.get("label", key)), "value": f"cache::{key}"})

    for path in _list_disk_image_outputs(output_dir):
        options.append({"label": f"Disk: {Path(path).name}", "value": f"disk::{path}"})

    return options, (options[0]["value"] if options else None)


@callback(
    Output("reduction_tab-lines_preview_dropdown", "options"),
    Output("reduction_tab-lines_preview_dropdown", "value"),
    Input("reduction_tab-lines_cache", "data"),
    Input("reduction_tab-output_dir", "data"),
)
def refresh_line_preview_options(
    line_cache: Optional[dict],
    output_dir: Optional[str],
) -> tuple[list[dict[str, str]], Optional[str]]:
    """Refresh lineprofile preview selector from cache and output-directory files."""
    options: list[dict[str, str]] = []
    for key, entry in sorted((line_cache or {}).items()):
        options.append({"label": str(entry.get("label", key)), "value": f"cache::{key}"})

    for path in _list_disk_line_outputs(output_dir):
        options.append({"label": f"Disk: {Path(path).name}", "value": f"disk::{path}"})

    return options, (options[0]["value"] if options else None)


@callback(
    Output("reduction_tab-images_preview_payload", "data"),
    Output("reduction_tab-images_zrange", "min"),
    Output("reduction_tab-images_zrange", "max"),
    Output("reduction_tab-images_zrange", "value"),
    Input("reduction_tab-images_preview_dropdown", "value"),
    Input("reduction_tab-images_zscale", "value"),
    State("reduction_tab-images_cache", "data"),
    prevent_initial_call=True,
)
def load_image_preview_payload(
    selected_value: Optional[str],
    zscale: Optional[str],
    image_cache: Optional[dict],
) -> tuple[Optional[dict[str, object]], float, float, list[float]]:
    """Load selected image preview payload and initialize z-range slider."""
    if not selected_value:
        raise PreventUpdate

    payload = _load_image_preview_payload(selected_value, dict(image_cache or {}))
    if payload is None:
        raise PreventUpdate

    z_data = _prepare_image_display_data(np.asarray(payload["intensity"]), zscale or "linear")
    z_min = float(np.nanmin(z_data))
    z_max = float(np.nanmax(z_data))
    if z_min == z_max:
        z_max = z_min + 1.0
    return payload, z_min, z_max, [z_min, z_max]


@callback(
    Output("reduction_tab-images_preview_plot", "figure"),
    Input("reduction_tab-images_preview_payload", "data"),
    Input("reduction_tab-images_zscale", "value"),
    Input("reduction_tab-images_zrange", "value"),
    prevent_initial_call=True,
)
def update_image_preview_plot(
    payload: Optional[dict[str, object]],
    zscale: Optional[str],
    zrange: Optional[list[float]],
) -> go.Figure:
    """Render selected image preview from preloaded payload."""
    if payload is None:
        raise PreventUpdate
    return _build_image_preview_figure(
        payload=payload,
        zscale=zscale or "linear",
        zrange=zrange,
    )


@callback(
    Output("reduction_tab-lines_preview_payload", "data"),
    Input("reduction_tab-lines_preview_dropdown", "value"),
    State("reduction_tab-lines_cache", "data"),
    prevent_initial_call=True,
)
def load_line_preview_payload(
    selected_value: Optional[str],
    line_cache: Optional[dict],
) -> Optional[dict[str, object]]:
    """Load selected lineprofile preview payload."""
    if not selected_value:
        raise PreventUpdate

    payload = _load_line_preview_payload(selected_value, dict(line_cache or {}))
    if payload is None:
        raise PreventUpdate
    return payload


@callback(
    Output("reduction_tab-lines_preview_plot", "figure"),
    Input("reduction_tab-lines_preview_payload", "data"),
    Input("reduction_tab-lines_xscale", "value"),
    Input("reduction_tab-lines_yscale", "value"),
    prevent_initial_call=True,
)
def update_line_preview_plot(
    payload: Optional[dict[str, object]],
    xscale: Optional[str],
    yscale: Optional[str],
) -> go.Figure:
    """Render selected lineprofile preview from preloaded payload."""
    if payload is None:
        raise PreventUpdate
    return _build_line_preview_figure(
        payload=payload,
        xscale=xscale or "linear",
        yscale=yscale or "linear",
    )
