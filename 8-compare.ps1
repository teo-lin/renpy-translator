# Translation Model Comparison Script (Thin Wrapper)
# Compares all installed models by translating the same content

param(
    [string]$GameName,
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

# Build orchestrator args; omit --game to fall through to the interactive picker
$scriptArgs = @("orchestrate", "--language", $Language)
if ($GameName) {
    $scriptArgs += @("--game", $GameName)
}

& $pythonCmd $compareScript $scriptArgs
exit $LASTEXITCODE
