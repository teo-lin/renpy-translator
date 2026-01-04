# Thin wrapper for scripts/config.py
# Character Discovery and Configuration Script

param(
    [string]$GamePath = "",
    [string]$Language = "",
    [string]$Model = ""
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

# Activate virtual environment
Activate-VirtualEnvironment

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
& python $configScript @pythonArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
