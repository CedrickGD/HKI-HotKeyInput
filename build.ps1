$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$spinner = @('|','/','-','\')

function Spin-Line($prefix, $text, $si) {
    $s = $spinner[$si % $spinner.Length]
    $short = if ($text.Length -gt 54) { $text.Substring(0,54) + "..." } else { $text }
    $line = "  $prefix $s $short"
    $pad = " " * [math]::Max(0, 78 - $line.Length)
    Write-Host "`r$line$pad" -ForegroundColor Yellow -NoNewline
}

# ── Header ────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  HKI Build" -ForegroundColor Cyan
Write-Host "  =========" -ForegroundColor DarkGray
Write-Host ""

# ── 1  Python ─────────────────────────────────────────────────────────

Write-Host "  [1/5]  " -ForegroundColor DarkGray -NoNewline
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python not found" -ForegroundColor Red
    exit 1
}
$pyVer = (& python --version 2>&1).ToString().Trim()
Write-Host "$pyVer" -ForegroundColor Green -NoNewline
Write-Host "  ($($py.Source))" -ForegroundColor DarkGray

# ── 2  Dependencies ──────────────────────────────────────────────────

Write-Host "  [2/5]  " -ForegroundColor DarkGray -NoNewline

$depCheck = & python -c "
import sys
pkgs = {}
try:
    import PySide6; pkgs['PySide6'] = PySide6.__version__
except ImportError: pass
try:
    import PIL; pkgs['Pillow'] = PIL.__version__
except ImportError: pass
try:
    import PyInstaller; pkgs['PyInstaller'] = PyInstaller.__version__
except ImportError: pass
if len(pkgs) == 3:
    print('OK|' + '  '.join(f'{k} {v}' for k,v in pkgs.items()))
else:
    missing = [p for p in ('PySide6','Pillow','PyInstaller') if p not in pkgs]
    print('NEED|' + ','.join(missing))
" 2>&1
$depStatus = "$depCheck".Trim()

if ($depStatus.StartsWith("OK|")) {
    $versions = $depStatus.Substring(3)
    Write-Host "All installed" -ForegroundColor Green -NoNewline
    Write-Host "  ($versions)" -ForegroundColor DarkGray
} else {
    $missing = $depStatus.Substring(5)
    Write-Host "Installing ($missing)..." -ForegroundColor Yellow
    $si = 0
    & python -m pip install -r requirements.txt 2>&1 | ForEach-Object {
        $l = "$_".Trim()
        $si++
        if ($l -match "^(Collecting|Downloading|Installing|Building|Using cached)") {
            Spin-Line "[2/5] " $l $si
        }
    }
    Write-Host "`r  [2/5]  Dependencies installed                                              " -ForegroundColor Green
}

# ── 3  Build ──────────────────────────────────────────────────────────

foreach ($dir in @("build","dist","release")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
}
if (Test-Path HKI.spec) { Remove-Item HKI.spec -Force }
New-Item release -ItemType Directory -Force | Out-Null

$buildStart = $sw.Elapsed
$si = 0
$phase = "Starting"

$ErrorActionPreference = "Continue"
& python -m PyInstaller --noconfirm --clean --windowed --onefile `
    --name HKI --icon "assets\hki.ico" --add-data "assets;assets" `
    --distpath release hki_app.pyw 2>&1 | ForEach-Object {
    $l = "$_".Trim()
    $si++
    if ($l -match "INFO:\s+(.+)") {
        $raw = $Matches[1]
        if     ($raw -match "^Analyzing")        { $phase = "Analyzing imports" }
        elseif ($raw -match "module hook")        { $phase = "Processing module hooks" }
        elseif ($raw -match "hidden import")      { $phase = "Resolving hidden imports" }
        elseif ($raw -match "^Looking for")       { $phase = "Scanning dynamic libs" }
        elseif ($raw -match "^Processing")        { $phase = "Processing resources" }
        elseif ($raw -match "^Building PYZ")      { $phase = "Compiling bytecode (PYZ)" }
        elseif ($raw -match "^Building PKG")      { $phase = "Packaging (PKG)" }
        elseif ($raw -match "^Building EXE")      { $phase = "Creating HKI.exe" }
        elseif ($raw -match "^Appending PKG")     { $phase = "Finalizing executable" }
        elseif ($raw -match "^Copying icon")      { $phase = "Embedding icon" }
    }
    $elapsed = [math]::Floor(($sw.Elapsed - $buildStart).TotalSeconds)
    Spin-Line "[3/5] " "$phase  (${elapsed}s)" $si
}

