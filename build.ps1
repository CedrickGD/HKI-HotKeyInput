$ErrorActionPreference = "Stop"

function Get-BootstrapPython {
    $candidates = @("py", "python")
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }

        try {
            & $command.Source -c "import sys" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $command.Source
            }
        } catch {
        }
    }

    throw "Python was not found. Install Python first, then run this script again."
}

function Ensure-VenvPython {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $bootstrapPython = Get-BootstrapPython
    $venvRoot = Join-Path $PSScriptRoot ".venv"
    Write-Host "Creating virtual environment in '$venvRoot'..."
    & $bootstrapPython -m venv $venvRoot
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        throw "Creating the virtual environment failed."
    }

    return $venvPython
}

function Test-ModuleInstalled {
    param(
        [Parameter(Mandatory = $true)][string]$Python,
        [Parameter(Mandatory = $true)][string]$ModuleName
    )

    & $Python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$ModuleName') else 1)" | Out-Null
    return $LASTEXITCODE -eq 0
}

$python = Ensure-VenvPython
$requirements = Join-Path $PSScriptRoot "requirements.txt"
if (
    -not (Test-ModuleInstalled -Python $python -ModuleName "PyInstaller") -or
    -not (Test-ModuleInstalled -Python $python -ModuleName "PySide6") -or
    -not (Test-ModuleInstalled -Python $python -ModuleName "PIL")
) {
    Write-Output "Installing build dependencies..."
    & $python -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Installing dependencies failed."
    }
}

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name HKI `
  --icon "$PSScriptRoot\assets\hki.ico" `
  --add-data "$PSScriptRoot\assets;assets" `
  "$PSScriptRoot\hki_app.pyw"
