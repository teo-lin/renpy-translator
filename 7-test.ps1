# Ren'Py Translation System - Automated Testing Script
# Run as: .\8-test.ps1 [--unit | --int | --e2e] [-Model <num>]

param(
    [switch]$Unit,   # Run only test_unit_* tests
    [switch]$Int,    # Run only test_int_* tests (integration tests)
    [switch]$E2e,    # Run only test_e2e_* tests (end-to-end tests)
    [int]$Model = 2  # Model number to test (1-based), 2 = Aya-23 (default), 0 = prompt user
)

$ErrorActionPreference = "Stop"

# Set HuggingFace home to local models directory
$env:HF_HOME = Join-Path $PSScriptRoot "models"

# Source the shared user selection module
. (Join-Path $PSScriptRoot "scripts\config_selector.ps1")

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

# Detect available device for integration/e2e tests
$testDevice = "cpu"
try {
    $deviceCheckScript = @"
import torch
print('cuda' if torch.cuda.is_available() else 'cpu', end='')
"@
    $testDevice = & $pythonExe -c $deviceCheckScript 2>$null
    if ($LASTEXITCODE -ne 0) {
        $testDevice = "cpu"
    }
} catch {
    $testDevice = "cpu"
}

# Load configurations
$modelsConfigFile = Join-Path $PSScriptRoot "models\models_config.json"
$currentConfigFile = Join-Path $PSScriptRoot "models\current_config.json"

if (-not (Test-Path $modelsConfigFile)) {
    Write-Failure "Models configuration not found at: $modelsConfigFile. Please run 0-setup.ps1."
    exit 1
}
if (-not (Test-Path $currentConfigFile)) {
    Write-Failure "Current configuration not found at: $currentConfigFile. Please run 1-config.ps1."
    exit 1
}

$modelsConfig = Get-Content $modelsConfigFile | ConvertFrom-Json
$currentConfig = Get-Content $currentConfigFile | ConvertFrom-Json

# Get current game, language, and model from current_config.json
$currentGameName = $currentConfig.current_game
if (-not $currentGameName) {
    Write-Failure "No 'current_game' set in $currentConfigFile. Please run 1-config.ps1."
    exit 1
}
$currentGameConfig = $currentConfig.games.$currentGameName
if (-not $currentGameConfig) {
    Write-Failure "Configuration for current game '$currentGameName' not found in $currentConfigFile."
    exit 1
}
$targetLanguageCode = $currentGameConfig.target_language
$targetModelName = $currentGameConfig.model

if (-not $targetLanguageCode) {
    Write-Failure "No 'target_language' set for the current game in $currentConfigFile. Please run 1-config.ps1."
    exit 1
}
if (-not $targetModelName) {
    Write-Failure "No 'model' set for the current game in $currentConfigFile. Please run 1-config.ps1."
    exit 1
}

# Create a selectedLanguage object for compatibility with the rest of the script
$selectedLanguage = @{ Code = $targetLanguageCode; Name = $targetLanguageCode }


# Get all available models from models_config.json
$allModels = [System.Collections.ArrayList]@()
foreach ($modelKey in $modelsConfig.available_models.PSObject.Properties.Name) {
    $modelConfig = $modelsConfig.available_models.$modelKey
    [void]$allModels.Add([PSCustomObject]@{
        Key = $modelKey
        Name = $modelConfig.name
        Description = $modelConfig.description
        Size = $modelConfig.size
        Config = $modelConfig
    })
}

# Filter to only include models that have been downloaded
$installedModels = [System.Collections.ArrayList]@()
foreach ($modelItem in $allModels) {
    $modelPath = Join-Path $PSScriptRoot $modelItem.Config.destination
    if (Test-Path $modelPath) {
        [void]$installedModels.Add($modelItem)
    }
}

if ($installedModels.Count -eq 0) {
    Write-Failure "ERROR: No downloaded models found. Please run 0-setup.ps1."
    exit 1
}

Write-Header "RUNNING ALL STANDALONE TESTS"

# Step 1: Select Model based on current_config.json
# Try to match by name first (exact match), then by key, then by fuzzy match
$selectedModel = $installedModels | Where-Object { $_.Name -eq $targetModelName } | Select-Object -First 1

if (-not $selectedModel) {
    # Try matching by key
    $selectedModel = $installedModels | Where-Object { $_.Key -eq $targetModelName } | Select-Object -First 1
}

if (-not $selectedModel) {
    # Try case-insensitive name match
    $selectedModel = $installedModels | Where-Object { $_.Name -like $targetModelName } | Select-Object -First 1
}

