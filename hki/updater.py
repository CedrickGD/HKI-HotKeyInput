"""Silent auto-updater — checks update.xml once per session, applies on close."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from urllib.request import urlopen, Request
from xml.etree import ElementTree

from hki.storage import VERSION

log = logging.getLogger(__name__)

# ── configuration ─────────────────────────────────────────────────────
# Raw URL to update.xml in the repo (main branch)
UPDATE_XML_URL = (
    "https://raw.githubusercontent.com/CedrickGD/HKI-HotKeyInput/main/update.xml"
)
REQUEST_TIMEOUT = 10  # seconds


def _is_frozen() -> bool:
    """True when running as a PyInstaller .exe."""
    return getattr(sys, "frozen", False)


def _exe_path() -> Path:
    """Path to the currently running .exe."""
    return Path(sys.executable)


def _version_tuple(v: str) -> tuple[int, ...]:
    """'1.2.3' → (1, 2, 3)"""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


# ── public API ────────────────────────────────────────────────────────

class UpdateInfo:
    __slots__ = ("remote_version", "download_url", "local_path")

    def __init__(self, remote_version: str, download_url: str) -> None:
        self.remote_version = remote_version
        self.download_url = download_url
        self.local_path: Path | None = None  # set after download completes


_pending: UpdateInfo | None = None


def check_for_update_async() -> None:
    """Kick off a background check. Call once at startup."""
    if not _is_frozen():
        return
    t = threading.Thread(target=_check_and_download, daemon=True)
    t.start()


def get_pending_update() -> UpdateInfo | None:
    """Return the downloaded update info, or None."""
    return _pending if (_pending and _pending.local_path) else None


def apply_pending_update() -> None:
    """Call during app shutdown to swap the exe. Silent, best-effort."""
    info = get_pending_update()
    if not info or not info.local_path:
        return
    exe = _exe_path()
    new = info.local_path

    # Strategy 1: rename-and-replace (works if exe isn't locked)
    old = exe.with_suffix(".old")
    try:
        if old.exists():
            old.unlink()
        exe.rename(old)
        new.rename(exe)
        # Clean up .old in background
        _spawn_cleanup(old)
        return
    except OSError:
        # Restore if partial failure
        try:
            if not exe.exists() and old.exists():
                old.rename(exe)
        except OSError:
            pass

    # Strategy 2: hidden cmd script waits for process exit, then replaces
    _spawn_replace_script(exe, new, old)


# ── internals ─────────────────────────────────────────────────────────

def _check_and_download() -> None:
    global _pending
    try:
        req = Request(UPDATE_XML_URL, headers={"User-Agent": f"HKI/{VERSION}"})
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            xml = resp.read()
        root = ElementTree.fromstring(xml)
        remote_ver = (root.findtext("version") or "").strip()
        download_url = (root.findtext("url") or "").strip()
        if not remote_ver or not download_url:
            return
        if _version_tuple(remote_ver) <= _version_tuple(VERSION):
            return

        # Newer version available — download to temp
        info = UpdateInfo(remote_ver, download_url)
        tmp = Path(tempfile.gettempdir()) / f"HKI_update_{remote_ver}.exe"
        req2 = Request(download_url, headers={"User-Agent": f"HKI/{VERSION}"})
        with urlopen(req2, timeout=60) as resp2:
            tmp.write_bytes(resp2.read())
        info.local_path = tmp
        _pending = info
    except Exception:
        log.debug("Update check failed", exc_info=True)


def _spawn_cleanup(old: Path) -> None:
    """Delete the .old file after a short delay via a hidden cmd."""
    try:
        script = f'@ping -n 3 127.0.0.1 >nul & del "{old}" 2>nul'
        subprocess.Popen(
            ["cmd.exe", "/c", script],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            close_fds=True,
        )
    except OSError:
        pass


def _spawn_replace_script(exe: Path, new: Path, old: Path) -> None:
    """Fallback: hidden cmd waits for HKI to exit, then swaps files."""
    pid = os.getpid()
    script = (
        f'@echo off\n'
        f':wait\n'
        f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul\n'
        f'if not errorlevel 1 (ping -n 2 127.0.0.1 >nul & goto wait)\n'
        f'if exist "{old}" del "{old}"\n'
        f'move "{exe}" "{old}" >nul 2>&1\n'
        f'move "{new}" "{exe}" >nul 2>&1\n'
        f'if exist "{old}" (ping -n 3 127.0.0.1 >nul & del "{old}" 2>nul)\n'
        f'del "%~f0" 2>nul\n'
    )
    script_path = Path(tempfile.gettempdir()) / "hki_update.cmd"
    script_path.write_text(script, encoding="utf-8")
    try:
        subprocess.Popen(
            ["cmd.exe", "/c", str(script_path)],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            close_fds=True,
        )
    except OSError:
        pass
