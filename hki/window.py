"""Main window — native Windows 11 look, no custom themes."""
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QMimeData, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QCursor, QGuiApplication, QIcon, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPushButton, QSizePolicy, QSplitter, QStatusBar,
    QSystemTrayIcon, QTextEdit, QToolBar, QVBoxLayout, QWidget,
)

from hki.storage import VERSION, Preset, Store, _utc_now
from hki.win32 import (
    MSG, WM_HOTKEY, apply_windows_11_backdrop, capture_hotkey_from_event,
    get_foreground_window, normalize_hotkey, parse_hotkey, register_hotkey,
    restore_foreground_window, send_ctrl_v, unregister_hotkeys,
)

# ── i18n ───────────────────────────────────────────────────────────────

LANGS = ("en", "de")
LANG_NAMES = {"en": "English", "de": "Deutsch"}
TR: dict[str, dict[str, str]] = {
    "en": {
        "capture_idle": "Click, then press a key combo",
        "capture_active": "Listening...",
        "untitled": "Untitled",
        "empty": "(empty)",
        "sb_title": "Quick paste",
        "sb_filter": "Filter...",
        "sb_hint": "Esc to close",
        "sb_hotkey": "Sidebar hotkey",
        "open_sb": "Sidebar",
        "close_tray": "Close to tray",
        "min_tray": "Minimize to tray",
        "search": "Search...",
        "new": "New", "dup": "Duplicate", "del": "Delete",
        "save": "Save", "copy": "Copy", "paste": "Paste",
        "lbl_name": "Name", "lbl_hotkey": "Hotkey", "lbl_text": "Text",
        "ph_name": "e.g. Ticket greeting",
        "ph_text": "Preset text...",
        "first": "Create your first preset.",
        "ready": "Ready",
        "tray_edit": "Edit presets", "tray_sb": "Open sidebar",
        "tray_hide": "Hide to tray", "tray_paste": "Paste selected",
        "tray_quit": "Quit",
        "edited": "Edited (auto-saves on switch)",
        "saved": "Saved '{p}'",
        "saved_bad_hk": "Saved '{p}' (hotkey invalid)",
        "def_name": "Example",
        "def_text": "Hello! This is a sample preset. Edit or delete it and add your own.",
        "new_base": "New preset",
        "copy_fmt": "Copy of {n}",
        "created": "Created '{p}'",
        "duped": "Duplicated '{p}'",
        "del_title": "Delete", "del_q": "Delete '{p}'?",
        "deleted": "Deleted '{p}'",
        "copied": "Copied to clipboard",
        "empty_paste": "Preset is empty",
        "pasted": "Pasted '{p}'",
        "warn_bad_hk": "Invalid hotkey on '{p}'",
        "warn_dup_hk": "Duplicate hotkey {h}",
        "warn_reg": "Could not register {h}",
        "warn_reg_sb": "Could not register sidebar hotkey {h}",
        "sb_hk_set": "Sidebar hotkey: {h}",
        "sb_hk_clear": "Sidebar hotkey cleared",
        "sb_hk_wait": "Press a key combo for sidebar...",
        "sb_hk_cancel": "Cancelled",
        "hk_wait": "Press a key combo...",
        "hk_cancel": "Cancelled",
        "hk_set": "Hotkey: {h}",
        "no_presets": "Add a preset first",
        "tray_title": "HKI",
        "tray_msg": "Running in tray.",
        "lang_set": "Language: {l}",
    },
    "de": {
        "capture_idle": "Klicken, dann Tastenkombination",
        "capture_active": "Warte...",
        "untitled": "Unbenannt",
        "empty": "(leer)",
        "sb_title": "Schnelleinfuegen",
        "sb_filter": "Filtern...",
        "sb_hint": "Esc zum Schliessen",
        "sb_hotkey": "Sidebar-Hotkey",
        "open_sb": "Sidebar",
        "close_tray": "Schliessen in Tray",
        "min_tray": "Minimieren in Tray",
        "search": "Suchen...",
        "new": "Neu", "dup": "Duplizieren", "del": "Loeschen",
        "save": "Speichern", "copy": "Kopieren", "paste": "Einfuegen",
        "lbl_name": "Name", "lbl_hotkey": "Hotkey", "lbl_text": "Text",
        "ph_name": "z.B. Ticket-Begruessung",
        "ph_text": "Preset-Text...",
        "first": "Erstelle dein erstes Preset.",
        "ready": "Bereit",
        "tray_edit": "Presets bearbeiten", "tray_sb": "Sidebar",
        "tray_hide": "In Tray", "tray_paste": "Einfuegen",
        "tray_quit": "Beenden",
        "edited": "Bearbeitet (speichert beim Wechsel)",
        "saved": "'{p}' gespeichert",
        "saved_bad_hk": "'{p}' gespeichert (Hotkey ungueltig)",
        "def_name": "Beispiel",
        "def_text": "Hallo! Dies ist ein Beispiel-Preset. Bearbeite oder loesche es und erstelle eigene.",
        "new_base": "Neues Preset",
        "copy_fmt": "Kopie von {n}",
        "created": "'{p}' erstellt",
        "duped": "'{p}' dupliziert",
        "del_title": "Loeschen", "del_q": "'{p}' loeschen?",
        "deleted": "'{p}' geloescht",
        "copied": "In Zwischenablage",
        "empty_paste": "Preset ist leer",
        "pasted": "'{p}' eingefuegt",
        "warn_bad_hk": "Ungueltiger Hotkey bei '{p}'",
        "warn_dup_hk": "Doppelter Hotkey {h}",
        "warn_reg": "{h} nicht registrierbar",
        "warn_reg_sb": "Sidebar-Hotkey {h} nicht registrierbar",
        "sb_hk_set": "Sidebar-Hotkey: {h}",
        "sb_hk_clear": "Sidebar-Hotkey entfernt",
        "sb_hk_wait": "Tastenkombination fuer Sidebar...",
        "sb_hk_cancel": "Abgebrochen",
        "hk_wait": "Tastenkombination druecken...",
        "hk_cancel": "Abgebrochen",
        "hk_set": "Hotkey: {h}",
        "no_presets": "Erst ein Preset anlegen",
        "tray_title": "HKI",
        "tray_msg": "Laeuft im Tray.",
        "lang_set": "Sprache: {l}",
    },
}


