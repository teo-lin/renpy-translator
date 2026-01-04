# Thin wrapper for src/extract.py
# Extraction Script - Extracts clean text and tags from .rpy translation files

param(
    [string]$Source = "",
    [string]$GameName = "",
    [switch]$All = $false
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

# Activate virtual environment
Activate-VirtualEnvironment

# Build arguments for Python script
$pythonArgs = @()

if ($GameName -ne "") {
    $pythonArgs += "--game-name", $GameName
}

if ($Source -ne "") {
    $pythonArgs += "--source", $Source
}

if ($All) {
    $pythonArgs += "--all"
}

# Run the Python script
$extractScript = Join-Path $PSScriptRoot "src\extract.py"
& python $extractScript @pythonArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
