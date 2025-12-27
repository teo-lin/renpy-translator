# Interactive PowerShell launcher for Ren'Py grammar correction
# Guided workflow: Mode -> Language -> Game selection

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$correctScript = Join-Path $scriptDir "scripts\correct_with_aya23.py"
$gamesFolder = Join-Path $scriptDir "games"

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

# Load configured languages from setup
$configFile = Join-Path $scriptDir "models\local_config.json"

if (Test-Path $configFile) {
    try {
        $savedConfig = Get-Content $configFile | ConvertFrom-Json
        $languages = $savedConfig.languages
        Write-Host "Loaded $($languages.Count) configured language(s) from setup" -ForegroundColor DarkGray
    }
    catch {
        Write-Host "WARNING: Could not load language configuration. Using all languages." -ForegroundColor Yellow
        # Fallback to all languages
        $languages = @(
            @{Name = "Romanian"; Code = "ro"},
            @{Name = "Spanish"; Code = "es"},
            @{Name = "French"; Code = "fr"},
            @{Name = "German"; Code = "de"},
            @{Name = "Italian"; Code = "it"},
            @{Name = "Portuguese"; Code = "pt"},
            @{Name = "Russian"; Code = "ru"},
            @{Name = "Turkish"; Code = "tr"},
            @{Name = "Czech"; Code = "cs"},
            @{Name = "Polish"; Code = "pl"},
            @{Name = "Ukrainian"; Code = "uk"},
            @{Name = "Bulgarian"; Code = "bg"},
            @{Name = "Chinese"; Code = "zh"},
            @{Name = "Japanese"; Code = "ja"},
            @{Name = "Korean"; Code = "ko"},
            @{Name = "Vietnamese"; Code = "vi"},
            @{Name = "Thai"; Code = "th"},
            @{Name = "Indonesian"; Code = "id"},
            @{Name = "Arabic"; Code = "ar"},
            @{Name = "Hebrew"; Code = "he"},
            @{Name = "Persian"; Code = "fa"},
            @{Name = "Hindi"; Code = "hi"},
            @{Name = "Bengali"; Code = "bn"},
            @{Name = "Dutch"; Code = "nl"},
            @{Name = "Swedish"; Code = "sv"},
            @{Name = "Norwegian"; Code = "no"},
            @{Name = "Danish"; Code = "da"},
            @{Name = "Finnish"; Code = "fi"},
            @{Name = "Greek"; Code = "el"},
            @{Name = "Hungarian"; Code = "hu"}
        )
    }
}
else {
    Write-Host "WARNING: Configuration not found at models\local_config.json" -ForegroundColor Yellow
    Write-Host "Please run setup.ps1 first. Using all 30 languages as fallback..." -ForegroundColor DarkGray
    # Fallback to all languages
    $languages = @(
        @{Name = "Romanian"; Code = "ro"},
        @{Name = "Spanish"; Code = "es"},
        @{Name = "French"; Code = "fr"},
        @{Name = "German"; Code = "de"},
        @{Name = "Italian"; Code = "it"},
        @{Name = "Portuguese"; Code = "pt"},
        @{Name = "Russian"; Code = "ru"},
        @{Name = "Turkish"; Code = "tr"},
        @{Name = "Czech"; Code = "cs"},
        @{Name = "Polish"; Code = "pl"},
        @{Name = "Ukrainian"; Code = "uk"},
        @{Name = "Bulgarian"; Code = "bg"},
        @{Name = "Chinese"; Code = "zh"},
        @{Name = "Japanese"; Code = "ja"},
        @{Name = "Korean"; Code = "ko"},
        @{Name = "Vietnamese"; Code = "vi"},
        @{Name = "Thai"; Code = "th"},
        @{Name = "Indonesian"; Code = "id"},
        @{Name = "Arabic"; Code = "ar"},
        @{Name = "Hebrew"; Code = "he"},
        @{Name = "Persian"; Code = "fa"},
        @{Name = "Hindi"; Code = "hi"},
        @{Name = "Bengali"; Code = "bn"},
        @{Name = "Dutch"; Code = "nl"},
        @{Name = "Swedish"; Code = "sv"},
        @{Name = "Norwegian"; Code = "no"},
        @{Name = "Danish"; Code = "da"},
        @{Name = "Finnish"; Code = "fi"},
        @{Name = "Greek"; Code = "el"},
        @{Name = "Hungarian"; Code = "hu"}
    )
}

# Helper function to display menu and get selection
function Show-Menu {
    param(
        [string]$Title,
        [array]$Items,
        [scriptblock]$DisplayItem
    )

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "       $Title" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $Items.Count; $i++) {
        $num = $i + 1
        & $DisplayItem $Items[$i] $num
    }

    Write-Host "  [Q] Quit" -ForegroundColor Red
    Write-Host ""

    while ($true) {
        $selection = Read-Host "Select (1-$($Items.Count) or Q)"

        if ($selection -eq "Q" -or $selection -eq "q") {
            Write-Host "Cancelled by user." -ForegroundColor Yellow
            exit 0
        }

        try {
            $index = [int]$selection - 1
            if ($index -ge 0 -and $index -lt $Items.Count) {
                return $Items[$index]
            }
            else {
                Write-Host "Invalid selection. Please enter a number between 1 and $($Items.Count)." -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Invalid input. Please enter a number or Q to quit." -ForegroundColor Red
        }
    }
}

