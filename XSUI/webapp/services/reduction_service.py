"""Reduction helper functions for GI/WAXS image processing."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

import fabio
import numpy as np
from pyFAI.integrator.azimuthal import AzimuthalIntegrator
from pyFAI.integrator.fiber import FiberIntegrator
from pyFAI.io.ponifile import PoniFile
from pyFAI.units import Unit, get_unit_fiber

_ALLOWED_EXTENSIONS: tuple[str, ...] = (".tif", ".tiff", ".edf", ".cbf")
"""Supported detector image extensions for directory scans."""


def list_image_files(directory: str) -> list[str]:
    """List detector image files in a directory.

    Parameters
    ----------
    directory : str
        Input directory.

    Returns
    -------
    list[str]
        Sorted image file paths.
    """
    if not os.path.isdir(directory):
        return []
    files: list[str] = []
    for name in sorted(os.listdir(directory)):
        suffix: str = Path(name).suffix.lower()
        if suffix in _ALLOWED_EXTENSIONS:
            files.append(str(Path(directory) / name))
    return files


def compile_angle_regex(pattern: str) -> tuple[bool, str]:
    """Compile a regex intended to parse angle-of-incidence from filenames.

    Parameters
    ----------
    pattern : str
        Regex expression expected to include a named capture group ``aoi``.

    Returns
    -------
    tuple[bool, str]
        ``(True, message)`` when valid; otherwise ``(False, reason)``.
    """
    if not pattern:
        return False, "Regex is empty."
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return False, f"Regex error: {exc}"
    if "aoi" not in compiled.groupindex:
        return False, "Regex must contain a named group: (?P<aoi>...)."
    return True, "Regex compiled successfully."


def parse_incident_angle_from_filename(file_name: str, pattern: str) -> float:
    """Parse incident angle from a filename using regex named group ``aoi``.

    Parameters
    ----------
    file_name : str
        Filename or path to parse.
    pattern : str
        Regex expression with named group ``aoi``.

    Returns
    -------
    float
        Incident angle in degrees.
    """
    compiled = re.compile(pattern)
    match = compiled.search(Path(file_name).name)
    if match is None:
        raise ValueError("Filename does not match regex.")
    raw_value: str = match.group("aoi").replace("p", ".")
    return float(raw_value)


def parse_angle_arcs(payload: str) -> list[tuple[float, float]]:
    """Parse lineprofile angle arcs from textarea text.

    Parameters
    ----------
    payload : str
        Newline-delimited ``start,end`` angle values.

    Returns
    -------
    list[tuple[float, float]]
        Parsed list of angle tuples.
    """
    arcs: list[tuple[float, float]] = []
    for row in payload.splitlines():
        clean_row = row.strip()
        if not clean_row:
            continue
        left, right = [item.strip() for item in clean_row.split(",", maxsplit=1)]
        arcs.append((float(left), float(right)))
    return arcs


def example_output_name(file_name: str, regex_pattern: str, mode: str) -> str:
    """Build an example output filename for display in the UI.

    Parameters
    ----------
    file_name : str
        Source image filename.
    regex_pattern : str
        Regex with optional groups ``sample`` and ``index``.
    mode : str
        Output mode label.

    Returns
    -------
    str
        Example output basename.
    """
    base_name: str = Path(file_name).name
    sample: str = Path(file_name).stem
    index: str = "0000"
    if regex_pattern:
        match = re.search(regex_pattern, base_name)
        if match:
            sample = match.groupdict().get("sample", sample)
            index = match.groupdict().get("index", index)
    return f"{sample}-{mode}-{index}.npz"


def reduce_image_2d(
    image_path: str,
    poni: PoniFile,
    grazing: bool,
    output_mode: str,
    angle_of_incidence_deg: float,
    npt: int = 800,
    mask: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reduce a detector image into a 2D map.

    Parameters
    ----------
    image_path : str
        Detector image path.
    poni : PoniFile
        Calibrated geometry.
    grazing : bool
        Whether to use fiber (GI) integration.
    output_mode : str
        One of ``cake``, ``qip_qoop`` or ``qx_qy``.
    angle_of_incidence_deg : float
        Incident angle in degrees for GI mode.
    npt : int, optional
        Number of points per integration axis.
    mask : np.ndarray | None, optional
        Optional boolean mask.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Intensity, x-axis values, y-axis values.
    """
    image_data = np.asarray(fabio.open(image_path).data)

    if grazing:
        integrator = FiberIntegrator.sload(poni)
        if output_mode == "qip_qoop":
            unit_ip = get_unit_fiber("qip_A^-1")
            unit_oop = get_unit_fiber("qoop_A^-1")
        elif output_mode == "cake":
            unit_ip = get_unit_fiber("chigi_deg")
            unit_oop = get_unit_fiber("qtot_A^-1")
        else:
            unit_ip = get_unit_fiber("qip_A^-1")
            unit_oop = get_unit_fiber("qoop_A^-1")

        incident_angle = np.deg2rad(angle_of_incidence_deg)
        unit_ip.set_incident_angle(incident_angle)
        unit_oop.set_incident_angle(incident_angle)
        result = integrator.integrate2d_grazing_incidence(
            image_data,
            npt_ip=npt,
            npt_oop=npt,
            unit_ip=unit_ip,
            unit_oop=unit_oop,
            mask=mask,
        )
        intensity, axis_x, axis_y = result[0:3]
        return np.asarray(intensity), np.asarray(axis_x), np.asarray(axis_y)

    integrator = AzimuthalIntegrator.sload(poni)
    if output_mode == "qx_qy":
        unit = (Unit.parse("qx_nm^-1"), Unit.parse("qy_nm^-1"))
    else:
        unit = (Unit.parse("2th_deg"), Unit.parse("chi_deg"))
    result = integrator.integrate2d(image_data, npt, npt, unit=unit, mask=mask)
    intensity, axis_x, axis_y = result[0:3]
    return np.asarray(intensity), np.asarray(axis_x), np.asarray(axis_y)


