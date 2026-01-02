# Interactive PowerShell launcher for Ren'Py grammar correction
# Guided workflow: Mode -> Language -> Game selection

param(
    [int]$Mode = 0,       # Mode number (1-based), 0 = prompt user
    [string]$ModeName,    # Mode name (e.g., "Both (Patterns + LLM)")
    [int]$Language = 0,   # Language number (1-based), 0 = prompt user
    [string]$LanguageName, # Language name (e.g., "romanian")
    [int]$Game = 0,       # Game number (1-based), 0 = prompt user
    [string]$GameName,     # Game name (e.g., "Example")
    [switch]$Yes,         # Skip confirmation prompt
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments  # Additional arguments to pass to Python script
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Source the shared user selection module
. (Join-Path $scriptDir "scripts\select.ps1")

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$correctScript = Join-Path $scriptDir "scripts\correct.py"
$gamesFolder = Join-Path $scriptDir "games"
$configFile = Join-Path $scriptDir "models\current_config.json"

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Set UTF-8 encoding for Python
$env:PYTHONIOENCODING = "utf-8"

# Check Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please run setup.ps1 to install the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Check correction script exists
if (-not (Test-Path $correctScript)) {
    Write-Host "ERROR: Correction script not found at $correctScript" -ForegroundColor Red
    exit 1
}

# Define available correction modes
$modes = @(
    @{
        Name = "Both (Patterns + LLM)"
        Description = "Apply pattern corrections, then LLM corrections (recommended)"
        Flag = $null
        Details = "Speed: Slow (~2-3s/sentence) | Quality: Best | Uses: Aya-23-8B + JSON rules"
    },
    @{
        Name = "Patterns Only"
        Description = "Fast pattern-based corrections using JSON rules"
        Flag = "--patterns-only"
        Details = "Speed: Very fast (<1s/file) | Quality: Good | Uses: JSON correction rules"
    },
    @{
        Name = "LLM Only"
        Description = "AI-powered corrections using Aya-23-8B model"
        Flag = "--llm-only"
        Details = "Speed: Slow (~2-3s/sentence) | Quality: Best | Uses: Aya-23-8B only"
    }
)

# Load available languages from models_config.json
$modelsConfigPath = Join-Path $scriptDir "models\models_config.json"
if (Test-Path $modelsConfigPath) {
    $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
    $languages = $modelsConfig.installed_languages
} else {
    Write-Host "ERROR: models_config.json not found at $modelsConfigPath" -ForegroundColor Red
    exit 1
}

# Banner
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Ren'Py Grammar Correction - Interactive Setup            " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Step 1: Select Mode
if ($ModeName) {
    $foundMode = $modes | Where-Object { $_.Name -eq $ModeName }
    if ($foundMode) {
        $Mode = ($modes.IndexOf($foundMode) + 1)
        Write-Host ""
        Write-Host "Auto-selecting mode by name '$ModeName'. Resolved to index $Mode." -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid mode name: $ModeName. Available modes: $($modes.Name -join ', ')" -ForegroundColor Red
        exit 1
    }
}
if ($Mode -gt 0) {
    if ($Mode -le $modes.Count) {
        $selectedMode = $modes[$Mode - 1]
        Write-Host ""
        Write-Host "Auto-selecting mode $Mode`: $($selectedMode.Name)" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid mode number: $Mode. Available modes: 1-$($modes.Count)" -ForegroundColor Red
        exit 1
    }
} else {
    try {
        $selectedMode = Select-Item `
            -Title "Step 1: Select Correction Mode" `
            -ItemTypeName "mode" `
            -Items $modes `
            -DisplayItem {
                param($mode, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host $mode.Name -NoNewline -ForegroundColor Green
                Write-Host " - $($mode.Description)" -ForegroundColor White
                Write-Host "      $($mode.Details)" -ForegroundColor DarkGray
                Write-Host ""
            }
    } catch {
        Write-Host "Selection cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Step 2: Select Language
if ($LanguageName) {
    $foundLanguage = $languages | Where-Object { $_.Code -eq $LanguageName }
    if ($foundLanguage) {
        $Language = ($languages.IndexOf($foundLanguage) + 1)
        Write-Host ""
        Write-Host "Auto-selecting language by name '$LanguageName'. Resolved to index $Language." -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid language name: $LanguageName. Available languages: $($languages.Name -join ', ')" -ForegroundColor Red
        exit 1
    }
}
if ($Language -gt 0) {
    if ($Language -le $languages.Count) {
        $selectedLanguage = $languages[$Language - 1]
        Write-Host ""
        Write-Host "Auto-selecting language $Language`: $($selectedLanguage.Name) ($($selectedLanguage.Code))" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid language number: $Language. Available languages: 1-$($languages.Count)" -ForegroundColor Red
        exit 1
    }
} else {
    try {
        $selectedLanguage = Select-Item `
            -Title "Step 2: Select Target Language" `
            -ItemTypeName "language" `
            -Items $languages `
            -DisplayItem {
                param($lang, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host "$($lang.Name) " -NoNewline -ForegroundColor Green
                Write-Host "($($lang.Code))" -ForegroundColor DarkGray
            }
    } catch {
        Write-Host "Selection cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Step 3: Scan games and select game
Write-Host ""
Write-Host "Scanning games folder for $($selectedLanguage.Name) translations..." -ForegroundColor Cyan

# Scan games folder
$games = @()
if (Test-Path $gamesFolder) {
    $gameFolders = Get-ChildItem -Path $gamesFolder -Directory
    foreach ($gameFolder in $gameFolders) {
        $tlPath = Join-Path $gameFolder.FullName "game\tl\$($selectedLanguage.Name.ToLower())"
        if (Test-Path $tlPath) {
            $renpyFiles = Get-ChildItem -Path $tlPath -Filter "*.rpy" -Recurse
            if ($renpyFiles.Count -gt 0) {
                $games += @{
                    Name = $gameFolder.Name
                    Path = $tlPath
                }
            }
        }
    }
}

if ($games.Count -eq 0) {
    Write-Host ""
    Write-Host "ERROR: No games found with $($selectedLanguage.Name) translations!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please generate translation files first using Ren'Py:" -ForegroundColor Yellow
    Write-Host "  renpy.exe `"path\to\game`" generate-translations $($selectedLanguage.Name.ToLower())" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

if ($GameName) {
    $foundGame = $games | Where-Object { $_.Name -eq $GameName }
    if ($foundGame) {
        $Game = ($games.IndexOf($foundGame) + 1)
        Write-Host ""
        Write-Host "Auto-selecting game by name '$GameName'. Resolved to index $Game." -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid game name: $GameName. Available games: $($games.Name -join ', ')" -ForegroundColor Red
        exit 1
    }
}
if ($Game -gt 0) {
    if ($Game -le $games.Count) {
        $selectedGame = $games[$Game - 1]
        Write-Host ""
        Write-Host "Auto-selecting game $Game`: $($selectedGame.Name)" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid game number: $Game. Available games: 1-$($games.Count)" -ForegroundColor Red
        exit 1
    }
} else {
    try {
        $selectedGame = Select-Item `
            -Title "Step 3: Select Game to Correct" `
            -ItemTypeName "game" `
            -Items $games `
            -DisplayItem {
                param($game, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host $game.Name -ForegroundColor Green
                Write-Host "      Path: $($game.Path)" -ForegroundColor DarkGray
            }
    } catch {
        Write-Host "Selection cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Summary
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       Correction Summary                                        " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Mode:     " -NoNewline -ForegroundColor White
Write-Host $selectedMode.Name -ForegroundColor Green
Write-Host "  Language: " -NoNewline -ForegroundColor White
Write-Host "$($selectedLanguage.Name) ($($selectedLanguage.Code))" -ForegroundColor Green
Write-Host "  Game:     " -NoNewline -ForegroundColor White
Write-Host $selectedGame.Name -ForegroundColor Green
Write-Host "  Path:     " -NoNewline -ForegroundColor White
Write-Host $selectedGame.Path -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Yes) {
    $confirm = Read-Host "Proceed with correction? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

# Build arguments
$scriptArgs = @($selectedGame.Path, "--language", $selectedLanguage.Code)
if ($selectedMode.Flag) {
    $scriptArgs += $selectedMode.Flag
}
if ($Arguments.Count -gt 0) {
    $scriptArgs += $Arguments
}

# Run the correction script
Write-Host ""
Write-Host "Starting correction with mode: $($selectedMode.Name)..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe $correctScript $scriptArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Correction failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Correction Completed Successfully!                       " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
