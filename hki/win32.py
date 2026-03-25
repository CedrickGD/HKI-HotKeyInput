from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
from typing import Iterable

from PySide6.QtCore import Qt


user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_V = 0x56
SW_RESTORE = 9

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWCP_ROUND = 2
DWMSBT_MAINWINDOW = 2


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
        ("lPrivate", wintypes.DWORD),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


@dataclass(frozen=True, slots=True)
class HotkeyGesture:
    display: str
    modifiers: int
    vk: int


QT_MODIFIER_KEYS = {
    int(Qt.Key.Key_Control),
    int(Qt.Key.Key_Shift),
    int(Qt.Key.Key_Alt),
    int(Qt.Key.Key_Meta),
}

TOKEN_TO_KEY = {
    "TAB": ("Tab", 0x09),
    "ENTER": ("Enter", 0x0D),
    "SPACE": ("Space", 0x20),
    "ESC": ("Esc", 0x1B),
    "ESCAPE": ("Esc", 0x1B),
    "UP": ("Up", 0x26),
    "DOWN": ("Down", 0x28),
    "LEFT": ("Left", 0x25),
    "RIGHT": ("Right", 0x27),
    "INSERT": ("Insert", 0x2D),
    "DELETE": ("Delete", 0x2E),
    "HOME": ("Home", 0x24),
    "END": ("End", 0x23),
    "PAGEUP": ("PageUp", 0x21),
    "PAGEDOWN": ("PageDown", 0x22),
}

VK_TO_LABEL = {vk: label for label, vk in TOKEN_TO_KEY.values()}


def _qt_key_to_vk_and_label(key_code: int) -> tuple[int, str] | None:
    if int(Qt.Key.Key_A) <= key_code <= int(Qt.Key.Key_Z):
        offset = key_code - int(Qt.Key.Key_A)
        label = chr(ord("A") + offset)
        return 0x41 + offset, label

    if int(Qt.Key.Key_0) <= key_code <= int(Qt.Key.Key_9):
        offset = key_code - int(Qt.Key.Key_0)
        label = str(offset)
        return 0x30 + offset, label

    if int(Qt.Key.Key_F1) <= key_code <= int(Qt.Key.Key_F24):
        offset = key_code - int(Qt.Key.Key_F1)
        return 0x70 + offset, f"F{offset + 1}"

    key_map = {
        int(Qt.Key.Key_Tab): 0x09,
        int(Qt.Key.Key_Return): 0x0D,
        int(Qt.Key.Key_Enter): 0x0D,
        int(Qt.Key.Key_Space): 0x20,
        int(Qt.Key.Key_Escape): 0x1B,
        int(Qt.Key.Key_Up): 0x26,
        int(Qt.Key.Key_Down): 0x28,
        int(Qt.Key.Key_Left): 0x25,
        int(Qt.Key.Key_Right): 0x27,
        int(Qt.Key.Key_Insert): 0x2D,
        int(Qt.Key.Key_Delete): 0x2E,
        int(Qt.Key.Key_Home): 0x24,
        int(Qt.Key.Key_End): 0x23,
        int(Qt.Key.Key_PageUp): 0x21,
        int(Qt.Key.Key_PageDown): 0x22,
    }

    vk = key_map.get(key_code)
    if vk is None:
        return None

    return vk, VK_TO_LABEL.get(vk, "")


def _format_modifiers(modifiers: int) -> list[str]:
    labels: list[str] = []
    if modifiers & MOD_CONTROL:
        labels.append("Ctrl")
    if modifiers & MOD_ALT:
        labels.append("Alt")
    if modifiers & MOD_SHIFT:
        labels.append("Shift")
    return labels


