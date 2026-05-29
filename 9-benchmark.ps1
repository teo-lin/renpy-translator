# Translation Quality Benchmark Script (Thin Wrapper)
# Benchmark a single model's translation quality using BLEU scores

param(
    [int]$Model = 0,                                  # Model number (1-based), 0 = prompt user
    [string]$ModelName,                               # Model key (e.g., "aya23")
    [string]$BenchmarkFile,                           # Optional; auto-detected (uncensored first, then regular) if omitted
    [string]$GlossaryFile,                            # Optional; auto-detected (uncensored first, then regular) if omitted
    [string]$Lang = "ro",                             # Language code for auto-detection
    [switch]$Yes                                      # Skip confirmation prompt
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$benchmarkScript = Join-Path $scriptDir "scripts\benchmark.py"

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $benchmarkScript)) {
    Write-Host "ERROR: Benchmark script not found at $benchmarkScript" -ForegroundColor Red
    exit 1
}

# Build arguments for the Python orchestrator
$scriptArgs = @("orchestrate", "--lang", $Lang)
if ($BenchmarkFile) {
    $scriptArgs += @("--benchmark", $BenchmarkFile)
}
if ($ModelName) {
    $scriptArgs += @("--model-key", $ModelName)
}
if ($Model -gt 0) {
    $scriptArgs += @("--model-number", $Model)
}
if ($GlossaryFile) {
    $scriptArgs += @("--glossary", $GlossaryFile)
}
if ($Yes) {
    $scriptArgs += "-y"
}

& $pythonExe $benchmarkScript $scriptArgs
exit $LASTEXITCODE
