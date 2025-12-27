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
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         Character Discovery & Game Configuration          ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Select-Game {
    Write-Host "🎮 Available Games:" -ForegroundColor Yellow
    Write-Host ""

    $gamesDir = Join-Path $PSScriptRoot "games"
    if (-not (Test-Path $gamesDir)) {
        New-Item -ItemType Directory -Path $gamesDir -Force | Out-Null
    }

    $games = Get-ChildItem -Path $gamesDir -Directory

    if ($games.Count -eq 0) {
        Write-Host "   No games found in 'games' directory!" -ForegroundColor Red
        Write-Host "   Please add your game folders to: $gamesDir" -ForegroundColor Yellow
        exit 1
    }

    for ($i = 0; $i -lt $games.Count; $i++) {
        Write-Host "   [$($i + 1)] $($games[$i].Name)" -ForegroundColor Cyan
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

    Write-Host "🌍 Available Languages:" -ForegroundColor Yellow
    Write-Host ""

    $tlDir = Join-Path $GamePath "game\tl"
    if (-not (Test-Path $tlDir)) {
        Write-Host "   No translation folders found in game!" -ForegroundColor Red
        exit 1
    }

    $languages = Get-ChildItem -Path $tlDir -Directory

    if ($languages.Count -eq 0) {
        Write-Host "   No language folders found!" -ForegroundColor Red
        exit 1
    }

    for ($i = 0; $i -lt $languages.Count; $i++) {
        Write-Host "   [$($i + 1)] $($languages[$i].Name)" -ForegroundColor Cyan
    }

    Write-Host ""
    $selection = Read-Host "Select language (1-$($languages.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $languages.Count) {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
        return $languages[$index].Name
    } catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Select-Model {
    Write-Host "🤖 Available Models:" -ForegroundColor Yellow
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
    Write-Host "🔍 Discovering characters from .rpy files..." -ForegroundColor Yellow

    $characterVars = @{}
    $rpyFiles = Get-ChildItem -Path $TlPath -Filter "*.rpy" -Recurse

    foreach ($file in $rpyFiles) {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8

        # Find dialogue patterns: character_var "text"
        $matches = [regex]::Matches($content, '^\s*(\w+)\s+"[^"\\]*(?:\\.[^"\\]*)*"', [Text.RegularExpressions.RegexOptions]::Multiline)

        foreach ($match in $matches) {
            $charVar = $match.Groups[1].Value

            # Skip if it's a keyword or already exists
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
            }
        }
    }

    # Add special characters
    $characterVars[""] = @{
        name = "Narrator"
        gender = "neutral"
        type = "narrator"
        description = "Narration without character"
    }

    $characterVars["d"] = @{
        name = "System"
        gender = "neutral"
        type = "system"
        description = "System/Drone messages"
    }

    Write-Host "   Found $($characterVars.Count) unique character variables" -ForegroundColor Green

    return $characterVars
}

function Save-Configuration {
    param(
        [string]$GameName,
        [string]$GamePath,
        [string]$Language,
        [string]$Model,
        [hashtable]$Characters
    )

    Write-Host ""
    Write-Host "💾 Saving configuration..." -ForegroundColor Yellow

    # Save to local_config.json
    $configPath = Join-Path $PSScriptRoot "models\local_config.json"
    $configDir = Split-Path $configPath -Parent

    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
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
        name = $GameName
        path = $GamePath
        target_language = $Language.ToLower()
        source_language = "english"
        model = $Model
        context_before = 3
        context_after = 1
    }

    if ($config.games -is [PSCustomObject]) {
        $config.games = @{}
    }
    $config.games[$GameName] = $gameConfig
    $config.current_game = $GameName

    # Save config
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
    Write-Host "   ✅ Saved game config to: $configPath" -ForegroundColor Green

    # Save characters.json
    $charactersPath = Join-Path $GamePath "game\tl\$Language\characters.json"
    $charactersDir = Split-Path $charactersPath -Parent

    if (-not (Test-Path $charactersDir)) {
        New-Item -ItemType Directory -Path $charactersDir -Force | Out-Null
    }

    $Characters | ConvertTo-Json -Depth 10 | Set-Content $charactersPath -Encoding UTF8
    Write-Host "   ✅ Saved characters to: $charactersPath" -ForegroundColor Green
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Show-Banner

# Step 1: Select Game
if ($GamePath -eq "") {
    $selectedGame = Select-Game
    $GamePath = $selectedGame.FullName
    $GameName = $selectedGame.Name
} else {
    $GameName = Split-Path $GamePath -Leaf
}

Write-Host "📁 Selected game: $GameName" -ForegroundColor Green
Write-Host "   Path: $GamePath" -ForegroundColor Gray
Write-Host ""

# Step 2: Select Language
if ($Language -eq "") {
    $Language = Select-Language -GamePath $GamePath
}

Write-Host "🌍 Selected language: $Language" -ForegroundColor Green
Write-Host ""

# Step 3: Select Model
if ($Model -eq "") {
    $Model = Select-Model
}

Write-Host "🤖 Selected model: $Model" -ForegroundColor Green

# Step 4: Discover Characters
$tlPath = Join-Path $GamePath "game\tl\$Language"
$characters = Discover-Characters -TlPath $tlPath

# Step 5: Save Configuration
Save-Configuration `
    -GameName $GameName `
    -GamePath $GamePath `
    -Language $Language `
    -Model $Model `
    -Characters $characters

Write-Host ""
Write-Host "✨ Configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 You can now manually edit the characters.json file to:" -ForegroundColor Yellow
Write-Host "   - Add proper character names" -ForegroundColor Gray
Write-Host "   - Set correct gender (male/female/neutral)" -ForegroundColor Gray
Write-Host "   - Update character types (main/protagonist/supporting)" -ForegroundColor Gray
Write-Host ""
Write-Host "📍 Characters file: $(Join-Path $GamePath "game\tl\$Language\characters.json")" -ForegroundColor Cyan
Write-Host ""
