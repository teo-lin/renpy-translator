# Modular Translation Pipeline Launcher (YAML version)
# Translates .parsed.yaml files using batch translation with context awareness
# Uses configuration from models\current_config.yaml

param(
    [string]$Game = "",        # Optional game name (uses current_game if not specified)
    [switch]$Help              # Show help
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Help) {
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "       Modular Translation Pipeline - Help                      " -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Translates .parsed.yaml files using batch translation."
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\x3-translate.ps1                  # Use current_game from config"
    Write-Host "  .\x3-translate.ps1 -Game 'MyGame'   # Translate specific game"
    Write-Host ""
    Write-Host "REQUIREMENTS:" -ForegroundColor Yellow
    Write-Host "  1. Run .\x1-config.ps1 first to set up game configuration"
    Write-Host "  2. Run .\x2-extract.ps1 to create .parsed.yaml files"
    Write-Host "  3. Then run this script to translate"
    Write-Host ""
    Write-Host "WHAT IT DOES:" -ForegroundColor Yellow
    Write-Host "  - Loads game config from models\current_config.yaml"
    Write-Host "  - Finds all .parsed.yaml files in game\tl\<language>\"
    Write-Host "  - Translates only untranslated blocks (empty target language field)"
    Write-Host "  - Uses context-aware translation:"
    Write-Host "    * DIALOGUE: 3 lines before + 1 line after"
    Write-Host "    * CHOICE: No context (only character info)"
    Write-Host "  - Saves translations back to .parsed.yaml files"
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "  After translation, run .\x5-merge.ps1 to reconstruct .rpy files"
    Write-Host ""
    exit 0
}

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$configFile = Join-Path $scriptDir "models\current_config.yaml"
$pythonScript = Join-Path $scriptDir "scripts\translate.py"

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Set UTF-8 encoding for Python
$env:PYTHONIOENCODING = "utf-8"

# Check Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please run x0-setup.ps1 to install the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Check Python script exists
if (-not (Test-Path $pythonScript)) {
    Write-Host "ERROR: Python script not found at $pythonScript" -ForegroundColor Red
    exit 1
}

# Check configuration exists
if (-not (Test-Path $configFile)) {
    Write-Host "ERROR: Configuration not found at $configFile" -ForegroundColor Red
    Write-Host "Please run x1-config.ps1 first to set up your game." -ForegroundColor Yellow
    exit 1
}

# Banner
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Modular Translation Pipeline                             " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Build arguments
$scriptArgs = @()
if ($Game) {
    Write-Host ""
    Write-Host "Using game: $Game" -ForegroundColor Cyan
    $scriptArgs += "--game"
    $scriptArgs += $Game
} else {
    Write-Host ""
    Write-Host "Using current_game from configuration" -ForegroundColor Cyan
}

# Run the Python script
& $pythonExe $pythonScript $scriptArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Translation failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Translation Complete!                                    " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Review the .parsed.yaml files for translation quality"
Write-Host "  2. Run .\x5-merge.ps1 to reconstruct .rpy files"
Write-Host ""
