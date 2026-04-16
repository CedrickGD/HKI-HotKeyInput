"""System tray icon wrapper."""
from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayIcon:
    """Wraps QSystemTrayIcon with a translatable context menu."""

    def __init__(self, parent: QWidget, icon: QIcon, t: Callable[..., str]) -> None:
        self._t = t
        self._tray = QSystemTrayIcon(parent)
        self._tray.setIcon(icon)
        self._tray.setToolTip("HKI")

        menu = QMenu(parent)
        self.act_edit = menu.addAction("")
        self.act_sidebar = menu.addAction("")
        self.act_hide = menu.addAction("")
        menu.addSeparator()
        self.act_quit = menu.addAction("")
        self._tray.setContextMenu(menu)

        self._on_show: Callable[[], None] | None = None
        self._tray.activated.connect(self._on_activated)

    def connect(
        self,
        on_show: Callable[[], None],
        on_sidebar: Callable[[], None],
        on_hide: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_show = on_show
        self.act_edit.triggered.connect(on_show)
        self.act_sidebar.triggered.connect(on_sidebar)
        self.act_hide.triggered.connect(on_hide)
        self.act_quit.triggered.connect(on_quit)

    def retranslate(self) -> None:
        self.act_edit.setText(self._t("tray_edit"))
        self.act_sidebar.setText(self._t("tray_sb"))
        self.act_hide.setText(self._t("tray_hide"))
        self.act_quit.setText(self._t("tray_quit"))

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def show_message(self, title: str, msg: str, duration: int = 2000) -> None:
        self._tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, duration)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ) and self._on_show:
            self._on_show()