# Function to scan games folder and find games with specific language
function Get-GamesWithLanguage {
    param([string]$LanguageFolder)

    if (-not (Test-Path $gamesFolder)) {
        Write-Host "ERROR: Games folder not found at $gamesFolder" -ForegroundColor Red
        return @{Available = @(); Missing = @()}
    }

    $allGames = Get-ChildItem -Path $gamesFolder -Directory
    $availableGames = @()
    $missingGames = @()

    foreach ($game in $allGames) {
        $tlPath = Join-Path $game.FullName "game\tl\$LanguageFolder"

        if (Test-Path $tlPath) {
            $availableGames += @{
                Name = $game.Name
                Path = $tlPath
                FullPath = $game.FullName
            }
        }
        else {
            $missingGames += $game.Name
        }
    }

    return @{
        Available = $availableGames
        Missing = $missingGames
    }
}

# Step 1: Select Mode
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       Ren'Py Grammar Correction - Interactive Setup            " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

if ($modes.Count -eq 1) {
    $selectedMode = $modes[0]
    Write-Host ""
    Write-Host "Auto-selecting the only available mode: $($selectedMode.Name)" -ForegroundColor Cyan
} else {
    $selectedMode = Show-Menu -Title "Step 1: Select Correction Mode" -Items $modes -DisplayItem {
        param($mode, $num)
        Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
        Write-Host $mode.Name -NoNewline -ForegroundColor Green
        if ($num -eq 1) {
            Write-Host " (Recommended)" -NoNewline -ForegroundColor Magenta
        }
        Write-Host ""
        Write-Host "      $($mode.Description)" -ForegroundColor White
        Write-Host "      $($mode.Details)" -ForegroundColor DarkGray
        Write-Host ""
    }
}

# Step 2: Select Language
if ($languages.Count -eq 1) {
    $selectedLanguage = $languages[0]
    Write-Host ""
    Write-Host "Auto-selecting the only available language: $($selectedLanguage.Name) ($($selectedLanguage.Code))" -ForegroundColor Cyan
} else {
    $selectedLanguage = Show-Menu -Title "Step 2: Select Target Language" -Items $languages -DisplayItem {
        param($lang, $num)
        Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
        Write-Host "$($lang.Name) " -NoNewline -ForegroundColor Green
        Write-Host "($($lang.Code))" -ForegroundColor DarkGray
    }
}# Step 3: Scan games and select game
Write-Host ""
Write-Host "Scanning games folder for $($selectedLanguage.Name) translations..." -ForegroundColor Cyan

$gameInfo = Get-GamesWithLanguage -LanguageFolder $selectedLanguage.Name.ToLower()

# Show warning if any games are missing the language
if ($gameInfo.Missing.Count -gt 0) {
    Write-Host ""
    Write-Host "WARNING: The following games do not have $($selectedLanguage.Name) translations:" -ForegroundColor Yellow
    foreach ($gameName in $gameInfo.Missing) {
        Write-Host "  - $gameName" -ForegroundColor DarkYellow
    }
    Write-Host ""
    Write-Host "To add $($selectedLanguage.Name) translations to these games, run:" -ForegroundColor DarkGray
    Write-Host "  renpy.exe `"path\to\game`" generate-translations $($selectedLanguage.Name.ToLower())" -ForegroundColor DarkGray
}

# Check if any games are available
if ($gameInfo.Available.Count -eq 0) {
    Write-Host ""
    Write-Host "ERROR: No games found with $($selectedLanguage.Name) translations!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please generate translation files first using Ren'Py:" -ForegroundColor Yellow
    Write-Host "  renpy.exe `"path\to\game`" generate-translations $($selectedLanguage.Name.ToLower())" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

$selectedGame = Show-Menu -Title "Step 3: Select Game to Correct" -Items $gameInfo.Available -DisplayItem {
    param($game, $num)
    Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
    Write-Host $game.Name -ForegroundColor Green
    Write-Host "      Path: $($game.Path)" -ForegroundColor DarkGray
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

$confirm = Read-Host "Proceed with correction? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled by user." -ForegroundColor Yellow
    exit 0
}

# Check if Python executable exists
if (-not (Test-Path $pythonExe)) {
    Write-Host ""
    Write-Host "ERROR: Python executable not found at $pythonExe" -ForegroundColor Red
    Write-Host "Please run setup.ps1 to install the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Check if script exists
if (-not (Test-Path $correctScript)) {
    Write-Host ""
    Write-Host "ERROR: Correction script not found at $correctScript" -ForegroundColor Red
    exit 1
}

# Build arguments
$scriptArgs = @()
if ($selectedMode.Flag) {
    $scriptArgs += $selectedMode.Flag
}
$scriptArgs += $selectedGame.Path
if ($Arguments.Count -gt 0) {
    $scriptArgs += $Arguments
}

# Run the correction script
Write-Host ""
Write-Host "Starting grammar correction..." -ForegroundColor Cyan
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
