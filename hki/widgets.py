"""Reusable UI widgets — HotkeyLineEdit and Sidebar."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from hki.translations import TR
from hki.storage import Preset
from hki.windows_api import capture_hotkey_from_event


# ── Hotkey capture field ──────────────────────────────────────────────

class HotkeyLineEdit(QLineEdit):
    hotkey_changed = Signal(str)
    capture_started = Signal()
    capture_cancelled = Signal()
    capture_finished = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._capturing = False
        self._prev = ""
        self._idle = TR["en"]["capture_idle"]
        self._active = TR["en"]["capture_active"]
        self.setReadOnly(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPlaceholderText(self._idle)

    def set_prompts(self, idle: str, active: str) -> None:
        self._idle = idle
        self._active = active
        self.setPlaceholderText(self._active if self._capturing else self._idle)

    def mousePressEvent(self, e) -> None:
        super().mousePressEvent(e)
        self._begin()

    def focusInEvent(self, e) -> None:
        super().focusInEvent(e)
        self._begin()

    def focusOutEvent(self, e) -> None:
        self._cancel()
        super().focusOutEvent(e)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        k = e.key()
        if k in (int(Qt.Key.Key_Tab), int(Qt.Key.Key_Backtab)):
            self._cancel()
            super().keyPressEvent(e)
            return
        if k == int(Qt.Key.Key_Escape):
            self._cancel()
            e.accept()
            return
        if k in (int(Qt.Key.Key_Backspace), int(Qt.Key.Key_Delete)):
            self.clear()
            self._prev = ""
            self._capturing = False
            self.setPlaceholderText(self._idle)
            self.hotkey_changed.emit("")
            return
        g = capture_hotkey_from_event(e)
        if not g:
            e.accept()
            return
        self.hotkey_changed.emit(g.display)
        self.setText(g.display)
        self._capturing = False
        self.setPlaceholderText(self._idle)
        self.capture_finished.emit(g.display)
        e.accept()

    def _begin(self) -> None:
        if self._capturing:
            return
        self._prev = self.text()
        self.clear()
        self._capturing = True
        self.setPlaceholderText(self._active)
        self.capture_started.emit()

    def _cancel(self) -> None:
        if not self._capturing:
            return
        self.setText(self._prev)
        self._capturing = False
        self.setPlaceholderText(self._idle)
        self.capture_cancelled.emit()


# ── Quick-paste sidebar ──────────────────────────────────────────────

class Sidebar(QWidget):
    chosen = Signal(str)

    def __init__(self, t: Callable[..., str], parent: QWidget | None = None) -> None:
        flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        super().__init__(parent, flags)
        self._t = t
        self._presets: list[Preset] = []
        self.resize(320, 400)

        # Drag functionality
        self._drag_start_pos: QPoint | None = None
        self._dragging = False

        lo = QVBoxLayout(self)
        lo.setContentsMargins(6, 6, 6, 6)
        lo.setSpacing(4)

        # Title bar with close button
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel()
        self.title.setStyleSheet("font-weight:bold;")
        self._close_btn = QPushButton("\u2715")
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.setFlat(True)
        self._close_btn.setStyleSheet("QPushButton{font-size:14px;border:none;color:gray;}"
                                      "QPushButton:hover{color:white;background:#c42b1c;border-radius:4px;}")
        self._close_btn.clicked.connect(self.hide)
        title_row.addWidget(self.title)
        title_row.addStretch()
        title_row.addWidget(self._close_btn)

        self.search = QLineEdit()
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.hint = QLabel()
        self.hint.setStyleSheet("color:gray; font-size:11px;")

        lo.addLayout(title_row)
        lo.addWidget(self.search)
        lo.addWidget(self.list, 1)
        lo.addWidget(self.hint)

        self.search.textChanged.connect(self._refresh)
        self.search.returnPressed.connect(self._emit)
        self.list.itemActivated.connect(lambda _: self._emit())
        self.retranslate()

    def retranslate(self) -> None:
        self.setWindowTitle(self._t("sb_title"))
        self.title.setText(self._t("sb_title"))
        self.search.setPlaceholderText(self._t("sb_filter"))
        self.hint.setText(self._t("sb_hint"))

    def set_presets(self, presets: list[Preset]) -> None:
        self._presets = list(presets)
        self.search.clear()
        self._refresh()

    def open(self) -> None:
        if self.isVisible():
            self.hide()
            return
        self._refresh()
        scr = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if scr:
            g = scr.availableGeometry()
            self.move(g.x() + g.width() - self.width() - 16, g.y() + 16)
        self.show()
        self.raise_()
        self.activateWindow()
        self.search.setFocus()
        self.search.selectAll()

    def _refresh(self) -> None:
        q = self.search.text().strip().lower()
        hits = [p for p in self._presets
                if not q or q in p.name.lower() or q in p.text.lower() or q in p.hotkey.lower()]
        hits.sort(key=lambda p: p.name.lower())
        self.list.clear()
        for p in hits:
            hk = f"  [{p.hotkey}]" if p.hotkey else ""
            item = QListWidgetItem(f"{p.name or '?'}{hk}")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _emit(self) -> None:
        it = self.list.currentItem()
        if it:
            self.chosen.emit(it.data(Qt.ItemDataRole.UserRole))

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == int(Qt.Key.Key_Escape):
            self.hide()
            e.accept()
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            # Check if click is on the title bar area (top part of the window)
            title_bar_height = 30  # Approximate height of title bar
            if e.pos().y() <= title_bar_height:
                self._drag_start_pos = e.globalPos() - self.frameGeometry().topLeft()
                self._dragging = True
                e.accept()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._dragging and self._drag_start_pos is not None:
            self.move(e.globalPos() - self._drag_start_pos)
            e.accept()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_start_pos = None
            e.accept()
        super().mouseReleaseEvent(e)
