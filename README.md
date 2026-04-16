# HKI — HotKey Input

A lightweight Windows utility for managing and pasting preset text snippets via global hotkeys. Assign keyboard shortcuts to frequently used texts, and HKI pastes them into any focused input field instantly.

Built with **Tauri 2 + React + TypeScript + Rust** — native Win32 hotkeys and clipboard, a modern React UI, and a ~12 MB self-contained `.exe` with no external runtime.

## Features

- **Preset management** — create, edit, duplicate, and reorder text snippets (drag handle on hover)
- **Global hotkeys** — assign any Ctrl/Alt/Shift/Win combination; Rust registers the shortcut with the OS and pastes via `SendInput`
- **Summon hotkey** — configurable shortcut that brings HKI to the front from anywhere
- **Placeholders** — write `{name}`, `{date}`, `{time}` etc. tokens in your text; the Edit/Preview tab lets you see resolved output
- **Hotkey conflict detection** — two presets on the same combo show an inline amber warning
- **Command palette** — `Ctrl+K` for fuzzy-search across presets, paste actions, theme, settings
- **Import / Export** — `.hki` JSON files via native file dialogs; imports get fresh IDs and reset hotkeys to avoid collisions
- **Dark / light theme** — animated moon ↔ sun toggle, honours `prefers-color-scheme` on first run
- **Accent colour** — 10 curated swatches plus a native colour picker and hex input; accent colour persists
- **Resizable sidebar** — drag the divider to set your width (220–520 px), persisted to localStorage
- **System tray** — close-to-tray and optional minimise-to-tray, keeps hotkeys active in the background
- **Multi-language** — English and German settings (UI localisation coming)
- **No admin rights required** — installs per-user, no elevated permissions needed
- **Portable** — `HKI.exe` runs standalone without any installer

## Installation

1. Grab `HKI.exe` from the release
2. Put it in a permanent folder (anywhere — it's portable)
3. Run it. Hotkeys and presets work immediately.

To make HKI searchable from the Windows Start menu, open **Settings → Installation → Add to Start Menu**. The shortcut points to wherever `HKI.exe` currently lives.

## Uninstallation

Open **Settings → Installation → Uninstall** (double-click to confirm). HKI removes:

- The Start Menu shortcut
- All settings + presets under `%LOCALAPPDATA%\HKI`

…then quits. The `HKI.exe` file itself is left in place — delete it manually.

## Data Storage

Presets and settings live in:

```
%LOCALAPPDATA%\HKI\presets.json
%LOCALAPPDATA%\HKI\settings.json
```

Both are plain JSON, safe to inspect or edit by hand. No registry entries, no system-level changes.

## Keyboard shortcuts (main window)

| Shortcut | Action |
|---|---|
| `Ctrl+K` | Command palette |
| `Ctrl+F` | Focus search |
| `Ctrl+N` | New preset |
| `Ctrl+D` | Duplicate current preset |
| `Ctrl+Shift+Backspace` | Delete current preset |
| `↑` / `↓` | Navigate preset list |

(Preset-manipulation shortcuts are suppressed while typing in a text field, so they don't hijack your editor caret.)

## Building from source

### Prerequisites

- **Node.js** 20 LTS or newer — <https://nodejs.org/>
- **Rust + Cargo** (stable) — <https://rustup.rs/>
- **Visual Studio 2022 BuildTools** with the "Desktop development with C++" workload, for the MSVC linker. `BUILD.bat` will auto-import `vcvars64.bat` when it finds one.

### Build

Double-click **`BUILD.bat`** in the repo root. That's it. The builder is a single self-extracting batch file: it embeds its own PowerShell and runs it from a temp file, so there's no separate `.ps1` to invoke.

Stages:

```
[1/5]  Toolchain check (Node + Cargo)
[2/5]  Frontend dependencies (npm install if needed)
[3/5]  Type-check + ESLint (zero-warning policy)
[4/5]  Tauri release build (cargo + Vite)
[5/5]  Code signing (if a matching cert exists)
```

Output lands in `release/`:

| File | Purpose |
|---|---|
| `HKI.exe` | Standalone, self-contained application (~12 MB) |
| `HKI-Setup.exe` | NSIS installer, only when `tauri.conf.json > bundle.targets` includes `nsis` |

Install and uninstall are handled from **inside the app**, under `Settings → Installation`.

### Developer run (hot reload)

```
cd app
npm install
npm run tauri dev
```

This runs Vite's dev server and Tauri with live reload on both the frontend and Rust backend (the latter recompiles on save).

## Code signing

`BUILD.bat` has an optional `[5/6] Code signing` stage that mirrors the VaultX setup:

```powershell
Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
  Where-Object { $_.Subject -match "HKI" -and $_.NotAfter -gt (Get-Date) } |
  Sort-Object NotAfter -Descending | Select-Object -First 1
```

If a certificate is found, both `release\HKI.exe` and `release\HKI-Setup.exe` (when present) are signed with SHA-256 and timestamped via `http://timestamp.digicert.com`. Otherwise the step prints a yellow notice and skips.

### Create a self-signed cert (one-time)

In PowerShell:

```powershell
New-SelfSignedCertificate `
  -Subject "CN=HKI, E=business.grabe@gmail.com, O=Cedrick Grabe" `
  -Type CodeSigningCert `
  -KeyUsage DigitalSignature `
  -KeyAlgorithm RSA `
  -KeyLength 2048 `
  -NotAfter (Get-Date).AddYears(5) `
  -CertStoreLocation "Cert:\CurrentUser\My"
```

Next `BUILD.bat` picks it up automatically.

> Self-signed certs still show **Unknown Publisher** on other machines. To avoid SmartScreen warnings on your own machine, open the certificate from `Cert:\CurrentUser\My`, *Copy to File…*, and import it into **Trusted Root Certification Authorities** under `Cert:\CurrentUser\Root`. For public distribution you'd need a proper EV/OV code-signing certificate from a CA.

## Project layout

```
.
├─ BUILD.bat              # self-extracting build script (batch + embedded PowerShell)
├─ app/                   # Tauri project root
│  ├─ src/                # React + TypeScript frontend
│  │  ├─ components/      # UI components (preset list, editor, palette, dialogs)
│  │  ├─ lib/             # backend wrapper, toast store, resizer hook, utils
│  │  ├─ theme/           # theme provider, context, hook
│  │  └─ types.ts         # Preset + Placeholder types
│  ├─ src-tauri/          # Rust backend
│  │  ├─ src/             # commands, hotkeys, paste, storage, tray, lib.rs
│  │  ├─ capabilities/    # Tauri v2 permission scopes
│  │  └─ tauri.conf.json  # window, CSP, bundle config
│  └─ package.json
├─ assets/                # Source logo (hki.png / hki.ico)
├─ hki/                   # Legacy Python implementation (reference only, not built)
└─ release/               # Build output
```

## License

See [LICENSE](LICENSE) for details.
