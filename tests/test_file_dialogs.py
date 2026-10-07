"""Tests for local file dialog helpers."""

from __future__ import annotations

from XSUI.webapp.services import file_dialogs


class _DummyApp:
    """Simple stand-in for QApplication during tests."""


class _DummyDialog:
    """Dummy dialog provider returning deterministic paths."""

    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return "C:/tmp/example.poni", "PONI Files (*.poni)"

    @staticmethod
    def getExistingDirectory(*args, **kwargs):
        return "C:/tmp/data"


class _DummyDialogCancel:
    """Dummy dialog provider returning empty selections."""

    @staticmethod
    def getOpenFileName(*args, **kwargs):
        return "", ""

    @staticmethod
    def getExistingDirectory(*args, **kwargs):
        return ""


def test_select_file_returns_path(monkeypatch) -> None:
    """File picker should return selected path."""
    monkeypatch.setattr(file_dialogs, "_ensure_qapp", lambda: _DummyApp())
    monkeypatch.setattr(file_dialogs, "QFileDialog", _DummyDialog)
    selected = file_dialogs.select_file("Select test file")
    assert selected == "C:/tmp/example.poni"


def test_select_file_cancel_returns_none(monkeypatch) -> None:
    """File picker should return None when cancelled."""
    monkeypatch.setattr(file_dialogs, "_ensure_qapp", lambda: _DummyApp())
    monkeypatch.setattr(file_dialogs, "QFileDialog", _DummyDialogCancel)
    selected = file_dialogs.select_file("Select test file")
    assert selected is None


def test_select_directory_returns_path(monkeypatch) -> None:
    """Directory picker should return selected path."""
    monkeypatch.setattr(file_dialogs, "_ensure_qapp", lambda: _DummyApp())
    monkeypatch.setattr(file_dialogs, "QFileDialog", _DummyDialog)
    selected = file_dialogs.select_directory("Select test directory")
    assert selected == "C:/tmp/data"
