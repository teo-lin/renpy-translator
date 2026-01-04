# Thin wrapper for src/extract.py
# Extraction Script - Extracts clean text and tags from .rpy translation files

param(
    [string]$Source = "",
    [string]$GameName = "",
    [switch]$All = $false
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

# Run the Python script
$extractScript = Join-Path $PSScriptRoot "src\extract.py"
& $venvPython $extractScript @pythonArgs

# Exit with same code
exit $LASTEXITCODE
