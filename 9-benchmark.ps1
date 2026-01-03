# Translation Quality Benchmark Script
# Benchmark a single model's translation quality using BLEU scores
# Compares model output against reference translations

param(
    [int]$Model = 0,       # Model number (1-based), 0 = prompt user
    [string]$ModelName,    # Model name (e.g., "aya23")
    [string]$BenchmarkFile = "data/ro_benchmark.json",
    [string]$GlossaryFile, # Optional glossary file
    [switch]$Yes,         # Skip confirmation prompt
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments  # Additional arguments to pass to Python script
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Source the shared user selection module
. (Join-Path $scriptDir "scripts\config_selector.ps1")

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$benchmarkScript = Join-Path $scriptDir "scripts\benchmark.py"
$modelsConfigPath = Join-Path $scriptDir "models\models_config.json"

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
    Write-Host "Please run 0-setup.ps1 to install the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Check benchmark script exists
if (-not (Test-Path $benchmarkScript)) {
    Write-Host "ERROR: Benchmark script not found at $benchmarkScript" -ForegroundColor Red
    exit 1
}

# Check benchmark data exists
$benchmarkPath = Join-Path $scriptDir $BenchmarkFile
if (-not (Test-Path $benchmarkPath)) {
    Write-Host "ERROR: Benchmark data not found at $benchmarkPath" -ForegroundColor Red
    Write-Host "Please create a benchmark file with reference translations." -ForegroundColor Yellow
    exit 1
}

# Load models configuration
if (-not (Test-Path $modelsConfigPath)) {
    Write-Host "ERROR: Models configuration not found at $modelsConfigPath" -ForegroundColor Red
    Write-Host "Please run 0-setup.ps1 first to install models." -ForegroundColor Yellow
    exit 1
}

$modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
$installedModels = $modelsConfig.installed_models

if (-not $installedModels -or $installedModels.Count -eq 0) {
    Write-Host "ERROR: No models are installed!" -ForegroundColor Red
    Write-Host "Please run 0-setup.ps1 first to install models." -ForegroundColor Yellow
    exit 1
}

# Create model selection list
$modelsList = @()
foreach ($modelKey in $installedModels) {
    $modelInfo = $modelsConfig.available_models.$modelKey
    $modelsList += @{
        Key = $modelKey
        Name = $modelInfo.name
        Size = $modelInfo.size
        Params = $modelInfo.params
    }
}

# Banner
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Translation Quality Benchmark (BLEU Scoring)            " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Step 1: Select Model
if ($ModelName) {
    $foundModel = $modelsList | Where-Object { $_.Key -eq $ModelName }
    if ($foundModel) {
        $Model = ($modelsList.IndexOf($foundModel) + 1)
        Write-Host ""
        Write-Host "Auto-selecting model by name '$ModelName'. Resolved to index $Model." -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid model name: $ModelName. Available models: $($modelsList.Key -join ', ')" -ForegroundColor Red
        exit 1
    }
}

if ($Model -gt 0) {
    if ($Model -le $modelsList.Count) {
        $selectedModel = $modelsList[$Model - 1]
        Write-Host ""
        Write-Host "Auto-selecting model $Model`: $($selectedModel.Name)" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid model number: $Model. Available models: 1-$($modelsList.Count)" -ForegroundColor Red
        exit 1
    }
} else {
    try {
        $selectedModel = Select-Item `
            -Title "Step 1: Select Model to Benchmark" `
            -ItemTypeName "model" `
            -Items $modelsList `
            -DisplayItem {
                param($model, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host $model.Name -NoNewline -ForegroundColor Green
                Write-Host " ($($model.Params), $($model.Size))" -ForegroundColor DarkGray
            }
    } catch {
        Write-Host "Selection cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Auto-detect glossary if not specified
if (-not $GlossaryFile) {
    # Try to find matching glossary from benchmark file name
    $benchmarkName = [System.IO.Path]::GetFileNameWithoutExtension($BenchmarkFile)
    $benchmarkDir = [System.IO.Path]::GetDirectoryName($benchmarkPath)

    # Extract language code (e.g., "ro" from "ro_benchmark")
    if ($benchmarkName -match "^([a-z]{2})_") {
        $langCode = $Matches[1]

        # Try different glossary naming patterns
        $glossaryPatterns = @(
            "$langCode`_uncensored_glossary.json",
            "$langCode`_glossary.json"
        )

        foreach ($pattern in $glossaryPatterns) {
            $testPath = Join-Path $benchmarkDir $pattern
            if (Test-Path $testPath) {
                $GlossaryFile = $testPath
                break
            }
        }
    }
}

# Summary
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       Benchmark Summary                                        " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Model:      " -NoNewline -ForegroundColor White
Write-Host "$($selectedModel.Name) ($($selectedModel.Params), $($selectedModel.Size))" -ForegroundColor Green
Write-Host "  Benchmark:  " -NoNewline -ForegroundColor White
Write-Host $BenchmarkFile -ForegroundColor Green
if ($GlossaryFile) {
    Write-Host "  Glossary:   " -NoNewline -ForegroundColor White
    Write-Host $GlossaryFile -ForegroundColor Green
} else {
    Write-Host "  Glossary:   " -NoNewline -ForegroundColor White
    Write-Host "None" -ForegroundColor Yellow
}
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Yes) {
    $confirm = Read-Host "Proceed with benchmark? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

# Build arguments
$scriptArgs = @($benchmarkPath, "--model", $selectedModel.Key)
if ($GlossaryFile) {
    $scriptArgs += @("--glossary", $GlossaryFile)
}
if ($Arguments.Count -gt 0) {
    $scriptArgs += $Arguments
}

# Run the benchmark script
Write-Host ""
Write-Host "Starting benchmark with model: $($selectedModel.Name)..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe $benchmarkScript $scriptArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Benchmark failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Benchmark Completed Successfully!                       " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
