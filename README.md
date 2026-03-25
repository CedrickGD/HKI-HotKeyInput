# HKI — HotKey Input

A lightweight Windows utility for managing and pasting preset text snippets via global hotkeys. Assign keyboard shortcuts to frequently used texts, and HKI pastes them into any focused input field instantly.

## Features

- **Preset management** — Create, edit, duplicate, and organize text presets
- **Global hotkeys** — Assign system-wide keyboard shortcuts to any preset (e.g. `Ctrl+3`)
- **Quick-paste sidebar** — A floating overlay (`Ctrl+Shift+Space` by default) for fast preset selection
- **System tray integration** — Minimize to tray and keep hotkeys active in the background
- **Multi-language** — English and German UI
- **No admin rights required** — Installs per-user, no elevated permissions needed
- **Portable** — Can also run standalone without installation

## Installation

### Option 1: Download and Install

1. Download the latest release (`HKI.exe`, `Install-HKI.cmd`, `Uninstall-HKI.cmd`)
2. Place all files in a permanent folder
3. Run `Install-HKI.cmd` — this creates a Start Menu shortcut so HKI appears in Windows Search

After installation, search for **HKI** in the Windows Start menu to launch.

### Option 2: Portable Use

Run `HKI.exe` directly from any folder. No installation required — hotkeys and presets work immediately.

### Tray Mode

To start HKI minimized to the system tray:

```
HKI.exe --tray
```

## Uninstallation

Run `Uninstall-HKI.cmd`. This removes:

- The Start Menu shortcut
- Application data (`%LOCALAPPDATA%\HKI`)
- All application files (HKI.exe, Install-HKI.cmd)
- The uninstaller itself

## Building from Source

Requires Python 3.10+ and the project dependencies.

```bash
pip install -r requirements.txt
```

Run the build script:

```
BUILD.bat
```

This produces a `release/` folder containing:

| File | Purpose |
|---|---|
| `HKI.exe` | Standalone application |
| `Install-HKI.cmd` | Start Menu shortcut installer |
| `Uninstall-HKI.cmd` | Complete uninstaller |

### Developer Run (without building)

```bash
pythonw hki_app.pyw
pythonw hki_app.pyw --tray
```

## Data Storage

All settings and presets are stored in:

```
%LOCALAPPDATA%\HKI\settings.json
```

No registry entries, no system-level changes.

## License

See [LICENSE](LICENSE) for details.
