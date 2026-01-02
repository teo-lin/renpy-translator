## Installation

**Setup Steps:**
1. **Model Selection** - Choose which models to install:
   - Aya-23-8B (4.8GB) - 23 languages, higher quality
   - MADLAD-400-3B (~6GB) - 400+ languages, broader coverage
   - Or install both models

2. **Python Environment** - Automatically:
   - Creates virtual environment (detects and repairs corruption)
   - Checks pip version (takes ~1 minute, only upgrades if needed)
   - Installs PyTorch with CUDA 12.4 (shows installation progress)
   - Installs model-specific packages:
     - llama-cpp-python with CUDA for Aya-23-8B (verifies CUDA support)
     - transformers for MADLAD-400-3B
   - Checks if packages already installed before reinstalling
   - Automatically uninstalls and reinstalls broken CUDA packages

3. **Model Download** - Downloads your selected models from HuggingFace

4. **External Tools** - Checks (all included in repository):
   - Ren'Py SDK (downloads if missing)
   - rpaExtract.exe (included at `renpy/rpaExtract.exe`)
   - UnRen (included at `renpy/unRen/`)

5. **Language Configuration** - Select which languages you'll work with
   - Only shows languages supported by your selected models
   - Saves to `data/local_languages.json`
   - Used to filter language choices in `5-translate.ps1` and `6-correct.ps1`

6. **Verification** - Tests all components:
   - Verifies Python packages can actually import (not just installed)
   - Checks CUDA availability
   - Confirms selected models are downloaded

**Optional Skip Flags:**
```powershell
.\setup.ps1 -SkipModel      # Skip model download
.\setup.ps1 -SkipTools      # Skip Ren'Py/tools download
.\setup.ps1 -SkipPython     # Skip Python environment setup
```

**Reconfigure Languages Later:**
```powershell
# Re-run setup with skip flags to only change language configuration
.\setup.ps1 -SkipPython -SkipModel -SkipTools
```

**Troubleshooting Setup Issues:**

If setup completes with warnings about missing packages:

```powershell
# Fix broken llama-cpp-python (if "NOT INSTALLED" warning appears)
.\setup.ps1 -SkipModel -SkipTools

# The script will:
# 1. Detect the broken installation
# 2. Uninstall the CPU-only version
# 3. Reinstall with CUDA support
# 4. Verify it actually works
```

**Common Issues:**
- **"llama-cpp-python: NOT INSTALLED"** - CUDA wheel didn't install properly. Re-run setup with skip flags.
- **"Could not find module 'llama.dll'"** - CPU-only torch installed instead of CUDA. The setup script now automatically detects this and reinstalls torch with CUDA support. Re-run `.\setup.ps1`.
- **"CMake Error: CMAKE_C_COMPILER not set" or "Building wheel failed"** - Setup tried to build from source instead of using prebuilt wheel:
  - **Cause:** Your Python version (3.12+) may not have prebuilt CUDA wheels available
  - **Solution 1:** Use Python 3.10 or 3.11 (best wheel support)
  - **Solution 2:** Setup will automatically fallback to CPU-only version
  - **Solution 3:** Install Visual Studio Build Tools if you want to compile from source
- **Pip check takes forever** - This is normal, checking for outdated packages takes ~1 minute.
- **Virtual environment corrupted** - Setup automatically detects and recreates it.

### Manual Setup

If you prefer manual installation:

#### 1. Install Python Dependencies

```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Or install manually with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

#### 2. Download Model
Pick a model from models/MODELS.md

```powershell
# Using huggingface-cli
huggingface-cli download bartowski/aya-23-8B-GGUF aya-23-8B-Q4_K_M.gguf --local-dir models\aya-23-8B-GGUF
```

**Model:** Aya-23-8B Q4_K_M (4.8GB, January 2025 SOTA multilingual model)
Pick a model from models/MODELS.md

#### 3. Download Tools (Optional)

Download from `renpy/tools_config.json` or manually:
- [Ren'Py SDK](https://www.renpy.org/latest.html)
- [rpaExtract](https://github.com/Kaskadee/rpaextract) (multiple fallback URLs configured)
- UnRen (already included in the repository at `renpy/unRen/`)
