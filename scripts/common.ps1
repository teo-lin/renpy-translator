# Common PowerShell Functions for Translation Pipeline

function Get-PythonCommand {
    # Explicitly return the Python executable within the virtual environment
    $venvPythonPath = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"
    if (Test-Path $venvPythonPath) {
        return $venvPythonPath
    } else {
        Write-Host "Virtual environment Python not found at: $venvPythonPath" -ForegroundColor Red
        Write-Host "Please ensure the virtual environment is set up correctly (run 0-setup.ps1)." -ForegroundColor Yellow
        exit 1
    }
}

function ConvertFrom-Yaml {
    param(
        [string]$YamlContent,
        [string]$YamlFilePath
    )
    $pythonCmd = Get-PythonCommand
    $tempYamlFile = Join-Path $env:TEMP ([System.Guid]::NewGuid().ToString() + ".yaml")
    $tempJsonFile = Join-Path $env:TEMP ([System.Guid]::NewGuid().ToString() + ".json")

    try {
        if ($YamlContent) {
            Set-Content -Path $tempYamlFile -Value $YamlContent -Encoding UTF8
        } elseif ($YamlFilePath) {
            # If path provided, use it directly
            $tempYamlFile = $YamlFilePath
        } else {
            Write-Host "Error: Either YamlContent or YamlFilePath must be provided." -ForegroundColor Red
            exit 1
        }

        & $pythonCmd (Join-Path $PSScriptRoot "scripts\convert_yaml_to_json.py") $tempYamlFile $tempJsonFile

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error converting YAML to JSON. Python script failed." -ForegroundColor Red
            exit $LASTEXITCODE
        }

        $jsonOutput = Get-Content -Path $tempJsonFile -Raw -Encoding UTF8
        return ($jsonOutput | ConvertFrom-Json)
    } finally {
        if ($YamlContent) { Remove-Item $tempYamlFile -ErrorAction SilentlyContinue }
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
    }
}

function ConvertTo-Yaml {
    param(
        [Parameter(ValueFromPipeline=$true)]
        [psobject]$InputObject,
        [string]$YamlFilePath
    )
    $pythonCmd = Get-PythonCommand
    $tempJsonFile = Join-Path $env:TEMP ([System.Guid]::NewGuid().ToString() + ".json")

    try {
        # Convert input object to JSON string
        $jsonContent = $InputObject | ConvertTo-Json -Depth 10

        # Write JSON content to a temporary file
        Set-Content -Path $tempJsonFile -Value $jsonContent -Encoding UTF8

        # Call Python script to convert JSON to YAML
        & $pythonCmd (Join-Path $PSScriptRoot "scripts\convert_json_to_yaml.py") $tempJsonFile $YamlFilePath

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error converting JSON to YAML. Python script failed." -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } finally {
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
    }
}

function Get-GameConfig {
    param([string]$GameName)

    $configPath = Join-Path $PSScriptRoot "..\models\current_config.yaml"

    if (-not (Test-Path $configPath)) {
    $config = ConvertFrom-Yaml -YamlFilePath $configPath

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
    Write-Host "   Please run 1-config.ps1 first" -ForegroundColor Yellow
    exit 1
}

function Select-ConfiguredGame {
    $configPath = Join-Path $PSScriptRoot "..\models\current_config.yaml"

    if (-not (Test-Path $configPath)) {
        Write-Host " No games configured!" -ForegroundColor Red
        Write-Host "   Please run 1-config.ps1 first" -ForegroundColor Yellow
        exit 1
    $config = ConvertFrom-Yaml -YamlFilePath $configPath
    $gameNames = @($config.games.PSObject.Properties.Name)

    if ($gameNames.Count -eq 0) {
        Write-Host " No games configured!" -ForegroundColor Red
        exit 1
    }

    # If current_game is set, use it automatically
    if ($config.current_game -and ($gameNames -contains $config.current_game)) {
        Write-Host " Using configured game: $($config.current_game)" -ForegroundColor Cyan
        return $config.current_game
    }

    if ($gameNames.Count -eq 1) {
        # Only one game, select it automatically
        return $gameNames[0]
    }

    # Multiple games and no current_game set, let user choose
    Write-Host " Configured Games:" -ForegroundColor Yellow
    Write-Host ""

    for ($i = 0; $i -lt $gameNames.Count; $i++) {
        $gameName = $gameNames[$i]
        Write-Host "   [$($i + 1)] $gameName" -ForegroundColor Cyan
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

    $configPath = Join-Path $PSScriptRoot "..\models\current_config.yaml"
    $config = Get-Content $configPath -Raw | ConvertFrom-Yaml
    $config.current_game = $GameName
    $config | ConvertTo-Yaml -Depth 10 | Set-Content $configPath -Encoding UTF8
}

function Show-GameInfo {
    param($GameConfig)

    Write-Host " Game: $($GameConfig.name)" -ForegroundColor Cyan
    Write-Host " Language: $($GameConfig.target_language)" -ForegroundColor Cyan
    Write-Host " Model: $($GameConfig.model)" -ForegroundColor Cyan
    Write-Host ""
}
