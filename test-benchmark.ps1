# Test script for 9-benchmark.ps1
# Validates that the benchmark script works correctly

param(
    [switch]$Cleanup = $false
)

$ErrorActionPreference = "Continue"  # Don't stop on errors, we want to see all test results
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                 Benchmark Script Test                          " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Test configuration
$testGame = "Example"
$testLanguage = "ro"
$testDir = Join-Path $scriptDir "games\$testGame\game\tl\romanian"

# Track test results
$testsPassed = 0
$testsFailed = 0

function Test-Condition {
    param(
        [string]$TestName,
        [bool]$Condition,
        [string]$SuccessMessage,
        [string]$FailureMessage
    )

    Write-Host "   [TEST] $TestName" -ForegroundColor Yellow
    if ($Condition) {
        Write-Host "      [PASS] $SuccessMessage" -ForegroundColor Green
        $script:testsPassed++
        return $true
    } else {
        Write-Host "      [FAIL] $FailureMessage" -ForegroundColor Red
        $script:testsFailed++
        return $false
    }
}

# Step 1: Pre-test checks
Write-Host "[1/5] Pre-test checks..." -ForegroundColor Yellow
Write-Host ""

$venvExists = Test-Path (Join-Path $scriptDir "venv\Scripts\python.exe")
Test-Condition -TestName "Virtual environment exists" `
    -Condition $venvExists `
    -SuccessMessage "Python venv found" `
    -FailureMessage "Python venv not found - run 0-setup.ps1 first"

$modelsConfigExists = Test-Path (Join-Path $scriptDir "models\models_config.json")
Test-Condition -TestName "Models configuration exists" `
    -Condition $modelsConfigExists `
    -SuccessMessage "models_config.json found" `
    -FailureMessage "models_config.json not found"

$gameExists = Test-Path (Join-Path $scriptDir "games\$testGame")
Test-Condition -TestName "Test game exists" `
    -Condition $gameExists `
    -SuccessMessage "Game '$testGame' found" `
    -FailureMessage "Game '$testGame' not found"

Write-Host ""

if (-not $venvExists -or -not $modelsConfigExists -or -not $gameExists) {
    Write-Host "Pre-test checks failed. Cannot continue." -ForegroundColor Red
    exit 1
}

# Step 2: Clean up any existing parsed files
Write-Host "[2/5] Cleaning up existing parsed files..." -ForegroundColor Yellow

if (Test-Path $testDir) {
    $existingParsedFiles = Get-ChildItem -Path $testDir -Filter "*.parsed.yaml" -ErrorAction SilentlyContinue
    if ($existingParsedFiles) {
        Write-Host "   Found $($existingParsedFiles.Count) existing parsed file(s)" -ForegroundColor Gray
        foreach ($file in $existingParsedFiles) {
            Remove-Item $file.FullName -Force
            Write-Host "      Removed: $($file.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   No existing parsed files to clean up" -ForegroundColor Gray
    }
} else {
    Write-Host "   Test directory doesn't exist yet" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Run the benchmark
Write-Host "[3/5] Running benchmark script..." -ForegroundColor Yellow
Write-Host ""
Write-Host "   This may take several minutes depending on the number of models..." -ForegroundColor Gray
Write-Host ""

$benchmarkScript = Join-Path $scriptDir "9-benchmark.ps1"
$benchmarkOutput = & $benchmarkScript -GameName $testGame -Language $testLanguage 2>&1
$benchmarkExitCode = $LASTEXITCODE

# Display output
$benchmarkOutput | ForEach-Object { Write-Host $_ }

Write-Host ""

Test-Condition -TestName "Benchmark script execution" `
    -Condition ($benchmarkExitCode -eq 0) `
    -SuccessMessage "Benchmark completed successfully (exit code: 0)" `
    -FailureMessage "Benchmark failed with exit code: $benchmarkExitCode"

Write-Host ""

# Step 4: Verify output files
Write-Host "[4/5] Verifying output files..." -ForegroundColor Yellow
Write-Host ""

# Check if parsed files were created
$parsedFiles = Get-ChildItem -Path $testDir -Filter "*.parsed.yaml" -ErrorAction SilentlyContinue

