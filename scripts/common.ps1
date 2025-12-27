# Common PowerShell Functions for Translation Pipeline

function Get-PythonCommand {
    # Try to find Python command
    $pythonCandidates = @("python", "python3", "py")

    foreach ($cmd in $pythonCandidates) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                return $cmd
            }
        } catch {
            continue
        }
    }

    Write-Host " Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

function Get-GameConfig {
    param([string]$GameName)

    $configPath = Join-Path $PSScriptRoot "..\models\local_config.json"

    if (-not (Test-Path $configPath)) {
        Write-Host " Configuration file not found!" -ForegroundColor Red
        Write-Host "   Please run characters.ps1 first to configure your game" -ForegroundColor Yellow
        exit 1
    }

    $config = Get-Content $configPath -Raw | ConvertFrom-Json

    if ($GameName) {
        if ($config.games.PSObject.Properties.Name -contains $GameName) {
            return $config.games.$GameName
        } else {
            Write-Host " Game '$GameName' not found in configuration!" -ForegroundColor Red
            exit 1
        }
    }

    # Return current game
    if ($config.current_game) {
        $currentGame = $config.current_game
        return $config.games.$currentGame
    }

    Write-Host " No game configured!" -ForegroundColor Red
    Write-Host "   Please run characters.ps1 first" -ForegroundColor Yellow
    exit 1
}

function Select-ConfiguredGame {
    $configPath = Join-Path $PSScriptRoot "..\models\local_config.json"

    if (-not (Test-Path $configPath)) {
        Write-Host " No games configured!" -ForegroundColor Red
        Write-Host "   Please run characters.ps1 first" -ForegroundColor Yellow
        exit 1
    }

    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $gameNames = $config.games.PSObject.Properties.Name

    if ($gameNames.Count -eq 0) {
        Write-Host " No games configured!" -ForegroundColor Red
        exit 1
    }

    if ($gameNames.Count -eq 1) {
        # Only one game, select it automatically
        return $gameNames[0]
    }

    # Multiple games, let user choose
    Write-Host " Configured Games:" -ForegroundColor Yellow
    Write-Host ""

    for ($i = 0; $i -lt $gameNames.Count; $i++) {
        $gameName = $gameNames[$i]
        $isCurrent = ($gameName -eq $config.current_game)
        $marker = if ($isCurrent) { " (current)" } else { "" }
        Write-Host "   [$($i + 1)] $gameName$marker" -ForegroundColor Cyan
    }

    Write-Host ""
    $selection = Read-Host "Select game (1-$($gameNames.Count))"

    try {
        $index = [int]$selection - 1
        if ($index -lt 0 -or $index -ge $gameNames.Count) {
            Write-Host "Invalid selection!" -ForegroundColor Red
            exit 1
        }
        return $gameNames[$index]
    } catch {
        Write-Host "Invalid input!" -ForegroundColor Red
        exit 1
    }
}

function Update-CurrentGame {
    param([string]$GameName)

    $configPath = Join-Path $PSScriptRoot "..\models\local_config.json"
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $config.current_game = $GameName
    $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
}

function Show-GameInfo {
    param($GameConfig)

    Write-Host " Game: $($GameConfig.name)" -ForegroundColor Cyan
    Write-Host " Language: $($GameConfig.target_language)" -ForegroundColor Cyan
    Write-Host " Model: $($GameConfig.model)" -ForegroundColor Cyan
    Write-Host ""
}
