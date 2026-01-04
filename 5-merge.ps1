# Thin wrapper for src/merge.py
# Merge Script - Merges translated YAML + tags YAML back into .rpy files

param(
    [string]$Source = "",
    [string]$GameName = "",
    [switch]$All = $false,
    [switch]$SkipValidation = $false
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

if ($GameName -ne "") {
    $pythonArgs += "--game-name", $GameName
}

if ($Source -ne "") {
    $pythonArgs += "--source", $Source
}

if ($All) {
    $pythonArgs += "--all"
}

if ($SkipValidation) {
    $pythonArgs += "--skip-validation"
}

# Run the Python script
$mergeScript = Join-Path $PSScriptRoot "src\merge.py"
& $venvPython $mergeScript @pythonArgs

# Exit with same code
exit $LASTEXITCODE
