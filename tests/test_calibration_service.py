"""Tests for calibration service helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from pyFAI.io.ponifile import PoniFile

from XSUI.webapp.services.calibration_service import (
    build_calibration_figure,
    build_qspace_overlay_figure,
    deserialize_poni,
    pixel_beamcentre,
    read_calibration_image,
    read_poni_file,
    run_geometry_refinement,
    serialize_poni,
    wavelength_to_energy,
)


_DATA_DIR = Path(__file__).parent / "test_data" / "R01_PBTTT"
"""Path to real GIWAXS sample data used for integration tests."""


@pytest.fixture
def real_data_paths() -> dict[str, Path]:
    """Collect key file paths used by calibration integration tests.

    Returns
    -------
    dict[str, Path]
        Mapping with keys for rough PONI and AgBeh calibration image.
    """
    return {
        "poni": _DATA_DIR / "exp_GIWAXS.poni",
        "calibration_image": _DATA_DIR / "agbeh_0008_0001.tif",
    }


def test_wavelength_to_energy_positive_conversion() -> None:
    """Wavelength conversion should return a positive value."""
    energy = wavelength_to_energy(1e-10)
    assert energy > 0


def test_wavelength_to_energy_zero_raises() -> None:
    """Zero wavelength must raise a ValueError."""
    with pytest.raises(ValueError):
        wavelength_to_energy(0)


def test_poni_serialize_roundtrip() -> None:
    """Serialized PONI payload should deserialize back to equivalent values."""
    source = PoniFile(dist=0.2, poni1=0.01, poni2=0.02, wavelength=1e-10)
    payload = serialize_poni(source)
    restored = deserialize_poni(payload)
    assert restored.dist == pytest.approx(source.dist)
    assert restored.poni1 == pytest.approx(source.poni1)
    assert restored.poni2 == pytest.approx(source.poni2)
    assert restored.wavelength == pytest.approx(source.wavelength)


def test_pixel_beamcentre_returns_three_values() -> None:
    """Beam centre should return y, x, z values."""
    poni = PoniFile(dist=0.2, poni1=0.01, poni2=0.02, wavelength=1e-10)
    result = pixel_beamcentre(poni, poni.detector)
    assert result.shape == (3,)


def test_build_calibration_figure_has_image_trace() -> None:
    """Calibration figure should include the image trace."""
    image = np.ones((10, 10), dtype=float)
    fig = build_calibration_figure(image)
    assert len(fig.data) >= 1


def test_build_calibration_figure_with_beamcentre_and_ring() -> None:
    """Calibration figure should include overlay traces when PONI and rings are provided."""
    image = np.ones((32, 32), dtype=float)
    poni = PoniFile(dist=0.2, poni1=0.01, poni2=0.02, wavelength=1e-10)
    fig = build_calibration_figure(
        image,
        poni=poni,
        detector_name=None,
        calibrant_name="AgBeh",
        ring_q_values=[1.0],
    )
    trace_names = [trace.name for trace in fig.data if getattr(trace, "name", None)]
    assert "Beam Centre" in trace_names


def test_read_real_poni_and_calibration_image(real_data_paths: dict[str, Path]) -> None:
    """Real test data should load as valid PONI and calibration image objects."""
    rough_poni = read_poni_file(str(real_data_paths["poni"]))
    calib_image = read_calibration_image(str(real_data_paths["calibration_image"]))
    assert rough_poni.dist > 0
    assert rough_poni.wavelength > 0
    assert calib_image.ndim == 2
    assert calib_image.size > 0


def test_run_geometry_refinement_with_real_agbeh_data(
    real_data_paths: dict[str, Path],
) -> None:
    """Geometry refinement should return finite chi2 values on real AgBeh data."""
    rough_poni = read_poni_file(str(real_data_paths["poni"]))
    calib_image = read_calibration_image(str(real_data_paths["calibration_image"]))
    refined_poni, metadata = run_geometry_refinement(
        image_data=calib_image,
        poni=rough_poni,
        calibrant_name="AgBh",
        max_rings=3,
    )

    assert refined_poni.wavelength > 0
    assert np.isfinite(metadata["initial_chi2"])
    assert np.isfinite(metadata["final_chi2"])
    assert len(metadata["ring_q_values"]) > 0


def test_build_qspace_overlay_figure_with_real_calibrated_data(
    real_data_paths: dict[str, Path],
) -> None:
    """Q-space overlay figure should include heatmap and calibrant ring traces."""
    rough_poni = read_poni_file(str(real_data_paths["poni"]))
    calib_image = read_calibration_image(str(real_data_paths["calibration_image"]))
    refined_poni, metadata = run_geometry_refinement(
        image_data=calib_image,
        poni=rough_poni,
        calibrant_name="AgBh",
        max_rings=3,
    )
    fig = build_qspace_overlay_figure(
        image_data=calib_image,
        poni=refined_poni,
        calibrant_name="AgBh",
        ring_q_values=metadata["ring_q_values"],
        npt=400,
    )
    assert len(fig.data) >= 2
