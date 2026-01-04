# Interactive PowerShell launcher for Ren'Py grammar correction
# Guided workflow: Mode -> Language -> Game selection

param(
    [int]$Mode = 0,       # Mode number (1-based), 0 = prompt user
    [string]$ModeName,    # Mode name (e.g., "Both (Patterns + LLM)")
    [int]$Language = 0,   # Language number (1-based), 0 = prompt user
    [string]$LanguageName, # Language name (e.g., "romanian")
    [int]$Game = 0,       # Game number (1-based), 0 = prompt user
    [string]$GameName,     # Game name (e.g., "Example")
    [switch]$Yes,         # Skip confirmation prompt
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments  # Additional arguments to pass to Python script
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$correctScript = Join-Path $scriptDir "scripts\correct.py"
$correctUtilsScript = Join-Path $scriptDir "scripts\correct_utils.py"

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib" # Corrected path
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Set UTF-8 encoding for Python
$env:PYTHONIOENCODING = "utf-8"

# Check Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please run setup.ps1 to install the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Check correction script exists
if (-not (Test-Path $correctScript)) {
    Write-Host "ERROR: Correction script not found at $correctScript" -ForegroundColor Red
    exit 1
}

# Check correct_utils.py exists
if (-not (Test-Path $correctUtilsScript)) {
    Write-Host "ERROR: Helper script correct_utils.py not found at $correctUtilsScript" -ForegroundColor Red
    Write-Host "This is a new feature. Please ensure your project is up-to-date or re-run setup.ps1." -ForegroundColor Yellow
    exit 1
}


# Prepare arguments for correct_utils.py
$correctUtilsArgs = @()
if ($Mode -ne 0) { $correctUtilsArgs += "--mode", $Mode }
if ($ModeName) { $correctUtilsArgs += "--mode-name", $ModeName }
if ($Language -ne 0) { $correctUtilsArgs += "--language", $Language }
if ($LanguageName) { $correctUtilsArgs += "--language-name", $LanguageName }
if ($Game -ne 0) { $correctUtilsArgs += "--game", $Game }
if ($GameName) { $correctUtilsArgs += "--game-name", $GameName }

# Pass along any remaining arguments from PowerShell to correct_utils.py
# The correct_utils.py script will then pass these along to scripts/correct.py
if ($Arguments.Count -gt 0) {
    # Need to prefix with --arguments to let correct_utils.py know these are generic additional args
    $correctUtilsArgs += "--arguments"
    $correctUtilsArgs += $Arguments
}

# Call correct_utils.py to get the actual script arguments
# It will print each argument on a new line
Write-Host "DEBUG: About to call Python script correct_utils.py" -ForegroundColor DarkYellow
Write-Host "DEBUG: Calling correct_utils.py with args: $correctUtilsArgs"
$pythonOutput = & $pythonExe -u $correctUtilsScript @correctUtilsArgs 2>&1 | Out-String
Write-Host "DEBUG: Returned from Python script correct_utils.py. LastExitCode: $LASTEXITCODE" -ForegroundColor DarkYellow
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to prepare arguments using correct_utils.py. Output: $pythonOutput" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Parse the multi-line string output from Python into a PowerShell array
# Each argument is printed on a new line by correct_utils.py
$scriptArgs = $pythonOutput.Trim().Split("`n") | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrEmpty($_) }

# Handle the confirmation if not auto-skipped
if (-not $Yes) {
    # The summary is already printed by correct_utils.py
    $confirm = Read-Host "Proceed with correction? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

# Run the actual correction script
Write-Host ""
Write-Host "Starting correction with mode (determined by Python script)..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe $correctScript $scriptArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Correction failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Correction Completed Successfully!                       " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""