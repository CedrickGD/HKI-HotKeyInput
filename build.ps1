$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$barLen = 30
$total = 5
$spinner = @('|','/','-','\')

function Show-Progress($step, $label, $color) {
    $pct = [math]::Floor($step * 100 / $total)
    $filled = [math]::Floor($step * $barLen / $total)
    $empty = $barLen - $filled
    $bar = ("#" * $filled) + ("-" * $empty)
    $line = "  |$bar| $($pct.ToString().PadLeft(3))%  $label"
    $pad = " " * [math]::Max(0, 70 - $line.Length)
    Write-Host "`r$line$pad" -ForegroundColor $color -NoNewline
}

function Step-Done($step, $label) {
    Show-Progress $step $label "Green"
    Write-Host ""
}

function Run-WithSpinner($step, $label, $scriptBlock) {
    $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $root
    $i = 0
    while ($job.State -eq "Running") {
        $s = $spinner[$i % 4]
        Show-Progress $step "$label $s" "Yellow"
        Start-Sleep -Milliseconds 200
        $i++
    }
    $result = Receive-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job
}

Write-Host ""
Write-Host "  HKI Build" -ForegroundColor Cyan
Write-Host ""

# Step 1 - Python
Show-Progress 0 "Checking Python..." "Yellow"
Start-Sleep -Milliseconds 500
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host ""
    Write-Host "  [FAIL] Python not found." -ForegroundColor Red
    exit 1
}
Step-Done 1 "Python found"

# Step 2 - Dependencies
Run-WithSpinner 1 "Installing dependencies" {
    param($r)
    Set-Location $r
    & python -m pip install -r requirements.txt 2>&1 | Out-Null
}
Step-Done 2 "Dependencies installed"

# Step 3 - Build
foreach ($dir in @("build","dist","release")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
}
if (Test-Path HKI.spec) { Remove-Item HKI.spec -Force }
New-Item release -ItemType Directory | Out-Null

Run-WithSpinner 2 "Building HKI.exe" {
    param($r)
    Set-Location $r
    & python -m PyInstaller --noconfirm --clean --windowed --onefile --name HKI --icon "assets\hki.ico" --add-data "assets;assets" --distpath release hki_app.pyw 2>&1 | Out-Null
}

if (-not (Test-Path "release\HKI.exe")) {
    Write-Host ""
    Write-Host "  [FAIL] Build failed." -ForegroundColor Red
    exit 1
}
Step-Done 3 "HKI.exe built"

# Step 4 - Clean
Show-Progress 3 "Cleaning up..." "Yellow"
foreach ($dir in @("build","dist")) {
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
}
if (Test-Path HKI.spec) { Remove-Item HKI.spec -Force }
Start-Sleep -Milliseconds 300
Step-Done 4 "Artifacts cleaned"

# Step 5 - Scripts
Show-Progress 4 "Creating scripts..." "Yellow"

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

Start-Sleep -Milliseconds 300
Step-Done 5 "Scripts created"

Write-Host ""
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host ""