# ── Hotkey capture field ───────────────────────────────────────────────

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


# ── Quick-paste sidebar ────────────────────────────────────────────────

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
            return  # Prevent multiple openings per session
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


# ── Main window ────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, resource_path: Callable[..., Path]) -> None:
        super().__init__()
        self._res = resource_path
        self._store = Store()
        self._state = self._store.load()
        self._lang = self._state.language if self._state.language in LANGS else "en"
        self._cur_id: str | None = None
        self._hotkeys: dict[int, tuple[str, str]] = {}
        self._next_hk_id = 0x5000
        self._clip_snap: QMimeData | None = None
        self._quitting = False
        self._suspend = False
        self._dirty = False
        self._tray_tipped = False
        self._backdrop_done = False
        self._sb_target = 0
        self._was_maximized = False
        self._was_minimized = False

        icon = QIcon(str(self._res("assets", "hki.ico")))
        self.setWindowTitle(f"Hot Key Input  —  v{VERSION}")
        self.setWindowIcon(icon)
        self.setMinimumSize(640, 400)
        self.resize(self._state.window.width or 860, self._state.window.height or 540)

        self._build_toolbar()
        self._build_central()
        self._sidebar = Sidebar(self._t)
        self._sidebar.chosen.connect(self._paste_from_sidebar)
        self._build_tray(icon)
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

        # left
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

        # right
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
        self._btn_paste.clicked.connect(partial(self._do_paste, True))

    # ── tray ───────────────────────────────────────────────────────────

    def _build_tray(self, icon: QIcon) -> None:
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(icon)
        self._tray.setToolTip("HKI")
        m = QMenu(self)
        self._tray_edit = m.addAction("")
        self._tray_sb = m.addAction("")
        self._tray_hide = m.addAction("")
        m.addSeparator()
        self._tray_quit = m.addAction("")
        self._tray.setContextMenu(m)
        self._tray.activated.connect(self._on_tray)
        self._tray_edit.triggered.connect(self._show_from_tray)
        self._tray_sb.triggered.connect(self._open_sb_ui)
        self._tray_hide.triggered.connect(self.hide_to_tray)
        self._tray_quit.triggered.connect(self._quit)

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
        self._tray_edit.setText(self._t("tray_edit"))
        self._tray_sb.setText(self._t("tray_sb"))
        self._tray_hide.setText(self._t("tray_hide"))
        self._tray_quit.setText(self._t("tray_quit"))
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

    def _toggle(self, attr: str, val: bool) -> None:
        setattr(self._state, attr, val)
        self._save()

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

    def _do_paste(self, hide: bool) -> None:
        p = self._get()
        if not p:
            return
        self._commit(False)
        self._paste_id(p.id, hide)

    def _paste_id(self, pid: str, hide: bool, target: int = 0) -> None:
        p = self._get(pid)
        if not p or not p.text:
            self._status(self._t("empty_paste"))
            return
        cb = QApplication.clipboard()
        self._clip_snap = self._snap_clip(cb.mimeData())
        cb.setText(p.text)
        if target:
            # Hotkey-triggered: we know the exact target window
            QTimer.singleShot(50, lambda: restore_foreground_window(target))
            QTimer.singleShot(250, send_ctrl_v)
            QTimer.singleShot(700, self._restore_clip)
        else:
            # UI-triggered: hide everything so Windows brings previous app forward
            self._sidebar.hide()
            self.hide_to_tray(msg=False)
            QTimer.singleShot(350, send_ctrl_v)
            QTimer.singleShot(800, self._restore_clip)
        self._status(self._t("pasted", p=p.name))

    @staticmethod
    def _snap_clip(src) -> QMimeData | None:
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

    def _restore_clip(self) -> None:
        if self._clip_snap:
            QApplication.clipboard().setMimeData(self._clip_snap)
            self._clip_snap = None

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
        self._paste_id(pid, False, target=t)

    # ── hotkey reg ─────────────────────────────────────────────────────

    def _reg_hotkeys(self) -> None:
        hwnd = int(self.winId())
        if not hwnd:
            return
        unregister_hotkeys(hwnd, list(self._hotkeys.keys()))
        self._hotkeys.clear()
        self._next_hk_id = 0x5000
        seen: set[str] = set()
        warns: list[str] = []

        sb = parse_hotkey(self._state.sidebar_hotkey)
        if sb:
            hid = self._next_hk_id; self._next_hk_id += 1
            seen.add(sb.display)
            if register_hotkey(hwnd, hid, sb):
                self._hotkeys[hid] = ("sb", "")
            else:
                warns.append(self._t("warn_reg_sb", h=sb.display))

        for p in self._state.presets:
            if not p.hotkey:
                continue
            g = parse_hotkey(p.hotkey)
            if not g:
                warns.append(self._t("warn_bad_hk", p=p.name))
                continue
            if g.display in seen:
                warns.append(self._t("warn_dup_hk", h=g.display))
                continue
            seen.add(g.display)
            hid = self._next_hk_id; self._next_hk_id += 1
            if register_hotkey(hwnd, hid, g):
                self._hotkeys[hid] = ("preset", p.id)
            else:
                warns.append(self._t("warn_reg", h=g.display))
        if warns:
            self._status(warns[0])

    def _on_sb_hk(self, val: str) -> None:
        self._state.sidebar_hotkey = normalize_hotkey(val)
        self._save()
        self._reg_hotkeys()
        self._status(self._t("sb_hk_set", h=self._state.sidebar_hotkey) if self._state.sidebar_hotkey else self._t("sb_hk_clear"))

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
            self._tray.showMessage(self._t("tray_title"), self._t("tray_msg"),
                                   QSystemTrayIcon.MessageIcon.Information, 2000)
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

    def _on_tray(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_from_tray()

    # ── window events ──────────────────────────────────────────────────

    def showEvent(self, e) -> None:
        super().showEvent(e)
        if not self._backdrop_done:
            try:
                apply_windows_11_backdrop(int(self.winId()))
            except Exception:
                pass
            self._backdrop_done = True

    def changeEvent(self, e: QEvent) -> None:
        # Removed minimize_to_tray behavior - minimize should just minimize
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
        unregister_hotkeys(int(self.winId()), list(self._hotkeys.keys()))
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
                act = self._hotkeys.get(int(msg.wParam))
                if act:
                    kind, val = act
                    if kind == "sb":
                        self._open_sb_hotkey()
                    elif kind == "preset":
                        fg = get_foreground_window()
                        self._paste_id(val, False, target=(0 if fg == int(self.winId()) else fg))
                    return True, 0
        return super().nativeEvent(event_type, message)
