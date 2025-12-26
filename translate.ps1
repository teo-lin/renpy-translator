# PowerShell launcher for Ren'Py translation script
# Handles paths with special characters better than .bat

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$translateScript = Join-Path $scriptDir "scripts\translate.py"

# Pass all arguments to Python, properly quoted
& $pythonExe $translateScript $args
