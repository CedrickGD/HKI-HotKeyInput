@echo off
:: ──────────────────────────────────────────────
::  Uninstall-HKI.cmd
::  Removes HKI completely:
::    - Start Menu shortcut
::    - App data (%LOCALAPPDATA%\HKI)
::    - All files in this folder (exe, scripts)
::  Run from the folder where HKI.exe lives.
:: ──────────────────────────────────────────────

echo.
echo   Uninstalling HKI...
echo.

:: Kill HKI if running
taskkill /F /IM HKI.exe >nul 2>&1

:: Remove Start Menu shortcut
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\HKI.lnk"
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo   [x] Start Menu shortcut removed
) else (
    echo   [ ] No Start Menu shortcut found
)

:: Remove app data
set "APPDATA_DIR=%LOCALAPPDATA%\HKI"
if exist "%APPDATA_DIR%" (
    rmdir /s /q "%APPDATA_DIR%"
    echo   [x] App data removed (%APPDATA_DIR%)
) else (
    echo   [ ] No app data found
)

:: Remove app files (exe + install script) from this folder
set "APPDIR=%~dp0"
if exist "%APPDIR%HKI.exe" (
    del "%APPDIR%HKI.exe"
    echo   [x] HKI.exe removed
)
if exist "%APPDIR%Install-HKI.cmd" (
    del "%APPDIR%Install-HKI.cmd"
    echo   [x] Install-HKI.cmd removed
)

echo.
echo   Done! HKI has been fully uninstalled.
echo   This script will delete itself on close.
echo.
pause

:: Self-delete
(goto) 2>nul & del "%~f0"
