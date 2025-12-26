# PowerShell launcher for Ren'Py grammar correction script
# Handles paths with special characters better than .bat

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$correctScript = Join-Path $scriptDir "scripts\correct.py"

# Pass all arguments to Python, properly quoted
& $pythonExe $correctScript $args
