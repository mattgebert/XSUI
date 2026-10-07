"""Local file and directory selection using PyQt6 dialogs."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from typing import Optional

from PyQt6.QtWidgets import QApplication, QFileDialog


def _ensure_qapp() -> QApplication:
    """Create or return an active QApplication instance.

    Returns
    -------
    QApplication
        The active Qt application instance.
    """
    app: QApplication | None = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _select_path_via_subprocess(
    dialog_kind: str,
    caption: str,
    file_filter: str = "All Files (*)",
    start_dir: str = "",
) -> Optional[str]:
    """Open a Qt dialog in a helper process and return the selected path.

    Parameters
    ----------
    dialog_kind : str
        Dialog mode, either ``file`` or ``directory``.
    caption : str
        Title text shown to the user.
    file_filter : str, optional
        Qt file filter used only for file dialogs.

    Returns
    -------
    str | None
        Selected path, otherwise ``None``.
    """
    script = (
        "import json,sys;"
        "from PyQt6.QtWidgets import QApplication,QFileDialog;"
        "app=QApplication.instance() or QApplication([]);"
        "kind=sys.argv[1];caption=sys.argv[2];flt=sys.argv[3] if len(sys.argv)>3 else 'All Files (*)';start_dir=sys.argv[4] if len(sys.argv)>4 else '';"
        "path,_=QFileDialog.getOpenFileName(None,caption,start_dir,flt) if kind=='file' else (QFileDialog.getExistingDirectory(None,caption,start_dir),'');"
        "print(json.dumps({'path': path or ''}))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script, dialog_kind, caption, file_filter, start_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError:
        return None

    selected_path = payload.get("path")
    return selected_path or None


def select_file(
    caption: str,
    file_filter: str = "All Files (*)",
    start_dir: str = "",
) -> Optional[str]:
    """Open a native file chooser and return a selected path.

    Parameters
    ----------
    caption : str
        Title displayed in the file dialog.
    file_filter : str, optional
        Qt file filter expression.

    Returns
    -------
    str | None
        Selected file path, otherwise ``None`` when cancelled.
    """
    if threading.current_thread() is not threading.main_thread():
        return _select_path_via_subprocess("file", caption, file_filter, start_dir)

    _ = _ensure_qapp()
    selected_path: str
    selected_filter: str
    selected_path, selected_filter = QFileDialog.getOpenFileName(
        None,
        caption,
        start_dir,
        file_filter,
    )
    if not selected_path:
        return None
    return selected_path


def select_directory(caption: str, start_dir: str = "") -> Optional[str]:
    """Open a native directory chooser and return a selected path.

    Parameters
    ----------
    caption : str
        Title displayed in the directory dialog.

    Returns
    -------
    str | None
        Selected directory path, otherwise ``None`` when cancelled.
    """
    if threading.current_thread() is not threading.main_thread():
        return _select_path_via_subprocess("directory", caption, start_dir=start_dir)

    _ = _ensure_qapp()
    selected_path: str = QFileDialog.getExistingDirectory(None, caption, start_dir)
    if not selected_path:
        return None
    return selected_path
