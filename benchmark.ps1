# PowerShell launcher for translation benchmark script
# Handles paths with special characters better than .bat

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$benchmarkScript = Join-Path $scriptDir "scripts\benchmark.py"

# Pass all arguments to Python, properly quoted
& $pythonExe $benchmarkScript $args
