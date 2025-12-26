# Ren'Py Translation System - Automated Setup Script
# Run as: .\setup.ps1

param(
    [switch]$SkipPython,
    [switch]$SkipTools,
    [switch]$SkipModel
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  Ren'Py Translation System - Setup Script" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Load configuration
$config = Get-Content "renpy\tools_config.json" | ConvertFrom-Json

# =============================================================================
# 1. Python Environment Setup
# =============================================================================
if (-not $SkipPython) {
    Write-Host "[1/4] Setting up Python environment..." -ForegroundColor Green

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
    if (-not (Test-Path "venv")) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv venv
    } else {
        Write-Host "  Virtual environment already exists" -ForegroundColor Gray
    }

    # Activate venv
    Write-Host "  Activating virtual environment..." -ForegroundColor Gray
    & "venv\Scripts\Activate.ps1"

    # Upgrade pip
    Write-Host "  Upgrading pip..." -ForegroundColor Gray
    python -m pip install --upgrade pip --quiet

    # Install PyTorch with CUDA
    Write-Host "  Installing PyTorch with CUDA 12.4..." -ForegroundColor Gray
    pip install torch --index-url https://download.pytorch.org/whl/cu124 --quiet

    # Install llama-cpp-python with CUDA
    Write-Host "  Installing llama-cpp-python with CUDA..." -ForegroundColor Gray
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 --quiet

    # Install other requirements
    Write-Host "  Installing other dependencies..." -ForegroundColor Gray
    pip install -r requirements.txt --quiet

    Write-Host "  Python environment setup complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/4] Skipping Python setup (--SkipPython)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 2. Download Model from HuggingFace
# =============================================================================
if (-not $SkipModel) {
    Write-Host "[2/4] Downloading translation model..." -ForegroundColor Green

    $modelConfig = $config.models."aya-23-8b"
    $modelPath = Join-Path $scriptDir $modelConfig.destination

    if (Test-Path $modelPath) {
        Write-Host "  Model already exists: $modelPath" -ForegroundColor Gray
    } else {
        Write-Host "  Model: $($modelConfig.repo)/$($modelConfig.file)" -ForegroundColor Gray
        Write-Host "  Size: $($modelConfig.size)" -ForegroundColor Gray
        Write-Host "  Downloading (this will take several minutes)..." -ForegroundColor Yellow

        # Ensure models directory exists
        $modelDir = Split-Path $modelPath -Parent
        New-Item -ItemType Directory -Force -Path $modelDir | Out-Null

        # Download using huggingface-cli
        python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='$($modelConfig.repo)', filename='$($modelConfig.file)', local_dir='$modelDir')"

        if (Test-Path $modelPath) {
            Write-Host "  Model downloaded successfully!" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: Model download failed" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host ""
} else {
    Write-Host "[2/4] Skipping model download (--SkipModel)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 3. Download External Tools
# =============================================================================
if (-not $SkipTools) {
    Write-Host "[3/4] Downloading external tools..." -ForegroundColor Green

    # Download Ren'Py SDK
    $renpyConfig = $config.tools.renpy
    $renpyPath = Join-Path $scriptDir $renpyConfig.destination

    if (Test-Path $renpyPath) {
        Write-Host "  Ren'Py SDK already exists" -ForegroundColor Gray
    } else {
        Write-Host "  Downloading Ren'Py SDK $($renpyConfig.version)..." -ForegroundColor Gray
        $tempZip = Join-Path $env:TEMP "renpy.zip"
        Invoke-WebRequest -Uri $renpyConfig.url -OutFile $tempZip -UseBasicParsing

        Write-Host "  Extracting Ren'Py SDK..." -ForegroundColor Gray
        Expand-Archive -Path $tempZip -DestinationPath $scriptDir -Force

        # Rename extracted folder to 'renpy'
        $extractedFolder = Get-ChildItem -Path $scriptDir -Filter "renpy-*" -Directory | Select-Object -First 1
        if ($extractedFolder) {
            Rename-Item -Path $extractedFolder.FullName -NewName "renpy" -Force
        }

        Remove-Item $tempZip
        Write-Host "  Ren'Py SDK installed!" -ForegroundColor Green
    }

    # Download rpaExtract
    $rpaConfig = $config.tools.rpaextract
    $rpaPath = Join-Path $scriptDir $rpaConfig.destination

    if (Test-Path $rpaPath) {
        Write-Host "  rpaExtract.exe already exists" -ForegroundColor Gray
    } else {
        Write-Host "  Downloading rpaExtract.exe..." -ForegroundColor Gray
        $rpaDir = Split-Path $rpaPath -Parent
        New-Item -ItemType Directory -Force -Path $rpaDir | Out-Null

        Invoke-WebRequest -Uri $rpaConfig.url -OutFile $rpaPath -UseBasicParsing
        Write-Host "  rpaExtract.exe installed!" -ForegroundColor Green
    }

    # Download UnRen
    $unrenConfig = $config.tools.unren
    $unrenPath = Join-Path $scriptDir $unrenConfig.destination

    if (Test-Path $unrenPath) {
        Write-Host "  UnRen already exists" -ForegroundColor Gray
    } else {
        Write-Host "  Downloading UnRen..." -ForegroundColor Gray
        $tempZip = Join-Path $env:TEMP "unren.zip"
        Invoke-WebRequest -Uri $unrenConfig.url -OutFile $tempZip -UseBasicParsing

        Write-Host "  Extracting UnRen..." -ForegroundColor Gray
        New-Item -ItemType Directory -Force -Path $unrenPath | Out-Null
        Expand-Archive -Path $tempZip -DestinationPath $unrenPath -Force

        Remove-Item $tempZip
        Write-Host "  UnRen installed!" -ForegroundColor Green
    }

    Write-Host ""
} else {
    Write-Host "[3/4] Skipping tools download (--SkipTools)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# 4. Verify Installation
# =============================================================================
Write-Host "[4/4] Verifying installation..." -ForegroundColor Green

$allGood = $true

# Check Python packages
Write-Host "  Checking Python packages..." -ForegroundColor Gray
try {
    python -c "import torch; import llama_cpp; import transformers; print('  - All packages installed')"
} catch {
    Write-Host "  ERROR: Some Python packages missing" -ForegroundColor Red
    $allGood = $false
}

# Check CUDA
Write-Host "  Checking CUDA support..." -ForegroundColor Gray
try {
    $cudaAvailable = python -c "import torch; print(torch.cuda.is_available())" 2>$null
    if ($cudaAvailable -eq "True") {
        Write-Host "  - CUDA available" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: CUDA not available (will use CPU)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  WARNING: Could not check CUDA" -ForegroundColor Yellow
}

# Check model
if (-not $SkipModel) {
    $modelPath = Join-Path $scriptDir $config.models."aya-23-8b".destination
    if (Test-Path $modelPath) {
        $size = (Get-Item $modelPath).Length / 1GB
        Write-Host "  - Model present: $([math]::Round($size, 2)) GB" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: Model not found" -ForegroundColor Yellow
        $allGood = $false
    }
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "     venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Test the translation:" -ForegroundColor White
    Write-Host "     python scripts\translate.py --help" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. See README.md for usage examples" -ForegroundColor White
} else {
    Write-Host "  SETUP COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "  Please review the messages above and install missing components" -ForegroundColor Yellow
}

Write-Host "=====================================================================" -ForegroundColor Cyan
