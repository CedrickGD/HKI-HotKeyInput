$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
$releaseRoot = Join-Path $repoRoot "release"
$packageRoot = Join-Path $releaseRoot "HKI-package"
$zipPath = Join-Path $releaseRoot "HKI-win-x64.zip"

& (Join-Path $repoRoot "build.ps1")

if (Test-Path $packageRoot) {
    Remove-Item -Recurse -Force $packageRoot
}

New-Item -ItemType Directory -Force $packageRoot | Out-Null

Copy-Item -Path (Join-Path $repoRoot "dist\\HKI\\*") -Destination $packageRoot -Recurse -Force
Copy-Item -Path (Join-Path $repoRoot "Install-HKI.ps1") -Destination (Join-Path $packageRoot "Install-HKI.ps1") -Force
Copy-Item -Path (Join-Path $repoRoot "Install-HKI.cmd") -Destination (Join-Path $packageRoot "Install-HKI.cmd") -Force

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path (Join-Path $packageRoot "*") -DestinationPath $zipPath

Write-Output "Created release package: $zipPath"
