# Interactive PowerShell launcher for Ren'Py translation
# Guided workflow: Model -> Language -> Game selection

param(
    [int]$Model = 0,      # Model number (1-based), 0 = prompt user
    [int]$Language = 0,   # Language number (1-based), 0 = prompt user
    [int]$Game = 0,       # Game number (1-based), 0 = prompt user
    [switch]$Yes,         # Skip confirmation prompt
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments  # Additional arguments to pass to Python script
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Source the shared user selection module
. (Join-Path $scriptDir "scripts\select.ps1")

$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
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

# Load configuration
if (-not (Test-Path $configFile)) {
    Write-Host "ERROR: Configuration not found at models\current_config.json" -ForegroundColor Red
    Write-Host "Please run setup.ps1 first." -ForegroundColor Yellow
    exit 1
}

$config = Get-Content $configFile | ConvertFrom-Json

# Get models as an array
if ($config.models -is [array]) {
    $allModels = $config.models
} else {
    $allModels = @($config.models)
}

# Filter to only include downloaded models
$installedModels = @()
foreach ($modelItem in $allModels) {
    $modelPath = Join-Path $scriptDir $modelItem.Config.destination
    if (Test-Path $modelPath) {
        $installedModels += $modelItem
    }
}

# Get languages as an array
if ($config.languages -is [array]) {
    $languages = $config.languages
} else {
    $languages = @($config.languages)
}

# Banner
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Ren'Py Translation - Interactive Setup                   " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Step 1: Select Model
if ($Model -gt 0) {
    if ($Model -le $installedModels.Count) {
        $selectedModel = $installedModels[$Model - 1]
        Write-Host ""
        Write-Host "Auto-selecting model $Model`: $($selectedModel.Name)" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Invalid model number: $Model. Available models: 1-$($installedModels.Count)" -ForegroundColor Red
        exit 1
    }
} else {
    try {
        $selectedModel = Select-Item `
            -Title "Step 1: Select Translation Model" `
            -ItemTypeName "model" `
            -Items $installedModels `
            -DisplayItem {
                param($model, $num)
                Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
                Write-Host $model.Name -NoNewline -ForegroundColor Green
                Write-Host " - $($model.Description)" -ForegroundColor White
                Write-Host "      Size: $($model.Size)" -ForegroundColor DarkGray
                Write-Host ""
            }
    } catch {
        Write-Host "Selection cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Step 2: Select Language
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
            -Title "Step 3: Select Game to Translate" `
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
Write-Host "       Translation Summary                                       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Model:    " -NoNewline -ForegroundColor White
Write-Host $selectedModel.Name -ForegroundColor Green
Write-Host "  Language: " -NoNewline -ForegroundColor White
Write-Host "$($selectedLanguage.Name) ($($selectedLanguage.Code))" -ForegroundColor Green
Write-Host "  Game:     " -NoNewline -ForegroundColor White
Write-Host $selectedGame.Name -ForegroundColor Green
Write-Host "  Path:     " -NoNewline -ForegroundColor White
Write-Host $selectedGame.Path -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Yes) {
    $confirm = Read-Host "Proceed with translation? (Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "Cancelled by user." -ForegroundColor Yellow
        exit 0
    }
}

# Get the model script path
$modelScript = Join-Path $scriptDir $selectedModel.Config.script

# Check if script exists
if (-not (Test-Path $modelScript)) {
    Write-Host ""
    Write-Host "ERROR: Translation script not found at $modelScript" -ForegroundColor Red
    exit 1
}

# Build arguments
$scriptArgs = @($selectedGame.Path, "--language", $selectedLanguage.Code)
if ($Arguments.Count -gt 0) {
    $scriptArgs += $Arguments
}

# Run the selected translation script
Write-Host ""
Write-Host "Starting translation with $($selectedModel.Name)..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe $modelScript $scriptArgs

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Translation failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Translation Completed Successfully!                      " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