$ErrorActionPreference = "Stop"
$buildSecs = [math]::Round(($sw.Elapsed - $buildStart).TotalSeconds, 1)

if (-not (Test-Path "release\HKI.exe")) {
    Write-Host ""
    Write-Host "  [FAIL] Build failed." -ForegroundColor Red
    exit 1
}

$exeSize = [math]::Round((Get-Item "release\HKI.exe").Length / 1MB, 1)
Write-Host "`r  [3/5]  HKI.exe built" -ForegroundColor Green -NoNewline
Write-Host "  (${exeSize} MB in ${buildSecs}s)                                    " -ForegroundColor DarkGray

# ── 4  Clean ──────────────────────────────────────────────────────────

Write-Host "  [4/5]  " -ForegroundColor DarkGray -NoNewline
foreach ($dir in @("build","dist")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
}
if (Test-Path HKI.spec) { Remove-Item HKI.spec -Force }
Write-Host "Cleaned build artifacts" -ForegroundColor Green

# ── 5  Scripts ────────────────────────────────────────────────────────

Write-Host "  [5/5]  " -ForegroundColor DarkGray -NoNewline

@'
@echo off
set "EXE=%~dp0HKI.exe"
if not exist "%EXE%" (
    echo ERROR: HKI.exe not found next to this script.
    pause
    exit /b 1
)
echo.
echo   Installing HKI...
echo.
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\HKI.lnk"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%SHORTCUT%'); $sc.TargetPath = '%EXE%'; $sc.WorkingDirectory = '%~dp0'; $sc.IconLocation = '%EXE%,0'; $sc.Description = 'HKI - HotKey Input'; $sc.Save()"
echo.
if exist "%SHORTCUT%" (
    echo   Done! HKI is now searchable in Windows Search.
) else (
    echo   ERROR: Failed to create shortcut.
)
echo.
pause
exit /b 0
'@ | Set-Content "release\Install-HKI.cmd" -Encoding ASCII

@'
@echo off
echo.
echo   Uninstalling HKI...
echo.
taskkill /F /IM HKI.exe 2>nul
timeout /t 2 /nobreak >nul
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\HKI.lnk" 2>nul
rmdir /s /q "%LOCALAPPDATA%\HKI" 2>nul
set "APPDIR=%~dp0"
echo.
echo   Done! HKI has been fully uninstalled.
echo.
pause
start "" /b cmd /c timeout /t 1 /nobreak & rmdir /s /q "%APPDIR%"
exit
'@ | Set-Content "release\Uninstall-HKI.cmd" -Encoding ASCII

Write-Host "Created install & uninstall scripts" -ForegroundColor Green

# ── Summary ───────────────────────────────────────────────────────────

$totalSecs = [math]::Round($sw.Elapsed.TotalSeconds, 1)
Write-Host ""
Write-Host "  -----------------------------------------" -ForegroundColor DarkGray
Write-Host "  Done in ${totalSecs}s" -ForegroundColor Green -NoNewline
Write-Host "  ->  release/" -ForegroundColor DarkGray
Write-Host ""
Get-ChildItem release | ForEach-Object {
    $sz = if ($_.Length -gt 1MB) { "$([math]::Round($_.Length/1MB,1)) MB" }
          else { "$([math]::Round($_.Length/1KB,1)) KB" }
    Write-Host "    $($_.Name.PadRight(25)) $sz" -ForegroundColor DarkGray
}
Write-Host ""
