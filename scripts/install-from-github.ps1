param(
    [Parameter(Mandatory = $true)][string]$Repo,
    [string]$Tag = "latest",
    [string]$AssetName = "HKI-win-x64.zip",
    [switch]$StartAfterInstall
)

$ErrorActionPreference = "Stop"

if ($Tag -eq "latest") {
    $releaseApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
} else {
    $releaseApiUrl = "https://api.github.com/repos/$Repo/releases/tags/$Tag"
}

$headers = @{
    "User-Agent" = "HKI-Installer"
    "Accept" = "application/vnd.github+json"
}

$release = Invoke-RestMethod -Uri $releaseApiUrl -Headers $headers
$asset = $release.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1
if (-not $asset) {
    throw "Asset '$AssetName' was not found in GitHub release '$($release.tag_name)'."
}

$tempRoot = Join-Path $env:TEMP ("hki-install-" + [guid]::NewGuid().ToString("N"))
$zipPath = Join-Path $tempRoot $AssetName
$extractPath = Join-Path $tempRoot "expanded"

New-Item -ItemType Directory -Force $extractPath | Out-Null

Invoke-WebRequest -Uri $asset.browser_download_url -Headers @{ "User-Agent" = "HKI-Installer" } -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

$installScript = Join-Path $extractPath "Install-HKI.ps1"
if (-not (Test-Path $installScript)) {
    throw "Install-HKI.ps1 was not found in the downloaded package."
}

& $installScript -StartAfterInstall:$StartAfterInstall
