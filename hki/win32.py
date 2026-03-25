"""Win32 helpers: global hotkeys, Ctrl+V simulation, DWM backdrop."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
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


# ── ctypes structures ──────────────────────────────────────────────────

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


# ── hotkey gesture ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class HotkeyGesture:
    display: str
    modifiers: int
    vk: int


QT_MODIFIER_KEYS = {
    int(Qt.Key.Key_Control), int(Qt.Key.Key_Shift),
    int(Qt.Key.Key_Alt), int(Qt.Key.Key_Meta),
}

TOKEN_TO_KEY = {
    "TAB": ("Tab", 0x09), "ENTER": ("Enter", 0x0D), "SPACE": ("Space", 0x20),
    "ESC": ("Esc", 0x1B), "ESCAPE": ("Esc", 0x1B),
    "UP": ("Up", 0x26), "DOWN": ("Down", 0x28),
    "LEFT": ("Left", 0x25), "RIGHT": ("Right", 0x27),
    "INSERT": ("Insert", 0x2D), "DELETE": ("Delete", 0x2E),
    "HOME": ("Home", 0x24), "END": ("End", 0x23),
    "PAGEUP": ("PageUp", 0x21), "PAGEDOWN": ("PageDown", 0x22),
}
VK_TO_LABEL = {vk: label for label, vk in TOKEN_TO_KEY.values()}


def _qt_key_to_vk(key: int) -> tuple[int, str] | None:
    if int(Qt.Key.Key_A) <= key <= int(Qt.Key.Key_Z):
        off = key - int(Qt.Key.Key_A)
        return 0x41 + off, chr(ord("A") + off)
    if int(Qt.Key.Key_0) <= key <= int(Qt.Key.Key_9):
        off = key - int(Qt.Key.Key_0)
        return 0x30 + off, str(off)
    if int(Qt.Key.Key_F1) <= key <= int(Qt.Key.Key_F24):
        off = key - int(Qt.Key.Key_F1)
        return 0x70 + off, f"F{off + 1}"
    vk_map = {
        int(Qt.Key.Key_Tab): 0x09, int(Qt.Key.Key_Return): 0x0D,
        int(Qt.Key.Key_Enter): 0x0D, int(Qt.Key.Key_Space): 0x20,
        int(Qt.Key.Key_Escape): 0x1B,
        int(Qt.Key.Key_Up): 0x26, int(Qt.Key.Key_Down): 0x28,
        int(Qt.Key.Key_Left): 0x25, int(Qt.Key.Key_Right): 0x27,
        int(Qt.Key.Key_Insert): 0x2D, int(Qt.Key.Key_Delete): 0x2E,
        int(Qt.Key.Key_Home): 0x24, int(Qt.Key.Key_End): 0x23,
        int(Qt.Key.Key_PageUp): 0x21, int(Qt.Key.Key_PageDown): 0x22,
    }
    vk = vk_map.get(key)
    return (vk, VK_TO_LABEL.get(vk, "")) if vk else None


def _mod_labels(mods: int) -> list[str]:
    out: list[str] = []
    if mods & MOD_CONTROL:
        out.append("Ctrl")
    if mods & MOD_ALT:
        out.append("Alt")
    if mods & MOD_SHIFT:
        out.append("Shift")
    return out


# ── public API ─────────────────────────────────────────────────────────

def capture_hotkey_from_event(event) -> HotkeyGesture | None:
    key = int(event.key())
    if key in QT_MODIFIER_KEYS:
        return None
    mods = 0
    qm = event.modifiers()
    if qm & Qt.KeyboardModifier.ControlModifier:
        mods |= MOD_CONTROL
    if qm & Qt.KeyboardModifier.AltModifier:
        mods |= MOD_ALT
    if qm & Qt.KeyboardModifier.ShiftModifier:
        mods |= MOD_SHIFT
    mapped = _qt_key_to_vk(key)
    if not mapped:
        return None
    vk, label = mapped
    return HotkeyGesture(display="+".join([*_mod_labels(mods), label]), modifiers=mods, vk=vk)


def parse_hotkey(value: str) -> HotkeyGesture | None:
    if not value.strip():
        return None
    tokens = [t.strip() for t in value.split("+") if t.strip()]
    mods = 0
    label = ""
    vk = None
    for tok in tokens:
        u = tok.upper()
        if u in ("CTRL", "CONTROL", "STRG"):
            mods |= MOD_CONTROL
            continue
        if u == "ALT":
            mods |= MOD_ALT
            continue
        if u == "SHIFT":
            mods |= MOD_SHIFT
            continue
        if vk is not None:
            return None
        if len(tok) == 1 and tok.isalpha():
            label = tok.upper()
            vk = 0x41 + (ord(label) - ord("A"))
            continue
        if len(tok) == 1 and tok.isdigit():
            label = tok
            vk = 0x30 + int(tok)
            continue
        if u.startswith("F") and u[1:].isdigit():
            idx = int(u[1:])
            if 1 <= idx <= 24:
                label = f"F{idx}"
                vk = 0x70 + idx - 1
                continue
        m = TOKEN_TO_KEY.get(u)
        if m:
            label, vk = m
            continue
        return None
    if vk is None:
        return None
    return HotkeyGesture(display="+".join([*_mod_labels(mods), label]), modifiers=mods, vk=vk)


def normalize_hotkey(value: str) -> str:
    g = parse_hotkey(value)
    return g.display if g else ""


def register_hotkey(hwnd: int, hid: int, g: HotkeyGesture) -> bool:
    return bool(user32.RegisterHotKey(hwnd, hid, g.modifiers, g.vk))


def unregister_hotkey(hwnd: int, hid: int) -> None:
    user32.UnregisterHotKey(hwnd, hid)


def unregister_hotkeys(hwnd: int, ids: Iterable[int]) -> None:
    for hid in ids:
        unregister_hotkey(hwnd, hid)


def get_foreground_window() -> int:
    return int(user32.GetForegroundWindow())


def restore_foreground_window(hwnd: int) -> bool:
    if not hwnd:
        return False
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))


def send_ctrl_v() -> None:
    def ki(vk: int, flags: int) -> INPUT:
        return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(
            ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)))
    seq = [ki(VK_CONTROL, 0), ki(VK_V, 0), ki(VK_V, KEYEVENTF_KEYUP), ki(VK_CONTROL, KEYEVENTF_KEYUP)]
    user32.SendInput(len(seq), (INPUT * len(seq))(*seq), ctypes.sizeof(INPUT))


def apply_windows_11_backdrop(hwnd: int) -> None:
    for attr, val in [
        (DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND),
        (DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_MAINWINDOW),
    ]:
        v = ctypes.c_int(val)
        dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
