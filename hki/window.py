from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QCloseEvent,
    QCursor,
    QGuiApplication,
    QIcon,
    QKeyEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from hki.app_state import Preset, SettingsStore, utc_now_iso
from hki.win32 import (
    MSG,
    WM_HOTKEY,
    apply_windows_11_backdrop,
    capture_hotkey_from_event,
    get_foreground_window,
    normalize_hotkey,
    parse_hotkey,
    register_hotkey,
    restore_foreground_window,
    send_ctrl_v,
    unregister_hotkeys,
)


LANGUAGES = ("en", "de")
LANGUAGE_CODES = {
    "en": "EN",
    "de": "DE",
}
LANGUAGE_NAMES = {
    "en": "English",
    "de": "Deutsch",
}
TRANSLATIONS = {
    "en": {
        "hotkey_capture_idle": "Click here, then press something like Ctrl+3",
        "hotkey_capture_active": "Press the hotkey now",
        "untitled_preset": "Untitled preset",
        "no_preset_text": "No preset text yet.",
        "quick_sidebar_window_title": "HKI Sidebar",
        "quick_sidebar_title": "Paste preset",
        "quick_sidebar_subtitle": "Type to filter, then press Enter or click a preset.",
        "quick_sidebar_search_placeholder": "Search preset name, text, or hotkey",
        "quick_sidebar_hint": "Esc closes the sidebar.",
        "hero_subtitle": "Starts as a normal window. Use the sidebar hotkey from any text field, then paste a preset.",
        "sidebar_hotkey_label": "Sidebar hotkey",
        "switch_language_tooltip": "Switch language",
        "open_sidebar": "Open sidebar",
        "send_to_tray_tooltip": "Send to tray",
        "presets_title": "Presets",
        "presets_caption": "Search, duplicate, and organize the text snippets you actually use.",
        "presets_search_placeholder": "Search presets by name, text, or hotkey",
        "new_button": "New",
        "duplicate_button": "Duplicate",
        "delete_button": "Delete",
        "editor_title": "Editor",
        "editor_caption": "Keep it compact. Press the hotkey later and HKI pastes into the focused field.",
        "save_now": "Save now",
        "copy": "Copy",
        "hide_and_paste": "Hide + paste",
        "preset_name_label": "Preset name",
        "paste_hotkey_label": "Paste hotkey",
        "preset_text_label": "Preset text",
        "preset_name_placeholder": "Example: Ticket greeting",
        "preset_text_placeholder": "Write the preset text here...",
        "paste_hotkey_hint": "Click the field, then press a key or combo. Esc cancels, Backspace clears.",
        "create_first_preset": "Create your first preset to get started.",
        "ready_status": "Ready. Presets are stored in {path}",
        "tray_action_edit": "Edit presets",
        "tray_action_open_sidebar": "Open sidebar",
        "tray_action_hide": "Hide to tray",
        "tray_action_paste_selected": "Paste selected",
        "tray_action_quit": "Close HKI",
        "edited_status": "Edited. Click save or switch presets; HKI will keep the latest changes.",
        "saved_status": "Saved '{preset}'.",
        "saved_hotkey_ignored_status": "Saved '{preset}'. The hotkey was ignored because HKI could not understand it.",
        "default_preset_name": "Welcome snippet",
        "default_preset_text": "Thanks for reaching out. We are checking this now.",
        "new_preset_base": "New preset",
        "copy_of_format": "Copy of {name}",
        "generic_preset_name": "preset",
        "created_status": "Created '{preset}'.",
        "duplicated_status": "Duplicated '{preset}'.",
        "delete_preset_title": "Delete preset",
        "delete_preset_question": "Delete '{preset}'?",
        "this_preset": "this preset",
        "deleted_status": "Deleted '{preset}'.",
        "copied_status": "Copied '{preset}' to the clipboard.",
        "empty_preset_status": "This preset is empty, so there was nothing to paste.",
        "pasted_status": "Pasted '{preset}'.",
        "warning_invalid_hotkey": "Skipped invalid hotkey on '{preset}'.",
        "warning_duplicate_hotkey": "Skipped duplicate hotkey {hotkey}.",
        "warning_register_hotkey": "Windows would not register {hotkey}.",
        "warning_register_sidebar_hotkey": "Windows would not register sidebar hotkey {hotkey}.",
        "sidebar_hotkey_set": "Sidebar hotkey set to {hotkey}.",
        "sidebar_hotkey_cleared": "Sidebar hotkey cleared.",
        "sidebar_hotkey_wait": "Waiting for the sidebar hotkey. Press a key or combo now.",
        "sidebar_hotkey_cancelled": "Sidebar hotkey capture cancelled.",
        "paste_hotkey_wait": "Waiting for a paste hotkey. Press a key or combo now.",
        "paste_hotkey_cancelled": "Hotkey capture cancelled.",
        "paste_hotkey_set": "Paste hotkey set to {hotkey}. Click save if you want to store it right now.",
        "add_preset_before_sidebar": "Add at least one preset with text before opening the sidebar.",
        "tray_running_title": "HKI is still running",
        "tray_running_message": "Use the tray icon to reopen HKI or paste the selected preset.",
        "language_switched": "Language switched to {language}.",
    },
    "de": {
        "hotkey_capture_idle": "Hier klicken und dann z. B. Ctrl+3 drucken",
        "hotkey_capture_active": "Jetzt die Tastenkombi drucken",
        "untitled_preset": "Unbenanntes Preset",
        "no_preset_text": "Noch kein Preset-Text vorhanden.",
        "quick_sidebar_window_title": "HKI Sidebar",
        "quick_sidebar_title": "Preset einfugen",
        "quick_sidebar_subtitle": "Zum Filtern tippen, dann Enter drucken oder ein Preset anklicken.",
        "quick_sidebar_search_placeholder": "Presetname, Text oder Hotkey suchen",
        "quick_sidebar_hint": "Esc schließt die Sidebar.",
        "hero_subtitle": "Startet als normales Fenster. Nutze den Sidebar-Hotkey in einem Textfeld und fige dann ein Preset ein.",
        "sidebar_hotkey_label": "Sidebar-Hotkey",
        "switch_language_tooltip": "Sprache wechseln",
        "close_to_tray": "X schickt das Fenster in den Tray",
        "minimize_to_tray": "Minimieren schickt das Fenster in den Tray",
        "open_sidebar": "Sidebar offnen",
        "hide_to_tray": "In Tray ausblenden",
        "presets_title": "Presets",
        "presets_caption": "Texte suchen, duplizieren und sortieren, die wirklich benutzt werden.",
        "presets_search_placeholder": "Presets nach Name, Text oder Hotkey suchen",
        "new_button": "Neu",
        "duplicate_button": "Duplizieren",
        "delete_button": "Loschen",
        "editor_title": "Editor",
        "editor_caption": "Kompakt halten. Spater den Hotkey drucken und HKI fugt in das fokussierte Feld ein.",
        "save_now": "Jetzt speichern",
        "copy": "Kopieren",
        "hide_and_paste": "Verstecken + einfugen",
        "preset_name_label": "Preset-Name",
        "paste_hotkey_label": "Einfuge-Hotkey",
        "preset_text_label": "Preset-Text",
        "preset_name_placeholder": "Beispiel: Ticket-Begrußung",
        "preset_text_placeholder": "Hier den Preset-Text eingeben...",
        "paste_hotkey_hint": "Ins Feld klicken und dann z. B. Ctrl+3 drucken. Esc bricht ab, Backspace leert den Hotkey.",
        "create_first_preset": "Lege dein erstes Preset an.",
        "ready_status": "Bereit. Presets werden hier gespeichert: {path}",
        "tray_action_edit": "Presets bearbeiten",
        "tray_action_open_sidebar": "Sidebar offnen",
        "tray_action_hide": "In Tray ausblenden",
        "tray_action_paste_selected": "Ausgewahltes Preset einfugen",
        "tray_action_quit": "HKI beenden",
        "edited_status": "Geandert. Speichern klicken oder Preset wechseln; HKI behalt die letzten Anderungen.",
        "saved_status": "'{preset}' wurde gespeichert.",
        "saved_hotkey_ignored_status": "'{preset}' wurde gespeichert. Der Hotkey wurde ignoriert, weil HKI ihn nicht verstanden hat.",
        "default_preset_name": "Begrußung",
        "default_preset_text": "Danke fur deine Nachricht. Wir prufen das gerade.",
        "new_preset_base": "Neues Preset",
        "copy_of_format": "Kopie von {name}",
        "generic_preset_name": "Preset",
        "created_status": "'{preset}' wurde erstellt.",
        "duplicated_status": "'{preset}' wurde dupliziert.",
        "delete_preset_title": "Preset loschen",
        "delete_preset_question": "'{preset}' loschen?",
        "this_preset": "dieses Preset",
        "deleted_status": "'{preset}' wurde geloscht.",
        "copied_status": "'{preset}' wurde in die Zwischenablage kopiert.",
        "empty_preset_status": "Dieses Preset ist leer, daher konnte nichts eingefugt werden.",
        "pasted_status": "'{preset}' wurde eingefugt.",
        "warning_invalid_hotkey": "Ungultiger Hotkey bei '{preset}' wurde ubersprungen.",
        "warning_duplicate_hotkey": "Doppelter Hotkey {hotkey} wurde ubersprungen.",
        "warning_register_hotkey": "{hotkey} konnte von Windows nicht registriert werden.",
        "warning_register_sidebar_hotkey": "Der Sidebar-Hotkey {hotkey} konnte von Windows nicht registriert werden.",
        "sidebar_hotkey_set": "Sidebar-Hotkey wurde auf {hotkey} gesetzt.",
        "sidebar_hotkey_cleared": "Sidebar-Hotkey wurde entfernt.",
        "sidebar_hotkey_wait": "Warte auf den Sidebar-Hotkey. Drucke z. B. Ctrl+Shift+Space.",
        "sidebar_hotkey_cancelled": "Sidebar-Hotkey-Erfassung abgebrochen.",
        "paste_hotkey_wait": "Warte auf einen Einfuge-Hotkey. Drucke z. B. Ctrl+3.",
        "paste_hotkey_cancelled": "Hotkey-Erfassung abgebrochen.",
        "paste_hotkey_set": "Einfuge-Hotkey auf {hotkey} gesetzt. Klicke auf Speichern, wenn du ihn sofort sichern willst.",
        "add_preset_before_sidebar": "Lege zuerst mindestens ein Preset mit Text an, bevor du die Sidebar offnest.",
        "tray_running_title": "HKI lauft weiter",
        "tray_running_message": "Nutze das Tray-Symbol, um HKI wieder zu offnen oder das ausgewahlte Preset einzufugen.",
        "language_switched": "Sprache auf {language} umgestellt.",
    },
}

