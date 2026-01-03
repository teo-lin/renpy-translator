# Merge Script
# Merges translated YAML + tags YAML back into .rpy files

param(
    [string]$Source = "",
    [string]$GameName = "",
    [switch]$All = $false,
    [switch]$SkipValidation = $false
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

function Show-Banner {
    Write-Host ""
    Write-Host "" -ForegroundColor Cyan
    Write-Host "               Translation File Merge                      " -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
    Write-Host ""
}

function Merge-File {
    param(
        [string]$YamlPath,
        [string]$PythonCmd,
        [bool]$Validate
    )

    $fileName = Split-Path $YamlPath -Leaf
    Write-Host " Merging: $fileName" -ForegroundColor Yellow

    # Prepare paths
    $baseName = $fileName -replace '\.parsed\.yaml$', ''
    $outputDir = Split-Path $YamlPath -Parent
    $tagsYamlPath = Join-Path $outputDir "$baseName.tags.yaml"
    $outputPath = Join-Path $outputDir "$baseName.translated.rpy"

    # Check if tags file exists
    if (-not (Test-Path $tagsYamlPath)) {
        Write-Host " Tags YAML file not found: $tagsYamlPath" -ForegroundColor Red
        return
    }

    # Prepare Python script
    $validateFlag = if ($Validate) { "True" } else { "False" }

    $scriptContent = @"
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, r'$PSScriptRoot\src')

from merge import RenpyMerger

# Merge
merger = RenpyMerger()
success = merger.merge_file(
    parsed_yaml_path=Path(r'$YamlPath'),
    tags_yaml_path=Path(r'$tagsYamlPath'),
    output_rpy_path=Path(r'$outputPath'),
    validate=$validateFlag
)

if not success:
    print('\n  Validation found issues. Please review the output file.')
    print(merger.get_validation_report())

print(f'\n Merge complete!')
print(f'   Output: $outputPath')
"@

    # Save script to temp file
    $tempScript = Join-Path $env:TEMP "merge_temp.py"
    $scriptContent | Set-Content $tempScript -Encoding UTF8

    # Run Python script
    try {
        & $PythonCmd $tempScript
        if ($LASTEXITCODE -ne 0) {
            throw "Python script failed with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Show-Banner

# Get Python command
$pythonCmd = Get-PythonCommand

# Select game
if ($GameName -eq "") {
    $GameName = Select-ConfiguredGame
    Update-CurrentGame -GameName $GameName
}

# Get game config
$gameConfig = Get-GameConfig -GameName $GameName
Show-GameInfo -GameConfig $gameConfig

# Get source file(s)
$tlPath = Join-Path $gameConfig.path "game\tl\$($gameConfig.target_language.Name.ToLower())"
$validate = -not $SkipValidation

if ($All) {
    # Merge all .parsed.yaml files
    Write-Host " Finding all .parsed.yaml files..." -ForegroundColor Yellow
    $yamlFiles = Get-ChildItem -Path $tlPath -Filter "*.parsed.yaml" -Recurse

    if ($yamlFiles.Count -eq 0) {
        Write-Host " No .parsed.yaml files found!" -ForegroundColor Red
        Write-Host "   Run 2-extract.ps1 first" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "   Found $($yamlFiles.Count) files" -ForegroundColor Green
    Write-Host ""

    foreach ($file in $yamlFiles) {
        Merge-File `
            -YamlPath $file.FullName `
            -PythonCmd $pythonCmd `
            -Validate $validate
        Write-Host ""
    }

} else {
    # Merge single file
    if ($Source -eq "") {
        Write-Host " Please specify -Source <filename> or use -All" -ForegroundColor Red
        Write-Host "   Example: .\x5-merge.ps1 -Source Cell01_JM" -ForegroundColor Yellow
        exit 1
    }

    # Find YAML file
    $yamlPath = Join-Path $tlPath "$Source.parsed.yaml"
    if (-not (Test-Path $yamlPath)) {
        Write-Host " YAML file not found: $yamlPath" -ForegroundColor Red
        exit 1
    }

    Merge-File `
        -YamlPath $yamlPath `
        -PythonCmd $pythonCmd `
        -Validate $validate
}

Write-Host "" 
Write-Host " Merge complete!" -ForegroundColor Green
Write-Host "" 
Write-Host " Next steps:" -ForegroundColor Yellow
Write-Host "   1. Review the .translated.rpy files" -ForegroundColor Gray
Write-Host "   2. Test the translations in the game" -ForegroundColor Gray
Write-Host "   3. Replace the original .rpy files if satisfied" -ForegroundColor Gray
Write-Host ""
