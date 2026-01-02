# Extraction Script
# Extracts clean text and tags from .rpy translation files

param(
    [string]$Source = "",
    [string]$GameName = "",
    [switch]$All = $false
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

function Show-Banner {
    Write-Host ""
    Write-Host "" -ForegroundColor Cyan
    Write-Host "               Translation File Extraction                 " -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
    Write-Host ""
}

function Extract-File {
    param(
        [string]$FilePath,
        [string]$GamePath,
        [string]$Language,
        [string]$PythonCmd
    )

    $fileName = Split-Path $FilePath -Leaf
    Write-Host " Extracting: $fileName" -ForegroundColor Yellow

    # Prepare output paths
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
    $outputDir = Split-Path $FilePath -Parent
    $yamlPath = Join-Path $outputDir "$baseName.parsed.yaml"
    $jsonPath = Join-Path $outputDir "$baseName.tags.json"

    # Prepare Python script
    $scriptContent = @"
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, r'$PSScriptRoot\src')

from extract import RenpyExtractor

# Load characters.json if exists
characters_path = Path(r'$GamePath\game\tl\$Language\characters.json')
character_map = {}
if characters_path.exists():
    with open(characters_path, 'r', encoding='utf-8-sig') as f:
        chars = json.load(f)
        character_map = {k: v['name'] for k, v in chars.items()}

# Extract
extractor = RenpyExtractor(character_map)
parsed_blocks, tags_file = extractor.extract_file(
    Path(r'$FilePath'),
    target_language='$Language',
    source_language='english'
)

# Save files
extractor.save_parsed_yaml(parsed_blocks, Path(r'$yamlPath'))
extractor.save_tags_json(tags_file, Path(r'$jsonPath'))

yaml_path = r'$yamlPath'
json_path = r'$jsonPath'
print(f'\n Extraction complete!')
print(f'   YAML: {yaml_path}')
print(f'   JSON: {json_path}')
"@

    # Save script to temp file
    $tempScript = Join-Path $env:TEMP "extract_temp.py"
    $scriptContent | Set-Content $tempScript -Encoding UTF8

    # Run Python script with UTF-8 encoding
    try {
        $env:PYTHONIOENCODING = "utf-8"
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

if ($All) {
    # Extract all .rpy files
    Write-Host " Finding all .rpy files..." -ForegroundColor Yellow
    $rpyFiles = Get-ChildItem -Path $tlPath -Filter "*.rpy" -Recurse | Where-Object {
        $_.Name -notlike "*.parsed.*" -and $_.Name -notlike "*.tags.*"
    }

    if ($rpyFiles.Count -eq 0) {
        Write-Host " No .rpy files found!" -ForegroundColor Red
        exit 1
    }

    Write-Host "   Found $($rpyFiles.Count) files" -ForegroundColor Green
    Write-Host ""

    foreach ($file in $rpyFiles) {
        Extract-File `
            -FilePath $file.FullName `
            -GamePath $gameConfig.path `
            -Language $gameConfig.target_language `
            -PythonCmd $pythonCmd
        Write-Host ""
    }

} else {
    # Extract single file
    if ($Source -eq "") {
        # Prompt user to select
        Write-Host " Extract Options:" -ForegroundColor Yellow
        Write-Host "   [1] Extract all .rpy files" -ForegroundColor Cyan
        Write-Host "   [2] Extract specific file" -ForegroundColor Cyan
        Write-Host ""
        $choice = Read-Host "Select option (1-2)"

        if ($choice -eq "1") {
            # Extract all files
            Write-Host ""
            Write-Host " Finding all .rpy files..." -ForegroundColor Yellow
            $rpyFiles = Get-ChildItem -Path $tlPath -Filter "*.rpy" -Recurse | Where-Object {
                $_.Name -notlike "*.parsed.*" -and $_.Name -notlike "*.tags.*"
            }

            if ($rpyFiles.Count -eq 0) {
                Write-Host " No .rpy files found!" -ForegroundColor Red
                exit 1
            }

            Write-Host "   Found $($rpyFiles.Count) files" -ForegroundColor Green
            Write-Host ""

            foreach ($file in $rpyFiles) {
                Extract-File `
                    -FilePath $file.FullName `
                    -GamePath $gameConfig.path `
                    -Language $gameConfig.target_language `
                    -PythonCmd $pythonCmd
                Write-Host ""
            }
        }
        elseif ($choice -eq "2") {
            # List available files
            Write-Host ""
            Write-Host " Available .rpy files:" -ForegroundColor Yellow
            Write-Host ""

            $rpyFiles = Get-ChildItem -Path $tlPath -Filter "*.rpy" -Recurse | Where-Object {
                $_.Name -notlike "*.parsed.*" -and $_.Name -notlike "*.tags.*"
            }

            if ($rpyFiles.Count -eq 0) {
                Write-Host " No .rpy files found!" -ForegroundColor Red
                exit 1
            }

            for ($i = 0; $i -lt $rpyFiles.Count; $i++) {
                Write-Host "   [$($i + 1)] $($rpyFiles[$i].Name)" -ForegroundColor Cyan
            }

            Write-Host ""
            $selection = Read-Host "Select file (1-$($rpyFiles.Count))"

            try {
                $index = [int]$selection - 1
                if ($index -lt 0 -or $index -ge $rpyFiles.Count) {
                    Write-Host "Invalid selection!" -ForegroundColor Red
                    exit 1
                }
                $selectedFile = $rpyFiles[$index]
                Write-Host ""
                Extract-File `
                    -FilePath $selectedFile.FullName `
                    -GamePath $gameConfig.path `
                    -Language $gameConfig.target_language `
                    -PythonCmd $pythonCmd
            } catch {
                Write-Host "Invalid input!" -ForegroundColor Red
                exit 1
            }
        }
        else {
            Write-Host "Invalid option!" -ForegroundColor Red
            exit 1
        }
    }
    else {
        # Source file specified via parameter
        $fullPath = Join-Path $tlPath $Source
        if (-not (Test-Path $fullPath)) {
            Write-Host " File not found: $fullPath" -ForegroundColor Red
            exit 1
        }

        Extract-File `
            -FilePath $fullPath `
            -GamePath $gameConfig.path `
            -Language $gameConfig.target_language `
            -PythonCmd $pythonCmd
    }
}

Write-Host ""
Write-Host " Extraction complete!" -ForegroundColor Green
Write-Host ""
Write-Host " Next steps:" -ForegroundColor Yellow
Write-Host "   1. Review the .parsed.yaml files for any issues" -ForegroundColor Gray
Write-Host "   2. Run '3-translate.ps1' to translate untranslated blocks" -ForegroundColor Gray
Write-Host ""