def reduce_lineprofile_1d(
    image_path: str,
    poni: PoniFile,
    angle_arc: tuple[float, float],
    angle_of_incidence_deg: float,
    npt: int = 1200,
    mask: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Reduce a GI image into a 1D line profile for an angular wedge.

    Parameters
    ----------
    image_path : str
        Detector image path.
    poni : PoniFile
        Calibrated geometry.
    angle_arc : tuple[float, float]
        Integration arc in degrees.
    angle_of_incidence_deg : float
        Incident angle in degrees.
    npt : int, optional
        Number of q points.
    mask : np.ndarray | None, optional
        Optional boolean mask.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(q, intensity)`` arrays.
    """
    image_data = np.asarray(fabio.open(image_path).data)
    integrator = FiberIntegrator.sload(poni)
    unit_ip = get_unit_fiber("chigi_deg")
    unit_oop = get_unit_fiber("qtot_A^-1")
    incident_angle = np.deg2rad(angle_of_incidence_deg)
    unit_ip.set_incident_angle(incident_angle)
    unit_oop.set_incident_angle(incident_angle)

    result = integrator.integrate1d_grazing_incidence(
        data=image_data,
        unit_ip=unit_ip,
        unit_oop=unit_oop,
        npt_ip=npt,
        npt_oop=npt,
        ip_range=angle_arc,
        mask=mask,
    )
    q_values, intensities = result
    return np.asarray(q_values), np.asarray(intensities)


def summarise_regex_match(file_paths: list[str], pattern: str) -> dict[str, Any]:
    """Summarise regex match status over a file list.

    Parameters
    ----------
    file_paths : list[str]
        Candidate image files.
    pattern : str
        Regex pattern for AOI parsing.

    Returns
    -------
    dict[str, Any]
        Status dictionary with compile flag and first example.
    """
    valid, message = compile_angle_regex(pattern)
    if not valid:
        return {"ok": False, "message": message, "example": None}

    for path in file_paths:
        try:
            parsed = parse_incident_angle_from_filename(path, pattern)
            return {
                "ok": True,
                "message": message,
                "example": f"{Path(path).name} -> {parsed:.4f} deg",
            }
        except ValueError:
            continue

    return {
        "ok": True,
        "message": "Regex compiled but no sample file matched.",
        "example": None,
    }
