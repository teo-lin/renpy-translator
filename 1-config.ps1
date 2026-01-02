# Character Discovery and Configuration Script
# Discovers characters from game translation files and configures game settings

param(
    [string]$GamePath = "",
    [string]$Language = "",
    [string]$Model = ""
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

# Set HuggingFace home to local models directory
$env:HF_HOME = Join-Path $PSScriptRoot "models"

function Show-Banner {
    Write-Host ""
    Write-Host "" -ForegroundColor Cyan
    Write-Host "         Character Discovery & Game Configuration          " -ForegroundColor Cyan
    Write-Host "" -ForegroundColor Cyan
    Write-Host ""
}

function Select-Game {
    Write-Host "[Game] Available Games:" -ForegroundColor Yellow
    Write-Host ""

    $gamesDir = Join-Path $PSScriptRoot "games"
    if (-not (Test-Path $gamesDir)) {
        new-Item -ItemType Directory -Path $gamesDir -Force | Out-null
    }

    $games = Get-ChildItem -Path $gamesDir -Directory

    if ($games.Count -eq 0) {
        Write-Host "   no games found in 'games' directory!" -ForegroundColor Red
        Write-Host "   Please add your game folders to: $gamesDir" -ForegroundColor Yellow
        exit 1
    }

    for ($i = 0; $i -lt $games.Count; $i++) {
        Write-Host "   [$($i + 1)] $($games[$i].name)" -ForegroundColor Cyan
    }

    Write-Host ""
    $selection = Read-Host "Select game (1-$($games.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $games.Count) {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
        return $games[$index]
    } catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Select-Language {
    Write-Host "[Language] Available Languages:" -ForegroundColor Yellow
    Write-Host ""

    $modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"
    if (-not (Test-Path $modelsConfigPath)) {
        Write-Host "Models configuration not found at $modelsConfigPath. Please run 0-setup.ps1." -ForegroundColor Red
        exit 1
    }
    $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json

    if (-not $modelsConfig.installed_languages -or $modelsConfig.installed_languages.Count -eq 0) {
        Write-Host "No languages configured in models_config.json. Please run 0-setup.ps1 and select languages." -ForegroundColor Red
        exit 1
    }

    $languages = $modelsConfig.installed_languages

    for ($i = 0; $i -lt $languages.Count; $i++) {
        Write-Host "   [$($i + 1)] $($languages[$i].Name) ($($languages[$i].Code))" -ForegroundColor Cyan
    }

    Write-Host ""
    if ($languages.Count -eq 1) {
        Write-Host "Auto-selecting the only available language: $($languages[0].Name)" -ForegroundColor Green
        return $languages[0]
    }

    $selection = Read-Host "Select language (1-$($languages.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $languages.Count) {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
        return $languages[$index]
    } catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Select-Model {
    # Load models configuration
    $modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"

    if (-not (Test-Path $modelsConfigPath)) {
        Write-Host "[ERROR] Models configuration not found at $modelsConfigPath" -ForegroundColor Red
        Write-Host "Please run 0-setup.ps1 first to configure models." -ForegroundColor Yellow
        exit 1
    }

    $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json

    # Get installed models
    if (-not $modelsConfig.installed_models -or $modelsConfig.installed_models.Count -eq 0) {
        Write-Host "[ERROR] No models are installed!" -ForegroundColor Red
        Write-Host "Please run 0-setup.ps1 first to install models." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "[Model] Installed Models:" -ForegroundColor Yellow
    Write-Host ""

    # Build list of installed models
    $installedModels = @()
    foreach ($modelKey in $modelsConfig.installed_models) {
        $modelConfig = $modelsConfig.available_models.$modelKey
        if ($modelConfig) {
            $installedModels += @{
                Key = $modelKey
                Name = $modelConfig.name
                Size = $modelConfig.size
                Description = $modelConfig.description
            }
        }
    }

    # Display models
    for ($i = 0; $i -lt $installedModels.Count; $i++) {
        $num = $i + 1
        $model = $installedModels[$i]
        Write-Host "   [$num] $($model.Name) ($($model.Size))" -ForegroundColor Cyan
    }
    Write-Host ""

    # Auto-select if only one model
    if ($installedModels.Count -eq 1) {
        $selectedModel = $installedModels[0]
        Write-Host "Auto-selecting the only installed model: $($selectedModel.Name)" -ForegroundColor Green
        return $selectedModel.Key
    }

    # Get user selection
    $selection = Read-Host "Select model (1-$($installedModels.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -ge 0 -and $index -lt $installedModels.Count) {
            return $installedModels[$index].Key
        }
        else {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Discover-Characters {
    param(
        [string]$TlPath
    )

    Write-Host ""
    Write-Host "[Search] Discovering characters from .rpy files..." -ForegroundColor Yellow

    $characterVars = @{}
    $characterFiles = @{}  # Track which files each character appears in
    $rpyFiles = Get-ChildItem -Path $TlPath -Filter "*.rpy" -Recurse

    foreach ($file in $rpyFiles) {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $fileName = $file.BaseName

        # Find dialogue patterns: character_var "text"
        $matches = [regex]::Matches($content, '^\s*(\w+)\s+"[^"\\]*(?:\\.[^"\\]*)*"', [Text.RegularExpressions.RegexOptions]::Multiline)

        foreach ($match in $matches) {
            $charVar = $match.Groups[1].Value

            # Skip if it's a keyword
            if ($charVar -match '^(translate|old|new)$') {
                continue
            }

            if (-not $characterVars.ContainsKey($charVar)) {
                $characterVars[$charVar] = @{
                    name = $charVar.ToUpper()
                    gender = "neutral"
                    type = "supporting"
                    description = ""
                }
                $characterFiles[$charVar] = @()
            }

            # Track this file for the character
            if ($characterFiles[$charVar] -notcontains $fileName) {
                $characterFiles[$charVar] += $fileName
            }
        }
    }

    # Extract character names from script.rpy define statements
    Write-Host "   [Search] Extracting character names from script.rpy..." -ForegroundColor Yellow

    $gamePath = Split-Path (Split-Path $TlPath -Parent) -Parent
    $scriptFiles = Get-ChildItem -Path $gamePath -Filter "script*.rpy" -Recurse | Where-Object { $_.FullName -notmatch "\\tl\\" }

    foreach ($scriptFile in $scriptFiles) {
        $content = Get-Content -Path $scriptFile.FullName -Raw -Encoding UTF8

        # Match: define var = Character('Name', ...) or Character(None)
        $defineMatches = [regex]::Matches($content, 'define\s+(\w+)\s*=\s*Character\((?:[''"](.+?)[''"]|None)\s*[,)]')

        foreach ($match in $defineMatches) {
            $charVar = $match.Groups[1].Value
            $charName = $match.Groups[2].Value

            # Initialize character in $characterVars if it doesn't exist
            if (-not $characterVars.ContainsKey($charVar)) {
                $characterVars[$charVar] = @{
                    name = $charVar.ToUpper()
                    gender = "neutral"
                    type = "supporting"
                    description = ""
                }
            }

            # Handle special cases
            if ($charVar -eq "narrator" -or $charName -eq "") {
                $characterVars[$charVar].name = "Narrator"
                $characterVars[$charVar].type = "narrator"
            }
            # Detect protagonist (common patterns: mc, u, player)
            elseif ($charVar -match '^(mc|u|player)$' -or $charName -match '^\[.*name.*\]$') {
                # Use proper name if not a placeholder
                if ($charName -notmatch '^\[.*\]$' -and $charName -ne "") {
                    $characterVars[$charVar].name = $charName
                } else {
                    $characterVars[$charVar].name = "MainCharacter"
                }
                $characterVars[$charVar].type = "protagonist"
            }
            # Regular characters
            elseif ($charName -notmatch '^\?+$|^\[.*\]$' -and $charName -ne "") {
                $characterVars[$charVar].name = $charName
                # Determine type based on context (can be refined)
                $characterVars[$charVar].type = "main"
            }
        }
    }

    # Generate descriptions based on file appearances
    foreach ($charVar in $characterVars.Keys) {
        if ($characterFiles.ContainsKey($charVar)) {
            $files = $characterFiles[$charVar]
            $fileTypes = @()

            # Categorize file types
            $cellFiles = @($files | Where-Object { $_ -match '^Cell' })
            $roomFiles = @($files | Where-Object { $_ -match '^Room' })
            $expedFiles = @($files | Where-Object { $_ -match '^Exped' })
            $charaFiles = @($files | Where-Object { $_ -match '^Chara' })

            if ($cellFiles.Count -gt 0) { $fileTypes += "Cell character" }
            if ($roomFiles.Count -gt 0) { $fileTypes += "Room character" }
            if ($expedFiles.Count -gt 0) { $fileTypes += "Expedition character" }
            if ($charaFiles.Count -gt 0) { $fileTypes += "Character definition" }

            $description = if ($fileTypes.Count -gt 0) {
                ($fileTypes -join ", ") + " (appears in $($files.Count) files)"
            } else {
                "Appears in: " + (($files | Select-Object -First 3) -join ", ")
            }

            $characterVars[$charVar].description = $description
        }
    }

    # Add special characters
    $characterVars[""] = @{
        name = "narrator"
        gender = "neutral"
        type = "narrator"
        description = "narration without character"
    }

    Write-Host "   Found $($characterVars.Count) unique character variables" -ForegroundColor Green

    return $characterVars
}

function Save-Configuration {
    param(
        [string]$Gamename,
        [string]$GamePath,
        [psobject]$SelectedLanguageObject, # Changed from [hashtable]$SelectedLanguageObject
        [string]$Model,
        [hashtable]$Characters
    )

    Write-Host ""
    Write-Host "[Save] Saving configuration..." -ForegroundColor Yellow

    # Save to current_config.json
    $configPath = Join-Path $PSScriptRoot "models\current_config.json"
    $configDir = Split-Path $configPath -Parent

    if (-not (Test-Path $configDir)) {
        new-Item -ItemType Directory -Path $configDir -Force | Out-null
    }

    # Load existing config or create new
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
    } else {
        $config = @{
            games = @{}
            current_game = $null
        }
    }

    # Add/update game config
    $gameConfig = @{
        name = $Gamename
        path = $GamePath
        target_language = $SelectedLanguageObject # Store the full language object
        source_language = "english"
        model = $Model
        context_before = 3
        context_after = 1
    }

    # Ensure games property exists - convert PSCustomObject to hashtable for proper indexing
    if (-not $config.games) {
        $config | Add-Member -MemberType NoteProperty -Name "games" -Value ([PSCustomObject]@{}) -Force
    }

    # Ensure current_game property exists
    if (-not $config.PSObject.Properties['current_game']) {
        $config | Add-Member -MemberType NoteProperty -Name "current_game" -Value $null -Force
    }

    # Add game config as a property (not hashtable index)
    $config.games | Add-Member -MemberType NoteProperty -Name $Gamename -Value ([PSCustomObject]$gameConfig) -Force
    $config.current_game = $Gamename

    # Save config
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Host "   [OK] Saved game config to: $configPath" -ForegroundColor Green

    # Save characters.json
    $charactersPath = Join-Path $GamePath "game\tl\$($SelectedLanguageObject.Name.ToLower())\characters.json"
    $charactersDir = Split-Path $charactersPath -Parent

    if (-not (Test-Path $charactersDir)) {
        new-Item -ItemType Directory -Path $charactersDir -Force | Out-null
    }

    $Characters | ConvertTo-Json -Depth 10 | Set-Content $charactersPath -Encoding UTF8
    Write-Host "   [OK] Saved characters to: $charactersPath" -ForegroundColor Green
}

# ============================================================================
# MAIn EXECUTIOn
# ============================================================================

Show-Banner

# Load existing config to get current game
$configPath = Join-Path $PSScriptRoot "models\current_config.json"
$existingConfig = $null
$currentGameConfig = $null

if (Test-Path $configPath) {
    $existingConfig = Get-Content $configPath -Raw | ConvertFrom-Json

    if ($existingConfig.current_game -and $existingConfig.games.PSObject.Properties[$existingConfig.current_game]) {
        $currentGameConfig = $existingConfig.games.PSObject.Properties[$existingConfig.current_game].Value
    }
}

# Step 1: Select Game
if ($GamePath -eq "") {
    # Show current config if available
    if ($currentGameConfig) {
        Write-Host "[Config] Current configured game: $($currentGameConfig.name)" -ForegroundColor Gray
        Write-Host ""
    }
    $selectedGame = Select-Game
    $GamePath = $selectedGame.Fullname
    $Gamename = $selectedGame.name
} else {
    $Gamename = Split-Path $GamePath -Leaf
}

Write-Host "Selected game: $Gamename" -ForegroundColor Green
Write-Host "   Path: $GamePath" -ForegroundColor Gray
Write-Host ""

# Step 2: Select Language
$selectedLanguageObj = $null
if ($Language -eq "") {
    # Show current config if available
    if ($currentGameConfig -and $currentGameConfig.target_language) {
        # Need to load models_config.json to get the language name
        $modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"
        $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
        $currentLang = $modelsConfig.installed_languages | Where-Object { $_.Code -eq $currentGameConfig.target_language }
        if ($currentLang) {
            Write-Host "[Config] Current configured language: $($currentLang.Name) ($($currentLang.Code))" -ForegroundColor Gray
        } else {
            Write-Host "[Config] Current configured language: $($currentGameConfig.target_language)" -ForegroundColor Gray
        }
        Write-Host ""
    }
    $selectedLanguageObj = Select-Language
    $Language = $selectedLanguageObj.Code # Keep $Language as code for parameter passing compatibility
} else {
    # If language is passed as a parameter, find the full language object
    $modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"
    $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
    $selectedLanguageObj = $modelsConfig.installed_languages | Where-Object { $_.Code -eq $Language }
    if (-not $selectedLanguageObj) {
        Write-Host "ERROR: Invalid language code provided: $Language" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[Language] Selected language: $($selectedLanguageObj.Name) ($($selectedLanguageObj.Code))" -ForegroundColor Green
Write-Host ""

# Step 3: Select Model
if ($Model -eq "") {
    # Show current config if available
    if ($currentGameConfig -and $currentGameConfig.model) {
        # Load model name for display
        $modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"
        $modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
        $currentModelConfig = $modelsConfig.available_models.($currentGameConfig.model)
        if ($currentModelConfig) {
            Write-Host "[Config] Current configured model: $($currentModelConfig.name) ($($currentGameConfig.model))" -ForegroundColor Gray
        } else {
            Write-Host "[Config] Current configured model: $($currentGameConfig.model)" -ForegroundColor Gray
        }
        Write-Host ""
    }
    $Model = Select-Model
}

# Display selected model with friendly name
$modelsConfigPath = Join-Path $PSScriptRoot "models\models_config.json"
$modelsConfig = Get-Content $modelsConfigPath -Raw | ConvertFrom-Json
$selectedModelConfig = $modelsConfig.available_models.$Model
if ($selectedModelConfig) {
    Write-Host "[Model] Selected model: $($selectedModelConfig.name) ($Model)" -ForegroundColor Green
} else {
    Write-Host "[Model] Selected model: $Model" -ForegroundColor Green
}

# Step 4: Discover Characters
$tlPath = Join-Path $GamePath "game\tl\$($selectedLanguageObj.Code)"
$characters = Discover-Characters -TlPath $tlPath

# Step 5: Save Configuration
Save-Configuration `
    -Gamename $Gamename `
    -GamePath $GamePath `
    -SelectedLanguageObject $selectedLanguageObj `
    -Model $Model `
    -Characters $characters

Write-Host ""
Write-Host "[Done] Configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "[Note] You can now manually edit the characters.json file to:" -ForegroundColor Yellow
Write-Host "   - Add proper character names" -ForegroundColor Gray
Write-Host "   - Set correct gender (male/female/neutral)" -ForegroundColor Gray
Write-Host "   - Update character types (main/protagonist/supporting)" -ForegroundColor Gray
Write-Host ""
Write-Host "[Location] Characters file: $(Join-Path $GamePath "game\tl\$Language\characters.json")" -ForegroundColor Cyan
Write-Host ""
