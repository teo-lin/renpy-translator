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

# Main script
$ErrorActionPreference = "Continue"
$testDir = Join-Path $PSScriptRoot "tests"
$pythonExe = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$results = @()

# Check if venv Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Failure "Virtual environment not found at: $pythonExe"
    Write-Failure "Please run setup first or ensure venv is created."
    exit 1
}

Write-Header "RUNNING ALL STANDALONE TESTS"

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

    # Run the test and capture exit code
    & $pythonExe $testFile.FullName
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
