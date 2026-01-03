# This script is a wrapper for the main Python setup script.
# It passes all arguments to src/setup.py

$ErrorActionPreference = "Stop"

# Get the directory of the current script to ensure paths are correct
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Construct the full path to the Python setup script
$pythonScriptPath = Join-Path $scriptDir "src/setup.py"

# Prefer the virtual environment's Python if it exists, otherwise use the system's default Python
$venvPython = Join-Path $scriptDir "venv/Scripts/python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }

# Helper function to check if a Python package is installed globally
function Test-GlobalPythonPackage {
    param(
        [string]$PackageName
    )
    try {
        $result = & python -c "import $PackageName" 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# If venv does not exist, ensure essential packages are installed globally for initial bootstrap
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found. Ensuring essential packages are installed globally for bootstrap..." -ForegroundColor Yellow
    $essentialPackages = @("PyYAML")
    foreach ($pkg in $essentialPackages) {
        if (-not (Test-GlobalPythonPackage -PackageName $pkg)) {
            Write-Host "  Installing global package: $pkg..." -ForegroundColor Cyan
            try {
                & python -m pip install $pkg
            }
            catch {
                Write-Host "  WARNING: Failed to install global package $pkg. This might cause issues." -ForegroundColor Red
            }
        } else {
            Write-Host "  Global package $pkg already installed." -ForegroundColor DarkGray
        }
    }
}

# Execute the Python script, forwarding all script arguments
& $pythonExe $pythonScriptPath @args
