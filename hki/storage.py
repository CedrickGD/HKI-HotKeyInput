"""Preset and settings persistence — stored in %LOCALAPPDATA%/HKI."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid

VERSION = "1.0.0"  # ← bump this + update.xml when releasing


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Preset:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    text: str = ""
    hotkey: str = ""
    updated_at: str = field(default_factory=_utc_now)

    @property
    def preview(self) -> str:
        compact = " ".join(self.text.split())
        return compact[:80] + ("…" if len(compact) > 80 else "")


@dataclass(slots=True)
class WinGeo:
    width: int = 860
    height: int = 540
    x: int | None = None
    y: int | None = None


@dataclass(slots=True)
class CustomPlaceholder:
    key: str = ""
    kind: str = "text"      # "text" or "datetime"
    value: str = ""


@dataclass(slots=True)
class AppState:
    presets: list[Preset] = field(default_factory=list)
    selected_id: str | None = None
    window: WinGeo = field(default_factory=WinGeo)
    close_to_tray: bool = True
    minimize_to_tray: bool = False
    sidebar_hotkey: str = "Ctrl+Shift+Space"
    language: str = "en"
    custom_placeholders: list[CustomPlaceholder] = field(default_factory=list)


class Store:
    def __init__(self) -> None:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        self.folder = Path(base) / "HKI"
        self.path = self.folder / "settings.json"

    def load(self) -> AppState:
        try:
            if not self.path.exists():
                return AppState()
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            presets = [Preset(**p) for p in raw.get("presets", [])]
            wg = raw.get("window", {})
            cps = [CustomPlaceholder(**c) for c in raw.get("custom_placeholders", [])]
            return AppState(
                presets=presets,
                selected_id=raw.get("selected_id"),
                window=WinGeo(
                    width=wg.get("width", 860),
                    height=wg.get("height", 540),
                    x=wg.get("x"),
                    y=wg.get("y"),
                ),
                close_to_tray=raw.get("close_to_tray", True),
                minimize_to_tray=raw.get("minimize_to_tray", False),
                sidebar_hotkey=raw.get("sidebar_hotkey", "Ctrl+Shift+Space"),
                language=raw.get("language", "en"),
                custom_placeholders=cps,
            )
        except Exception:
            return AppState()

    def save(self, state: AppState) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(state), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
