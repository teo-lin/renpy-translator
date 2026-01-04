# Thin wrapper for scripts/config.py
# Character Discovery and Configuration Script

param(
    [string]$GamePath = "",
    [string]$Language = "",
    [string]$Model = ""
)

# Get Python executable from virtual environment
$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment not found at $venvPython" -ForegroundColor Red
    Write-Host "Please run 0-setup.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Build arguments for Python script
$pythonArgs = @()

if ($GamePath -ne "") {
    $pythonArgs += "--game-path", $GamePath
}

if ($Language -ne "") {
    $pythonArgs += "--language", $Language
}

if ($Model -ne "") {
    $pythonArgs += "--model", $Model
}

# Run the Python script
$configScript = Join-Path $PSScriptRoot "scripts\config.py"
& $venvPython $configScript @pythonArgs

# Exit with same code
exit $LASTEXITCODE
