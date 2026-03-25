from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Preset:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    text: str = ""
    hotkey: str = ""
    updated_at: str = field(default_factory=utc_now_iso)

    @property
    def preview(self) -> str:
        compact = " ".join(self.text.split())
        return compact[:86] + ("..." if len(compact) > 86 else "")


@dataclass(slots=True)
class WindowState:
    width: int = 960
    height: int = 620
    x: int | None = None
    y: int | None = None


@dataclass(slots=True)
class AppState:
    presets: list[Preset] = field(default_factory=list)
    selected_preset_id: str | None = None
    window: WindowState = field(default_factory=WindowState)
    close_to_tray: bool = True
    minimize_to_tray: bool = False
    sidebar_hotkey: str = "Ctrl+Shift+Space"
    language: str = "en"


class SettingsStore:
    def __init__(self) -> None:
        base_folder = os.environ.get("LOCALAPPDATA")
        if not base_folder:
            base_folder = str(Path.home() / "AppData" / "Local")

        self.app_folder = Path(base_folder) / "HKI"
        self.settings_file = self.app_folder / "settings.json"

    def load(self) -> AppState:
        try:
            if not self.settings_file.exists():
                return AppState()

            payload = json.loads(self.settings_file.read_text(encoding="utf-8"))
            presets = [Preset(**entry) for entry in payload.get("presets", [])]
            window_payload = payload.get("window", {})

            return AppState(
                presets=presets,
                selected_preset_id=payload.get("selected_preset_id"),
                window=WindowState(
                    width=window_payload.get("width", 960),
                    height=window_payload.get("height", 620),
                    x=window_payload.get("x"),
                    y=window_payload.get("y"),
                ),
                close_to_tray=payload.get("close_to_tray", True),
                minimize_to_tray=payload.get("minimize_to_tray", False),
                sidebar_hotkey=payload.get("sidebar_hotkey", "Ctrl+Shift+Space"),
                language=payload.get("language", "en"),
            )
        except Exception:
            return AppState()

    def save(self, state: AppState) -> None:
        self.app_folder.mkdir(parents=True, exist_ok=True)
        payload = asdict(state)
        self.settings_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
