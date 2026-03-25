$ErrorActionPreference = "Stop"

$startupFolder = [Environment]::GetFolderPath("Startup")
$projectRoot = Split-Path $PSScriptRoot -Parent
$launcher = Join-Path $PSScriptRoot "start-hki-tray.vbs"
$shortcutPath = Join-Path $startupFolder "HKI Tray.lnk"
$iconPath = Join-Path $projectRoot "assets\hki.ico"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $projectRoot
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Save()

Write-Output "Created startup shortcut: $shortcutPath"