TRANSLATIONS["de"] = {
    "hotkey_capture_idle": "Hier klicken und dann eine Taste oder Kombination druecken",
    "hotkey_capture_active": "Jetzt die Tastenkombi druecken",
    "untitled_preset": "Unbenanntes Preset",
    "no_preset_text": "Noch kein Preset-Text vorhanden.",
    "quick_sidebar_window_title": "HKI Sidebar",
    "quick_sidebar_title": "Preset einfuegen",
    "quick_sidebar_subtitle": "Zum Filtern tippen, dann Enter druecken oder ein Preset anklicken.",
    "quick_sidebar_search_placeholder": "Presetname, Text oder Hotkey suchen",
    "quick_sidebar_hint": "Esc schliesst die Sidebar.",
    "hero_subtitle": "Startet als normales Fenster. Nutze den Sidebar-Hotkey in einem Textfeld und fuege dann ein Preset ein.",
    "sidebar_hotkey_label": "Sidebar-Hotkey",
    "switch_language_tooltip": "Sprache wechseln",
    "open_sidebar": "Sidebar offnen",
    "send_to_tray_tooltip": "In den Tray senden",
    "presets_title": "Presets",
    "presets_caption": "Texte suchen, duplizieren und sortieren, die wirklich benutzt werden.",
    "presets_search_placeholder": "Presets nach Name, Text oder Hotkey suchen",
    "new_button": "Neu",
    "duplicate_button": "Duplizieren",
    "delete_button": "Loschen",
    "editor_title": "Editor",
    "editor_caption": "Kompakt halten. Spaeter den Hotkey druecken und HKI fuegt in das fokussierte Feld ein.",
    "save_now": "Jetzt speichern",
    "copy": "Kopieren",
    "hide_and_paste": "Verstecken + einfuegen",
    "preset_name_label": "Preset-Name",
    "paste_hotkey_label": "Einfuege-Hotkey",
    "preset_text_label": "Preset-Text",
    "preset_name_placeholder": "Beispiel: Ticket-Begruessung",
    "preset_text_placeholder": "Hier den Preset-Text eingeben...",
    "paste_hotkey_hint": "Ins Feld klicken und dann eine Taste oder Kombination druecken. Esc bricht ab, Backspace leert den Hotkey.",
    "create_first_preset": "Lege dein erstes Preset an.",
    "ready_status": "Bereit. Presets werden hier gespeichert: {path}",
        "tray_action_edit": "Presets bearbeiten",
        "tray_action_open_sidebar": "Sidebar offnen",
        "tray_action_hide": "In Tray ausblenden",
        "tray_action_paste_selected": "Ausgewaehltes Preset einfuegen",
        "tray_action_quit": "HKI schliessen",
    "edited_status": "Geaendert. Speichern klicken oder Preset wechseln; HKI behaelt die letzten Aenderungen.",
    "saved_status": "'{preset}' wurde gespeichert.",
    "saved_hotkey_ignored_status": "'{preset}' wurde gespeichert. Der Hotkey wurde ignoriert, weil HKI ihn nicht verstanden hat.",
    "default_preset_name": "Begruessung",
    "default_preset_text": "Danke fuer deine Nachricht. Wir pruefen das gerade.",
    "new_preset_base": "Neues Preset",
    "copy_of_format": "Kopie von {name}",
    "generic_preset_name": "Preset",
    "created_status": "'{preset}' wurde erstellt.",
    "duplicated_status": "'{preset}' wurde dupliziert.",
    "delete_preset_title": "Preset loschen",
    "delete_preset_question": "'{preset}' loschen?",
    "this_preset": "dieses Preset",
    "deleted_status": "'{preset}' wurde geloscht.",
    "copied_status": "'{preset}' wurde in die Zwischenablage kopiert.",
    "empty_preset_status": "Dieses Preset ist leer, daher konnte nichts eingefuegt werden.",
    "pasted_status": "'{preset}' wurde eingefuegt.",
    "warning_invalid_hotkey": "Ungueltiger Hotkey bei '{preset}' wurde uebersprungen.",
    "warning_duplicate_hotkey": "Doppelter Hotkey {hotkey} wurde uebersprungen.",
    "warning_register_hotkey": "{hotkey} konnte von Windows nicht registriert werden.",
    "warning_register_sidebar_hotkey": "Der Sidebar-Hotkey {hotkey} konnte von Windows nicht registriert werden.",
    "sidebar_hotkey_set": "Sidebar-Hotkey wurde auf {hotkey} gesetzt.",
    "sidebar_hotkey_cleared": "Sidebar-Hotkey wurde entfernt.",
    "sidebar_hotkey_wait": "Warte auf den Sidebar-Hotkey. Druecke jetzt eine Taste oder Kombination.",
    "sidebar_hotkey_cancelled": "Sidebar-Hotkey-Erfassung abgebrochen.",
    "paste_hotkey_wait": "Warte auf einen Einfuege-Hotkey. Druecke jetzt eine Taste oder Kombination.",
    "paste_hotkey_cancelled": "Hotkey-Erfassung abgebrochen.",
    "paste_hotkey_set": "Einfuege-Hotkey auf {hotkey} gesetzt. Klicke auf Speichern, wenn du ihn sofort sichern willst.",
    "add_preset_before_sidebar": "Lege zuerst mindestens ein Preset mit Text an, bevor du die Sidebar offnest.",
    "tray_running_title": "HKI laeuft weiter",
    "tray_running_message": "Nutze das Tray-Symbol, um HKI wieder zu offnen oder das ausgewaehlte Preset einzufuegen.",
    "language_switched": "Sprache auf {language} umgestellt.",
}