def capture_hotkey_from_event(event) -> HotkeyGesture | None:
    key_code = int(event.key())
    if key_code in QT_MODIFIER_KEYS:
        return None

    modifier_value = 0
    qt_modifiers = event.modifiers()
    if qt_modifiers & Qt.KeyboardModifier.ControlModifier:
        modifier_value |= MOD_CONTROL
    if qt_modifiers & Qt.KeyboardModifier.AltModifier:
        modifier_value |= MOD_ALT
    if qt_modifiers & Qt.KeyboardModifier.ShiftModifier:
        modifier_value |= MOD_SHIFT

    mapped = _qt_key_to_vk_and_label(key_code)
    if not mapped:
        return None

    vk, label = mapped
    display = "+".join([*_format_modifiers(modifier_value), label])
    return HotkeyGesture(display=display, modifiers=modifier_value, vk=vk)


def parse_hotkey(value: str) -> HotkeyGesture | None:
    if not value.strip():
        return None

    tokens = [token.strip() for token in value.split("+") if token.strip()]
    modifiers = 0
    label = ""
    vk = None

    for token in tokens:
        upper = token.upper()
        if upper in {"CTRL", "CONTROL"}:
            modifiers |= MOD_CONTROL
            continue
        if upper == "ALT":
            modifiers |= MOD_ALT
            continue
        if upper == "SHIFT":
            modifiers |= MOD_SHIFT
            continue

        if vk is not None:
            return None

        if len(token) == 1 and token.isalpha():
            label = token.upper()
            vk = 0x41 + (ord(label) - ord("A"))
            continue

        if len(token) == 1 and token.isdigit():
            label = token
            vk = 0x30 + int(token)
            continue

        if upper.startswith("F") and upper[1:].isdigit():
            index = int(upper[1:])
            if 1 <= index <= 24:
                label = f"F{index}"
                vk = 0x70 + index - 1
                continue

        mapped = TOKEN_TO_KEY.get(upper)
        if mapped:
            label, vk = mapped
            continue

        return None

    if vk is None:
        return None

    display = "+".join([*_format_modifiers(modifiers), label])
    return HotkeyGesture(display=display, modifiers=modifiers, vk=vk)


def normalize_hotkey(value: str) -> str:
    gesture = parse_hotkey(value)
    return gesture.display if gesture else ""


def register_hotkey(hwnd: int, hotkey_id: int, gesture: HotkeyGesture) -> bool:
    return bool(user32.RegisterHotKey(hwnd, hotkey_id, gesture.modifiers, gesture.vk))


def unregister_hotkey(hwnd: int, hotkey_id: int) -> None:
    user32.UnregisterHotKey(hwnd, hotkey_id)


def unregister_hotkeys(hwnd: int, hotkey_ids: Iterable[int]) -> None:
    for hotkey_id in hotkey_ids:
        unregister_hotkey(hwnd, hotkey_id)


def get_foreground_window() -> int:
    return int(user32.GetForegroundWindow())


def restore_foreground_window(hwnd: int) -> bool:
    if hwnd == 0:
        return False

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))


def send_ctrl_v() -> None:
    def keyboard_input(vk: int, flags: int) -> INPUT:
        return INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(
                ki=KEYBDINPUT(
                    wVk=vk,
                    wScan=0,
                    dwFlags=flags,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )

    sequence = [
        keyboard_input(VK_CONTROL, 0),
        keyboard_input(VK_V, 0),
        keyboard_input(VK_V, KEYEVENTF_KEYUP),
        keyboard_input(VK_CONTROL, KEYEVENTF_KEYUP),
    ]
    user32.SendInput(len(sequence), (INPUT * len(sequence))(*sequence), ctypes.sizeof(INPUT))


def apply_windows_11_backdrop(hwnd: int) -> None:
    use_light_title_bar = ctypes.c_int(0)
    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(use_light_title_bar),
        ctypes.sizeof(use_light_title_bar),
    )

    rounded_corners = ctypes.c_int(DWMWCP_ROUND)
    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(rounded_corners),
        ctypes.sizeof(rounded_corners),
    )

    backdrop = ctypes.c_int(DWMSBT_MAINWINDOW)
    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SYSTEMBACKDROP_TYPE,
        ctypes.byref(backdrop),
        ctypes.sizeof(backdrop),
    )
