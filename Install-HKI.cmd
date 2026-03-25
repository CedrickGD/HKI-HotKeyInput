@echo off
:: ──────────────────────────────────────────────
::  Install-HKI.cmd
::  Creates a Start Menu shortcut for HKI so
::  Windows Search can find it from anywhere.
::  Run once, from wherever HKI.exe lives.
:: ──────────────────────────────────────────────

set "EXE=%~dp0HKI.exe"
if not exist "%EXE%" (
    echo ERROR: HKI.exe not found next to this script.
    echo        Place Install-HKI.cmd in the same folder as HKI.exe.
    pause
    exit /b 1
)

echo.
echo   Installing HKI...
echo.

:: Step 1/3 — Verify files
call :progress 1 3 "Checking files"
timeout /t 1 /nobreak >nul

:: Step 2/3 — Create shortcut
call :progress 2 3 "Creating Start Menu shortcut"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\HKI.lnk"

powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$sc = $ws.CreateShortcut('%SHORTCUT%');" ^
    "$sc.TargetPath = '%EXE%';" ^
    "$sc.WorkingDirectory = '%~dp0';" ^
    "$sc.IconLocation = '%EXE%,0';" ^
    "$sc.Description = 'HKI - HotKey Input';" ^
    "$sc.Save()"

:: Step 3/3 — Done
call :progress 3 3 "Finishing up"
timeout /t 1 /nobreak >nul

echo.
if exist "%SHORTCUT%" (
    echo   [========================================] 100%%
    echo.
    echo   Done! HKI is now searchable in Windows Search.
    echo   Shortcut: %SHORTCUT%
) else (
    echo   ERROR: Failed to create shortcut.
)
echo.
pause
exit /b 0

:: ── progress bar subroutine ──────────────────
:progress
setlocal
set /a "step=%~1"
set /a "total=%~2"
set "label=%~3"
set /a "pct=step * 100 / total"
set /a "filled=step * 40 / total"
set /a "empty=40 - filled"
set "bar="
for /l %%i in (1,1,%filled%) do call set "bar=%%bar%%="
for /l %%i in (1,1,%empty%) do call set "bar=%%bar%% "
echo   [%bar%] %pct%%%  %label%
endlocal
goto :eof
