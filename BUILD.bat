@echo off
title HKI Builder
echo.
echo  HKI Builder
echo  ===========
echo.
where pwsh >nul 2>&1
if %errorlevel%==0 (set "PS=pwsh") else (set "PS=powershell")
set "HKI_BUILD_DIR=%~dp0"
set "T=%TEMP%\hki-build-%RANDOM%.ps1"
%PS% -NoProfile -Command "$s=(Get-Content -LiteralPath '%~f0' -Raw) -split '#>\r?\n',2; Set-Content -LiteralPath '%T%' -Value $s[1] -NoNewline"
%PS% -NoProfile -ExecutionPolicy Bypass -File "%T%"
del "%T%" 2>nul
pause
exit /b
<#
#>

$ErrorActionPreference = "Stop"

$root = $env:HKI_BUILD_DIR
if ($root) { $root = $root.TrimEnd('\') }
if ([string]::IsNullOrWhiteSpace($root) -or -not (Test-Path $root)) {
    $root = $PWD.Path
}
Set-Location $root

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$spinner = @('|','/','-','\')

# --- MSVC environment bootstrap --------------------------------------
# cc-rs / cargo need LIB / INCLUDE / PATH for the MSVC toolchain. On some
# machines a stripped onecore install gets picked first and fails to link
# (no kernel32.lib / no headers). Import vars from VS 2022 BuildTools
# vcvars64.bat when the real toolchain is missing from env.

function Import-VcVars {
    if ($env:LIB -and $env:INCLUDE -and ($env:INCLUDE -match "MSVC")) { return }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    )
    $vcvars = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $vcvars) {
        Write-Host "  vcvars64.bat not found - cargo may fail to link." -ForegroundColor Yellow
        return
    }
    $cmdline = '"' + $vcvars + '" >NUL & set'
    $dumped = & cmd /c $cmdline
    foreach ($line in $dumped) {
        if ($line -match '^([^=]+)=(.*)$') {
            Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
        }
    }
}

function Spin-Line($prefix, $text, $si) {
    $s = $spinner[$si % $spinner.Length]
    $short = if ($text.Length -gt 54) { $text.Substring(0,54) + "..." } else { $text }
    $line = "  $prefix $s $short"
    $pad = " " * [math]::Max(0, 78 - $line.Length)
    Write-Host "`r$line$pad" -ForegroundColor Yellow -NoNewline
}

try {

    # --- Header -----------------------------------------------------

    Write-Host ""
    Write-Host "  HKI Build (Tauri + React)" -ForegroundColor Cyan
    Write-Host "  =========================" -ForegroundColor DarkGray
    Write-Host ""

    # --- 1  Toolchain check -----------------------------------------

    Import-VcVars

    Write-Host "  [1/5]  " -ForegroundColor DarkGray -NoNewline
    $node = Get-Command node -ErrorAction SilentlyContinue
    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    if (-not $node) {
        Write-Host "Node.js not found" -ForegroundColor Red
        Write-Host "         Install from https://nodejs.org/ (LTS)" -ForegroundColor DarkGray
        exit 1
    }
    if (-not $cargo) {
        Write-Host "Rust/Cargo not found" -ForegroundColor Red
        Write-Host "         Install from https://rustup.rs/" -ForegroundColor DarkGray
        exit 1
    }
    $nodeVer = (& node --version 2>&1).ToString().Trim()
    $cargoVer = ((& cargo --version 2>&1).ToString().Trim() -split ' ')[1]
    Write-Host "Node $nodeVer" -ForegroundColor Green -NoNewline
    Write-Host "  Cargo $cargoVer" -ForegroundColor DarkGray

    # --- 2  Frontend deps -------------------------------------------

    Write-Host "  [2/5]  " -ForegroundColor DarkGray -NoNewline
    Set-Location "$root\app"

    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm deps..." -ForegroundColor Yellow
        $si = 0
        & npm install 2>&1 | ForEach-Object {
            $si++
            $l = "$_".Trim()
            if ($l -match "^(added|removed|changed|npm warn|npm notice)") {
                Spin-Line "[2/5] " $l $si
            }
        }
        Write-Host "`r  [2/5]  npm install done                                                      " -ForegroundColor Green
    } else {
        $pkgCount = (Get-ChildItem "node_modules" -Directory -ErrorAction SilentlyContinue).Count
        Write-Host "Dependencies ready" -ForegroundColor Green -NoNewline
        Write-Host ("  ({0} packages)" -f $pkgCount) -ForegroundColor DarkGray
    }

    # --- 3  Type-check + lint ---------------------------------------

    Write-Host "  [3/5]  " -ForegroundColor DarkGray -NoNewline
    $si = 0
    Spin-Line "[3/5] " "Type-check + lint" $si

    $tscOut = & npx tsc -b 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`r  [3/5]  Type-check failed                                                    " -ForegroundColor Red
        $tscOut | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
        exit 1
    }

    $eslintOut = & npx eslint . --max-warnings 0 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`r  [3/5]  Lint failed (zero-warning policy)                                    " -ForegroundColor Red
        $eslintOut | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
        exit 1
    }

    Write-Host "`r  [3/5]  Type-check + lint clean                                              " -ForegroundColor Green

    # --- 4  Tauri build (release) -----------------------------------

    New-Item "$root\release" -ItemType Directory -Force | Out-Null
    # Kill any running HKI.exe / app.exe so Windows releases the file
    # lock before we try to replace it.
    Get-Process -Name 'HKI','app' -ErrorAction SilentlyContinue | ForEach-Object {
        try { $_ | Stop-Process -Force -ErrorAction Stop } catch { }
    }
    Start-Sleep -Milliseconds 300
    # Clear release/ contents (leaves the directory itself alone in
    # case it is open in Explorer or held by another process's cwd).
    Get-ChildItem "$root\release" -Force | ForEach-Object {
        try {
            Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop
        } catch {
            Write-Host "  Could not remove $($_.Name): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    $buildStart = $sw.Elapsed
    $si = 0
    $phase = "Starting"

    $ErrorActionPreference = "Continue"
    & npx tauri build 2>&1 | ForEach-Object {
        $l = "$_".Trim()
        $si++
        if     ($l -match "Compiling\s+(\S+)")        { $phase = "Compiling " + $Matches[1] }
        elseif ($l -match "^Building")                 { $phase = "Building frontend" }
        elseif ($l -match "building for production")   { $phase = "Bundling Vite assets" }
        elseif ($l -match "Finished")                  { $phase = "Finished compilation" }
        elseif ($l -match "Running.*build command")    { $phase = "Running build" }
        elseif ($l -match "bundling")                  { $phase = "Packaging installer" }
        elseif ($l -match "Warning")                   { $phase = "Warning (see final output)" }
        elseif ($l -match "error\[")                   { $phase = "Compilation error" }
        $elapsedSecs = [math]::Floor(($sw.Elapsed - $buildStart).TotalSeconds)
        Spin-Line "[4/5] " ("{0}  ({1}s)" -f $phase, $elapsedSecs) $si
    }
    $tauriExitCode = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    $buildSecs = [math]::Round(($sw.Elapsed - $buildStart).TotalSeconds, 1)

    # Locate output exe
    $targetDir = "$root\app\src-tauri\target\release"
    $exe = $null
    foreach ($name in @("HKI.exe","hki.exe","app.exe")) {
        $candidate = Join-Path $targetDir $name
        if (Test-Path $candidate) { $exe = $candidate; break }
    }

    if ($tauriExitCode -ne 0 -or -not $exe) {
        Write-Host ""
        Write-Host "  [FAIL] Tauri build failed (exit $tauriExitCode)" -ForegroundColor Red
        exit 1
    }

    Copy-Item $exe "$root\release\HKI.exe" -Force

    # Also grab the NSIS installer if Tauri produced one
    $nsis = Get-ChildItem "$targetDir\bundle\nsis\*-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($nsis) { Copy-Item $nsis.FullName "$root\release\HKI-Setup.exe" -Force }

    $exeSize = [math]::Round((Get-Item "$root\release\HKI.exe").Length / 1MB, 1)
    Write-Host "`r  [4/5]  HKI.exe built" -ForegroundColor Green -NoNewline
    Write-Host ("  ({0} MB in {1}s)                                    " -f $exeSize, $buildSecs) -ForegroundColor DarkGray

    Set-Location $root

    # --- 5  Code signing --------------------------------------------
    # Find a valid code signing cert in the CurrentUser store whose
    # subject mentions "HKI" (self-signed is fine, as long as the cert
    # has the Code Signing EKU). Sign release\HKI.exe with a DigiCert
    # timestamp + SHA256, and also sign release\HKI-Setup.exe if an
    # NSIS installer was produced.

    Write-Host "  [5/5]  " -ForegroundColor DarkGray -NoNewline

    $signingCert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
        Where-Object { $_.Subject -match "HKI" -and $_.NotAfter -gt (Get-Date) } |
        Sort-Object NotAfter -Descending | Select-Object -First 1

    if ($signingCert) {
        $subject = ($signingCert.Subject -split ',')[0].Trim()
        Write-Host "Signing ($subject)" -ForegroundColor Green
        $targets = @("$root\release\HKI.exe")
        if (Test-Path "$root\release\HKI-Setup.exe") {
            $targets += "$root\release\HKI-Setup.exe"
        }
        foreach ($t in $targets) {
            try {
                $sig = Set-AuthenticodeSignature -FilePath $t -Certificate $signingCert `
                    -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm SHA256 -ErrorAction Stop
                $leaf = Split-Path $t -Leaf
                if ($sig.Status -eq "Valid") {
                    Write-Host ("         Signed and timestamped: {0}" -f $leaf) -ForegroundColor DarkGray
                } else {
                    Write-Host ("         Warning: {0} -> status '{1}'" -f $leaf, $sig.Status) -ForegroundColor Yellow
                }
            } catch {
                Write-Host ("         Signing failed for {0}: {1}" -f (Split-Path $t -Leaf), $_.Exception.Message) -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "No HKI code signing cert found in Cert:\CurrentUser\My" -ForegroundColor Yellow
        Write-Host "         (Subject must contain 'HKI' and not be expired.) Skipping." -ForegroundColor DarkGray
    }

    # --- Summary ----------------------------------------------------

    $totalSecs = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    Write-Host ""
    Write-Host "  -----------------------------------------" -ForegroundColor DarkGray
    Write-Host ("  Done in {0}s" -f $totalSecs) -ForegroundColor Green -NoNewline
    Write-Host "  ->  release/" -ForegroundColor DarkGray
    Write-Host ""
    Get-ChildItem "$root\release" | ForEach-Object {
        $sz = if ($_.Length -gt 1MB) { ("{0} MB" -f [math]::Round($_.Length/1MB,1)) }
              else { ("{0} KB" -f [math]::Round($_.Length/1KB,1)) }
        Write-Host ("    {0} {1}" -f $_.Name.PadRight(25), $sz) -ForegroundColor DarkGray
    }
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "BUILD FAILED: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}
