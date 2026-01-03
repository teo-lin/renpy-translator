# Translation Model Benchmark Script
# Compares all installed models by translating the same content
# and saving results under numbered keys (01, 02, 03, etc.) for comparison

param(
    [string]$GameName = "Example",
    [string]$Language = "ro"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Banner
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                 Translation Model Benchmark                    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Load models configuration to get all installed models
Write-Host "[1/5] Loading models configuration..." -ForegroundColor Yellow
$modelsConfigPath = Join-Path $scriptDir "models\models_config.json"

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

Write-Host "   Found $($installedModels.Count) installed models:" -ForegroundColor Green
foreach ($modelKey in $installedModels) {
    $modelInfo = $modelsConfig.available_models.$modelKey
    Write-Host "      - $($modelInfo.name)" -ForegroundColor Cyan
}
Write-Host ""

# Step 2: Configure game with first model (just to set up the structure)
Write-Host "[2/5] Configuring game: $GameName with language: $Language..." -ForegroundColor Yellow
$firstModel = $installedModels[0]
Write-Host "   Using initial model: $firstModel" -ForegroundColor Gray

# Get full game path
$fullGamePath = Join-Path $scriptDir "games\$GameName"
if (-not (Test-Path $fullGamePath)) {
    Write-Host "ERROR: Game directory not found: $fullGamePath" -ForegroundColor Red
    exit 1
}

$configScript = Join-Path $scriptDir "1-config.ps1"
& $configScript -GamePath $fullGamePath -Language $Language -Model $firstModel

# Note: 1-config.ps1 doesn't always return proper exit code, so we check if config file exists instead
$currentConfigPath = Join-Path $scriptDir "models\current_config.json"
if (-not (Test-Path $currentConfigPath)) {
    Write-Host "ERROR: Configuration failed - config file not created!" -ForegroundColor Red
    exit 1
}
Write-Host "   [OK] Configuration successful" -ForegroundColor Green

Write-Host ""

# Step 3: Extract translation files
Write-Host "[3/5] Extracting translation files..." -ForegroundColor Yellow
$extractScript = Join-Path $scriptDir "2-extract.ps1"
& $extractScript -GameName $GameName -All

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Extraction failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Benchmark each model
Write-Host "[4/5] Running benchmark translations..." -ForegroundColor Yellow
Write-Host ""

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$benchmarkScript = Join-Path $scriptDir "scripts\benchmark_translate.py"

# Check Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    exit 1
}

# Set UTF-8 encoding
$env:PYTHONIOENCODING = "utf-8"

# Add PyTorch lib directory to PATH for CUDA DLLs
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Track results
$benchmarkResults = @()
$benchmarkStartTime = Get-Date

foreach ($modelIdx in 0..($installedModels.Count - 1)) {
    $modelKey = $installedModels[$modelIdx]
    $modelInfo = $modelsConfig.available_models.$modelKey
    $keyNumber = "r$modelIdx"  # Format as r0, r1, r2, etc.

    Write-Host ""
    Write-Host "   [$($modelIdx + 1)/$($installedModels.Count)] Model: $($modelInfo.name) -> Key: $keyNumber" -ForegroundColor Cyan
    Write-Host "   " + ("=" * 65) -ForegroundColor Gray

    $modelStartTime = Get-Date

    # Run benchmark translation
    $output = & $pythonExe $benchmarkScript --game $GameName --model $modelKey --key $keyNumber 2>&1

    # Display output
    $output | ForEach-Object { Write-Host $_ }

    $modelEndTime = Get-Date
    $modelDuration = ($modelEndTime - $modelStartTime).TotalSeconds

    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [ERROR] Translation failed for model $modelKey!" -ForegroundColor Red
        $benchmarkResults += @{
            Model = $modelInfo.name
            Key = $keyNumber
            Duration = $modelDuration
            Status = "FAILED"
        }
    }
    else {
        # Try to extract duration from output (Python script outputs it)
        $durationLine = $output | Where-Object { $_ -match "BENCHMARK_DURATION:(\d+\.?\d*)" }
        if ($durationLine -and $Matches[1]) {
            $actualDuration = [double]$Matches[1]
        }
        else {
            $actualDuration = $modelDuration
        }

        Write-Host "   [OK] Completed in $($actualDuration.ToString('F2')) seconds" -ForegroundColor Green

        $benchmarkResults += @{
            Model = $modelInfo.name
            Key = $keyNumber
            Duration = $actualDuration
            Status = "SUCCESS"
            Size = $modelInfo.size
            Params = $modelInfo.params
        }
    }
}

$benchmarkEndTime = Get-Date
$totalDuration = ($benchmarkEndTime - $benchmarkStartTime).TotalSeconds

Write-Host ""
Write-Host ""

# Step 5: Display comparison results
Write-Host "[5/5] Benchmark Results" -ForegroundColor Yellow
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                   MODEL COMPARISON                              " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Sort by duration (fastest first)
$sortedResults = $benchmarkResults | Sort-Object { $_.Duration }

Write-Host ("   {0,-3} {1,-20} {2,-10} {3,-12} {4,-10}" -f "Key", "Model", "Size", "Duration", "Status") -ForegroundColor Yellow
Write-Host ("   " + ("-" * 65)) -ForegroundColor Gray

foreach ($result in $sortedResults) {
    $statusColor = if ($result.Status -eq "SUCCESS") { "Green" } else { "Red" }
    $durationStr = if ($result.Status -eq "SUCCESS") { "$($result.Duration.ToString('F2'))s" } else { "N/A" }

    Write-Host ("   {0,-3} {1,-20} {2,-10} {3,-12} {4,-10}" -f `
        $result.Key, `
        $result.Model, `
        $result.Size, `
        $durationStr, `
        $result.Status) -ForegroundColor $statusColor
}

Write-Host ""
Write-Host "   Total benchmark duration: $($totalDuration.ToString('F2')) seconds" -ForegroundColor Cyan
Write-Host ""

# Find fastest and slowest
$successful = $benchmarkResults | Where-Object { $_.Status -eq "SUCCESS" }
if ($successful.Count -gt 1) {
    $fastest = $successful | Sort-Object { $_.Duration } | Select-Object -First 1
    $slowest = $successful | Sort-Object { $_.Duration } -Descending | Select-Object -First 1

    $speedup = $slowest.Duration / $fastest.Duration

    Write-Host "   Fastest: $($fastest.Model) ($($fastest.Duration.ToString('F2'))s)" -ForegroundColor Green
    Write-Host "   Slowest: $($slowest.Model) ($($slowest.Duration.ToString('F2'))s)" -ForegroundColor Yellow
    Write-Host "   Speedup: $($speedup.ToString('F2'))x faster" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Benchmark complete!" -ForegroundColor Green
Write-Host ""
Write-Host "   Translation files saved with numbered keys (r0, r1, r2, etc.)" -ForegroundColor Yellow
Write-Host "   Review the .parsed.yaml files to compare model outputs." -ForegroundColor Yellow
Write-Host ""
Write-Host "   Location: games\$GameName\game\tl\romanian\*.parsed.yaml" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Each block now contains:" -ForegroundColor Gray
Write-Host "      en:  Original English text" -ForegroundColor Gray
foreach ($result in $benchmarkResults) {
    Write-Host "      $($result.Key): Translation from $($result.Model)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
