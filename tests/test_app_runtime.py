"""Runtime tests for FastAPI mount, Dash endpoints, and __main__ launcher."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from XSUI import __main__ as xsui_main
from XSUI.webapp.fastapi.main import app


def test_fastapi_root_endpoint() -> None:
    """FastAPI root endpoint should return hello payload."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json().get("message") == "Hello World"


def test_dash_mount_serves_index_page() -> None:
    """Dash app should render without duplicate-id failure under mounted route."""
    client = TestClient(app)
    response = client.get("/dashboard1/")
    assert response.status_code == 200
    assert "Duplicate component id" not in response.text


def test_dash_layout_endpoint_is_available() -> None:
    """Dash internal layout endpoint should resolve through mounted prefix."""
    client = TestClient(app)
    response = client.get("/dashboard1/_dash-layout")
    assert response.status_code == 200
    payload = response.json()
    assert "props" in payload


def _collect_ids(component: dict, ids: set[str]) -> None:
    """Recursively collect Dash component ids from serialized layout payload.

    Parameters
    ----------
    component : dict
        Serialized Dash component.
    ids : set[str]
        Accumulator set for collected ids.
    """
    props = component.get("props", {})
    component_id = props.get("id")
    if isinstance(component_id, str):
        ids.add(component_id)

    children = props.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                _collect_ids(child, ids)
    elif isinstance(children, dict):
        _collect_ids(children, ids)


def _collect_text(component: dict, values: list[str]) -> None:
    """Recursively collect text children from serialized layout payload.

    Parameters
    ----------
    component : dict
        Serialized Dash component.
    values : list[str]
        Accumulator list for text values.
    """
    props = component.get("props", {})
    label = props.get("label")
    if isinstance(label, str):
        values.append(label)
    children = props.get("children")
    if isinstance(children, str):
        values.append(children)
    elif isinstance(children, list):
        for child in children:
            if isinstance(child, str):
                values.append(child)
            elif isinstance(child, dict):
                _collect_text(child, values)
    elif isinstance(children, dict):
        _collect_text(children, values)


def test_gui_workflow_layout_structure() -> None:
    """Mounted GUI should expose calibration and reduction workflow controls."""
    client = TestClient(app)
    response = client.get("/dashboard1/_dash-layout")
    assert response.status_code == 200
    payload = response.json()

    found_ids: set[str] = set()
    _collect_ids(payload, found_ids)
    assert "main-tabs" in found_ids
    assert "tab-calibration" in found_ids
    assert "tab-reduction" in found_ids
    assert "tab-giwaxs" not in found_ids
    assert "tab-waxs" not in found_ids

    assert "calibration_tab-btn-select_poni" in found_ids
    assert "calibration_tab-btn-select_calibration_data" in found_ids
    assert "calibration_tab-input-max_rings" in found_ids
    assert "calibration_tab-display_mode_toggle" in found_ids
    assert "calibration_tab-calibrated_indicator" in found_ids
    assert "reduction_tab-scattering_tabs" not in found_ids
    assert "reduction_tab-output_dir_label" in found_ids
    assert "reduction_tab-btn-view_output_dir" in found_ids
    assert "reduction_tab-images_preview_dropdown" in found_ids
    assert "reduction_tab-lines_preview_dropdown" in found_ids
    assert "reduction_tab-images_progress" in found_ids
    assert "reduction_tab-lines_progress" in found_ids
    assert "reduction_tab-subtabs" in found_ids

    text_values: list[str] = []
    _collect_text(payload, text_values)
    assert any(text.strip() == "Rings:" for text in text_values)
    assert any(text.strip() == "Image Preview" for text in text_values)
    assert any(text.strip() == "Lineprofile Preview" for text in text_values)
    assert any(text.strip() == "Output Directory" for text in text_values)


def test_dash_dependencies_endpoint_is_available() -> None:
    """Dash dependencies endpoint should be served under mounted prefix path."""
    client = TestClient(app)
    response = client.get("/dashboard1/_dash-dependencies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_main_uses_current_interpreter(monkeypatch) -> None:
    """Main launcher should call subprocess with sys.executable and fastapi path."""
    captured: dict[str, object] = {}

    def _fake_run(cmd, shell, check):
        captured["cmd"] = cmd
        captured["shell"] = shell
        captured["check"] = check
        return 0

    monkeypatch.setattr(xsui_main.subprocess, "run", _fake_run)
    xsui_main.main()

    assert captured["shell"] is False
    assert captured["check"] is True
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert cmd[0] == sys.executable
    expected_suffix = "XSUI/webapp/fastapi/main.py"
    assert str(cmd[1]).replace("\\", "/").endswith(expected_suffix)
