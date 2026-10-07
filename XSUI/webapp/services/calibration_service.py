"""Calibration helper functions for pyFAI workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import fabio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import scipy.constants as sc
from pyFAI.calibrant import get_calibrant
from pyFAI.detectors import Detector, detector_factory
from pyFAI.goniometer import SingleGeometry
from pyFAI.geometry import Geometry
from pyFAI.integrator.azimuthal import AzimuthalIntegrator
from pyFAI.io.ponifile import PoniFile
from pyFAI.units import Unit


def wavelength_to_energy(wavelength: float) -> float:
    """Convert wavelength in meters to photon energy in eV.

    Parameters
    ----------
    wavelength : float
        X-ray wavelength in meters.

    Returns
    -------
    float
        Photon energy in electronvolts.
    """
    safe_wavelength: float = abs(wavelength)
    if safe_wavelength == 0:
        raise ValueError("Wavelength must be non-zero.")
    return sc.h * sc.c / safe_wavelength / sc.e


def read_poni_file(path: str) -> PoniFile:
    """Read a PONI file from disk.

    Parameters
    ----------
    path : str
        Path to a ``.poni`` file.

    Returns
    -------
    PoniFile
        Parsed pyFAI PONI object.
    """
    return PoniFile(data=path)


def read_calibration_image(path: str) -> np.ndarray:
    """Read a calibration image using fabio.

    Parameters
    ----------
    path : str
        Path to detector image.

    Returns
    -------
    np.ndarray
        Image intensity array.
    """
    return np.asarray(fabio.open(path).data)


def pixel_beamcentre(poni: PoniFile, detector: Detector) -> np.ndarray:
    """Get beam centre in pixel coordinates.

    Parameters
    ----------
    poni : PoniFile
        Calibration geometry object.
    detector : Detector
        Detector object with pixel sizes.

    Returns
    -------
    np.ndarray
        Beam centre coordinate vector ``[y, x, z]``.
    """
    pixel1_value = float(detector.pixel1) if detector.pixel1 else 1.72e-4
    """Fallback detector pixel1 in meters when unavailable."""
    pixel2_value = float(detector.pixel2) if detector.pixel2 else 1.72e-4
    """Fallback detector pixel2 in meters when unavailable."""
    pixel_size: tuple[float, float] = (pixel1_value, pixel2_value)
    detect_coords: np.ndarray = np.array([0.0, 0.0, 0.0])
    pix_coords: np.ndarray = np.array([1 / pixel_size[0], 1 / pixel_size[1], 0.0]) * (
        detect_coords - np.array([-poni.poni1, -poni.poni2, poni.dist])
    ) - np.array([0.5, 0.5, 0.0])
    return pix_coords


def build_calibration_figure(
    image_data: np.ndarray,
    poni: Optional[PoniFile] = None,
    detector_name: Optional[str] = None,
    calibrant_name: Optional[str] = None,
    ring_q_values: Optional[list[float]] = None,
) -> go.Figure:
    """Build calibration figure with optional beam centre and ring overlay.

    Parameters
    ----------
    image_data : np.ndarray
        Raw detector image array.
    poni : PoniFile | None, optional
        Geometry object used for beam centre and overlays.
    detector_name : str | None, optional
        Detector name used when provided independently of PONI.
    calibrant_name : str | None, optional
        Calibrant label used for legend text.
    ring_q_values : list[float] | None, optional
        Calibrant ring q values to draw as circles.

    Returns
    -------
    go.Figure
        Plotly image figure with overlays.
    """
    positive_pixels: np.ndarray = image_data[image_data > 0]
    floor_value: float = float(np.nanmin(positive_pixels)) if positive_pixels.size else 1.0
    safe_floor: float = max(floor_value, 1.0)
    transformed: np.ndarray = np.clip(np.log10(np.where(image_data > 0, image_data, safe_floor)), 0.0, None)
    figure: go.Figure = px.imshow(
        transformed,
        color_continuous_scale="inferno",
        title="Calibrant Image (log10 intensity)",
        labels={"color": "Intensity"},
    )

    if poni is not None:
        detector: Detector = detector_factory(detector_name) if detector_name else poni.detector
        beamcentre: np.ndarray = pixel_beamcentre(poni, detector)
        figure.add_trace(
            go.Scatter(
                x=[float(beamcentre[1])],
                y=[float(beamcentre[0])],
                mode="markers",
                marker={"color": "cyan", "size": 10, "symbol": "x"},
                name="Beam Centre",
            )
        )

        if ring_q_values:
            calibrant_label: str = calibrant_name or "Calibrant"
            for index, q_value in enumerate(ring_q_values):
                if q_value <= 0:
                    continue
                radius: float = q_value * 100
                theta: np.ndarray = np.linspace(0, 2 * np.pi, 361)
                x_coords: np.ndarray = radius * np.cos(theta) + beamcentre[1]
                y_coords: np.ndarray = radius * np.sin(theta) + beamcentre[0]
                figure.add_trace(
                    go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode="lines",
                        line={"color": "yellow", "width": 1, "dash": "dash"},
                        name=f"{calibrant_label} ring {index + 1}",
                        showlegend=index == 0,
                    )
                )
    return figure


def build_qspace_overlay_figure(
    image_data: np.ndarray,
    poni: PoniFile,
    calibrant_name: str,
    ring_q_values: Optional[list[float]] = None,
    mask: Optional[np.ndarray] = None,
    npt: int = 1200,
) -> go.Figure:
    """Build q-space image with calibrant rings overlaid.

    Parameters
    ----------
    image_data : np.ndarray
        Detector image data.
    poni : PoniFile
        Calibrated geometry.
    calibrant_name : str
        Calibrant label for figure legend.
    ring_q_values : list[float] | None, optional
        Ring q values in 1/nm for circle overlays.
    mask : np.ndarray | None, optional
        Optional detector mask.
    npt : int, optional
        Number of integration points per axis.

    Returns
    -------
    go.Figure
        Q-space image and calibrant-ring overlay figure.
    """
    transformed, axis_x, axis_y = compute_qspace_image_data(
        image_data=image_data,
        poni=poni,
        mask=mask,
        npt=npt,
    )

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

    for index, q_value in enumerate(ring_q_values or []):
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


def compute_qspace_image_data(
    image_data: np.ndarray,
    poni: PoniFile,
    mask: Optional[np.ndarray] = None,
    npt: int = 1200,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Integrate detector image into q-space and return log-intensity map data.

    Parameters
    ----------
    image_data : np.ndarray
        Detector image data.
    poni : PoniFile
        Calibrated geometry.
    mask : np.ndarray | None, optional
        Optional detector mask.
    npt : int, optional
        Number of integration points per axis.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        Log-intensity map, qx axis and qy axis.
    """
    integrator = AzimuthalIntegrator.sload(poni)
    result = integrator.integrate2d(
        image_data,
        npt,
        npt,
        unit=(Unit.parse("qx_nm^-1"), Unit.parse("qy_nm^-1")),
        mask=mask,
    )
    intensity = np.asarray(result[0])
    axis_x = np.asarray(result[1])
    axis_y = np.asarray(result[2])

    positive_pixels = intensity[intensity > 0]
    floor_value = float(np.nanmin(positive_pixels)) if positive_pixels.size else 1.0
    safe_floor = max(floor_value, 1.0)
    transformed = np.clip(np.log10(np.where(intensity > 0, intensity, safe_floor)), 0.0, None)
    return transformed, axis_x, axis_y


