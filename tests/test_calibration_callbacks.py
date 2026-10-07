"""Tests for calibration callback behavior."""

from __future__ import annotations

import numpy as np
from pyFAI.io.ponifile import PoniFile

from XSUI.webapp.dash.callbacks.callback_calibration import (
    precompute_qspace_cache,
    sync_energy_from_wavelength,
    update_calibration_preview,
    update_display_toggle_style,
)
from XSUI.webapp.services.calibration_service import serialize_poni, wavelength_to_energy


def test_toggle_style_enabled_after_image_and_complete_poni_inputs() -> None:
    """Display-mode toggle should enable when image data and full PONI editor values exist."""
    style = update_display_toggle_style(
        calibration_ready=False,
        image_data_payload=np.ones((8, 8), dtype=float).tolist(),
        detector_name="Eiger4M",
        energy=12000.0,
        sdd=0.2,
        poni1=0.01,
        poni2=0.02,
        rot1=0.0,
        rot2=0.0,
        rot3=0.0,
    )
    assert style["pointerEvents"] == "auto"
    assert style["opacity"] == 1.0


def test_toggle_style_disabled_when_required_poni_field_missing() -> None:
    """Display-mode toggle should remain disabled with incomplete PONI editor values."""
    style = update_display_toggle_style(
        calibration_ready=False,
        image_data_payload=np.ones((8, 8), dtype=float).tolist(),
        detector_name="Eiger4M",
        energy=12000.0,
        sdd=0.2,
        poni1=0.01,
        poni2=0.02,
        rot1=0.0,
        rot2=None,
        rot3=0.0,
    )
    assert style["pointerEvents"] == "none"


def test_sync_energy_from_wavelength_infers_energy() -> None:
    """Wavelength edits should infer energy through physical conversion."""
    wavelength = 1.033e-10
    expected_energy = wavelength_to_energy(wavelength)
    inferred_energy = sync_energy_from_wavelength(wavelength)
    assert inferred_energy == expected_energy


def test_update_calibration_preview_with_payload_and_wavelength_change() -> None:
    """Preview update should recalculate q-space with edited wavelength without setter errors."""
    image = np.ones((195, 487), dtype=float)
    source_poni = PoniFile(
        dist=0.25,
        poni1=0.01,
        poni2=0.02,
        rot1=0.0,
        rot2=0.0,
        rot3=0.0,
        wavelength=1.2e-10,
        detector="Pilatus100k",
    )
    payload = serialize_poni(source_poni)

    qspace_cache = precompute_qspace_cache(
        image_data_payload=image.tolist(),
        poni_payload=payload,
        detector_name="Pilatus100k",
        wavelength=1.0e-10,
        sdd=0.25,
        poni1=0.01,
        poni2=0.02,
        rot1=0.0,
        rot2=0.0,
        rot3=0.0,
        mask_data=None,
    )

    figure = update_calibration_preview(
        image_data_payload=image.tolist(),
        poni_payload=payload,
        display_mode="qspace",
        detector_name="Pilatus100k",
        calibrant_name="AgBh",
        wavelength=1.0e-10,
        sdd=0.25,
        poni1=0.01,
        poni2=0.02,
        rot1=0.0,
        rot2=0.0,
        rot3=0.0,
        qspace_cache=qspace_cache,
        mask_data=None,
        ring_q_values=[1.0],
    )

    assert len(figure.data) >= 1
