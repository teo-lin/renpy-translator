# Ren'Py Translation System - Automated Setup Script
# Run as: .\setup.ps1

param(
    [switch]$SkipPython,
    [switch]$SkipTools,
    [switch]$SkipModel,
    [string]$Languages = "",  # Comma-separated language codes (e.g., "ro,es,fr") or "all"
    [string]$Models = ""      # Comma-separated model numbers (e.g., "1,2") or "all"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  Ren'Py Translation System - Setup Script" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Helper function for retrying web requests
function Invoke-WebRequestWithRetry {
    param(
        [string]$Uri,
        [string]$OutFile,
        [int]$MaxRetries = 3,
        [int]$DelaySeconds = 2
    )

    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing
            return $true
        }
        catch {
            if ($i -eq $MaxRetries) {
                Write-Host "  ERROR: Download failed after $MaxRetries attempts: $_" -ForegroundColor Red
                return $false
            }
            Write-Host "  Download failed (attempt $i/$MaxRetries), retrying in $DelaySeconds seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

# Load configuration
$config = Get-Content "renpy\tools_config.json" | ConvertFrom-Json

# Helper function to check if a Python package is installed
function Test-PythonPackage {
    param(
        [string]$PackageName,
        [string]$PythonExe
    )
    try {
        $result = & $PythonExe -c "import $PackageName" 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Helper function to display menu and get selection
function Show-Menu {
    param(
        [string]$Title,
        [array]$Items,
        [scriptblock]$DisplayItem
    )

    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host "       $Title" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan
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

# =============================================================================
# 0. Language Selection (FIRST STEP)
# =============================================================================
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "       Step 0: Select Languages to Work With" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Select the languages you want to translate to." -ForegroundColor White
Write-Host "Models will be filtered based on your language selection." -ForegroundColor White
Write-Host "You can select multiple languages by entering numbers separated by commas." -ForegroundColor White
Write-Host "Example: 1,2,5" -ForegroundColor Gray
Write-Host ""

# Build language map from all 30 supported languages
$languageMap = @{
    "ro" = "Romanian"
    "es" = "Spanish"
    "fr" = "French"
    "de" = "German"
    "it" = "Italian"
    "pt" = "Portuguese"
    "ru" = "Russian"
    "tr" = "Turkish"
    "cs" = "Czech"
    "pl" = "Polish"
    "uk" = "Ukrainian"
    "bg" = "Bulgarian"
    "zh" = "Chinese"
    "ja" = "Japanese"
    "ko" = "Korean"
    "vi" = "Vietnamese"
    "th" = "Thai"
    "id" = "Indonesian"
    "ar" = "Arabic"
    "he" = "Hebrew"
    "fa" = "Persian"
    "hi" = "Hindi"
    "bn" = "Bengali"
    "nl" = "Dutch"
    "sv" = "Swedish"
    "no" = "Norwegian"
    "da" = "Danish"
    "fi" = "Finnish"
    "el" = "Greek"
    "hu" = "Hungarian"
}

# Build language list (all 30 languages) - Romanian first, then alphabetical
$allLanguages = @()

# Add Romanian first
$allLanguages += @{
    Name = "Romanian"
    Code = "ro"
}

# Add rest alphabetically (exclude Romanian)
foreach ($code in ($languageMap.Keys | Sort-Object)) {
    if ($code -ne "ro") {
        $allLanguages += @{
            Name = $languageMap[$code]
            Code = $code
        }
    }
}

# Display languages in columns for easier selection
$colCount = 2
$rowCount = [Math]::Ceiling($allLanguages.Count / $colCount)

for ($row = 0; $row -lt $rowCount; $row++) {
    $line = ""
    for ($col = 0; $col -lt $colCount; $col++) {
        $index = $col * $rowCount + $row
        if ($index -lt $allLanguages.Count) {
            $num = $index + 1
            $lang = $allLanguages[$index]
            $item = "  [$num] $($lang.Name) ($($lang.Code))"
            $line += $item.PadRight(35)
        }
    }
    Write-Host $line
}

Write-Host ""
Write-Host "  [A] Select All" -ForegroundColor Yellow
Write-Host ""

$selectedLanguages = @()

# Check if Languages parameter was provided
if ($Languages -ne "") {
    if ($Languages -eq "all" -or $Languages -eq "A") {
        $selectedLanguages = $allLanguages
        Write-Host "  Auto-selected: All languages" -ForegroundColor Green
    }
    else {
        # Parse language codes from parameter
        $langCodes = $Languages -split ',' | ForEach-Object { $_.Trim().ToLower() }
        $selectedCodes = @()

        foreach ($code in $langCodes) {
            $lang = $allLanguages | Where-Object { $_.Code -eq $code }
            if ($lang) {
                if ($selectedCodes -notcontains $lang.Code) {
                    $selectedLanguages += $lang
                    $selectedCodes += $lang.Code
                }
            }
            else {
                Write-Host "  WARNING: Unknown language code: $code (skipping)" -ForegroundColor Yellow
            }
        }

        if ($selectedLanguages.Count -gt 0) {
            Write-Host "  Auto-selected $($selectedLanguages.Count) language(s):" -ForegroundColor Green
            foreach ($lang in $selectedLanguages) {
                Write-Host "    - $($lang.Name) ($($lang.Code))" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "  ERROR: No valid languages selected from parameter: $Languages" -ForegroundColor Red
            exit 1
        }
    }
}
else {
    # Interactive mode
    while ($selectedLanguages.Count -eq 0) {
        $selection = Read-Host "Enter your selection (numbers separated by commas, or A for all)"

        if ($selection -eq "A" -or $selection -eq "a") {
            $selectedLanguages = $allLanguages
            Write-Host "  Selected: All languages" -ForegroundColor Green
            break
        }

        # Parse comma-separated numbers
        $numbers = $selection -split ',' | ForEach-Object { $_.Trim() }
        $validSelections = @()
        $selectedCodes = @()

        foreach ($num in $numbers) {
            try {
                $index = [int]$num - 1
                if ($index -ge 0 -and $index -lt $allLanguages.Count) {
                    $lang = $allLanguages[$index]
                    # Only add if not already selected
                    if ($selectedCodes -notcontains $lang.Code) {
                        $validSelections += $lang
                        $selectedCodes += $lang.Code
                    }
                }
                else {
                    Write-Host "  Invalid selection: $num (out of range)" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "  Invalid input: $num (not a number)" -ForegroundColor Red
            }
        }

        if ($validSelections.Count -gt 0) {
            $selectedLanguages = $validSelections
            Write-Host "  Selected $($selectedLanguages.Count) language(s):" -ForegroundColor Green
            foreach ($lang in $selectedLanguages) {
                Write-Host "    - $($lang.Name) ($($lang.Code))" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "  No valid languages selected. Please try again." -ForegroundColor Red
            exit 1
        }
    }
}

# Language selection will be saved after model selection
Write-Host ""

# =============================================================================
# 1. Model Selection (FILTERED BY LANGUAGES)
# =============================================================================
if (-not $SkipModel) {
    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host "       Step 1: Select Translation Models to Install" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select the translation models you want to install." -ForegroundColor White
    Write-Host "Only showing models that support your selected languages." -ForegroundColor White
    Write-Host "You can select multiple models by entering numbers separated by commas." -ForegroundColor White
    Write-Host "Example: 1,2 (selects both models)" -ForegroundColor Gray
    Write-Host ""

    # Convert models object to array and filter by language support
    $allModels = @()
    $config.models.PSObject.Properties | ForEach-Object {
        $allModels += @{
            Key = $_.Name
            Name = $_.Value.name
            Description = $_.Value.description
            Size = $_.Value.size
            Languages = $_.Value.languages
            Config = $_.Value
        }
    }

    # Filter models to only show those supporting at least one selected language
    $availableModels = @()
    foreach ($model in $allModels) {
        $supportsLanguage = $false
        foreach ($langCode in $selectedCodes) {
            if ($model.Languages -contains $langCode) {
                $supportsLanguage = $true
                break
            }
        }
        if ($supportsLanguage) {
            # Count how many selected languages this model supports
            $supportedCount = 0
            foreach ($langCode in $selectedCodes) {
                if ($model.Languages -contains $langCode) {
                    $supportedCount++
                }
            }
            $model.SupportedCount = $supportedCount
            $availableModels += $model
        }
    }

    if ($availableModels.Count -eq 0) {
        Write-Host "  ERROR: No models support your selected languages!" -ForegroundColor Red
        Write-Host "  This should not happen - all 30 languages are supported by at least one model." -ForegroundColor Yellow
        exit 1
    }

    # Display models with language support info
    for ($i = 0; $i -lt $availableModels.Count; $i++) {
        $num = $i + 1
        $model = $availableModels[$i]
        Write-Host "  [$num] " -NoNewline -ForegroundColor Yellow
        Write-Host "$($model.Name) " -NoNewline -ForegroundColor Green
        Write-Host "($($model.Size)) " -NoNewline -ForegroundColor DarkGray
        Write-Host "- Supports $($model.SupportedCount)/$($selectedLanguages.Count) of your languages" -ForegroundColor Cyan
        Write-Host "      $($model.Description)" -ForegroundColor White
        Write-Host ""
    }

    Write-Host "  [A] Install All Models" -ForegroundColor Yellow
    Write-Host ""

    $selectedModels = @()

    # Check if Models parameter was provided
    if ($Models -ne "") {
        if ($Models -eq "all" -or $Models -eq "A") {
            $selectedModels = $availableModels
            Write-Host "  Auto-selected: All models" -ForegroundColor Green
        }
        else {
            # Parse model numbers from parameter
            $modelNumbers = $Models -split ',' | ForEach-Object { $_.Trim() }
            $validSelections = @()
            $selectedKeys = @()

            foreach ($num in $modelNumbers) {
                try {
                    $index = [int]$num - 1
                    if ($index -ge 0 -and $index -lt $availableModels.Count) {
                        $model = $availableModels[$index]
                        if ($selectedKeys -notcontains $model.Key) {
                            $validSelections += $model
                            $selectedKeys += $model.Key
                        }
                    }
                    else {
                        Write-Host "  WARNING: Invalid model number: $num (out of range)" -ForegroundColor Yellow
                    }
                }
                catch {
                    Write-Host "  WARNING: Invalid model number: $num (not a number)" -ForegroundColor Yellow
                }
            }

            if ($validSelections.Count -gt 0) {
                $selectedModels = $validSelections
                Write-Host "  Auto-selected $($selectedModels.Count) model(s):" -ForegroundColor Green
                foreach ($model in $selectedModels) {
                    Write-Host "    - $($model.Name) ($($model.Size))" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "  ERROR: No valid models selected from parameter: $Models" -ForegroundColor Red
                exit 1
            }
        }
    }
    else {
        # Interactive mode
        while ($selectedModels.Count -eq 0) {
            $selection = Read-Host "Enter your selection (numbers separated by commas, or A for all)"

            if ($selection -eq "A" -or $selection -eq "a") {
                $selectedModels = $availableModels
                Write-Host "  Selected: All models" -ForegroundColor Green
                break
            }

            # Parse comma-separated numbers
            $numbers = $selection -split ',' | ForEach-Object { $_.Trim() }
            $validSelections = @()
            $selectedKeys = @()

            foreach ($num in $numbers) {
                try {
                    $index = [int]$num - 1
                    if ($index -ge 0 -and $index -lt $availableModels.Count) {
                        $model = $availableModels[$index]
                        # Only add if not already selected
                        if ($selectedKeys -notcontains $model.Key) {
                            $validSelections += $model
                            $selectedKeys += $model.Key
                        }
                    }
                    else {
                        Write-Host "  Invalid selection: $num (out of range)" -ForegroundColor Red
                    }
                }
                catch {
                    Write-Host "  Invalid input: $num (not a number)" -ForegroundColor Red
                }
            }

            if ($validSelections.Count -gt 0) {
                $selectedModels = $validSelections
                Write-Host "  Selected $($selectedModels.Count) model(s):" -ForegroundColor Green
                foreach ($model in $selectedModels) {
                    Write-Host "    - $($model.Name) ($($model.Size))" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "  No valid models selected. Please try again." -ForegroundColor Red
                exit 1
            }
        }
    }

    # Save combined configuration (languages + models) to single file
    $modelsDir = Join-Path $scriptDir "models"
    New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
    $configFile = Join-Path $modelsDir "local_config.json"

    # Build a clean array of selected models for the config file
    # By saving the $selectedModels array as is, all its properties are preserved.
    $combinedConfig = @{
        languages = $selectedLanguages
        models = $selectedModels # Save the full selectedModels objects
    }

    $combinedConfig | ConvertTo-Json -Depth 3 | Set-Content -Path $configFile -Encoding UTF8

    Write-Host ""
    Write-Host "  Configuration saved to: models\local_config.json" -ForegroundColor Green
    Write-Host "    - Languages: $($selectedLanguages.Count)" -ForegroundColor Gray
    Write-Host "    - Models: $($selectedModels.Count)" -ForegroundColor Gray
    Write-Host ""
}
else {
    Write-Host "[0/6] Skipping model selection (--SkipModel)" -ForegroundColor Yellow
    Write-Host ""

    # Load previously selected configuration
    $configFile = Join-Path $scriptDir "models\local_config.json"
    if (Test-Path $configFile) {
        $savedConfig = Get-Content $configFile | ConvertFrom-Json

        # Load languages
        $selectedLanguages = $savedConfig.languages

        # Load models directly from savedConfig.models
        $selectedModels = $savedConfig.models

        Write-Host "  Loaded configuration from: models\local_config.json" -ForegroundColor Gray
        Write-Host "    - Languages: $($selectedLanguages.Count)" -ForegroundColor Gray
        Write-Host "    - Models: $($selectedModels.Count)" -ForegroundColor Gray
    }
}

# =============================================================================
# 2. Python Environment Setup
# =============================================================================
if (-not $SkipPython) {
    Write-Host "[2/6] Setting up Python environment..." -ForegroundColor Green

    # Check Python version
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "  Found: $pythonVersion" -ForegroundColor Gray

        if ($pythonVersion -notmatch "Python 3\.(1[0-9]|[0-9]{2})") {
            Write-Host "  WARNING: Python 3.10+ recommended" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ERROR: Python not found. Please install Python 3.12.7 first." -ForegroundColor Red
        exit 1
    }

    # Create virtual environment
    $venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
    if (-not (Test-Path "venv")) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv venv
    } elseif (-not (Test-Path $venvPython)) {
        Write-Host "  Virtual environment corrupted, recreating..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
        python -m venv venv
    } else {
        Write-Host "  Virtual environment already exists" -ForegroundColor Gray
    }

    # Check and upgrade pip if needed
    Write-Host "  Checking pip version... (patience, this one takes about a minute)" -ForegroundColor Gray
    $pipVersion = & $venvPython -m pip --version 2>&1
    $pipUpgradeCheck = & $venvPython -m pip list --outdated --format=json 2>&1 | ConvertFrom-Json | Where-Object { $_.name -eq "pip" }

    if ($pipUpgradeCheck) {
        Write-Host "  Upgrading pip from $($pipUpgradeCheck.version) to $($pipUpgradeCheck.latest_version)..." -ForegroundColor Gray
        & $venvPython -m pip install --upgrade pip
    } else {
        Write-Host "  pip already up to date" -ForegroundColor Gray
    }

    # Check and install PyTorch
    if (Test-PythonPackage -PackageName "torch" -PythonExe $venvPython) {
        Write-Host "  PyTorch already installed" -ForegroundColor Gray
    } else {
        Write-Host "  Installing PyTorch with CUDA 12.4 (this may take a few minutes)..." -ForegroundColor Gray
        & $venvPython -m pip install torch --index-url https://download.pytorch.org/whl/cu124
    }

    # Check and install llama-cpp-python (only if Aya-23-8B is selected)
    $needsLlamaCpp = $false
    if ($selectedModels) {
        foreach ($model in $selectedModels) {
            if ($model.Key -eq "aya-23-8b") {
                $needsLlamaCpp = $true
                break
            }
        }
    }

    if ($needsLlamaCpp) {
        # Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
        $torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
        if (Test-Path $torchLibPath) {
            $env:PATH += ";$torchLibPath"
        }

        # Check if llama-cpp-python with CUDA is properly installed
        $llamaCppWorking = $false
        try {
            $testResult = & $venvPython -c "import llama_cpp; print('OK')" 2>&1
            if ($testResult -match "OK") {
                $llamaCppWorking = $true
            }
        } catch {
            $llamaCppWorking = $false
        }

        if ($llamaCppWorking) {
            Write-Host "  llama-cpp-python already installed with CUDA" -ForegroundColor Gray
        } else {
            Write-Host "  Installing llama-cpp-python with CUDA (this may take a few minutes)..." -ForegroundColor Gray
            Write-Host "  Using prebuilt CUDA 12.4 wheels from abetlen..." -ForegroundColor DarkGray

            # Get Python version to ensure wheel compatibility
            $pyVersion = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            Write-Host "  Python version: $pyVersion" -ForegroundColor DarkGray

            # Uninstall existing version if present, to ensure a clean install
            Write-Host "  Checking for existing llama-cpp-python installation..." -ForegroundColor DarkGray
            # Use `pip list` and `findstr` which is more robust than `pip show` for checking existence.
            # We pipe the output of `pip list` to `findstr` and then discard the output. We only care about the exit code.
            $null = & $venvPython -m pip list | findstr /i "llama-cpp-python"
            if ($LASTEXITCODE -eq 0) {
                # findstr returns 0 if the string is found
                Write-Host "  Found existing version, uninstalling it first..." -ForegroundColor DarkGray
                $null = & $venvPython -m pip uninstall -y llama-cpp-python -ErrorAction SilentlyContinue 2>$null
            }

            # Install from CUDA wheel repository with forced binary installation
            # --only-binary prevents source builds (requires Visual Studio)
            # --force-reinstall ensures clean installation
            Write-Host "  Downloading prebuilt wheel (prevents compilation)..." -ForegroundColor DarkGray
            $installResult = & $venvPython -m pip install llama-cpp-python `
                --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 `
                --only-binary :all: `
                --force-reinstall `
                --no-cache-dir 2>&1

            # Check for build errors
            if ($installResult -match "Building wheel" -or $installResult -match "CMake") {
                Write-Host ""
                Write-Host "  ERROR: pip tried to build from source instead of using prebuilt wheel!" -ForegroundColor Red
                Write-Host "  This usually means:" -ForegroundColor Yellow
                Write-Host "    1. No prebuilt wheel available for Python $pyVersion" -ForegroundColor Yellow
                Write-Host "    2. Network issue accessing wheel repository" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "  Attempting alternative installation from PyPI..." -ForegroundColor Cyan

                # Try alternative: install CPU version from PyPI as fallback
                $null = & $venvPython -m pip uninstall -y llama-cpp-python 2>&1
                & $venvPython -m pip install llama-cpp-python --only-binary :all:
            }

            # Verify installation
            $testResult = & $venvPython -c "import llama_cpp; print('OK')" 2>&1
            if ($testResult -match "OK") {
                # Check if CUDA is actually available
                $cudaCheck = & $venvPython -c "import llama_cpp; print(llama_cpp.llama_supports_gpu_offload())" 2>&1
                if ($cudaCheck -match "True") {
                    Write-Host "  llama-cpp-python installed successfully with CUDA support!" -ForegroundColor Green
                } else {
                    Write-Host "  llama-cpp-python installed (CPU-only fallback)" -ForegroundColor Yellow
                    Write-Host "  CUDA wheel may not be available for Python $pyVersion" -ForegroundColor DarkYellow
                }
            } else {
                Write-Host "  WARNING: llama-cpp-python installation failed" -ForegroundColor Yellow
                Write-Host "  Error: $testResult" -ForegroundColor DarkYellow
                Write-Host ""
                Write-Host "  You may need to:" -ForegroundColor Yellow
                Write-Host "    1. Use Python 3.10 or 3.11 (best wheel support)" -ForegroundColor Yellow
                Write-Host "    2. Install Visual Studio Build Tools for source compilation" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  Skipping llama-cpp-python (not needed for selected models)" -ForegroundColor Gray
    }

    # Check and install transformers (only if MADLAD is selected)
    $needsTransformers = $false
    if ($selectedModels) {
        foreach ($model in $selectedModels) {
            if ($model.Key -eq "madlad-400-3b") {
                $needsTransformers = $true
                break
            }
        }
    }

    if ($needsTransformers) {
        if (Test-PythonPackage -PackageName "transformers" -PythonExe $venvPython) {
            Write-Host "  transformers already installed" -ForegroundColor Gray
        } else {
            Write-Host "  Installing transformers for MADLAD model..." -ForegroundColor Gray
            & $venvPython -m pip install transformers
        }
    } else {
        Write-Host "  Skipping transformers (not needed for selected models)" -ForegroundColor Gray
    }

    # Install other requirements
    Write-Host "  Installing other dependencies from requirements.txt..." -ForegroundColor Gray
    & $venvPython -m pip install -r requirements.txt

    Write-Host "  Python environment setup complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[2/6] Skipping Python setup (--SkipPython)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 3. Download Selected Models from HuggingFace
# =============================================================================
if (-not $SkipModel -and $selectedModels) {
    Write-Host "[3/6] Downloading selected translation models..." -ForegroundColor Green

    foreach ($model in $selectedModels) {
        $modelConfig = $model.Config
        Write-Host ""
        Write-Host "  Model: $($model.Name)" -ForegroundColor Cyan

        if ($modelConfig.huggingface_download) {
            # MADLAD-400-3B uses transformers auto-download
            $modelPath = Join-Path $scriptDir $modelConfig.destination
            if (Test-Path $modelPath) {
                Write-Host "    Already downloaded" -ForegroundColor Gray
            } else {
                Write-Host "    Repository: $($modelConfig.repo)" -ForegroundColor Gray
                Write-Host "    Size: $($modelConfig.size)" -ForegroundColor Gray
                Write-Host "    Downloading from HuggingFace (this will take several minutes)..." -ForegroundColor Yellow

                # Ensure models directory exists
                New-Item -ItemType Directory -Force -Path $modelPath | Out-Null

                # Download using transformers snapshot_download
                $venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
                $modelPathUnix = $modelPath -replace '\\', '/'
                & $venvPython -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; model = AutoModelForSeq2SeqLM.from_pretrained('$($modelConfig.repo)'); tokenizer = AutoTokenizer.from_pretrained('$($modelConfig.repo)'); model.save_pretrained('$modelPathUnix'); tokenizer.save_pretrained('$modelPathUnix')"

                if (Test-Path $modelPath) {
                    Write-Host "    Downloaded successfully!" -ForegroundColor Green
                } else {
                    Write-Host "    WARNING: Download may have failed" -ForegroundColor Yellow
                }
            }
        } else {
            # Aya-23-8B uses GGUF file download
            $modelPath = Join-Path $scriptDir $modelConfig.destination

            if (Test-Path $modelPath) {
                Write-Host "    Already downloaded" -ForegroundColor Gray
            } else {
                Write-Host "    File: $($modelConfig.file)" -ForegroundColor Gray
                Write-Host "    Size: $($modelConfig.size)" -ForegroundColor Gray
                Write-Host "    Downloading (this will take several minutes)..." -ForegroundColor Yellow

                # Ensure models directory exists
                $modelDir = Split-Path $modelPath -Parent
                New-Item -ItemType Directory -Force -Path $modelDir | Out-Null

                # Download using huggingface-cli
                $venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
                $modelDirUnix = $modelDir -replace '\\', '/'
                & $venvPython -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='$($modelConfig.repo)', filename='$($modelConfig.file)', local_dir='$modelDirUnix')"

                if (Test-Path $modelPath) {
                    Write-Host "    Downloaded successfully!" -ForegroundColor Green
                } else {
                    Write-Host "    ERROR: Download failed" -ForegroundColor Red
                    exit 1
                }
            }
        }
    }
    Write-Host ""
} else {
    Write-Host "[3/6] Skipping model download (--SkipModel or no models selected)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 4. Download External Tools
# =============================================================================
if (-not $SkipTools) {
    Write-Host "[4/6] Downloading external tools..." -ForegroundColor Green

    # Download Ren'Py SDK
    $renpyConfig = $config.tools.renpy
    $renpyPath = Join-Path $scriptDir $renpyConfig.destination

    if (Test-Path $renpyPath) {
        Write-Host "  Ren'Py SDK already exists" -ForegroundColor Gray
    } else {
        Write-Host "  Downloading Ren'Py SDK $($renpyConfig.version)..." -ForegroundColor Gray
        $tempZip = Join-Path $env:TEMP "renpy.zip"

        if (Invoke-WebRequestWithRetry -Uri $renpyConfig.url -OutFile $tempZip) {
            Write-Host "  Extracting Ren'Py SDK..." -ForegroundColor Gray
            Expand-Archive -Path $tempZip -DestinationPath $scriptDir -Force

            # Rename extracted folder to 'renpy'
            $extractedFolder = Get-ChildItem -Path $scriptDir -Filter "renpy-*" -Directory | Select-Object -First 1
            if ($extractedFolder) {
                Rename-Item -Path $extractedFolder.FullName -NewName "renpy" -Force
            }

            Remove-Item $tempZip
            Write-Host "  Ren'Py SDK installed!" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Could not download Ren'Py SDK" -ForegroundColor Yellow
        }
    }

    # rpaExtract.exe is synced to repository, no download needed
    $rpaPath = Join-Path $scriptDir "renpy\rpaExtract.exe"
    if (Test-Path $rpaPath) {
        Write-Host "  rpaExtract.exe already in repository" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: rpaExtract.exe not found at renpy\rpaExtract.exe" -ForegroundColor Yellow
        Write-Host "  rpaExtract is optional and only needed for extracting RPA archives" -ForegroundColor DarkGray
    }

    # UnRen is synced to repository, no download needed
    $unrenPath = Join-Path $scriptDir "renpy\unRen"
    if (Test-Path $unrenPath) {
        Write-Host "  UnRen already in repository" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: UnRen folder not found at renpy\unRen" -ForegroundColor Yellow
    }

    Write-Host ""
} else {
    Write-Host "[4/6] Skipping tools download (--SkipTools)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 5. Verify Installation
# =============================================================================
Write-Host "[5/6] Verifying installation..." -ForegroundColor Green

$allGood = $true
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"

# Add PyTorch lib directory to PATH for CUDA DLLs (needed by llama-cpp-python)
$torchLibPath = Join-Path $scriptDir "venv\Lib\site-packages\torch\lib"
if (Test-Path $torchLibPath) {
    $env:PATH += ";$torchLibPath"
}

# Check Python packages
Write-Host "  Checking Python packages..." -ForegroundColor Gray

# Check PyTorch
if (Test-PythonPackage -PackageName "torch" -PythonExe $venvPython) {
    Write-Host "    - PyTorch: installed" -ForegroundColor Gray
} else {
    Write-Host "    - PyTorch: NOT INSTALLED" -ForegroundColor Red
    $allGood = $false
}

# Check model-specific packages
if ($selectedModels) {
    foreach ($model in $selectedModels) {
        if ($model.Key -eq "aya-23-8b") {
            if (Test-PythonPackage -PackageName "llama_cpp" -PythonExe $venvPython) {
                Write-Host "    - llama-cpp-python: installed" -ForegroundColor Gray
            } else {
                Write-Host "    - llama-cpp-python: NOT INSTALLED" -ForegroundColor Red
                $allGood = $false
            }
        }
        elseif ($model.Key -eq "madlad-400-3b") {
            if (Test-PythonPackage -PackageName "transformers" -PythonExe $venvPython) {
                Write-Host "    - transformers: installed" -ForegroundColor Gray
            } else {
                Write-Host "    - transformers: NOT INSTALLED" -ForegroundColor Red
                $allGood = $false
            }
        }
    }
}

# Check CUDA
Write-Host "  Checking CUDA support..." -ForegroundColor Gray
try {
    $cudaAvailable = & $venvPython -c "import torch; print(torch.cuda.is_available())" 2>$null
    if ($cudaAvailable -eq "True") {
        Write-Host "    - CUDA available" -ForegroundColor Gray
    } else {
        Write-Host "    - WARNING: CUDA not available (will use CPU)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    - WARNING: Could not check CUDA" -ForegroundColor Yellow
}

# Check selected models
if (-not $SkipModel -and $selectedModels) {
    Write-Host "  Checking selected models..." -ForegroundColor Gray
    foreach ($model in $selectedModels) {
        $modelConfig = $model.Config
        $modelPath = Join-Path $scriptDir $modelConfig.destination

        if (Test-Path $modelPath) {
            if ($modelConfig.huggingface_download) {
                Write-Host "    - $($model.Name): downloaded" -ForegroundColor Gray
            } else {
                $size = (Get-Item $modelPath).Length / 1GB
                Write-Host "    - $($model.Name): $([math]::Round($size, 2)) GB" -ForegroundColor Gray
            }
        } else {
            Write-Host "    - $($model.Name): NOT FOUND" -ForegroundColor Yellow
            $allGood = $false
        }
    }
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  You're all set! Next steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. Copy your Ren'Py game to the games/ folder" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. Translate your game using the interactive launcher:" -ForegroundColor White
    Write-Host "     .\translate.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. (Optional) Correct grammar with:" -ForegroundColor White
    Write-Host "     .\correct.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  The interactive scripts will use your configuration:" -ForegroundColor DarkGray
    Write-Host "    - Languages: $($selectedLanguages.Count) configured during setup" -ForegroundColor DarkGray
    Write-Host "    - Models: $($selectedModels.Count) installed during setup" -ForegroundColor DarkGray
    Write-Host "    - Games: auto-scanned from games/ folder" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  For advanced usage, see README.md" -ForegroundColor White
} else {
    Write-Host "  SETUP COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "  Please review the messages above and install missing components" -ForegroundColor Yellow
}

Write-Host "=====================================================================" -ForegroundColor Cyan