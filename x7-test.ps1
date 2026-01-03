# Ren'Py Translation System - Automated Testing Script (Thin Wrapper)
# Run as: .\x7-test.ps1 [--unit | --int | --e2e]

param(
    [switch]$Unit,   # Run only test_unit_* tests
    [switch]$Int,    # Run only test_int_* tests (integration tests)
    [switch]$E2e     # Run only test_e2e_* tests (end-to-end tests)
)

$ErrorActionPreference = "Stop"

# Determine test category
$category = $null
if ($Unit) {
    $category = "unit"
} elseif ($Int) {
    $category = "int"
} elseif ($E2e) {
    $category = "e2e"
}

# Get Python command
$pythonCmd = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

# Prepare Python script
$scriptContent = @"
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, r'$PSScriptRoot')

from tests.utils import TestRunner

# Run tests
runner = TestRunner(Path(r'$PSScriptRoot'))
exit_code = runner.run(category=$(if ($category) { "'$category'" } else { "None" }))
sys.exit(exit_code)
"@

# Save script to temp file
$tempScript = Join-Path $env:TEMP "test_runner_temp.py"
$scriptContent | Set-Content $tempScript -Encoding UTF8

# Run Python script
try {
    & $pythonCmd $tempScript
    $exitCode = $LASTEXITCODE
} finally {
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}

exit $exitCode