def run_geometry_refinement(
    image_data: np.ndarray,
    poni: PoniFile,
    calibrant_name: str,
    max_rings: int,
) -> tuple[PoniFile, dict[str, Any]]:
    """Run pyFAI geometry refinement using a calibrant image.

    Parameters
    ----------
    image_data : np.ndarray
        Detector image used for calibration.
    poni : PoniFile
        Initial PONI geometry.
    calibrant_name : str
        Name of calibrant from pyFAI calibrant registry.
    max_rings : int
        Maximum number of rings to extract.

    Returns
    -------
    tuple[PoniFile, dict[str, Any]]
        Refined PONI and metadata including chi2 metrics and ring values.
    """
    calibrant = get_calibrant(calibrant_name, wavelength=poni.wavelength)
    geometry = Geometry.sload(poni)
    single_geometry = SingleGeometry(
        label=Path(calibrant_name).stem,
        calibrant=calibrant,
        image=image_data,
        detector=poni.detector,
        geometry=geometry,
    )
    control_points = single_geometry.extract_cp(max_rings=max_rings, Imin=10)
    refiner = single_geometry.geometry_refinement
    refiner.data = np.asarray(control_points.getList())
    initial_chi2: float = float(refiner.chi2())
    refiner.set_tolerance(50)
    refiner.curve_fit(with_rot=False)
    final_chi2: float = float(refiner.chi2())
    refined_poni = PoniFile(**refiner.get_config())

    metadata: dict[str, Any] = {
        "initial_chi2": initial_chi2,
        "final_chi2": final_chi2,
        "ring_q_values": [
            float(4 * np.pi / (refined_poni.wavelength / 1e-9) * np.sin(tth / 2))
            for tth in calibrant.get_2th()[:max_rings]
        ],
    }
    return refined_poni, metadata


def serialize_poni(poni: PoniFile) -> str:
    """Serialize a PONI object to JSON string.

    Parameters
    ----------
    poni : PoniFile
        PONI object to serialize.

    Returns
    -------
    str
        JSON representation of ``poni.as_dict()``.
    """
    return json.dumps(poni.as_dict())


def deserialize_poni(payload: str) -> PoniFile:
    """Deserialize a PONI JSON payload.

    Parameters
    ----------
    payload : str
        JSON string containing PONI dictionary.

    Returns
    -------
    PoniFile
        Reconstructed PONI object.
    """
    return PoniFile(**json.loads(payload))
