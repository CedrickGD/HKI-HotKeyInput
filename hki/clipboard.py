"""Clipboard management and placeholder resolution."""
from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from hki.storage import CustomPlaceholder

log = logging.getLogger(__name__)


def resolve_placeholders(text: str, custom_placeholders: list[CustomPlaceholder]) -> str:
    """Replace built-in and custom placeholders in text."""
    now = datetime.now()
    text = text.replace("{date}", now.strftime("%d.%m.%Y"))
    text = text.replace("{time}", now.strftime("%H:%M"))
    for cp in custom_placeholders:
        if not cp.key:
            continue
        token = "{" + cp.key + "}"
        if token not in text:
            continue
        if cp.kind == "datetime":
            try:
                text = text.replace(token, now.strftime(cp.value))
            except Exception:
                log.warning("Invalid strftime pattern '%s' for placeholder {%s}", cp.value, cp.key)
        else:
            text = text.replace(token, cp.value)
    return text


def snap_clipboard(src: QMimeData | None) -> QMimeData | None:
    """Take a snapshot of the current clipboard contents."""
    if not src:
        return None
    s = QMimeData()
    for f in src.formats():
        s.setData(f, src.data(f))
    if src.hasText():
        s.setText(src.text())
    if src.hasHtml():
        s.setHtml(src.html())
    return s


def restore_clipboard(snapshot: QMimeData | None) -> None:
    """Restore a previously snapped clipboard."""
    if snapshot:
        QApplication.clipboard().setMimeData(snapshot)
