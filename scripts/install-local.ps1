param(
    [string]$AppSource = "",
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

$repoRoot = Split-Path $PSScriptRoot -Parent
if (-not $AppSource) {
    $releaseSource = Join-Path $PSScriptRoot "..\\release\\HKI-package\\app"
    $distSource = Join-Path $repoRoot "dist\\HKI"
    if (Test-Path $releaseSource) {
        $AppSource = $releaseSource
    } else {
        $AppSource = $distSource
    }
}

$AppSource = [IO.Path]::GetFullPath($AppSource)
if (-not (Test-Path (Join-Path $AppSource "HKI.exe"))) {
    throw "HKI.exe not found in '$AppSource'. Build or package the app first."
}

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

Copy-Item -Path (Join-Path $AppSource "*") -Destination $installRoot -Recurse -Force

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
Write-Output "Windows Search entry created in $startMenuFolder"

if ($StartAfterInstall) {
    Start-Process -FilePath $exePath -WorkingDirectory $installRoot
}
