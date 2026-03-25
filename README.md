# HKI

HKI is a small Windows helper for preset texts. A user opens the app normally, stores texts, assigns hotkeys like `Ctrl+3`, and HKI pastes the selected preset into the currently focused input field.

## For Colleagues

The simple install file is:

`Install-HKI.cmd`

Double-click it. It installs HKI into your own user profile without admin rights and adds HKI to the Windows Start menu / Windows search.

After that you can open:

- `HKI`
- `HKI Tray`
- `Uninstall HKI`

## Build A Release Package

```powershell
.\scripts\package-release.ps1
```

That creates:

`release\HKI-win-x64.zip`

`dist\` is not committed to git. On a fresh clone, run `.\build.ps1` to create `dist\HKI\HKI.exe`, or run `Install-HKI.cmd` and let it build the app first if needed.

When someone extracts that ZIP, they only need to run:

`Install-HKI.cmd`

If they do not want to install it, they can also start:

`HKI.exe`

## GitHub Install Command

If `raw.githubusercontent.com` is blocked by a company proxy, use the release download directly from `github.com`:

```powershell
$zip = Join-Path $env:TEMP 'HKI-win-x64.zip'; $dir = Join-Path $env:TEMP 'HKI-install'; Invoke-WebRequest 'https://github.com/CedrickGD/HKI/releases/latest/download/HKI-win-x64.zip' -OutFile $zip; if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }; Expand-Archive $zip -DestinationPath $dir -Force; & (Join-Path $dir 'Install-HKI.ps1') -StartAfterInstall
```

This avoids `raw.githubusercontent.com` completely.

If `github.com` downloads are blocked too, the fallback is:

1. open the release page in a browser
2. download `HKI-win-x64.zip`
3. unzip it
4. double-click `Install-HKI.cmd`

## Local Developer Run

```powershell
.\.venv\Scripts\pythonw.exe .\hki_app.pyw
```

Optional tray start:

```powershell
.\.venv\Scripts\pythonw.exe .\hki_app.pyw --tray
```

## Notes

- No admin rights required for install
- Data is stored in `%LocalAppData%\HKI\settings.json`
- The main app starts as a normal window
- `X` and minimize can send the window into the tray
