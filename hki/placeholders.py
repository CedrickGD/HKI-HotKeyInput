"""Collapsible placeholder panel widget."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from hki.translations import BUILTIN_PH_KEYS
from hki.storage import CustomPlaceholder


class PlaceholderPanel(QWidget):
    """Collapsible panel for managing built-in and custom placeholders."""

    changed = Signal()

    def __init__(self, t: Callable[..., str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._t = t
        self._rows: list[dict] = []
        self._build()

    def _build(self) -> None:
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        # Toggle button
        self._toggle = QPushButton()
        self._toggle.setFlat(True)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle.setStyleSheet(
            "QPushButton{text-align:left;color:gray;font-size:12px;padding:2px 0;}"
            "QPushButton:hover{color:palette(text);}"
        )
        self._toggle.clicked.connect(self._on_toggle)
        lo.addWidget(self._toggle)

        # Content panel
        self._content = QWidget()
        cl = QVBoxLayout(self._content)
        cl.setContentsMargins(8, 4, 0, 4)
        cl.setSpacing(4)

        # Built-in section
        self._builtin_lbl = QLabel()
        self._builtin_lbl.setStyleSheet("font-weight:bold; font-size:12px;")
        cl.addWidget(self._builtin_lbl)
        self._date_lbl = QLabel()
        self._time_lbl = QLabel()
        for lbl in (self._date_lbl, self._time_lbl):
            lbl.setStyleSheet(
                "color:gray; font-size:12px; font-family:Consolas,monospace; padding-left:8px;"
            )
            cl.addWidget(lbl)

        # Custom section
        self._custom_lbl = QLabel()
        self._custom_lbl.setStyleSheet("font-weight:bold; font-size:12px; margin-top:4px;")
        cl.addWidget(self._custom_lbl)
        self._rows_widget = QWidget()
        self._rows_lo = QVBoxLayout(self._rows_widget)
        self._rows_lo.setContentsMargins(0, 0, 0, 0)
        self._rows_lo.setSpacing(2)
        cl.addWidget(self._rows_widget)

        self._add_btn = QPushButton()
        self._add_btn.setFixedWidth(80)
        self._add_btn.setStyleSheet("font-size:12px;")
        self._add_btn.clicked.connect(self._add_row)
        cl.addWidget(self._add_btn)

        self._content.hide()
        lo.addWidget(self._content)

    # ── public API ────────────────────────────────────────────────────

    def retranslate(self) -> None:
        arrow = "\u25BC" if self._content.isVisible() else "\u25B6"
        self._toggle.setText(f"{arrow}  {self._t('placeholders')}")
        self._builtin_lbl.setText(self._t("ph_builtin"))
        self._date_lbl.setText(self._t("ph_info_date"))
        self._time_lbl.setText(self._t("ph_info_time"))
        self._custom_lbl.setText(self._t("ph_custom"))
        self._add_btn.setText(self._t("ph_add"))

    def load(self, placeholders: list[CustomPlaceholder]) -> None:
        """Rebuild UI rows from a list of custom placeholders."""
        for row in self._rows:
            row["widget"].setParent(None)
            row["widget"].deleteLater()
        self._rows.clear()
        for cp in placeholders:
            self._build_row(cp.key, cp.kind, cp.value)

    def collect(self) -> list[CustomPlaceholder]:
        """Read current rows back as a list, clearing any reserved keys."""
        cps: list[CustomPlaceholder] = []
        for row in self._rows:
            key = row["key"].text().strip()
            if key in BUILTIN_PH_KEYS:
                row["key"].clear()
                key = ""
            kind = row["type"].currentData()
            val = row["value"].text()
            cps.append(CustomPlaceholder(key=key, kind=kind, value=val))
        return cps

    def reserved_key(self) -> str | None:
        """Return a reserved key name if any row uses one, else None."""
        for row in self._rows:
            key = row["key"].text().strip()
            if key in BUILTIN_PH_KEYS:
                return key
        return None

    # ── internals ─────────────────────────────────────────────────────

    def _on_toggle(self) -> None:
        vis = not self._content.isVisible()
        self._content.setVisible(vis)
        arrow = "\u25BC" if vis else "\u25B6"
        self._toggle.setText(f"{arrow}  {self._t('placeholders')}")

    def _build_row(self, key: str = "", kind: str = "text", value: str = "") -> None:
        row_w = QWidget()
        row_lo = QHBoxLayout(row_w)
        row_lo.setContentsMargins(0, 0, 0, 0)
        row_lo.setSpacing(4)

        key_edit = QLineEdit(key)
        key_edit.setPlaceholderText(self._t("ph_key"))
        key_edit.setFixedWidth(90)
        key_edit.setStyleSheet("font-size:12px;")

        type_cb = QComboBox()
        type_cb.addItem(self._t("ph_type_text"), "text")
        type_cb.addItem(self._t("ph_type_dt"), "datetime")
        type_cb.setCurrentIndex(0 if kind == "text" else 1)
        type_cb.setFixedWidth(90)
        type_cb.setStyleSheet("font-size:12px;")

        val_edit = QLineEdit(value)
        val_edit.setPlaceholderText(
            self._t("ph_val_hint_text") if kind == "text" else self._t("ph_val_hint_dt")
        )
        val_edit.setStyleSheet("font-size:12px;")

        del_btn = QPushButton("\u2715")
        del_btn.setFixedSize(22, 22)
        del_btn.setFlat(True)
        del_btn.setStyleSheet(
            "QPushButton{font-size:12px;color:gray;border:none;}"
            "QPushButton:hover{color:white;background:#c42b1c;border-radius:3px;}"
        )

        row_lo.addWidget(key_edit)
        row_lo.addWidget(type_cb)
        row_lo.addWidget(val_edit, 1)
        row_lo.addWidget(del_btn)

        self._rows_lo.addWidget(row_w)
        entry = {"widget": row_w, "key": key_edit, "type": type_cb, "value": val_edit}
        self._rows.append(entry)

        def _on_type_change(idx: int, ve=val_edit, tc=type_cb) -> None:
            k = tc.itemData(idx)
            ve.setPlaceholderText(
                self._t("ph_val_hint_text") if k == "text" else self._t("ph_val_hint_dt")
            )
            self.changed.emit()
        type_cb.currentIndexChanged.connect(_on_type_change)

        key_edit.editingFinished.connect(self.changed.emit)
        val_edit.editingFinished.connect(self.changed.emit)
        del_btn.clicked.connect(lambda _, e=entry: self._del_row(e))

    def _add_row(self) -> None:
        self._build_row()
        self.changed.emit()

    def _del_row(self, entry: dict) -> None:
        if entry in self._rows:
            self._rows.remove(entry)
        entry["widget"].setParent(None)
        entry["widget"].deleteLater()
        self.changed.emit()