if (-not $selectedModel) {
    # Try fuzzy match: normalize and check if target starts with key or contains key
    # e.g., "Aya-23-8B" contains "aya23", "madlad400-3b-mt" contains "madlad400"
    $normalizedTarget = ($targetModelName -replace '[^a-zA-Z0-9]', '').ToLower()
    foreach ($modelItem in $installedModels) {
        $normalizedKey = ($modelItem.Key -replace '[^a-zA-Z0-9]', '').ToLower()
        $normalizedName = ($modelItem.Name -replace '[^a-zA-Z0-9]', '').ToLower()

        # Check if normalized target starts with or contains the key/name
        if ($normalizedTarget -like "$normalizedKey*" -or $normalizedTarget -like "*$normalizedKey*" -or
            $normalizedKey -like "$normalizedTarget*" -or $normalizedKey -like "*$normalizedTarget*") {
            $selectedModel = $modelItem
            break
        }
    }
}

if (-not $selectedModel) {
    Write-Failure "The configured model '$targetModelName' is not installed. Please run 0-setup.ps1 to install it."
    Write-Info "Available installed models:"
    foreach ($installedModel in $installedModels) {
        Write-Host "  - Key: $($installedModel.Key), Name: $($installedModel.Name)"
    }
    exit 1
}

Write-Info "Using configured model: $($selectedModel.Name)"

Write-Info "Test Language: $($selectedLanguage.Name) ($($selectedLanguage.Code))"

# Show device info for integration/e2e tests
if ($testDevice -eq "cuda") {
    Write-Info "Test Device: CUDA (GPU acceleration enabled)"
} else {
    Write-Info "Test Device: CPU"
}

# Find all test files based on flags
$allTestFiles = Get-ChildItem -Path $testDir -Filter "test_*.py" -File | Sort-Object Name

# Apply filtering based on flags
if ($Unit) {
    $testFiles = $allTestFiles | Where-Object { $_.Name -like "test_unit_*" }
    $testCategory = "Unit Tests"
} elseif ($Int) {
    $testFiles = $allTestFiles | Where-Object { $_.Name -like "test_int_*" }
    $testCategory = "Integration Tests"
} elseif ($E2e) {
    $testFiles = $allTestFiles | Where-Object { $_.Name -like "test_e2e_*" }
    $testCategory = "End-to-End Tests"
} else {
    $testFiles = $allTestFiles
    $testCategory = "All Tests"
}

if ($testFiles.Count -eq 0) {
    Write-Failure "No test files found in $testDir matching the specified category"
    exit 1
}

Write-Info ""
Write-Info "Running: $testCategory"
Write-Info "Found $($testFiles.Count) test file(s):"
Write-Info ""
foreach ($file in $testFiles) {
    Write-Host "  - $($file.Name)"
}

$modelSpecificE2eTests = @{
    "test_e2e_aya23.py" = "aya23";
    "test_e2e_madlad400.py" = "madlad400";
    "test_e2e_mbartRo.py" = "mbartRo";
    "test_e2e_helsinkyRo.py" = "helsinkiRo";
    "test_e2e_seamlessm96.py" = "seamlessm96";
}

# Tests that are outdated or incompatible with current architecture
$deprecatedTests = @(
    # None currently
)

# Filter out deprecated tests and model-specific E2E tests if their model is not installed
$filteredTestFiles = @()
foreach ($testFile in $testFiles) {
    # Skip deprecated tests
    if ($deprecatedTests -contains $testFile.Name) {
        Write-Info "Skipping deprecated test $($testFile.Name) - incompatible with current architecture"
        continue
    }

    # Check model-specific tests
    if ($modelSpecificE2eTests.ContainsKey($testFile.Name)) {
        $modelKeyForTest = $modelSpecificE2eTests[$testFile.Name]
        $isModelInstalled = $false
        foreach ($installedModel in $installedModels) {
            if ($installedModel.Key -eq $modelKeyForTest) {
                $isModelInstalled = $true
                break
            }
        }
        if ($isModelInstalled) {
            $filteredTestFiles += $testFile
        } else {
            Write-Info "Skipping test $($testFile.Name) - associated model '$modelKeyForTest' is not installed."
        }
    } else {
        $filteredTestFiles += $testFile
    }
}
$testFiles = $filteredTestFiles

