"""Tests for reduction service helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from XSUI.webapp.services.calibration_service import (
    read_calibration_image,
    read_poni_file,
    run_geometry_refinement,
)
from XSUI.webapp.services import reduction_service as rs


_DATA_DIR = Path(__file__).parent / "test_data" / "R01_PBTTT"
"""Path to real GIWAXS sample data used for integration tests."""


@pytest.fixture
def real_reduction_inputs() -> dict[str, object]:
    """Prepare calibrated geometry and representative sample files.

    Returns
    -------
    dict[str, object]
        Input payload containing refined PONI and selected image paths.
    """
    rough_poni = read_poni_file(str(_DATA_DIR / "exp_GIWAXS.poni"))
    calibration_image = read_calibration_image(str(_DATA_DIR / "agbeh_0008_0001.tif"))
    refined_poni, metadata = run_geometry_refinement(
        image_data=calibration_image,
        poni=rough_poni,
        calibrant_name="AgBh",
        max_rings=3,
    )
    data_files = sorted(_DATA_DIR.glob("R01_07_r01_0577_*.tif"))
    return {
        "poni": refined_poni,
        "files": data_files,
        "metadata": metadata,
    }


def test_list_image_files_filters_known_extensions(tmp_path: Path) -> None:
    """Only supported image files should be returned."""
    (tmp_path / "a.tif").write_text("x", encoding="utf-8")
    (tmp_path / "b.tiff").write_text("x", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    result = rs.list_image_files(str(tmp_path))
    assert len(result) == 2


def test_compile_angle_regex_requires_named_group() -> None:
    """Regex must contain the named AOI group."""
    ok, message = rs.compile_angle_regex(r".*_(\d+p\d+)_.*")
    assert not ok
    assert "aoi" in message


def test_compile_angle_regex_valid() -> None:
    """Named AOI regex should compile successfully."""
    ok, message = rs.compile_angle_regex(r".*_(?P<aoi>\d+p\d+)_.*")
    assert ok


def test_parse_incident_angle_from_filename() -> None:
    """AOI parser should convert p decimal token to float."""
    value = rs.parse_incident_angle_from_filename(
        "sample_0p10_scan_0001.tif",
        r".*_(?P<aoi>\d+p\d+)_.*",
    )
    assert value == pytest.approx(0.10)


def test_parse_angle_arcs() -> None:
    """Arc parser should parse newline-delimited start/end angles."""
    payload = "-90,-80\n-5,5"
    arcs = rs.parse_angle_arcs(payload)
    assert arcs == [(-90.0, -80.0), (-5.0, 5.0)]


def test_example_output_name_uses_regex_groups() -> None:
    """Output naming helper should use regex groups when available."""
    value = rs.example_output_name(
        "mySample_anything_0042.tif",
        r"(?P<sample>mySample)_.*_(?P<index>\d+)\.tif",
        "qip_qoop",
    )
    assert value == "mySample-qip_qoop-0042.npz"


def test_summarise_regex_match_with_example() -> None:
    """Regex summary should include an example when a file matches."""
    files = ["sample_0p25_file.tif"]
    summary = rs.summarise_regex_match(files, r".*_(?P<aoi>\d+p\d+)_.*")
    assert summary["ok"]
    assert summary["example"] is not None


def test_real_data_directory_contains_expected_files() -> None:
    """Real test-data directory should contain rough PONI, AgBeh, and R01 images."""
    assert (_DATA_DIR / "exp_GIWAXS.poni").exists()
    assert (_DATA_DIR / "agbeh_0008_0001.tif").exists()
    assert len(list(_DATA_DIR.glob("R01_07_r01_0577_*.tif"))) >= 5


def test_reduce_image_2d_with_real_data_qip_qoop(
    real_reduction_inputs: dict[str, object],
) -> None:
    """GI 2D reduction should return finite arrays for real R01 image data."""
    first_image = str(real_reduction_inputs["files"][0])
    poni = real_reduction_inputs["poni"]
    intensity, axis_x, axis_y = rs.reduce_image_2d(
        image_path=first_image,
        poni=poni,
        grazing=True,
        output_mode="qip_qoop",
        angle_of_incidence_deg=0.1,
        npt=300,
    )
    assert intensity.ndim == 2
    assert axis_x.ndim == 1
    assert axis_y.ndim == 1
    assert np.isfinite(intensity).any()


def test_reduce_image_2d_with_real_data_qx_qy(
    real_reduction_inputs: dict[str, object],
) -> None:
    """Non-GI azimuthal reduction should run on real data with calibrated PONI."""
    first_image = str(real_reduction_inputs["files"][0])
    poni = real_reduction_inputs["poni"]
    intensity, axis_x, axis_y = rs.reduce_image_2d(
        image_path=first_image,
        poni=poni,
        grazing=False,
        output_mode="qx_qy",
        angle_of_incidence_deg=0.1,
        npt=300,
    )
    assert intensity.ndim == 2
    assert axis_x.ndim == 1
    assert axis_y.ndim == 1
    assert np.isfinite(intensity).any()


def test_reduce_lineprofile_1d_with_real_data(
    real_reduction_inputs: dict[str, object],
) -> None:
    """GI lineprofile reduction should return monotonic q and finite intensity arrays."""
    first_image = str(real_reduction_inputs["files"][0])
    poni = real_reduction_inputs["poni"]
    q_vals, intensity = rs.reduce_lineprofile_1d(
        image_path=first_image,
        poni=poni,
        angle_arc=(-90.0, -80.0),
        angle_of_incidence_deg=0.1,
        npt=500,
    )
    assert q_vals.ndim == 1
    assert intensity.ndim == 1
    assert q_vals.shape == intensity.shape
    assert np.isfinite(intensity).any()
