# Translation Model Comparison Script (Thin Wrapper)
# Compares all installed models by translating the same content

param(
    [string]$GameName = "Example",
    [string]$Language = "ro"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Get Python command
$pythonCmd = Join-Path $scriptDir "venv\Scripts\python.exe"
$compareScript = Join-Path $scriptDir "scripts\compare.py"

# Check if Python exists
if (-not (Test-Path $pythonCmd)) {
    Write-Host "ERROR: Python executable not found at $pythonCmd" -ForegroundColor Red
    exit 1
}

# Run the Python orchestrator
& $pythonCmd $compareScript orchestrate --game $GameName --language $Language
exit $LASTEXITCODE
