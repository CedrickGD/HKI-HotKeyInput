"""Main window — native Windows 11 look, no custom themes."""
from __future__ import annotations

import logging
import time
from functools import partial
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QPushButton,
    QSizePolicy, QSplitter, QStatusBar, QTextEdit,
    QToolBar, QVBoxLayout, QWidget,
)

from hki.hotkeys import HotkeyRegistry
from hki.translations import LANGS, LANG_NAMES, TR
from hki.clipboard import resolve_placeholders, restore_clipboard, snap_clipboard
from hki.placeholders import PlaceholderPanel
from hki.storage import VERSION, Preset, Store, _utc_now
from hki.tray import TrayIcon
from hki.widgets import HotkeyLineEdit, Sidebar
from hki.windows_api import (
    MSG, WM_HOTKEY, apply_windows_11_backdrop,
    get_foreground_window, normalize_hotkey,
    restore_foreground_window, send_ctrl_v,
)

log = logging.getLogger(__name__)

# Minimum interval between two hotkey-triggered pastes (seconds).
_HK_DEBOUNCE = 0.3


# ── Main window ──────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, resource_path: Callable[..., Path]) -> None:
        super().__init__()
        self._res = resource_path
        self._store = Store()
        self._state = self._store.load()
        self._lang = self._state.language if self._state.language in LANGS else "en"
        self._cur_id: str | None = None
        self._hk_reg = HotkeyRegistry()
        self._clip_snap = None
        self._quitting = False
        self._suspend = False
        self._dirty = False
        self._tray_tipped = False
        self._backdrop_done = False
        self._sb_target = 0
        self._last_external_hwnd = get_foreground_window()
        self._was_maximized = False
        self._was_minimized = False
        self._last_hk_time = 0.0

        icon = QIcon(str(self._res("assets", "hki.ico")))
        self.setWindowTitle(f"Hot Key Input  —  v{VERSION}")
        self.setWindowIcon(icon)
        self.setMinimumSize(640, 400)
        self.resize(self._state.window.width or 860, self._state.window.height or 540)

        self._build_toolbar()
        self._build_central()
        self._sidebar = Sidebar(self._t)
        self._sidebar.chosen.connect(self._paste_from_sidebar)
        self._tray = TrayIcon(self, icon, self._t)
        self._tray.connect(self._show_from_tray, self._open_sb_ui,
                           self.hide_to_tray, self._quit)
        self._fg_timer = QTimer(self)
        self._fg_timer.setInterval(250)
        self._fg_timer.timeout.connect(self._track_foreground_window)
        self._fg_timer.start()
        self.setStatusBar(QStatusBar())
        self._retranslate(init=True)
        self._restore_pos()
        self._load_ui()

    def _t(self, key: str, **kw) -> str:
        tbl = TR.get(self._lang, TR["en"])
        return tbl.get(key, TR["en"].get(key, key)).format(**kw)

    # ── toolbar ────────────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)
        self.addToolBar(tb)

        self._lang_btn = QPushButton("EN")
        self._lang_menu = QMenu(self)
        self._lang_acts: dict[str, QAction] = {}
        for lang in LANGS:
            a = QAction(LANG_NAMES[lang], self)
            a.setCheckable(True)
            a.triggered.connect(partial(self._switch_lang, lang))
            self._lang_menu.addAction(a)
            self._lang_acts[lang] = a
        self._lang_btn.setMenu(self._lang_menu)
        self._lang_btn.setFixedWidth(48)
        tb.addWidget(self._lang_btn)
        tb.addSeparator()

        self._sb_hk_lbl = QLabel()
        tb.addWidget(self._sb_hk_lbl)
        self._sb_hk_edit = HotkeyLineEdit()
        self._sb_hk_edit.setFixedWidth(150)
        tb.addWidget(self._sb_hk_edit)
        tb.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self._sb_btn = QPushButton()
        self._sb_btn.clicked.connect(self._open_sb_ui)
        tb.addWidget(self._sb_btn)

    # ── central: list + editor ─────────────────────────────────────────

    def _build_central(self) -> None:
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)

        # left — preset list
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(4, 4, 4, 4)
        ll.setSpacing(4)
        self._search = QLineEdit()
        ll.addWidget(self._search)
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        ll.addWidget(self._list, 1)
        btns = QHBoxLayout()
        btns.setSpacing(4)
        self._btn_new = QPushButton()
        self._btn_dup = QPushButton()
        self._btn_del = QPushButton()
        btns.addWidget(self._btn_new)
        btns.addWidget(self._btn_dup)
        btns.addWidget(self._btn_del)
        ll.addLayout(btns)

        # right — editor
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(4, 4, 4, 4)
        rl.setSpacing(6)
        self._form = QFormLayout()
        self._form.setSpacing(4)
        self._name = QLineEdit()
        self._hk = HotkeyLineEdit()
        self._form.addRow("Name", self._name)
        self._form.addRow("Hotkey", self._hk)
        rl.addLayout(self._form)
        self._txt_lbl = QLabel("Text")
        rl.addWidget(self._txt_lbl)
        self._text = QTextEdit()
        self._text.setAcceptRichText(False)
        rl.addWidget(self._text, 1)

        self._ph_panel = PlaceholderPanel(self._t)
        self._ph_panel.changed.connect(self._on_ph_changed)
        rl.addWidget(self._ph_panel)

        eb = QHBoxLayout()
        eb.setSpacing(4)
        self._btn_save = QPushButton()
        self._btn_copy = QPushButton()
        self._btn_paste = QPushButton()
        eb.addStretch()
        eb.addWidget(self._btn_save)
        eb.addWidget(self._btn_copy)
        eb.addWidget(self._btn_paste)
        rl.addLayout(eb)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([240, 620])
        self.setCentralWidget(split)

        # signals
        self._sb_hk_edit.hotkey_changed.connect(self._on_sb_hk)
        self._sb_hk_edit.capture_started.connect(lambda: self._status(self._t("sb_hk_wait")))
        self._sb_hk_edit.capture_cancelled.connect(lambda: self._status(self._t("sb_hk_cancel")))
        self._sb_hk_edit.capture_finished.connect(lambda v: self._status(self._t("sb_hk_set", h=v)))
        self._search.textChanged.connect(self._refresh_list)
        self._list.currentItemChanged.connect(self._on_sel)
        self._btn_new.clicked.connect(self._new)
        self._btn_dup.clicked.connect(self._dup)
        self._btn_del.clicked.connect(self._del)
        self._name.textChanged.connect(self._mark_dirty)
        self._hk.hotkey_changed.connect(self._mark_dirty)
        self._hk.capture_started.connect(lambda: self._status(self._t("hk_wait")))
        self._hk.capture_cancelled.connect(lambda: self._status(self._t("hk_cancel")))
        self._hk.capture_finished.connect(lambda v: self._status(self._t("hk_set", h=v)))
        self._text.textChanged.connect(self._mark_dirty)
        self._btn_save.clicked.connect(partial(self._commit, True, True))
        self._btn_copy.clicked.connect(self._copy)
        self._btn_paste.clicked.connect(self._do_paste)

    # ── i18n ───────────────────────────────────────────────────────────

    def _retranslate(self, init: bool = False) -> None:
        self._lang_btn.setText(self._lang.upper())
        for l, a in self._lang_acts.items():
            a.setChecked(l == self._lang)
        self._sb_hk_lbl.setText(f"  {self._t('sb_hotkey')}  ")
        self._sb_btn.setText(self._t("open_sb"))
        self._search.setPlaceholderText(self._t("search"))
        self._btn_new.setText(self._t("new"))
        self._btn_dup.setText(self._t("dup"))
        self._btn_del.setText(self._t("del"))
        self._form.labelForField(self._name).setText(self._t("lbl_name"))
        self._form.labelForField(self._hk).setText(self._t("lbl_hotkey"))
        self._txt_lbl.setText(self._t("lbl_text"))
        self._name.setPlaceholderText(self._t("ph_name"))
        self._text.setPlaceholderText(self._t("ph_text"))
        self._btn_save.setText(self._t("save"))
        self._btn_copy.setText(self._t("copy"))
        self._btn_paste.setText(self._t("paste"))
        self._sb_hk_edit.set_prompts(self._t("capture_idle"), self._t("capture_active"))
        self._hk.set_prompts(self._t("capture_idle"), self._t("capture_active"))
        self._tray.retranslate()
        self._ph_panel.retranslate()
        self._sidebar.retranslate()
        if not init:
            self._commit(False, False)
            self._refresh_list(self._cur_id)
            self._status(self._t("lang_set", l=LANG_NAMES[self._lang]))

    def _switch_lang(self, lang: str, checked: bool = True) -> None:
        if not checked or lang == self._lang:
            return
        self._lang = lang
        self._state.language = lang
        self._save()
        self._retranslate()

    # ── state ──────────────────────────────────────────────────────────

    def _load_ui(self) -> None:
        self._sb_hk_edit.setText(self._state.sidebar_hotkey)
        if not self._state.presets:
            self._state.presets.append(Preset(name=self._t("def_name"), text=self._t("def_text")))
        self._ph_panel.load(self._state.custom_placeholders)
        self._refresh_list(self._state.selected_id or self._state.presets[0].id)
        self._status(self._t("ready"))
        self._update_enabled()
        self._reg_hotkeys()

    def _restore_pos(self) -> None:
        x, y = self._state.window.x, self._state.window.y
        if x is None or y is None:
            return
        r = QRect(QPoint(x, y), QSize(self.width(), self.height()))
        for s in QGuiApplication.screens():
            if s.availableGeometry().intersects(r):
                self.move(x, y)
                return

    def _save(self) -> None:
        g = self.normalGeometry() if self.isMaximized() else self.geometry()
        self._state.window.width = max(g.width(), 640)
        self._state.window.height = max(g.height(), 400)
        self._state.window.x = g.x()
        self._state.window.y = g.y()
        self._state.selected_id = self._cur_id
        self._state.sidebar_hotkey = normalize_hotkey(self._sb_hk_edit.text().strip())
        self._state.language = self._lang
        self._store.save(self._state)

    # ── preset list ────────────────────────────────────────────────────

    def _refresh_list(self, want_id: str | None = None) -> None:
        q = self._search.text().strip().lower()
        sel = want_id or self._cur_id
        self._list.blockSignals(True)
        self._list.clear()
        hits = [p for p in self._state.presets
                if not q or q in p.name.lower() or q in p.text.lower() or q in p.hotkey.lower()]
        hits.sort(key=lambda p: p.name.lower())
        for p in hits:
            hk = f"  [{p.hotkey}]" if p.hotkey else ""
            it = QListWidgetItem(f"{p.name or self._t('untitled')}{hk}")
            it.setData(Qt.ItemDataRole.UserRole, p.id)
            it.setToolTip(p.preview or self._t("empty"))
            self._list.addItem(it)
            if p.id == sel:
                self._list.setCurrentItem(it)
        if self._list.count() and not self._list.currentItem():
            self._list.setCurrentRow(0)
        self._list.blockSignals(False)
        cur = self._list.currentItem()
        if cur:
            self._cur_id = cur.data(Qt.ItemDataRole.UserRole)
            self._load_editor()
        else:
            self._cur_id = None
            self._clear_editor()
        self._update_enabled()

    def _on_sel(self, cur: QListWidgetItem | None, prev: QListWidgetItem | None) -> None:
        pid = prev.data(Qt.ItemDataRole.UserRole) if prev else None
        cid = cur.data(Qt.ItemDataRole.UserRole) if cur else None
        if pid and pid != cid:
            self._commit(False, False, pid=pid)
        self._cur_id = cid
        self._load_editor()
        self._update_enabled()

    # ── editor ─────────────────────────────────────────────────────────

    def _get(self, pid: str | None = None) -> Preset | None:
        look = pid or self._cur_id
        if not look:
            return None
        return next((p for p in self._state.presets if p.id == look), None)

    def _load_editor(self) -> None:
        p = self._get()
        if not p:
            self._clear_editor()
            return
        self._suspend = True
        self._name.setText(p.name)
        self._hk.setText(p.hotkey)
        self._text.setPlainText(p.text)
        self._suspend = False
        self._dirty = False

    def _clear_editor(self) -> None:
        self._suspend = True
        self._name.clear()
        self._hk.clear()
        self._text.clear()
        self._suspend = False
        self._dirty = False

    def _update_enabled(self) -> None:
        on = self._cur_id is not None
        for w in (self._name, self._hk, self._text, self._btn_save,
                  self._btn_copy, self._btn_paste, self._btn_dup, self._btn_del):
            w.setEnabled(on)

    def _mark_dirty(self, *_) -> None:
        if self._suspend or not self._cur_id:
            return
        self._dirty = True
        self._status(self._t("edited"))

    def _commit(self, show: bool, rebuild: bool = False, pid: str | None = None) -> None:
        p = self._get(pid)
        if not p:
            return
        name = self._name.text().strip() or self._uname("Untitled", exc=p.id)
        hk_raw = self._hk.text().strip()
        norm = normalize_hotkey(hk_raw)
        p.name = name
        p.text = self._text.toPlainText()
        p.hotkey = norm
        p.updated_at = _utc_now()
        self._dirty = False
        self._save()
        if rebuild:
            self._refresh_list(p.id)
        self._reg_hotkeys()
        if show:
            msg = self._t("saved", p=p.name) if (not hk_raw or norm) else self._t("saved_bad_hk", p=p.name)
            self._status(msg)

    # ── actions ────────────────────────────────────────────────────────

    def _new(self) -> None:
        self._commit(False)
        p = Preset(name=self._uname(self._t("new_base")))
        self._state.presets.append(p)
        self._save()
        self._refresh_list(p.id)
        self._name.setFocus()
        self._name.selectAll()
        self._status(self._t("created", p=p.name))

    def _dup(self) -> None:
        src = self._get()
        if not src:
            return
        self._commit(False)
        d = Preset(name=self._uname(self._t("copy_fmt", n=src.name or "?")), text=src.text)
        self._state.presets.append(d)
        self._save()
        self._refresh_list(d.id)
        self._status(self._t("duped", p=src.name))

    def _del(self) -> None:
        p = self._get()
        if not p:
            return
        if QMessageBox.question(
            self, self._t("del_title"), self._t("del_q", p=p.name or "?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        self._state.presets = [x for x in self._state.presets if x.id != p.id]
        fb = self._state.presets[0].id if self._state.presets else None
        self._save()
        self._refresh_list(fb)
        self._reg_hotkeys()
        self._status(self._t("deleted", p=p.name))

    def _copy(self) -> None:
        p = self._get()
        if not p:
            return
        self._commit(False)
        QApplication.clipboard().setText(p.text)
        self._status(self._t("copied"))

    def _do_paste(self) -> None:
        p = self._get()
        if not p:
            return
        self._commit(False)
        self._paste_id(p.id, target=self._resolve_paste_target(0), minimize_if_needed=False)

    # ── paste ──────────────────────────────────────────────────────────

    def _paste_id(self, pid: str, target: int = 0, minimize_if_needed: bool = True) -> None:
        p = self._get(pid)
        if not p or not p.text:
            self._status(self._t("empty_paste"))
            return
        resolved = resolve_placeholders(p.text, self._state.custom_placeholders)
        cb = QApplication.clipboard()
        self._clip_snap = snap_clipboard(cb.mimeData())
        cb.setText(resolved)
        if target:
            QTimer.singleShot(50, lambda hwnd=target: restore_foreground_window(hwnd))
            QTimer.singleShot(250, send_ctrl_v)
            QTimer.singleShot(700, self._restore_clip)
        else:
            if not minimize_if_needed:
                self._restore_clip()
                self._status(self._t("paste_target_missing"))
                return
            self._sidebar.hide()
            self.hide_to_tray(msg=False)
            QTimer.singleShot(350, send_ctrl_v)
            QTimer.singleShot(800, self._restore_clip)
        self._status(self._t("pasted", p=p.name))

    def _restore_clip(self) -> None:
        restore_clipboard(self._clip_snap)
        self._clip_snap = None

    # ── foreground tracking ────────────────────────────────────────────

    def _own_hwnds(self) -> set[int]:
        hwnds = {int(self.winId())}
        sidebar_hwnd = int(self._sidebar.winId()) if hasattr(self, "_sidebar") else 0
        if sidebar_hwnd:
            hwnds.add(sidebar_hwnd)
        return {hwnd for hwnd in hwnds if hwnd}

    def _track_foreground_window(self) -> None:
        fg = get_foreground_window()
        if fg and fg not in self._own_hwnds():
            self._last_external_hwnd = fg

    def _resolve_paste_target(self, target: int) -> int:
        resolved = target or self._last_external_hwnd
        return 0 if resolved in self._own_hwnds() else resolved

    # ── sidebar ────────────────────────────────────────────────────────

    def _open_sb(self, target: int = 0) -> None:
        ps = [p for p in self._state.presets if p.text]
        if not ps:
            self._status(self._t("no_presets"))
            return
        self._sb_target = target
        self._sidebar.set_presets(ps)
        self._sidebar.open()

    def _open_sb_ui(self) -> None:
        self._open_sb()

    def _open_sb_hotkey(self) -> None:
        fg = get_foreground_window()
        self._open_sb(0 if fg == int(self.winId()) else fg)

    def _paste_from_sidebar(self, pid: str) -> None:
        t = self._sb_target
        self._sidebar.hide()
        self._paste_id(pid, target=t)

    # ── hotkeys ────────────────────────────────────────────────────────

    def _reg_hotkeys(self) -> None:
        hwnd = int(self.winId())
        if not hwnd:
            return
        warns = self._hk_reg.register_all(
            hwnd, self._state.sidebar_hotkey, self._state.presets, self._t,
        )
        if warns:
            self._status(warns[0])

    def _on_sb_hk(self, val: str) -> None:
        self._state.sidebar_hotkey = normalize_hotkey(val)
        self._save()
        self._reg_hotkeys()
        self._status(self._t("sb_hk_set", h=self._state.sidebar_hotkey)
                     if self._state.sidebar_hotkey else self._t("sb_hk_clear"))

    # ── placeholders ───────────────────────────────────────────────────

    def _on_ph_changed(self) -> None:
        reserved = self._ph_panel.reserved_key()
        if reserved:
            self._status(self._t("ph_reserved", k=reserved))
        self._state.custom_placeholders = self._ph_panel.collect()
        self._save()

    # ── helpers ────────────────────────────────────────────────────────

    def _uname(self, base: str, exc: str | None = None) -> str:
        c, n = base, 2
        while any(p.id != exc and p.name.casefold() == c.casefold() for p in self._state.presets):
            c = f"{base} {n}"; n += 1
        return c

    def _status(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 8000)

    # ── tray ───────────────────────────────────────────────────────────

    def _show_from_tray(self) -> None:
        self._tray.hide()
        if self._was_maximized:
            self.showMaximized()
        elif self._was_minimized:
            self.showMinimized()
        else:
            self.showNormal()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self, msg: bool = True) -> None:
        self._commit(False)
        self._save()
        self._was_maximized = self.isMaximized()
        self._was_minimized = self.isMinimized()
        self._tray.show()
        self.hide()
        if msg and not self._tray_tipped:
            self._tray.show_message(self._t("tray_title"), self._t("tray_msg"))
            self._tray_tipped = True

    def _quit(self) -> None:
        self._commit(False)
        self._save()
        self._quitting = True
        self._sidebar.hide()
        self._tray.hide()
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    # ── window events ──────────────────────────────────────────────────

    def showEvent(self, e) -> None:
        super().showEvent(e)
        if not self._backdrop_done:
            try:
                apply_windows_11_backdrop(int(self.winId()))
            except Exception:
                log.debug("DWM backdrop not available", exc_info=True)
            self._backdrop_done = True

    def changeEvent(self, e: QEvent) -> None:
        super().changeEvent(e)

    def closeEvent(self, e: QCloseEvent) -> None:
        self._commit(False)
        self._save()
        if not self._quitting:
            e.ignore()
            self.hide_to_tray()
            return
        self._quitting = True
        self._sidebar.hide()
        self._hk_reg.unregister_all(int(self.winId()))
        self._tray.hide()
        super().closeEvent(e)
        app = QApplication.instance()
        if app:
            app.quit()

    def nativeEvent(self, event_type, message):
        if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            addr = message.__int__() if hasattr(message, "__int__") else int(message)
            msg = MSG.from_address(addr)
            if msg.message == WM_HOTKEY:
                now = time.monotonic()
                if now - self._last_hk_time < _HK_DEBOUNCE:
                    return True, 0
                self._last_hk_time = now
                act = self._hk_reg.lookup(int(msg.wParam))
                if act:
                    kind, val = act
                    if kind == "sb":
                        self._open_sb_hotkey()
                    elif kind == "preset":
                        fg = get_foreground_window()
                        self._paste_id(val, target=(0 if fg == int(self.winId()) else fg))
                    return True, 0
        return super().nativeEvent(event_type, message)
