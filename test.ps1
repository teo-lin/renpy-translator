#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run all standalone tests in the tests directory

.DESCRIPTION
    This script automatically finds and runs all test_*.py files in the tests directory.
    It reports individual test results and provides an overall summary.

.EXAMPLE
    .\test.ps1
#>

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

# Helper function to display menu and get selection
function Show-Menu {
    param(
        [string]$Title,
        [array]$Items,
        [scriptblock]$DisplayItem
    )

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "       $Title" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $Items.Count; $i++) {
        $num = $i + 1
        & $DisplayItem $Items[$i] $num
    }

    Write-Host "  [Q] Quit" -ForegroundColor Red
    Write-Host ""

    while ($true) {
        $selection = Read-Host "Select (1-$($Items.Count) or Q)"

        if ($selection -eq "Q" -or $selection -eq "q") {
            Write-Host "Cancelled by user." -ForegroundColor Yellow
            exit 0
        }

        try {
            $index = [int]$selection - 1
            if ($index -ge 0 -and $index -lt $Items.Count) {
                return $Items[$index]
            }
            else {
                Write-Host "Invalid selection. Please enter a number between 1 and $($Items.Count)." -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Invalid input. Please enter a number or Q to quit." -ForegroundColor Red
        }
    }
}

# Main script
$ErrorActionPreference = "Stop"
$testDir = Join-Path $PSScriptRoot "tests"
$pythonExe = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$configFile = Join-Path $PSScriptRoot "models\local_config.json"
$results = @()

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

$installedModels = $config.models
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
} elseif ($installedModels.Count -eq 1) {
    $selectedModel = $installedModels[0]
    Write-Info "Auto-selecting the only available model: $($selectedModel.Name)"
} else {
    $selectedModel = Show-Menu -Title "Select Translation Model for Testing" -Items $installedModels -DisplayItem {
        param($model, $num)
        Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
        Write-Host $model.Name -NoNewline -ForegroundColor Green
        Write-Host " - $($model.Description)" -ForegroundColor White
        Write-Host "      $($model.Details)" -ForegroundColor DarkGray
        Write-Host ""
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
            Write-Host "DEBUG: selectedModel.Script is: $($selectedModel.Script)"
            $modelScriptPath = "$PSScriptRoot\$($selectedModel.Script)" # More robust string concatenation
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

$passedCount = ($results | Where-Object { $_.Passed }).Count
$failedCount = ($results | Where-Object { -not $_.Passed }).Count
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
    Write-Host "Failed: $failedCount" -ForegroundColor Red -NoNewline
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
