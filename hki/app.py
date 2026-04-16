"""Entry point for HKI."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PySide6.QtCore import QSharedMemory
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from hki.updater import apply_pending_update, check_for_update_async
from hki.window import MainWindow


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


def run() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tray", action="store_true")
    args, qt_args = parser.parse_known_args()

    # Check for existing instance
    shared_memory = QSharedMemory("HKI_SingleInstance")
    if not shared_memory.create(1):
        # Another instance is already running
        print("HKI is already running.")
        return 1

    # Start background update check (once per session, silent)
    check_for_update_async()

    app = QApplication([sys.argv[0], *qt_args])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("HKI")
    app.setOrganizationName("HKI")
    app.setWindowIcon(QIcon(str(resource_path("assets", "hki.ico"))))
    app.setFont(QFont("Segoe UI", 9))

    window = MainWindow(resource_path)
    if args.tray:
        window.hide_to_tray(msg=False)
    else:
        window.show()
    rc = app.exec()

    # Clean up shared memory
    shared_memory.detach()

    # Silently apply downloaded update on exit
    apply_pending_update()

    return rc