class HotkeyLineEdit(QLineEdit):
    hotkey_changed = Signal(str)
    capture_started = Signal()
    capture_cancelled = Signal()
    capture_finished = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_capturing = False
        self._previous_text = ""
        self._idle_prompt = TRANSLATIONS["en"]["hotkey_capture_idle"]
        self._active_prompt = TRANSLATIONS["en"]["hotkey_capture_active"]
        self.setReadOnly(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_capture_state(False)

    def set_prompt_texts(self, idle_text: str, active_text: str) -> None:
        self._idle_prompt = idle_text
        self._active_prompt = active_text
        self._set_capture_state(self._is_capturing)

    def _set_capture_state(self, active: bool) -> None:
        self._is_capturing = active
        self.setProperty("captureActive", active)
        self.setPlaceholderText(self._active_prompt if active else self._idle_prompt)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _begin_capture(self) -> None:
        if self._is_capturing:
            return

        self._previous_text = self.text()
        self.clear()
        self._set_capture_state(True)
        self.capture_started.emit()

    def _cancel_capture(self) -> None:
        if not self._is_capturing:
            return

        self.setText(self._previous_text)
        self._set_capture_state(False)
        self.capture_cancelled.emit()

    def _finish_capture(self, value: str) -> None:
        self.setText(value)
        self._set_capture_state(False)
        self.capture_finished.emit(value)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self._begin_capture()

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self._begin_capture()

    def focusOutEvent(self, event) -> None:
        self._cancel_capture()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (int(Qt.Key.Key_Tab), int(Qt.Key.Key_Backtab)):
            self._cancel_capture()
            super().keyPressEvent(event)
            return

        if event.key() == int(Qt.Key.Key_Escape):
            self._cancel_capture()
            event.accept()
            return

        if event.key() in (int(Qt.Key.Key_Backspace), int(Qt.Key.Key_Delete)):
            self.clear()
            self._previous_text = ""
            self._set_capture_state(False)
            self.hotkey_changed.emit("")
            return

        gesture = capture_hotkey_from_event(event)
        if gesture is None:
            event.accept()
            return

        self.hotkey_changed.emit(gesture.display)
        self._finish_capture(gesture.display)
        event.accept()


class PresetListCard(QFrame):
    def __init__(self, preset: Preset, translate: Callable[..., str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._translate = translate
        self.setObjectName("presetCard")

        self._name_label = QLabel()
        self._name_label.setObjectName("cardTitle")
        self._hotkey_label = QLabel()
        self._hotkey_label.setObjectName("hotkeyBadge")
        self._preview_label = QLabel()
        self._preview_label.setObjectName("cardPreview")
        self._preview_label.setWordWrap(True)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        top_row.addWidget(self._name_label, 1)
        top_row.addWidget(self._hotkey_label, 0, Qt.AlignmentFlag.AlignRight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        layout.addLayout(top_row)
        layout.addWidget(self._preview_label)

        self.update_preset(preset)
        self.set_selected(False)

    def update_preset(self, preset: Preset) -> None:
        self._name_label.setText(preset.name or self._translate("untitled_preset"))
        self._preview_label.setText(preset.preview or self._translate("no_preset_text"))
        self._hotkey_label.setVisible(bool(preset.hotkey))
        self._hotkey_label.setText(preset.hotkey)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class QuickPasteSidebar(QWidget):
    preset_chosen = Signal(str)

    def __init__(self, translate: Callable[..., str], parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._translate = translate
        self._presets: list[Preset] = []

        self.setObjectName("quickPasteSidebar")
        self.resize(380, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setObjectName("panelTitle")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("panelCaption")
        self.subtitle_label.setWordWrap(True)

        self.search_edit = QLineEdit()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_widget.setSpacing(8)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("fieldHint")

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.hint_label)

        self.search_edit.textChanged.connect(self._refresh_list)
        self.search_edit.returnPressed.connect(self._emit_current_selection)
        self.list_widget.itemActivated.connect(lambda _item: self._emit_current_selection())
        self.list_widget.currentItemChanged.connect(lambda *_args: self._sync_selection_states())
        self.retranslate()

    def retranslate(self) -> None:
        self.setWindowTitle(self._translate("quick_sidebar_window_title"))
        self.title_label.setText(self._translate("quick_sidebar_title"))
        self.subtitle_label.setText(self._translate("quick_sidebar_subtitle"))
        self.search_edit.setPlaceholderText(self._translate("quick_sidebar_search_placeholder"))
        self.hint_label.setText(self._translate("quick_sidebar_hint"))

    def set_presets(self, presets: list[Preset]) -> None:
        self._presets = list(presets)
        self.search_edit.clear()
        self._refresh_list()

    def open_sidebar(self) -> None:
        self._refresh_list()
        self._position_on_active_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _position_on_active_screen(self) -> None:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        margin = 24
        self.move(
            geometry.x() + geometry.width() - self.width() - margin,
            geometry.y() + margin,
        )

    def _refresh_list(self) -> None:
        query = self.search_edit.text().strip().lower()

        matching_presets = [
            preset
            for preset in self._presets
            if not query
            or query in preset.name.lower()
            or query in preset.text.lower()
            or query in preset.hotkey.lower()
        ]
        matching_presets.sort(key=lambda preset: preset.name.lower())

        self.list_widget.clear()
        for preset in matching_presets:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, preset.id)
            item.setSizeHint(QSize(0, 82))
            card = PresetListCard(preset, self._translate)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, card)

        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        self._sync_selection_states()

    def _sync_selection_states(self) -> None:
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            card = self.list_widget.itemWidget(item)
            if isinstance(card, PresetListCard):
                card.set_selected(item == self.list_widget.currentItem())

    def _emit_current_selection(self) -> None:
        current_item = self.list_widget.currentItem()
        if current_item is None:
            return
        preset_id = current_item.data(Qt.ItemDataRole.UserRole)
        if preset_id:
            self.preset_chosen.emit(preset_id)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == int(Qt.Key.Key_Escape):
            self.hide()
            event.accept()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, resource_path: Callable[..., Path]) -> None:
        super().__init__()
        self._resource_path = resource_path
        self._store = SettingsStore()
        self._state = self._store.load()
        self._language = self._normalize_language(self._state.language)
        self._current_preset_id: str | None = None
        self._registered_hotkeys: dict[int, tuple[str, str]] = {}
        self._next_hotkey_id = 0x5000
        self._clipboard_snapshot = None
        self._quit_requested = False
        self._suspend_editor_updates = False
        self._dirty = False
        self._tray_tip_shown = False
        self._window_style_applied = False
        self._sidebar_target_hwnd = 0

        self.setWindowTitle("HOTKEYINPUT")
        self.setMinimumSize(820, 520)
        self.resize(self._state.window.width or 960, self._state.window.height or 620)
        self.setWindowIcon(QIcon(str(self._resource_path("assets", "hki.ico"))))

        self._build_ui()
        self._build_sidebar()
        self._apply_styles()
        self._build_tray()
        self._apply_language(initial=True)
        self._restore_window_position()
        self._load_state_into_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(14)

        brand_icon = QLabel()
        brand_icon.setPixmap(self._load_brand_pixmap())
        brand_icon.setFixedSize(42, 42)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        self.title_label = QLabel("HOTKEYINPUT")
        self.title_label.setObjectName("heroTitle")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("heroSubtitle")
        title_layout.addWidget(self.subtitle_label)
        title_layout.addStretch(1)

        launcher_layout = QVBoxLayout()
        launcher_layout.setContentsMargins(0, 0, 0, 0)
        launcher_layout.setSpacing(4)
        self.launcher_label = QLabel()
        self.launcher_label.setObjectName("fieldLabel")
        self.sidebar_hotkey_edit = HotkeyLineEdit()
        self.sidebar_hotkey_edit.setMinimumWidth(180)
        launcher_layout.addWidget(self.launcher_label)
        launcher_layout.addWidget(self.sidebar_hotkey_edit)

        self.language_button = QToolButton()
        self.language_button.setObjectName("secondaryToolButton")
        self.language_button.setIcon(self._create_globe_icon())
        self.language_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.language_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.language_menu = QMenu(self)
        self.language_actions: dict[str, QAction] = {}
        for language in LANGUAGES:
            action = QAction(LANGUAGE_NAMES[language], self)
            action.setCheckable(True)
            action.triggered.connect(partial(self._set_language, language))
            self.language_menu.addAction(action)
            self.language_actions[language] = action
        self.language_button.setMenu(self.language_menu)
        self.language_button.setMinimumWidth(84)

        self.open_sidebar_button = QPushButton()
        self.open_sidebar_button.setObjectName("secondaryButton")
        self.send_to_tray_button = QToolButton()
        self.send_to_tray_button.setObjectName("secondaryToolButton")
        self.send_to_tray_button.setIcon(self._create_send_to_tray_icon())
        self.send_to_tray_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.send_to_tray_button.setAutoRaise(False)
        self.send_to_tray_button.setFixedSize(42, 42)

        settings_card = QFrame()
        settings_card.setObjectName("headerControlsCard")
        settings_card.setMaximumWidth(420)

        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(14, 14, 14, 14)
        settings_layout.setSpacing(10)

        settings_top_row = QHBoxLayout()
        settings_top_row.setContentsMargins(0, 0, 0, 0)
        settings_top_row.setSpacing(10)
        settings_top_row.addWidget(self.language_button, 0, Qt.AlignmentFlag.AlignTop)
        settings_top_row.addLayout(launcher_layout, 1)

        settings_layout.addLayout(settings_top_row)

        settings_button_row = QHBoxLayout()
        settings_button_row.setContentsMargins(0, 0, 0, 0)
        settings_button_row.setSpacing(10)
        settings_button_row.addWidget(self.open_sidebar_button)
        settings_button_row.addWidget(self.send_to_tray_button, 0, Qt.AlignmentFlag.AlignRight)
        settings_layout.addLayout(settings_button_row)

        header_layout.addWidget(brand_icon, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(title_layout, 1)
        header_layout.addWidget(settings_card, 0, Qt.AlignmentFlag.AlignTop)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)

        left_panel = QFrame()
        left_panel.setObjectName("panelCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        self.sidebar_title_label = QLabel()
        self.sidebar_title_label.setObjectName("panelTitle")
        self.sidebar_caption_label = QLabel()
        self.sidebar_caption_label.setObjectName("panelCaption")
        self.sidebar_caption_label.setWordWrap(True)

        self.search_edit = QLineEdit()

        self.preset_list = QListWidget()
        self.preset_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.preset_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.preset_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preset_list.setSpacing(8)

        left_button_row = QHBoxLayout()
        left_button_row.setSpacing(10)
        self.new_button = QPushButton()
        self.new_button.setObjectName("primaryButton")
        self.duplicate_button = QPushButton()
        self.duplicate_button.setObjectName("secondaryButton")
        self.delete_button = QPushButton()
        self.delete_button.setObjectName("dangerButton")
        left_button_row.addWidget(self.new_button)
        left_button_row.addWidget(self.duplicate_button)
        left_button_row.addWidget(self.delete_button)

        left_layout.addWidget(self.sidebar_title_label)
        left_layout.addWidget(self.sidebar_caption_label)
        left_layout.addWidget(self.search_edit)
        left_layout.addWidget(self.preset_list, 1)
        left_layout.addLayout(left_button_row)

        right_panel = QFrame()
        right_panel.setObjectName("panelCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(16)

        editor_header = QVBoxLayout()
        editor_header.setContentsMargins(0, 0, 0, 0)
        editor_header.setSpacing(12)
        editor_title_layout = QVBoxLayout()
        editor_title_layout.setContentsMargins(0, 0, 0, 0)
        editor_title_layout.setSpacing(2)
        self.editor_title_label = QLabel()
        self.editor_title_label.setObjectName("panelTitle")
        self.editor_caption_label = QLabel()
        self.editor_caption_label.setObjectName("panelCaption")
        self.editor_caption_label.setWordWrap(True)
        editor_title_layout.addWidget(self.editor_title_label)
        editor_title_layout.addWidget(self.editor_caption_label)

        header_actions = QHBoxLayout()
        header_actions.setSpacing(10)
        self.save_button = QPushButton()
        self.save_button.setObjectName("secondaryButton")
        self.copy_button = QPushButton()
        self.copy_button.setObjectName("secondaryButton")
        self.paste_button = QPushButton()
        self.paste_button.setObjectName("primaryButton")
        header_actions.addStretch(1)
        header_actions.addWidget(self.save_button)
        header_actions.addWidget(self.copy_button)
        header_actions.addWidget(self.paste_button)

        editor_header.addLayout(editor_title_layout)
        editor_header.addLayout(header_actions)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(10)

        self.name_label = QLabel()
        self.name_label.setObjectName("fieldLabel")
        self.hotkey_label = QLabel()
        self.hotkey_label.setObjectName("fieldLabel")
        self.text_label = QLabel()
        self.text_label.setObjectName("fieldLabel")

        self.name_edit = QLineEdit()
        self.hotkey_edit = HotkeyLineEdit()
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(False)

        self.hotkey_hint_label = QLabel()
        self.hotkey_hint_label.setObjectName("fieldHint")
        self.hotkey_hint_label.setWordWrap(True)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")

        form_grid.addWidget(self.name_label, 0, 0)
        form_grid.addWidget(self.hotkey_label, 0, 1)
        form_grid.addWidget(self.name_edit, 1, 0)
        form_grid.addWidget(self.hotkey_edit, 1, 1)
        form_grid.addWidget(self.hotkey_hint_label, 2, 1)
        form_grid.addWidget(self.text_label, 3, 0, 1, 2)
        form_grid.addWidget(self.text_edit, 4, 0, 1, 2)
        form_grid.setColumnStretch(0, 3)
        form_grid.setColumnStretch(1, 2)
        form_grid.setRowStretch(4, 1)

        right_layout.addLayout(editor_header)
        right_layout.addLayout(form_grid, 1)
        right_layout.addWidget(self.status_label)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([330, 610])

        root_layout.addWidget(header)
        root_layout.addWidget(splitter, 1)
        self.setCentralWidget(root)
        self._connect_events()

    def _build_sidebar(self) -> None:
        self.sidebar_window = QuickPasteSidebar(self._t)
        self.sidebar_window.preset_chosen.connect(self._paste_preset_from_sidebar)

    def _normalize_language(self, language: str) -> str:
        return language if language in LANGUAGES else "en"

    def _t(self, key: str, **values) -> str:
        language_table = TRANSLATIONS.get(self._language, TRANSLATIONS["en"])
        text = language_table.get(key, TRANSLATIONS["en"].get(key, key))
        return text.format(**values)

    def _create_globe_icon(self) -> QIcon:
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#2550a9"))
        pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, 14, 14)
        painter.drawLine(9, 2, 9, 16)
        painter.drawEllipse(5, 2, 8, 14)
        painter.drawLine(4, 6, 14, 6)
        painter.drawLine(4, 12, 14, 12)
        painter.end()

        return QIcon(pixmap)

    def _create_send_to_tray_icon(self) -> QIcon:
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#2550a9"))
        pen.setWidthF(1.6)
        painter.setPen(pen)
        painter.drawLine(4, 13, 14, 13)
        painter.drawLine(9, 4, 9, 11)
        painter.drawLine(6, 8, 9, 11)
        painter.drawLine(12, 8, 9, 11)
        painter.end()

        return QIcon(pixmap)

    def _apply_language(self, initial: bool = False) -> None:
        self.subtitle_label.setText(self._t("hero_subtitle"))
        self.launcher_label.setText(self._t("sidebar_hotkey_label"))
        self.language_button.setText(LANGUAGE_CODES[self._language])
        self.language_button.setToolTip(self._t("switch_language_tooltip"))
        for language, action in self.language_actions.items():
            action.setChecked(language == self._language)

        self.open_sidebar_button.setText(self._t("open_sidebar"))
        self.send_to_tray_button.setToolTip(self._t("send_to_tray_tooltip"))

        self.sidebar_title_label.setText(self._t("presets_title"))
        self.sidebar_caption_label.setText(self._t("presets_caption"))
        self.search_edit.setPlaceholderText(self._t("presets_search_placeholder"))
        self.new_button.setText(self._t("new_button"))
        self.duplicate_button.setText(self._t("duplicate_button"))
        self.delete_button.setText(self._t("delete_button"))

        self.editor_title_label.setText(self._t("editor_title"))
        self.editor_caption_label.setText(self._t("editor_caption"))
        self.save_button.setText(self._t("save_now"))
        self.copy_button.setText(self._t("copy"))
        self.paste_button.setText(self._t("hide_and_paste"))
        self.name_label.setText(self._t("preset_name_label"))
        self.hotkey_label.setText(self._t("paste_hotkey_label"))
        self.text_label.setText(self._t("preset_text_label"))
        self.name_edit.setPlaceholderText(self._t("preset_name_placeholder"))
        self.text_edit.setPlaceholderText(self._t("preset_text_placeholder"))
        self.hotkey_hint_label.setText(self._t("paste_hotkey_hint"))
        self.hotkey_edit.set_prompt_texts(
            self._t("hotkey_capture_idle"),
            self._t("hotkey_capture_active"),
        )
        self.sidebar_hotkey_edit.set_prompt_texts(
            self._t("hotkey_capture_idle"),
            self._t("hotkey_capture_active"),
        )

        self.show_action.setText(self._t("tray_action_edit"))
        self.open_sidebar_action.setText(self._t("tray_action_open_sidebar"))
        self.hide_action.setText(self._t("tray_action_hide"))
        self.paste_selected_action.setText(self._t("tray_action_paste_selected"))
        self.quit_action.setText(self._t("tray_action_quit"))

        self.sidebar_window.retranslate()

        if initial:
            self.status_label.setText(self._t("create_first_preset"))
            return

        self._commit_editor_to_current(False, False)
        self._refresh_preset_list(self._current_preset_id)
        if self.sidebar_window.isVisible():
            self.sidebar_window.set_presets([preset for preset in self._state.presets if preset.text])
        self._set_status(self._t("language_switched", language=LANGUAGE_NAMES[self._language]))

    def _set_language(self, language: str, checked: bool = True) -> None:
        if not checked:
            return

        normalized = self._normalize_language(language)
        if normalized == self._language:
            return

        self._language = normalized
        self._state.language = normalized
        self._persist_state()
        self._apply_language()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #eef3f9;
            }
            QWidget#quickPasteSidebar {
                background: rgba(255, 255, 255, 0.97);
                border: 1px solid #d7dfeb;
                border-radius: 22px;
            }
            QFrame#headerControlsCard {
                background: rgba(248, 251, 255, 0.96);
                border: 1px solid #d7dfeb;
                border-radius: 18px;
            }
            QFrame#heroCard, QFrame#panelCard {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid #d7dfeb;
                border-radius: 20px;
            }
            QLabel#heroTitle {
                font-size: 22px;
                font-weight: 700;
                color: #0f172a;
            }
            QLabel#heroSubtitle, QLabel#panelCaption, QLabel#fieldHint {
                color: #5f6f86;
            }
            QLabel#panelTitle {
                font-size: 16px;
                font-weight: 700;
                color: #142033;
            }
            QLabel#fieldLabel {
                font-size: 12px;
                font-weight: 600;
                color: #334155;
            }
            QLabel#statusLabel {
                padding: 12px 14px;
                border-radius: 14px;
                background: #eff5ff;
                color: #244886;
                border: 1px solid #d3e1ff;
            }
            QLineEdit, QTextEdit, QListWidget {
                background: #fbfdff;
                border: 1px solid #d5dfec;
                border-radius: 14px;
                padding: 10px 12px;
                color: #0f172a;
                selection-background-color: #dce9ff;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus {
                border: 1px solid #4e8cff;
            }
            QLineEdit[captureActive="true"] {
                background: #edf4ff;
                border: 1px solid #2268f5;
                color: #1d4ed8;
            }
            QListWidget {
                padding: 10px;
            }
            QPushButton {
                border: 0;
                border-radius: 12px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QToolButton#secondaryToolButton {
                border: 0;
                border-radius: 12px;
                padding: 10px 12px;
                font-weight: 600;
                background: #ebf1fb;
                color: #1f365c;
            }
            QToolButton#secondaryToolButton:hover {
                background: #dce7f8;
            }
            QToolButton#secondaryToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
            QPushButton#primaryButton {
                background: #2268f5;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background: #1d5cda;
            }
            QPushButton#secondaryButton {
                background: #ebf1fb;
                color: #1f365c;
            }
            QPushButton#secondaryButton:hover {
                background: #dce7f8;
            }
            QPushButton#dangerButton {
                background: #fdecec;
                color: #9f2d2d;
            }
            QPushButton#dangerButton:hover {
                background: #fbdede;
            }
            QCheckBox {
                color: #334155;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 6px;
                border: 1px solid #b9c6d8;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #2268f5;
                border-color: #2268f5;
            }
            QFrame#presetCard {
                background: white;
                border: 1px solid #dde5f0;
                border-radius: 16px;
            }
            QFrame#presetCard[selected="true"] {
                background: #edf4ff;
                border: 1px solid #91b7ff;
            }
            QLabel#cardTitle {
                font-size: 13px;
                font-weight: 700;
                color: #122035;
            }
            QLabel#cardPreview {
                color: #61748f;
            }
            QLabel#hotkeyBadge {
                padding: 4px 8px;
                border-radius: 9px;
                background: #e8f0ff;
                color: #2550a9;
                font-size: 11px;
                font-weight: 600;
            }
            """
        )
        if hasattr(self, "sidebar_window"):
            self.sidebar_window.setStyleSheet(self.styleSheet())

    def _build_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(self._resource_path("assets", "hki.ico"))))
        self.tray_icon.setToolTip("HOTKEYINPUT")

        menu = QMenu(self)
        self.show_action = QAction("Edit presets", self)
        self.open_sidebar_action = QAction("Open sidebar", self)
        self.hide_action = QAction("Hide to tray", self)
        self.paste_selected_action = QAction("Paste selected", self)
        self.quit_action = QAction("Quit HKI", self)

        menu.addAction(self.show_action)
        menu.addAction(self.open_sidebar_action)
        menu.addAction(self.hide_action)
        menu.addAction(self.paste_selected_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.show_action.triggered.connect(self._show_from_tray)
        self.open_sidebar_action.triggered.connect(self._open_sidebar_from_ui)
        self.hide_action.triggered.connect(self.hide_to_tray)
        self.paste_selected_action.triggered.connect(partial(self._paste_selected_preset, True))
        self.quit_action.triggered.connect(self._quit_from_menu)

    def _connect_events(self) -> None:
        self.sidebar_hotkey_edit.hotkey_changed.connect(self._on_sidebar_hotkey_changed)
        self.sidebar_hotkey_edit.capture_started.connect(self._on_sidebar_hotkey_capture_started)
        self.sidebar_hotkey_edit.capture_cancelled.connect(self._on_sidebar_hotkey_capture_cancelled)
        self.sidebar_hotkey_edit.capture_finished.connect(self._on_sidebar_hotkey_capture_finished)
        self.open_sidebar_button.clicked.connect(self._open_sidebar_from_ui)
        self.send_to_tray_button.clicked.connect(self.hide_to_tray)

        self.search_edit.textChanged.connect(self._refresh_preset_list)
        self.preset_list.currentItemChanged.connect(self._on_current_item_changed)

        self.new_button.clicked.connect(self._create_preset)
        self.duplicate_button.clicked.connect(self._duplicate_preset)
        self.delete_button.clicked.connect(self._delete_preset)

        self.name_edit.textChanged.connect(self._mark_dirty)
        self.hotkey_edit.hotkey_changed.connect(self._mark_dirty)
        self.hotkey_edit.capture_started.connect(self._on_hotkey_capture_started)
        self.hotkey_edit.capture_cancelled.connect(self._on_hotkey_capture_cancelled)
        self.hotkey_edit.capture_finished.connect(self._on_hotkey_capture_finished)
        self.text_edit.textChanged.connect(self._mark_dirty)

        self.save_button.clicked.connect(partial(self._commit_editor_to_current, True, True))
        self.copy_button.clicked.connect(self._copy_selected_preset)
        self.paste_button.clicked.connect(partial(self._paste_selected_preset, True))

    def _load_state_into_ui(self) -> None:
        self.sidebar_hotkey_edit.setText(self._state.sidebar_hotkey)

        if not self._state.presets:
            self._state.presets.append(
                Preset(
                    name=self._t("default_preset_name"),
                    text=self._t("default_preset_text"),
                )
            )

        selected_id = self._state.selected_preset_id or self._state.presets[0].id
        self._refresh_preset_list(selected_id)
        self._set_status(self._t("ready_status", path=self._store.settings_file))
        self._update_editor_enabled_state()
        self._register_hotkeys()

    def _load_brand_pixmap(self) -> QPixmap:
        pixmap = QPixmap(str(self._resource_path("assets", "hki.png")))
        return pixmap.scaled(
            42,
            42,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _restore_window_position(self) -> None:
        x = self._state.window.x
        y = self._state.window.y
        if x is None or y is None:
            return

        target = QRect(QPoint(x, y), QSize(self.width(), self.height()))
        for screen in QGuiApplication.screens():
            if screen.availableGeometry().intersects(target):
                self.move(x, y)
                break

    def _persist_state(self) -> None:
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        self._state.window.width = max(geometry.width(), 820)
        self._state.window.height = max(geometry.height(), 520)
        self._state.window.x = geometry.x()
        self._state.window.y = geometry.y()
        self._state.selected_preset_id = self._current_preset_id
        self._state.sidebar_hotkey = normalize_hotkey(self.sidebar_hotkey_edit.text().strip())
        self._state.language = self._language
        self._store.save(self._state)

    def _refresh_preset_list(self, preferred_id: str | None = None) -> None:
        query = self.search_edit.text().strip().lower()
        selected_id = preferred_id or self._current_preset_id

        self.preset_list.blockSignals(True)
        self.preset_list.clear()

        matching_presets = [
            preset
            for preset in self._state.presets
            if not query
            or query in preset.name.lower()
            or query in preset.text.lower()
            or query in preset.hotkey.lower()
        ]
        matching_presets.sort(key=lambda preset: preset.name.lower())

        for preset in matching_presets:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, preset.id)
            item.setSizeHint(QSize(0, 82))
            card = PresetListCard(preset, self._t)
            self.preset_list.addItem(item)
            self.preset_list.setItemWidget(item, card)

            if preset.id == selected_id:
                self.preset_list.setCurrentItem(item)

        if self.preset_list.count() and self.preset_list.currentItem() is None:
            self.preset_list.setCurrentRow(0)

        self.preset_list.blockSignals(False)
        self._sync_card_selection_states()

        current_item = self.preset_list.currentItem()
        if current_item is not None:
            self._current_preset_id = current_item.data(Qt.ItemDataRole.UserRole)
            self._load_selected_preset_into_editor()
        else:
            self._current_preset_id = None
            self._clear_editor()

        self._update_editor_enabled_state()
        self.paste_selected_action.setEnabled(self._current_preset_id is not None)

    def _sync_card_selection_states(self) -> None:
        for index in range(self.preset_list.count()):
            item = self.preset_list.item(index)
            card = self.preset_list.itemWidget(item)
            if isinstance(card, PresetListCard):
                card.set_selected(item == self.preset_list.currentItem())

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        previous_id = previous.data(Qt.ItemDataRole.UserRole) if previous else None
        current_id = current.data(Qt.ItemDataRole.UserRole) if current else None

        if previous_id and previous_id != current_id:
            self._commit_editor_to_current(False, False, preset_id=previous_id)

        self._current_preset_id = current_id
        self._load_selected_preset_into_editor()
        self._sync_card_selection_states()
        self._update_editor_enabled_state()

    def _selected_preset(self, preset_id: str | None = None) -> Preset | None:
        lookup_id = preset_id or self._current_preset_id
        if lookup_id is None:
            return None

        for preset in self._state.presets:
            if preset.id == lookup_id:
                return preset
        return None

    def _load_selected_preset_into_editor(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            self._clear_editor()
            return

        self._suspend_editor_updates = True
        self.name_edit.setText(preset.name)
        self.hotkey_edit.setText(preset.hotkey)
        self.text_edit.setPlainText(preset.text)
        self._suspend_editor_updates = False
        self._dirty = False

    def _clear_editor(self) -> None:
        self._suspend_editor_updates = True
        self.name_edit.clear()
        self.hotkey_edit.clear()
        self.text_edit.clear()
        self._suspend_editor_updates = False
        self._dirty = False

    def _update_editor_enabled_state(self) -> None:
        enabled = self._current_preset_id is not None
        for widget in (
            self.name_edit,
            self.hotkey_edit,
            self.text_edit,
            self.save_button,
            self.copy_button,
            self.paste_button,
            self.duplicate_button,
            self.delete_button,
        ):
            widget.setEnabled(enabled)

    def _mark_dirty(self, *_args) -> None:
        if self._suspend_editor_updates or self._current_preset_id is None:
            return
        self._dirty = True
        self._set_status(self._t("edited_status"))

    def _commit_editor_to_current(
        self,
        show_status: bool,
        rebuild_list: bool = False,
        preset_id: str | None = None,
    ) -> None:
        target_id = preset_id or self._current_preset_id
        preset = self._selected_preset(target_id)
        if preset is None:
            return

        name = self.name_edit.text().strip()
        text = self.text_edit.toPlainText()
        hotkey_text = self.hotkey_edit.text().strip()

        if not name:
            name = self._make_unique_name("Untitled preset", exclude_id=preset.id)

        normalized_hotkey = normalize_hotkey(hotkey_text)
        preset.name = name
        preset.text = text
        preset.hotkey = normalized_hotkey
        preset.updated_at = utc_now_iso()
        self._dirty = False
        self._persist_state()
        if rebuild_list:
            self._refresh_preset_list(preset.id)
        else:
            self._update_visible_card(preset)
        self._register_hotkeys()

        if show_status:
            message = self._t("saved_status", preset=preset.name)
            if hotkey_text and not normalized_hotkey:
                message = self._t("saved_hotkey_ignored_status", preset=preset.name)
            self._set_status(message)

    def _create_preset(self) -> None:
        self._commit_editor_to_current(False, False)
        preset = Preset(name=self._make_unique_name(self._t("new_preset_base")), text="")
        self._state.presets.append(preset)
        self._persist_state()
        self._refresh_preset_list(preset.id)
        self.name_edit.setFocus()
        self.name_edit.selectAll()
        self._set_status(self._t("created_status", preset=preset.name))

    def _duplicate_preset(self) -> None:
        source = self._selected_preset()
        if source is None:
            return

        self._commit_editor_to_current(False, False)
        duplicate = Preset(
            name=self._make_unique_name(
                self._t("copy_of_format", name=source.name or self._t("generic_preset_name"))
            ),
            text=source.text,
        )
        self._state.presets.append(duplicate)
        self._persist_state()
        self._refresh_preset_list(duplicate.id)
        self._set_status(self._t("duplicated_status", preset=source.name or self._t("generic_preset_name")))

    def _delete_preset(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return

        answer = QMessageBox.question(
            self,
            self._t("delete_preset_title"),
            self._t("delete_preset_question", preset=preset.name or self._t("this_preset")),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._state.presets = [entry for entry in self._state.presets if entry.id != preset.id]
        fallback = self._state.presets[0].id if self._state.presets else None
        self._persist_state()
        self._refresh_preset_list(fallback)
        self._register_hotkeys()
        self._set_status(self._t("deleted_status", preset=preset.name))

    def _copy_selected_preset(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return

        self._commit_editor_to_current(False, False)
        QApplication.clipboard().setText(preset.text)
        self._set_status(self._t("copied_status", preset=preset.name))

    def _paste_selected_preset(self, hide_window_first: bool) -> None:
        preset = self._selected_preset()
        if preset is None:
            return

        self._commit_editor_to_current(False, False)
        self._paste_preset_by_id(preset.id, hide_window_first)

    def _paste_preset_by_id(self, preset_id: str, hide_window_first: bool, target_hwnd: int = 0) -> None:
        preset = self._selected_preset(preset_id)
        if preset is None:
            return

        if not preset.text:
            self._set_status(self._t("empty_preset_status"))
            return

        clipboard = QApplication.clipboard()
        self._clipboard_snapshot = self._clone_mime_data(clipboard.mimeData())
        clipboard.setText(preset.text)

        if target_hwnd:
            QTimer.singleShot(20, lambda: restore_foreground_window(target_hwnd))
            QTimer.singleShot(160, send_ctrl_v)
            QTimer.singleShot(560, self._restore_clipboard)
        elif hide_window_first:
            self.hide_to_tray(show_message=False)
            QTimer.singleShot(180, send_ctrl_v)
            QTimer.singleShot(560, self._restore_clipboard)
        else:
            send_ctrl_v()
            QTimer.singleShot(420, self._restore_clipboard)

        self._set_status(self._t("pasted_status", preset=preset.name))

    def _clone_mime_data(self, source) -> object | None:
        if source is None:
            return None

        from PySide6.QtCore import QMimeData

        snapshot = QMimeData()
        for mime_format in source.formats():
            snapshot.setData(mime_format, source.data(mime_format))
        if source.hasText():
            snapshot.setText(source.text())
        if source.hasHtml():
            snapshot.setHtml(source.html())
        return snapshot

    def _restore_clipboard(self) -> None:
        if self._clipboard_snapshot is None:
            return

        QApplication.clipboard().setMimeData(self._clipboard_snapshot)
        self._clipboard_snapshot = None

    def _register_hotkeys(self) -> None:
        hwnd = int(self.winId())
        if hwnd == 0:
            return

        unregister_hotkeys(hwnd, list(self._registered_hotkeys.keys()))
        self._registered_hotkeys.clear()
        self._next_hotkey_id = 0x5000

        seen_hotkeys: set[str] = set()
        warnings: list[str] = []

        sidebar_hotkey = parse_hotkey(self._state.sidebar_hotkey)
        if sidebar_hotkey is not None:
            sidebar_hotkey_id = self._next_hotkey_id
            self._next_hotkey_id += 1
            seen_hotkeys.add(sidebar_hotkey.display)
            if register_hotkey(hwnd, sidebar_hotkey_id, sidebar_hotkey):
                self._registered_hotkeys[sidebar_hotkey_id] = ("sidebar", "")
            else:
                warnings.append(self._t("warning_register_sidebar_hotkey", hotkey=sidebar_hotkey.display))

        for preset in self._state.presets:
            if not preset.hotkey:
                continue

            gesture = parse_hotkey(preset.hotkey)
            if gesture is None:
                warnings.append(self._t("warning_invalid_hotkey", preset=preset.name))
                continue

            if gesture.display in seen_hotkeys:
                warnings.append(self._t("warning_duplicate_hotkey", hotkey=gesture.display))
                continue

            seen_hotkeys.add(gesture.display)
            hotkey_id = self._next_hotkey_id
            self._next_hotkey_id += 1

            if register_hotkey(hwnd, hotkey_id, gesture):
                self._registered_hotkeys[hotkey_id] = ("preset", preset.id)
            else:
                warnings.append(self._t("warning_register_hotkey", hotkey=gesture.display))

        if warnings:
            self._set_status(warnings[0])

    def _make_unique_name(self, base_name: str, exclude_id: str | None = None) -> str:
        candidate = base_name
        counter = 2

        while any(
            preset.id != exclude_id and preset.name.casefold() == candidate.casefold()
            for preset in self._state.presets
        ):
            candidate = f"{base_name} {counter}"
            counter += 1
        return candidate

    def _update_visible_card(self, preset: Preset) -> None:
        for index in range(self.preset_list.count()):
            item = self.preset_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) != preset.id:
                continue

            card = self.preset_list.itemWidget(item)
            if isinstance(card, PresetListCard):
                card.update_preset(preset)
            break

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _on_sidebar_hotkey_changed(self, value: str) -> None:
        self._state.sidebar_hotkey = normalize_hotkey(value)
        self._persist_state()
        self._register_hotkeys()
        if self._state.sidebar_hotkey:
            self._set_status(self._t("sidebar_hotkey_set", hotkey=self._state.sidebar_hotkey))
        else:
            self._set_status(self._t("sidebar_hotkey_cleared"))

    def _on_sidebar_hotkey_capture_started(self) -> None:
        self._set_status(self._t("sidebar_hotkey_wait"))

    def _on_sidebar_hotkey_capture_cancelled(self) -> None:
        self._set_status(self._t("sidebar_hotkey_cancelled"))

    def _on_sidebar_hotkey_capture_finished(self, value: str) -> None:
        self._set_status(self._t("sidebar_hotkey_set", hotkey=value))

    def _on_hotkey_capture_started(self) -> None:
        if self._current_preset_id is None:
            return
        self._set_status(self._t("paste_hotkey_wait"))

    def _on_hotkey_capture_cancelled(self) -> None:
        if self._current_preset_id is None:
            return
        self._set_status(self._t("paste_hotkey_cancelled"))

    def _on_hotkey_capture_finished(self, value: str) -> None:
        if self._current_preset_id is None:
            return
        self._set_status(self._t("paste_hotkey_set", hotkey=value))

    def _open_sidebar(self, target_hwnd: int = 0) -> None:
        presets = [preset for preset in self._state.presets if preset.text]
        if not presets:
            self._set_status(self._t("add_preset_before_sidebar"))
            return

        self._sidebar_target_hwnd = target_hwnd
        self.sidebar_window.set_presets(presets)
        self.sidebar_window.open_sidebar()

    def _open_sidebar_from_ui(self) -> None:
        self._open_sidebar()

    def _open_sidebar_from_hotkey(self) -> None:
        foreground_hwnd = get_foreground_window()
        if foreground_hwnd == int(self.winId()):
            foreground_hwnd = 0
        self._open_sidebar(foreground_hwnd)

    def _paste_preset_from_sidebar(self, preset_id: str) -> None:
        target_hwnd = self._sidebar_target_hwnd
        self.sidebar_window.hide()
        self._paste_preset_by_id(preset_id, False, target_hwnd=target_hwnd)

    def _show_from_tray(self) -> None:
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self, show_message: bool = True) -> None:
        self._commit_editor_to_current(False, False)
        self._persist_state()
        self.hide()
        if show_message and not self._tray_tip_shown:
            self.tray_icon.showMessage(
                self._t("tray_running_title"),
                self._t("tray_running_message"),
                QSystemTrayIcon.MessageIcon.Information,
                2400,
            )
            self._tray_tip_shown = True

    def _quit_from_menu(self) -> None:
        self._commit_editor_to_current(False, False)
        self._persist_state()
        self._quit_requested = True
        self.sidebar_window.hide()
        self.tray_icon.hide()
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self._show_from_tray()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._window_style_applied:
            try:
                apply_windows_11_backdrop(int(self.winId()))
            except Exception:
                pass
            self._window_style_applied = True

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._commit_editor_to_current(False, False)
        self._persist_state()
        self._quit_requested = True
        self.sidebar_window.hide()
        unregister_hotkeys(int(self.winId()), list(self._registered_hotkeys.keys()))
        self.tray_icon.hide()
        super().closeEvent(event)
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def nativeEvent(self, event_type, message):
        if event_type in {"windows_generic_MSG", "windows_dispatcher_MSG"}:
            message_address = message.__int__() if hasattr(message, "__int__") else int(message)
            msg = MSG.from_address(message_address)
            if msg.message == WM_HOTKEY:
                action = self._registered_hotkeys.get(int(msg.wParam))
                if action:
                    kind, value = action
                    if kind == "sidebar":
                        self._open_sidebar_from_hotkey()
                    elif kind == "preset":
                        target_hwnd = get_foreground_window()
                        if target_hwnd == int(self.winId()):
                            target_hwnd = 0
                        self._paste_preset_by_id(value, False, target_hwnd=target_hwnd)
                    return True, 0
        return super().nativeEvent(event_type, message)
