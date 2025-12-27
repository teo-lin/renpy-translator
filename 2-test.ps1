# Ren'Py Translation System - Automated Testing Script
# Run as: .\test.ps1

param(
    [int]$Model = 0  # Model number to test (1-based), 0 = prompt user
)

$ErrorActionPreference = "Stop"

# Source the shared user selection module
. (Join-Path $PSScriptRoot "scripts\user_selection.ps1")

# Color output helpers
function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Header {
    param([string]$Message)
    $separator = "=" * 70
    Write-Host ""
    Write-Host $separator -ForegroundColor Yellow
    Write-Host $Message -ForegroundColor Yellow
    Write-Host $separator -ForegroundColor Yellow
}

# Main script
$testDir = Join-Path $PSScriptRoot "tests"
$pythonExe = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$configFile = Join-Path $PSScriptRoot "models\local_config.json"
$results = @()

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $PSScriptRoot "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Set UTF-8 encoding for Python
$env:PYTHONIOENCODING = "utf-8"

# Check if venv Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Failure "Virtual environment not found at: $pythonExe"
    Write-Failure "Please run setup first or ensure venv is created."
    exit 1
}

# Load configuration
if (-not (Test-Path $configFile)) {
    Write-Failure "Configuration file not found at: $configFile"
    Write-Failure "Please run setup.ps1 to create the configuration."
    exit 1
}
$config = Get-Content $configFile | ConvertFrom-Json

# Get models as an array
if ($config.models -is [array]) {
    $allModels = $config.models
} else {
    $allModels = @($config.models)
}

# Filter to only include models that have been downloaded
$installedModels = @()
foreach ($modelItem in $allModels) {
    $modelPath = Join-Path $PSScriptRoot $modelItem.Config.destination
    if (Test-Path $modelPath) {
        $installedModels += $modelItem
    } else {
        Write-Info "Skipping model $($modelItem.Name) - not yet downloaded"
    }
}

$selectedLanguage = $config.languages | Where-Object { $_.Code -eq 'ro' } | Select-Object -First 1

if (-not $selectedLanguage) {
    Write-Failure "Romanian ('ro') not found in languages configuration in $configFile"
    exit 1
}

Write-Header "RUNNING ALL STANDALONE TESTS"

# Step 1: Select Model
if ($installedModels.Count -eq 0) {
    Write-Failure "ERROR: No translation models found in $configFile"
    exit 1
} elseif ($Model -gt 0) {
    # Model specified via parameter
    if ($Model -le $installedModels.Count) {
        $selectedModel = $installedModels[$Model - 1]
        Write-Info "Auto-selecting model $Model`: $($selectedModel.Name)"
    } else {
        Write-Failure "Invalid model number: $Model. Available models: 1-$($installedModels.Count)"
        exit 1
    }
} else {
    try {
        $selectedModel = Select-Item `
            -Title "Select Translation Model for Testing" `
            -ItemTypeName "model" `
            -Items $installedModels `
            -DisplayItem {
                param($model, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host $model.Name -NoNewline -ForegroundColor Green
                Write-Host " - $($model.Description)" -ForegroundColor White
                Write-Host "      Size: $($model.Size)" -ForegroundColor DarkGray
                Write-Host ""
            }
    } catch {
        Write-Failure "Selection cancelled."
        exit 0
    }
}

Write-Info "Test Language: $($selectedLanguage.Name) ($($selectedLanguage.Code))"

# Find all test files
$testFiles = Get-ChildItem -Path $testDir -Filter "test_*.py" -File | Sort-Object Name

if ($testFiles.Count -eq 0) {
    Write-Failure "No test files found in $testDir"
    exit 1
}

Write-Info ""
Write-Info "Found $($testFiles.Count) test file(s):"
Write-Info ""
foreach ($file in $testFiles) {
    Write-Host "  - $($file.Name)"
}

# Run each test
foreach ($testFile in $testFiles) {
    Write-Header "Running: $($testFile.Name)"

    $startTime = Get-Date

            # Build arguments
            Write-Host "DEBUG: PSScriptRoot is: $PSScriptRoot"
            Write-Host "DEBUG: selectedModel.Config.script is: $($selectedModel.Config.script)"
            $modelScriptPath = Join-Path $PSScriptRoot $selectedModel.Config.script
            Write-Host "DEBUG: modelScriptPath (constructed) is: $modelScriptPath"
        
            $scriptArgs = @(
                "--model_script", $modelScriptPath,
                "--language", $selectedLanguage.Code
            )    
        # Run the test and capture exit code
        & $pythonExe $testFile.FullName $scriptArgs
    $exitCode = $LASTEXITCODE

    $duration = (Get-Date) - $startTime

    # Record result
    $result = [PSCustomObject]@{
        Name = $testFile.Name
        Passed = ($exitCode -eq 0)
        Duration = $duration
        ExitCode = $exitCode
    }
    $results += $result

    # Print result
    Write-Host ""
    if ($result.Passed) {
        $msg = "PASSED: $($testFile.Name) (took $($duration.TotalSeconds.ToString('F2'))s)"
        Write-Success $msg
    } else {
        $msg = "FAILED: $($testFile.Name) (exit code: $exitCode, took $($duration.TotalSeconds.ToString('F2'))s)"
        Write-Failure $msg
    }
}

# Print summary
Write-Header "TEST SUMMARY"

# Force results into arrays to ensure .Count works even with single items
$passedCount = @($results | Where-Object { $_.Passed }).Count
$failedCount = @($results | Where-Object { -not $_.Passed }).Count
$totalDuration = [TimeSpan]::Zero
foreach ($result in $results) {
    $totalDuration += $result.Duration
}

Write-Host ""
foreach ($result in $results) {
    $status = if ($result.Passed) { "PASS" } else { "FAIL" }
    $color = if ($result.Passed) { "Green" } else { "Red" }
    $durationStr = $result.Duration.TotalSeconds.ToString('F2')

    Write-Host "  [$status] " -ForegroundColor $color -NoNewline
    Write-Host "$($result.Name) " -NoNewline
    Write-Host "($durationStr`s)" -ForegroundColor Gray
}

$separator = "=" * 70
Write-Host ""
Write-Host $separator
Write-Host "Total: $($results.Count) tests | " -NoNewline
Write-Host "Passed: $passedCount" -ForegroundColor Green -NoNewline
Write-Host " | " -NoNewline
if ($failedCount -gt 0) {
    Write-Host "Failed: " -NoNewline
    Write-Host "$failedCount" -ForegroundColor Red -NoNewline
} else {
    Write-Host "Failed: $failedCount" -NoNewline
}
$totalDurationStr = $totalDuration.TotalSeconds.ToString('F2')
Write-Host " | Duration: $totalDurationStr`s"
Write-Host $separator

# Exit with appropriate code
if ($failedCount -gt 0) {
    Write-Host ""
    Write-Failure "Some tests failed!"
    exit 1
} else {
    Write-Host ""
    Write-Success "All tests passed!"
    exit 0
}
