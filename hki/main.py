from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from hki.window import MainWindow


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


def run() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tray", action="store_true")
    args, qt_args = parser.parse_known_args()

    app = QApplication([sys.argv[0], *qt_args])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("HOTKEYINPUT")
    app.setOrganizationName("HKI")
    app.setWindowIcon(QIcon(str(resource_path("assets", "hki.ico"))))
    app.setFont(QFont("Segoe UI Variable Text", 10))

    window = MainWindow(resource_path)
    if args.tray:
        window.hide_to_tray(show_message=False)
    else:
        window.show()
    return app.exec()