# Run each test
$testCounter = 0
foreach ($testFile in $testFiles) {
    $testCounter++
    Write-Header "Running test $testCounter of $($testFiles.Count): $($testFile.Name)"

    $startTime = Get-Date

    # Only pass model script arguments to tests that need them
    # Note: test_e2e_all_example_game.py now uses Python API directly, doesn't need arguments
    $testsNeedingModelScript = @(
        "test_e2e_translate_aio.py",
        "test_e2e_translate_aio_uncensored.py"
    )

    if ($testsNeedingModelScript -contains $testFile.Name) {
        # Build arguments for tests that need model script
        # Normalize path separators for Windows
        $scriptRelativePath = $selectedModel.Config.script -replace '/', '\'
        $modelScriptPath = Join-Path $PSScriptRoot $scriptRelativePath

        $scriptArgs = @(
            "--model_script", $modelScriptPath,
            "--language", $selectedLanguage.Code,
            "--model_key", $selectedModel.Key
        )

        # Run the test with model script arguments
        & $pythonExe $testFile.FullName $scriptArgs
    } else {
        # Run the test without arguments
        & $pythonExe $testFile.FullName
    }

    $exitCode = $LASTEXITCODE

    $duration = (Get-Date) - $startTime

    # Determine if this is an integration or e2e test (needs device info)
    $needsDevice = $testFile.Name -like "test_int_*" -or $testFile.Name -like "test_e2e_*"

    # Record result
    $result = [PSCustomObject]@{
        Name = $testFile.Name
        Passed = ($exitCode -eq 0)
        Duration = $duration
        ExitCode = $exitCode
        Device = if ($needsDevice) { $testDevice } else { $null }
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
# Calculate max name length for alignment
$maxNameLength = ($results | ForEach-Object { $_.Name.Length } | Measure-Object -Maximum).Maximum

foreach ($result in $results) {
    $status = if ($result.Passed) { "PASS" } else { "FAIL" }
    $color = if ($result.Passed) { "Green" } else { "Red" }

    # Format duration
    $totalSeconds = $result.Duration.TotalSeconds
    if ($totalSeconds -lt 60) {
        $durationStr = "{0,6:F2}s" -f $totalSeconds
    } else {
        $minutes = [Math]::Floor($totalSeconds / 60)
        $seconds = $totalSeconds % 60
        $durationStr = "{0}m {1:F0}s" -f $minutes, $seconds
    }

    # Pad name for alignment
    $paddedName = $result.Name.PadRight($maxNameLength)

    Write-Host "  [$status] " -ForegroundColor $color -NoNewline
    Write-Host "$paddedName " -NoNewline
    Write-Host "took " -ForegroundColor DarkGray -NoNewline
    Write-Host "$durationStr" -ForegroundColor Cyan -NoNewline

    # Show device for integration/e2e tests
    if ($result.Device) {
        $deviceColor = if ($result.Device -eq "cuda") { "Yellow" } else { "DarkGray" }
        Write-Host " on " -ForegroundColor DarkGray -NoNewline
        Write-Host "$($result.Device.ToUpper())" -ForegroundColor $deviceColor
    } else {
        Write-Host ""
    }
}

$separator = "=" * 70
Write-Host ""
Write-Host $separator

# Format total duration
$totalSeconds = $totalDuration.TotalSeconds
if ($totalSeconds -lt 60) {
    $totalDurationStr = "{0:F2}s" -f $totalSeconds
} elseif ($totalSeconds -lt 3600) {
    $minutes = [Math]::Floor($totalSeconds / 60)
    $seconds = $totalSeconds % 60
    $totalDurationStr = "{0}m {1:F0}s" -f $minutes, $seconds
} else {
    $hours = [Math]::Floor($totalSeconds / 3600)
    $remainingSeconds = $totalSeconds % 3600
    $minutes = [Math]::Floor($remainingSeconds / 60)
    $seconds = $remainingSeconds % 60
    $totalDurationStr = "{0}h {1}m {2:F0}s" -f $hours, $minutes, $seconds
}

Write-Host "Total: $($results.Count) tests | " -NoNewline
Write-Host "Passed: $passedCount" -ForegroundColor Green -NoNewline
Write-Host " | " -NoNewline
if ($failedCount -gt 0) {
    Write-Host "Failed: " -NoNewline
    Write-Host "$failedCount" -ForegroundColor Red -NoNewline
} else {
    Write-Host "Failed: $failedCount" -NoNewline
}
Write-Host " | " -NoNewline
Write-Host "Total Time: " -NoNewline
Write-Host "$totalDurationStr" -ForegroundColor Cyan
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
