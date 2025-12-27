# Character Discovery and Configuration Script
# Discovers characters from game translation files and configures game settings

param(
    [string]$GamePath = "",
    [string]$Language = "",
    [string]$Model = ""
)

# Import common functions
. "$PSScriptRoot\scripts\common.ps1"

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
    param([string]$GamePath)

    Write-Host "[Language] Available Languages:" -ForegroundColor Yellow
    Write-Host ""

    $tlDir = Join-Path $GamePath "game\tl"
    if (-not (Test-Path $tlDir)) {
        Write-Host "   no translation folders found in game!" -ForegroundColor Red
        exit 1
    }

    $languages = Get-ChildItem -Path $tlDir -Directory

    if ($languages.Count -eq 0) {
        Write-Host "   no language folders found!" -ForegroundColor Red
        exit 1
    }

    for ($i = 0; $i -lt $languages.Count; $i++) {
        Write-Host "   [$($i + 1)] $($languages[$i].name)" -ForegroundColor Cyan
    }

    Write-Host ""
    $selection = Read-Host "Select language (1-$($languages.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $languages.Count) {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
        return $languages[$index].name
    } catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Select-Model {
    Write-Host "[Model] Available Models:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   [1] Aya-23-8B (Higher quality, 4.8GB)" -ForegroundColor Cyan
    Write-Host "   [2] MADLAD-400-3B (400+ languages, 6GB)" -ForegroundColor Cyan
    Write-Host ""

    $selection = Read-Host "Select model (1-2)"

    switch ($selection) {
        "1" { return "Aya-23-8B" }
        "2" { return "MADLAD-400-3B" }
        default {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
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

            if (-not $characterVars.ContainsKey($charVar)) {
                continue
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
        [string]$Language,
        [string]$Model,
        [hashtable]$Characters
    )

    Write-Host ""
    Write-Host "[Save] Saving configuration..." -ForegroundColor Yellow

    # Save to local_config.json
    $configPath = Join-Path $PSScriptRoot "models\local_config.json"
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
        target_language = $Language.ToLower()
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
    $charactersPath = Join-Path $GamePath "game\tl\$Language\characters.json"
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

# Step 1: Select Game
if ($GamePath -eq "") {
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
if ($Language -eq "") {
    $Language = Select-Language -GamePath $GamePath
}

Write-Host "[Language] Selected language: $Language" -ForegroundColor Green
Write-Host ""

# Step 3: Select Model
if ($Model -eq "") {
    $Model = Select-Model
}

Write-Host "[Model] Selected model: $Model" -ForegroundColor Green

# Step 4: Discover Characters
$tlPath = Join-Path $GamePath "game\tl\$Language"
$characters = Discover-Characters -TlPath $tlPath

# Step 5: Save Configuration
Save-Configuration `
    -Gamename $Gamename `
    -GamePath $GamePath `
    -Language $Language `
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
