"""Global hotkey registration and dispatch."""
from __future__ import annotations

from typing import Callable

from hki.storage import Preset
from hki.windows_api import parse_hotkey, register_hotkey, unregister_hotkeys


class HotkeyRegistry:
    """Manages Win32 global hotkey registration."""

    def __init__(self) -> None:
        self._hotkeys: dict[int, tuple[str, str]] = {}
        self._next_id = 0x5000

    @property
    def ids(self) -> list[int]:
        return list(self._hotkeys.keys())

    def register_all(
        self,
        hwnd: int,
        sidebar_hotkey: str,
        presets: list[Preset],
        t: Callable[..., str],
    ) -> list[str]:
        """Re-register all hotkeys. Returns warning messages."""
        unregister_hotkeys(hwnd, self.ids)
        self._hotkeys.clear()
        self._next_id = 0x5000
        seen: set[str] = set()
        warns: list[str] = []

        sb = parse_hotkey(sidebar_hotkey)
        if sb:
            hid = self._next_id; self._next_id += 1
            seen.add(sb.display)
            if register_hotkey(hwnd, hid, sb):
                self._hotkeys[hid] = ("sb", "")
            else:
                warns.append(t("warn_reg_sb", h=sb.display))

        for p in presets:
            if not p.hotkey:
                continue
            g = parse_hotkey(p.hotkey)
            if not g:
                warns.append(t("warn_bad_hk", p=p.name))
                continue
            if g.display in seen:
                warns.append(t("warn_dup_hk", h=g.display))
                continue
            seen.add(g.display)
            hid = self._next_id; self._next_id += 1
            if register_hotkey(hwnd, hid, g):
                self._hotkeys[hid] = ("preset", p.id)
            else:
                warns.append(t("warn_reg", h=g.display))

        return warns

    def lookup(self, hid: int) -> tuple[str, str] | None:
        """Look up action for a hotkey ID. Returns (kind, value) or None."""
        return self._hotkeys.get(hid)

    def unregister_all(self, hwnd: int) -> None:
        unregister_hotkeys(hwnd, self.ids)
        self._hotkeys.clear()
