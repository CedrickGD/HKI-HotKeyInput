param(
    [switch]$StartAfterInstall
)

$ErrorActionPreference = "Stop"

function New-Shortcut {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = "",
        [string]$IconLocation = ""
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $TargetPath
    if ($Arguments) {
        $shortcut.Arguments = $Arguments
    }
    if ($WorkingDirectory) {
        $shortcut.WorkingDirectory = $WorkingDirectory
    }
    if ($IconLocation) {
        $shortcut.IconLocation = $IconLocation
    }
    $shortcut.Save()
}

function Stop-InstalledProcess {
    param([string]$InstallDir)

    $normalizedInstallDir = [IO.Path]::GetFullPath($InstallDir)
    $processes = Get-CimInstance Win32_Process -Filter "Name = 'HKI.exe'" -ErrorAction SilentlyContinue
    foreach ($process in $processes) {
        if (-not $process.ExecutablePath) {
            continue
        }

        $normalizedExePath = [IO.Path]::GetFullPath($process.ExecutablePath)
        if ($normalizedExePath.StartsWith($normalizedInstallDir, [System.StringComparison]::OrdinalIgnoreCase)) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
}

function Resolve-AppSource {
    param([Parameter(Mandatory = $true)][string]$ScriptRoot)

    if (Test-Path (Join-Path $ScriptRoot "HKI.exe")) {
        return $ScriptRoot
    }

    $distSource = Join-Path $ScriptRoot "dist\\HKI"
    if (Test-Path (Join-Path $distSource "HKI.exe")) {
        return $distSource
    }

    $buildScript = Join-Path $ScriptRoot "build.ps1"
    $appEntry = Join-Path $ScriptRoot "hki_app.pyw"
    if ((Test-Path $buildScript) -and (Test-Path $appEntry)) {
        Write-Host "HKI.exe was not found. Building from source..."
        & $buildScript
        if ($LASTEXITCODE -ne 0) {
            throw "Building HKI from source failed."
        }

        if (Test-Path (Join-Path $distSource "HKI.exe")) {
            return $distSource
        }
    }

    throw "HKI.exe was not found next to Install-HKI.ps1. Use the packaged release or build the app first."
}

$scriptRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
$appSource = Resolve-AppSource -ScriptRoot $scriptRoot

$appSource = [IO.Path]::GetFullPath($appSource)
$installRoot = Join-Path $env:LOCALAPPDATA "Programs\\HKI"
$startMenuFolder = Join-Path $env:APPDATA "Microsoft\\Windows\\Start Menu\\Programs\\HKI"
$trayLauncherPath = Join-Path $installRoot "HKI Tray.vbs"
$uninstallScriptPath = Join-Path $installRoot "uninstall.ps1"

Stop-InstalledProcess -InstallDir $installRoot

if (Test-Path $installRoot) {
    Remove-Item -Recurse -Force $installRoot
}

New-Item -ItemType Directory -Force $installRoot | Out-Null
New-Item -ItemType Directory -Force $startMenuFolder | Out-Null

Copy-Item -Path (Join-Path $appSource "*") -Destination $installRoot -Recurse -Force

$trayLauncherContent = @'
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptFolder = fso.GetParentFolderName(WScript.ScriptFullName)
appPath = scriptFolder & "\HKI.exe"
If fso.FileExists(appPath) Then
    shell.Run """" & appPath & """ --tray", 0, False
Else
    MsgBox "HKI.exe was not found.", vbExclamation, "HKI"
End If
'@
$trayLauncherContent | Set-Content -Path $trayLauncherPath -Encoding ASCII

$uninstallScriptContent = @"
`$ErrorActionPreference = 'Stop'
`$installRoot = '$installRoot'
`$startMenuFolder = '$startMenuFolder'

`$processes = Get-CimInstance Win32_Process -Filter "Name = 'HKI.exe'" -ErrorAction SilentlyContinue
foreach (`$process in `$processes) {
    if (`$process.ExecutablePath -and [IO.Path]::GetFullPath(`$process.ExecutablePath).StartsWith([IO.Path]::GetFullPath(`$installRoot), [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Process -Id `$process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path `$startMenuFolder) {
    Remove-Item -Recurse -Force `$startMenuFolder
}
if (Test-Path `$installRoot) {
    Remove-Item -Recurse -Force `$installRoot
}
Write-Output 'HKI was removed from this user profile.'
"@
$uninstallScriptContent | Set-Content -Path $uninstallScriptPath -Encoding UTF8

$exePath = Join-Path $installRoot "HKI.exe"
$iconLocation = "$exePath,0"

New-Shortcut -Path (Join-Path $startMenuFolder "HKI.lnk") `
    -TargetPath $exePath `
    -WorkingDirectory $installRoot `
    -IconLocation $iconLocation

New-Shortcut -Path (Join-Path $startMenuFolder "HKI Tray.lnk") `
    -TargetPath $trayLauncherPath `
    -WorkingDirectory $installRoot `
    -IconLocation $iconLocation

New-Shortcut -Path (Join-Path $startMenuFolder "Uninstall HKI.lnk") `
    -TargetPath "powershell.exe" `
    -Arguments "-ExecutionPolicy Bypass -File `"$uninstallScriptPath`"" `
    -WorkingDirectory $installRoot `
    -IconLocation $iconLocation

Write-Output "HKI installed to $installRoot"
Write-Output "Use Windows Search for: HKI"

if ($StartAfterInstall) {
    Start-Process -FilePath $exePath -WorkingDirectory $installRoot
}