Test-Condition -TestName "Parsed files created" `
    -Condition ($parsedFiles.Count -gt 0) `
    -SuccessMessage "Found $($parsedFiles.Count) parsed file(s)" `
    -FailureMessage "No parsed files found"

if ($parsedFiles.Count -gt 0) {
    # Load models config to know how many models we have
    $modelsConfig = Get-Content (Join-Path $scriptDir "models\models_config.json") -Raw | ConvertFrom-Json
    $expectedModelCount = $modelsConfig.installed_models.Count

    Write-Host "   Expected $expectedModelCount model translations" -ForegroundColor Gray
    Write-Host ""

    # Check first parsed file for numbered keys
    $firstParsedFile = $parsedFiles[0]
    Write-Host "   Examining: $($firstParsedFile.Name)" -ForegroundColor Gray

    $parsedContent = Get-Content $firstParsedFile.FullName -Raw

    # Simple regex-based check for numbered keys
    $keysFound = @()

    # Check for each expected key (01, 02, 03, etc.)
    for ($i = 1; $i -le $expectedModelCount; $i++) {
        $key = "{0:D2}" -f $i
        # Look for pattern like "  01: " or "  '01': " in YAML
        if ($parsedContent -match "^\s+[']?$key[']?:\s+" -or $parsedContent -match "^\s+$key:\s+") {
            $keysFound += $key
        }
    }

    Write-Host ""
    Test-Condition -TestName "Numbered translation keys exist" `
        -Condition ($keysFound.Count -gt 0) `
        -SuccessMessage "Found keys: $($keysFound -join ', ')" `
        -FailureMessage "No numbered keys (01, 02, etc.) found in parsed files"

    Test-Condition -TestName "All model keys present" `
        -Condition ($keysFound.Count -eq $expectedModelCount) `
        -SuccessMessage "All $expectedModelCount model keys found" `
        -FailureMessage "Only found $($keysFound.Count) keys, expected $expectedModelCount"

    # Extract sample block to show the structure
    if ($keysFound.Count -gt 0) {
        Write-Host ""
        Write-Host "   Sample translations found in file:" -ForegroundColor Gray

        # Extract a few lines showing the structure
        $lines = $parsedContent -split "`n"
        $inBlock = $false
        $linesShown = 0
        $maxLinesToShow = 10

        for ($i = 0; $i -lt $lines.Count -and $linesShown -lt $maxLinesToShow; $i++) {
            $line = $lines[$i]

            # Start of a block (not separator)
            if ($line -match "^[a-zA-Z0-9_]+-[a-zA-Z0-9_]+:") {
                $inBlock = $true
            }

            if ($inBlock) {
                Write-Host "      $line" -ForegroundColor Cyan
                $linesShown++

                # Stop after showing one complete block
                if ($line -match "^\s+$($keysFound[-1]):" -and $linesShown -gt 3) {
                    # Show one more line (the translation value)
                    if ($i + 1 -lt $lines.Count) {
                        Write-Host "      $($lines[$i + 1])" -ForegroundColor Cyan
                    }
                    break
                }
            }
        }
    }
}

Write-Host ""

# Step 5: Verify benchmark output
Write-Host "[5/5] Verifying benchmark output..." -ForegroundColor Yellow
Write-Host ""

$outputText = $benchmarkOutput -join "`n"

Test-Condition -TestName "Model comparison table present" `
    -Condition ($outputText -match "MODEL COMPARISON") `
    -SuccessMessage "Found model comparison table in output" `
    -FailureMessage "Model comparison table not found in output"

Test-Condition -TestName "Duration tracking present" `
    -Condition ($outputText -match "Duration") `
    -SuccessMessage "Duration tracking found in output" `
    -FailureMessage "Duration tracking not found in output"

Test-Condition -TestName "Fastest/Slowest comparison" `
    -Condition ($outputText -match "Fastest:") `
    -SuccessMessage "Performance comparison found in output" `
    -FailureMessage "Performance comparison not found in output"

Write-Host ""

# Final summary
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                    TEST SUMMARY                                 " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Tests passed: $testsPassed" -ForegroundColor Green
Write-Host "   Tests failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "   ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   The benchmark script is working correctly." -ForegroundColor Cyan
    Write-Host "   Parsed files are located at:" -ForegroundColor Cyan
    Write-Host "      $testDir" -ForegroundColor Gray
} else {
    Write-Host "   SOME TESTS FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please review the errors above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Cleanup option
if ($Cleanup) {
    Write-Host "Cleanup requested - removing test files..." -ForegroundColor Yellow
    if (Test-Path $testDir) {
        $parsedFiles = Get-ChildItem -Path $testDir -Filter "*.parsed.yaml" -ErrorAction SilentlyContinue
        foreach ($file in $parsedFiles) {
            Remove-Item $file.FullName -Force
            Write-Host "   Removed: $($file.Name)" -ForegroundColor Gray
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Green
    Write-Host ""
}

# Exit with appropriate code
exit $(if ($testsFailed -eq 0) { 0 } else { 1 })
