# Ren'Py Translation System

Translate **any Ren'Py visual novel** into **400+ languages** using state-of-the-art local AI models (Aya-23-8B or MADLAD-400-3B) on consumer grade laptop GPU (tested with RTX 3060, Windows)

**Game-Agnostic:** Works with any Ren'Py game - simply point it at your game's translation directory.

**Language-Agnostic:** Supports translation to:
- **23 major languages** via Aya-23-8B (Romanian, Spanish, French, German, Italian, Portuguese, Russian, Arabic, Chinese, Japanese, Korean, and more)
- **400+ languages** via MADLAD-400-3B (includes all Aya-23 languages plus hundreds more)

## Features

✅ **Dual Model Support** - Choose between Aya-23-8B (23 languages) or MADLAD-400-3B (400+ languages)
✅ **Modular Pipeline** - Extract → Translate → Merge workflow for better control and performance
✅ **Local Translation** - No cloud services, complete privacy
✅ **Preserves Ren'Py Formatting** - Keeps `{color=...}`, `{size=...}`, `[variables]` intact
✅ **Glossary Support** - Consistent terminology across your translations
✅ **Grammar Correction** - Optional post-processing for improved quality (Aya-23-8B)
✅ **Quality Benchmarking** - BLEU score testing against reference translations
✅ **Batch Processing** - Translate entire games automatically
✅ **Full GPU Acceleration** - Fast translation with CUDA support
✅ **Human Review Workflow** - Edit translations in YAML format before merging
✅ **Git-Friendly** - Track translation changes with clean diffs

## Translation Workflows

This system supports **two translation workflows**:

### 1. **All-in-One Workflow** (Original)
Simple, automated translation in a single step. Best for quick translations.

```powershell
.\translate.ps1  # Processes .rpy files directly
```

### 2. **Modular Workflow** (NEW - Recommended for Control)
Three-phase pipeline with human review checkpoints. Better for quality and collaboration.

```powershell
.\characters.ps1  # Phase 0: Setup (one-time)
.\extract.ps1     # Phase 1: Extract clean text
# → Edit .parsed.yaml files manually or translate
.\merge.ps1       # Phase 2: Merge back to .rpy
```

**Benefits of Modular Workflow:**
- ✅ **Human review** - Edit YAML files between steps
- ✅ **Better performance** - Batch translation instead of sequential
- ✅ **Git-friendly** - YAML diffs show exactly what changed
- ✅ **Token efficiency** - LLM only sees clean text, no tags
- ✅ **Integrity validation** - Syntax checking before final output

📖 **Detailed Guide:** See Pipelines section below for more info..

---

## Requirements

- **Python 3.10 or 3.11** (recommended for best CUDA wheel support)
  - Python 3.12+ may work but prebuilt CUDA wheels may not be available
  - If using Python 3.12+, you may need Visual Studio Build Tools for compilation
- NVIDIA GPU with 6GB+ VRAM (CUDA 12.4) - tested with RTX3060 on Windows. Uses all available GPU layers.
- ~8GB disk space (Aya-23-8B) or ~6GB disk space (MADLAD-400-3B)
- For MADLAD: `transformers` and `torch` packages (auto-installed with requirements.txt)

## Quick Start

### Interactive Mode (Recommended)

The easiest way to translate games is using the interactive PowerShell launchers:

```powershell
# Step 1: Run setup to select models and configure languages
.\setup.ps1

# Step 2: Translate your game (interactive menus guide you)
.\translate.ps1

# Step 3 (Optional): Correct grammar/conjugation errors
.\correct.ps1
```

The interactive scripts will:
1. **Select Model** - Choose Aya-23-8B or MADLAD-400-3B
2. **Select Language** - Pick from your configured languages
3. **Select Game** - Choose from automatically scanned games in `games/` folder
4. **Translate** - Process all translation files automatically

### Manual Mode (Advanced)

You can also call the Python scripts directly with specific arguments:

**Aya-23-8B (23 Languages, Higher Quality):**
```powershell
python scripts\translate_with_aya23.py "path\to\game\game\tl\<language>" --language <Language>
python scripts\correct_with_aya23.py "path\to\game\game\tl\<language>"
```

**MADLAD-400-3B (400+ Languages):**
```powershell
python scripts\translate_with_madlad.py "path\to\game\game\tl\<language>" --language <Language>
```

## Installation

### Automated Setup (Recommended)

Run the automated setup script which will guide you through an interactive configuration:

```powershell
# Run interactive setup script
.\setup.ps1
```

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
   - Used to filter language choices in `translate.ps1` and `correct.ps1`

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
- **"Could not find module 'llama.dll'"** - CPU version installed instead of CUDA. Re-run setup.
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

## Scripts

### Translation Script: `scripts\translate_with_aya23.py` (Aya-23-8B)

Translates Ren'Py files from English to target language using Aya-23-8B.

**Features:**
- Preserves Ren'Py tags (`{color=...}`, `{size=...}`) and variables (`[variable_name]`)
- Uses glossary for consistent terminology (optional)
- Context-aware translation for better dialogue quality
- ~2-3 seconds per sentence with GPU acceleration
- Best quality for 23 major languages

**Usage:**
```powershell
# Translate single file
python scripts\translate_with_aya23.py "path\to\file.rpy"

# Translate entire directory
python scripts\translate_with_aya23.py "path\to\game\game\tl\<language>"

# Or use interactive launcher (recommended)
.\translate.ps1
```

### Translation Script: `scripts\translate_with_madlad.py` (MADLAD-400-3B)

Translates Ren'Py files from English to any of 400+ languages using Google's MADLAD-400-3B model.

**Features:**
- Supports 400+ languages (far more than Aya-23-8B)
- Preserves Ren'Py tags and variables
- Uses language-agnostic glossary system
- Auto-detects language from path
- Uses uncensored prompts with fallback
- GPU acceleration via transformers

**Usage:**
```powershell
# Translate with explicit language specification
python scripts\translate_with_madlad.py "path\to\game\game\tl\japanese" --language Japanese --lang-code ja

# Auto-detect language from path
python scripts\translate_with_madlad.py "path\to\game\game\tl\spanish"
```

**Supported Language Codes (examples):**
- `ro` (Romanian), `es` (Spanish), `fr` (French), `de` (German), `it` (Italian)
- `pt` (Portuguese), `ru` (Russian), `tr` (Turkish), `pl` (Polish), `cs` (Czech)
- `zh` (Chinese), `ja` (Japanese), `ko` (Korean), `ar` (Arabic), `hi` (Hindi)
- And 380+ more languages...

### Correction Script: `scripts\correct_with_aya23.py`

Corrects grammar, conjugations, and gender agreement in translated files.

**Three Modes:**
- `--patterns-only`: Fast pattern-based corrections (uses JSON rules)
- `--llm-only`: Intelligent LLM corrections (slow, uses Aya-23-8B)
- Default: Both (patterns first, then LLM)

**Usage:**
```powershell
# Fast pattern corrections only
.\correct.ps1 "path\to\game\game\tl\<language>" --patterns-only

# Full correction (patterns + LLM)
.\correct.ps1 "path\to\game\game\tl\<language>"

# Preview changes without modifying files
.\correct.ps1 "path\to\game\game\tl\<language>" --dry-run
```

### Benchmark Script: `scripts\benchmark.py`

Benchmarks translation quality using BLEU scores by comparing model outputs to reference translations.

**Features:**
- Calculates BLEU scores for translation quality assessment
- Auto-detects language from filename
- Auto-detects matching glossary
- Shows average, min, max scores and best/worst examples

**Benchmark Data Format:**
Create `data/<language>_benchmark.json` with reference translations:
```json
[
  {
    "source": "English text to translate",
    "target": "Reference translation",
    "context": "Optional previous dialogue"
  }
]
```

**Usage:**
```powershell
# Run benchmark with auto-detected glossary
.\benchmark.ps1 data\ro_benchmark.json

# Run with explicit glossary
.\benchmark.ps1 data\ro_uncensored_benchmark.json --glossary data\ro_uncensored_glossary.json

# Run for other languages
.\benchmark.ps1 data\de_benchmark.json
```

**Template Files:**
- `data/ro_glossary.json` - Example SFW glossary template
- `data/ro_benchmark.json` - Example benchmark data template

## Configuration

### Custom Prompts

The translation and correction prompts can be customized by editing the template files in `data/prompts/`:
- `data/prompts/translate.txt` - SFW translation prompt template
- `data/prompts/correct.txt` - SFW grammar correction prompt template
- `data/prompts/translate_uncensored.txt` - Uncensored translation prompt (default if exists)
- `data/prompts/correct_uncensored.txt` - Uncensored correction prompt (default if exists)

**Fallback hierarchy:**
1. Try `*_uncensored.txt` (for adult/explicit content)
2. Fall back to `*.txt` (SFW version)
3. Fall back to embedded template in code

These files use Python's `{variable}` syntax for placeholders. Edit them to adjust the translation style, add language-specific rules, or modify the behavior.

### Custom Glossary

Create a glossary JSON file to enforce consistent translations for game-specific terms:

```json
{
  "health potion": "poțiune de viață",
  "magic points": "puncte magice",
  "inventory": "inventar"
}
```

Place in `data\<language_code>_glossary.json` (e.g., `data\ro_glossary.json`, `data\es_glossary.json`, `data\ja_glossary.json`)

**Template:** See `data/ro_glossary.json` for an example with UI elements, character stats, and common game terms.

**Fallback Hierarchy:**
1. `data\<code>_uncensored_glossary.json` (for adult content)
2. `data\<code>_glossary.json` (SFW version)
3. No glossary (translation without term enforcement)

Both Aya-23-8B and MADLAD-400-3B support glossaries.

### Grammar Correction Rules

Create correction rules JSON file for pattern-based corrections:

```json
{
  "exact_replacements": {
    "wrong phrase": "correct phrase"
  },
  "verb_conjugations": [
    {
      "pattern": "incorrectă forma",
      "replacement": "formă corectă"
    }
  ],
  "protected_words": ["ProperName", "GameTitle"]
}
```

Place in `data\<language>_corrections.json`

## Supported Languages

### Aya-23-8B (23 languages, higher quality)
- **European:** Romanian, Spanish, French, German, Italian, Portuguese, Russian, Turkish, Czech, Polish, Ukrainian, Bulgarian
- **Asian:** Chinese (Simplified/Traditional), Japanese, Korean, Vietnamese, Thai, Indonesian
- **Middle Eastern:** Arabic, Hebrew, Persian
- **Other:** Hindi, Bengali

**Note:** Translation quality varies by language. Romanian, Spanish, French, and German have the best support.

### MADLAD-400-3B (400+ languages, broader coverage)
- **All Aya-23-8B languages** plus 380+ additional languages
- **Major Languages:** All European, Asian, Middle Eastern languages
- **Regional Languages:** Catalan, Basque, Welsh, Gaelic, Swahili, Zulu, and hundreds more
- **Use Cases:** Ideal for less common languages, regional dialects, and low-resource languages

**Choosing a Model:**
- Use **Aya-23-8B** for: Romanian, Spanish, French, German (highest quality)
- Use **MADLAD-400-3B** for: Japanese, Korean, Chinese, rare languages, or when Aya-23 doesn't support your language

## Performance

### Aya-23-8B
- **Speed:** ~2-3 seconds/sentence (full GPU acceleration)
- **GPU Config:** ALL layers offloaded (-1), uses ~5.8GB VRAM
- **Quality:** SOTA multilingual model (January 2025)
- **Privacy:** 100% local processing, no data sent to cloud services
- **Status:** Production-ready

### MADLAD-400-3B
- **Speed:** ~1-2 seconds/sentence (GPU with transformers)
- **GPU Config:** Auto-detects CUDA, uses ~4GB VRAM
- **Quality:** Excellent for 400+ languages, Google Research model
- **Privacy:** 100% local processing, no data sent to cloud services
- **Status:** Production-ready

## Quality Assurance

### Automated Tests

```powershell
# Comprehensive end-to-end test suite (~2-3 minutes)
python tests\test_end_to_end.py

# Unit tests for tag preservation (fast, no model required)
python tests\test_renpy_tags.py

# Modular pipeline tests (extraction/merge)
python tests\test_extraction_merge.py
```

The tests verify:
- ✅ Game structure independence
- ✅ EN→target language conversion workflow
- ✅ Translation pipeline with Aya-23-8B
- ✅ Tag preservation (`{color=...}`, `[variables]`)
- ✅ Glossary usage
- ✅ Output format validation
- ✅ Extraction → YAML/JSON conversion
- ✅ Merge → .rpy reconstruction
- ✅ Integrity validation (quotes, brackets, variables)

### BLEU Benchmarking

Measure translation quality against reference translations:

```powershell
# Run benchmark (requires nltk: pip install nltk)
.\benchmark.ps1 data\ro_benchmark.json
```

Create your own benchmark data files with source/target pairs to track quality improvements over time.

## Examples

### Translate a Single File

```powershell
python scripts\translate_with_aya23.py "data\test.rpy"
```

### Translate Entire Game Directory

```powershell
# Step 1: Generate translation files with Ren'Py
renpy.exe "path\to\game" generate-translations romanian

# Step 2: Translate all files
.\translate.ps1 "path\to\game\game\tl\romanian"

# Step 3: Correct grammar (optional)
.\correct.ps1 "path\to\game\game\tl\romanian"
```

### Benchmark Translation Quality

Test your translations against reference data:

```powershell
# Create benchmark data (data/ro_benchmark.json with source/target pairs)
# Then run benchmark
.\benchmark.ps1 data\ro_benchmark.json

# Example output:
# Average BLEU: 0.7234
# Min BLEU:     0.5123
# Max BLEU:     0.9456
```

### Run Automated Tests

Verify the system works correctly:

```powershell
# Run all tests
python tests\test_end_to_end.py
python tests\test_renpy_tags.py
```

## Troubleshooting

### Line Ending and Encoding Issues (CRLF/LF)

**Affected File Types:**

Different file types require different line endings:

| File Type | Required | Why | Impact if Wrong |
|-----------|----------|-----|-----------------|
| `.ps1` (PowerShell) | **CRLF** | Windows PowerShell parser requirement | Parse errors, "unexpected token" |
| `.bat`, `.cmd` (Batch) | **CRLF** | Windows command interpreter | Script failure, commands not recognized |
| `.sh` (Shell) | **LF** | Unix/Linux shell requirement | Script fails with `\r: command not found` |
| `.py` (Python) | **LF** (preferred) | Cross-platform standard | Usually works but non-standard |
| `.rpy` (Ren'Py) | **LF** | Cross-platform game engine | May cause parsing issues |

**Symptoms:**
- **PowerShell (.ps1)**: "unexpected token" or "missing terminator" errors
- **Shell scripts (.sh)**: `/bin/bash^M: bad interpreter` or `\r: command not found`
- **Batch files (.bat)**: Commands not recognized or script stops unexpectedly
- Scripts worked before but fail after git operations
- Error mentions valid code as having syntax errors

**Cause:**
Mixed line endings (LF vs CRLF) or UTF-8 encoding issues. This can happen when:
- Git converts line endings inconsistently
- Files have UTF-8 emojis/special characters without a BOM (PowerShell only)
- `.gitattributes` settings conflict with actual file content
- Files edited on different operating systems (Windows vs Linux/Mac)

**Solution:**

1. **Check current line endings:**
```powershell
# View git's line ending configuration
git config core.autocrlf
git ls-files --eol characters.ps1

# Check actual file encoding
file characters.ps1
```

2. **Fix line endings for all PowerShell scripts:**
```powershell
# Option 1: Using Python (recommended)
python -c "
import glob
for file in glob.glob('*.ps1') + glob.glob('scripts/*.ps1'):
    with open(file, 'rb') as f:
        content = f.read()
    # Remove non-ASCII characters (emojis, special chars)
    text = content.decode('utf-8', errors='ignore')
    text_ascii = ''.join(c if ord(c) < 128 else '' for c in text)
    # Normalize to CRLF
    text_ascii = text_ascii.replace('\r\n', '\n').replace('\n', '\r\n')
    with open(file, 'wb') as f:
        f.write(text_ascii.encode('ascii'))
print('Fixed all .ps1 files')
"

# Option 2: Renormalize git index
git add --renormalize *.ps1 scripts/*.ps1
git status  # Check what changed
```

3. **Prevent future issues:**
```powershell
# Ensure .gitattributes is configured (already set in this repo)
cat .gitattributes
# Should show: *.ps1 text eol=crlf

# Normalize all tracked files
git add --renormalize .
git status

# Commit the normalized files
git commit -m "Normalize line endings"
```

4. **Avoid non-ASCII characters in PowerShell:**
- Don't use emojis in PowerShell scripts (use `[OK]` instead of `✅`)
- Don't use Unicode box-drawing characters
- If you must use Unicode, add UTF-8 BOM to the file

**Prevention - Pre-Commit Hook:**

This repository includes a pre-commit hook at `.git/hooks/pre-commit` that automatically validates line endings for all file types.

**Installation:**
```bash
# The hook is already installed if you cloned this repo
# To manually install/update:
chmod +x .git/hooks/pre-commit
```

**What it checks:**
- ✅ **PowerShell (.ps1)**: Blocks non-ASCII characters, warns about LF
- ✅ **Batch files (.bat, .cmd)**: Warns about LF line endings
- ✅ **Shell scripts (.sh)**: **Blocks CRLF** (will break on Unix/Linux)
- ⚠️ **Python (.py)**: Warns about CRLF (LF is standard)
- 💡 Suggests fixes with helpful error messages

**Testing the hook:**
```bash
# This will be blocked:
echo 'Write-Host "✅ Success"' > test.ps1
git add test.ps1
git commit -m "test"
# Output: ERROR: test.ps1 contains non-ASCII characters

# This will succeed:
echo 'Write-Host "[OK] Success"' > test.ps1
git add test.ps1
git commit -m "test"
```

**Git Configuration:**
This repository uses `.gitattributes` to enforce correct line endings:

```gitattributes
# Windows-specific files (CRLF required)
*.ps1 text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf

# Unix/Linux files (LF required)
*.sh text eol=lf

# Cross-platform files (LF standard)
*.py text eol=lf
*.rpy text eol=lf
*.md text
*.json text
```

Plus `core.autocrlf=true` for automatic conversion on Windows.

**One-Time Setup After Cloning:**
```bash
# Normalize all files to prevent issues
git add --renormalize .
git commit -m "Normalize line endings"
```

### CUDA DLL Not Found

If you get CUDA errors, add torch's lib directory to PATH:

```powershell
$env:PATH = "path\to\venv\Lib\site-packages\torch\lib;" + $env:PATH
```

### Out of Memory

If you run out of VRAM, reduce GPU layers:

```python
# In src\core.py, change:
translator = Aya23Translator(model_path, n_gpu_layers=30)  # Instead of -1
```

### Poor Translation Quality

1. Check if language is well-supported by Aya-23-8B
2. Add domain-specific terms to your glossary
3. Use grammar correction with `--llm-only` for better results
4. Run benchmarks to measure quality against reference translations
5. Consider fine-tuning the model with your training data

## File Structure

```
├── src/                    # Core translation modules
│   ├── models.py          # Type-safe data structures for modular pipeline
│   ├── extraction.py      # Extract .rpy → clean YAML + tags JSON
│   ├── merger.py          # Merge YAML + JSON → .rpy with validation
│   ├── batch_translator.py # Context-aware batch translation
│   ├── renpy_utils.py     # Ren'Py parsing and tag handling utilities
│   ├── core.py            # Aya23Translator class (original pipeline)
│   └── prompts.py         # Translation/correction prompts
├── scripts/               # Translation engine scripts (called by launchers)
│   ├── translate_with_aya23.py     # Aya-23-8B translation engine
│   ├── translate_with_madlad.py    # MADLAD-400-3B translation engine
│   ├── correct_with_aya23.py       # Aya-23-8B grammar correction engine
│   ├── benchmark.py       # BLEU benchmark script
│   ├── common.ps1         # Shared PowerShell functions
│   └── user_selection.ps1 # Interactive game/language selection
├── tests/                 # Automated tests
│   ├── test_end_to_end.py           # End-to-end translation tests
│   ├── test_renpy_tags.py           # Tag preservation tests
│   └── test_extraction_merge.py     # Modular pipeline tests (NEW)
├── data/                  # Prompts, glossaries, benchmarks, and correction rules
│   ├── prompts/
│   │   ├── translate.txt              # Translation prompt template (customizable)
│   │   ├── translate_uncensored.txt   # Uncensored translation prompt (gitignored)
│   │   ├── correct.txt                # Correction prompt template (customizable)
│   │   └── correct_uncensored.txt     # Uncensored correction prompt (gitignored)
│   ├── ro_glossary.json          # Example SFW glossary template
│   ├── ro_uncensored_glossary.json   # Example uncensored glossary (gitignored)
│   ├── ro_benchmark.json         # Example benchmark data template
│   └── ro_uncensored_corrections.json # Example correction rules (gitignored)
├── models/                # Downloaded models and configuration
│   └── local_config.json  # Per-game configuration (NEW)
├── tools/                 # External tools (gitignored)
├── renpy/                 # Ren'Py SDK (gitignored)
│   └── tools_config.json  # External tools configuration
├── games/                 # Game directories (gitignored)
│   └── <Game>/
│       └── game/tl/<language>/
│           ├── characters.json        # Character mappings (NEW)
│           ├── *.rpy                  # Original translation files
│           ├── *.parsed.yaml          # Clean text for editing (NEW)
│           ├── *.tags.json            # Tags and metadata (NEW)
│           └── *.translated.rpy       # Merged output (NEW)
├── requirements.txt       # Python dependencies
├── setup.ps1              # Automated setup script
├── translate.ps1          # Interactive launcher (selects model, language, game)
├── correct.ps1            # Interactive launcher for grammar correction
├── benchmark.ps1          # PowerShell launcher for benchmark.py
├── characters.ps1         # Character discovery & game setup (NEW)
├── extract.ps1            # Extract .rpy → YAML/JSON (NEW)
├── merge.ps1              # Merge YAML/JSON → .rpy (NEW)
├── PIPELINE_USAGE.md      # Modular pipeline user guide (NEW)
├── MODULARISATION_PLAN.md # Technical specification (NEW)
└── IMPLEMENTATION_SUMMARY.md # Implementation details (NEW)

```

## Contributing

See [DEV-NOTES.md](DEV-NOTES.md) for development history and technical implementation details.

## License

MIT License - Use for any purpose, including commercial projects.

---

## Acknowledgments

- **Models:**
  - [Aya-23-8B](https://huggingface.co/CohereForAI/aya-23-8B) by Cohere For AI
  - [MADLAD-400-3B](https://huggingface.co/google/madlad400-3b-mt) by Google Research
- **Quantization:** [bartowski's GGUF conversion](https://huggingface.co/bartowski/aya-23-8B-GGUF)
- **Frameworks:**
  - [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) (Aya-23-8B)
  - [transformers](https://github.com/huggingface/transformers) (MADLAD-400-3B)



# Modular Translation Pipeline - Usage Guide

## Overview

The modular translation pipeline separates the translation workflow into three distinct phases:

1. **Extraction**: Parse .rpy files → Extract clean text + tags
2. **Translation**: Translate clean text using LLMs
3. **Merge**: Reconstruct .rpy files with tags restored

This separation provides:
- ✅ **Better performance**: Batch translation instead of sequential
- ✅ **Human review**: Edit YAML files between phases
- ✅ **Token efficiency**: LLM only sees clean text
- ✅ **Git-friendly**: YAML diffs show exactly what changed
- ✅ **Integrity validation**: Syntax checking before final output

---

## Quick Start

### Phase 0: Initial Setup (One-Time)

```powershell
# 1. Discover characters and configure game
.\characters.ps1

# This will:
# - Let you select a game from games/ folder
# - Select target language
# - Select translation model
# - Auto-discover character variables
# - Save configuration to models/local_config.json
# - Save characters.json to game/tl/<language>/
```

**After this step:**
- Edit `game/tl/<language>/characters.json` to add proper character names
- Update gender, type, and descriptions

---

### Phase 1: Extraction

```powershell
# Extract a single file
.\extract.ps1 -Source "Cell01_JM.rpy"

# Extract all files in the game
.\extract.ps1 -All
```

**What happens:**
- Reads `Cell01_JM.rpy`
- Extracts clean English and Romanian text
- Removes all tags (`{color=#fff}`, `[name]`, etc.)
- Creates two files:
  - `Cell01_JM.parsed.yaml` - Human-readable, editable
  - `Cell01_JM.tags.json` - Machine-readable metadata

**Output Example (`Cell01_JM.parsed.yaml`):**
```yaml
"1-Jasmine":
  en: "See you later. Bye!"
  ro: "Ne vedem mai târziu. Ciao!"

"2-Amelia":
  en: "It could help us speed up her corruption."
  ro: ""

"3-Choice":
  en: "I'd like to show you Sherazade's unicorn horn"
  ro: ""
```

**✋ STOP HERE - Review the YAML files for any parsing issues!**

---

### Phase 2: Translation

```powershell
# Use existing translate.ps1 (works with the current pipeline)
.\translate.ps1

# The script will:
# - Prompt for game selection
# - Load the model
# - Translate only untranslated blocks (ro: "")
# - Update the .rpy files directly
```

**Alternative (Manual YAML editing):**
You can manually edit the `.parsed.yaml` files to add translations, then skip to Phase 3.

**✋ STOP HERE - Review translations in YAML files!**

---

### Phase 3: Merge

```powershell
# Merge a single file
.\merge.ps1 -Source "Cell01_JM"

# Merge all files
.\merge.ps1 -All

# Skip validation (faster, but not recommended)
.\merge.ps1 -Source "Cell01_JM" -SkipValidation
```

**What happens:**
- Reads `Cell01_JM.parsed.yaml` and `Cell01_JM.tags.json`
- Restores tags to translated text
- Reconstructs .rpy file structure
- Validates syntax (quotes, brackets, variables)
- Creates `Cell01_JM.translated.rpy`

**Validation checks:**
- ✅ Unmatched quotes
- ✅ Unmatched braces/brackets
- ✅ Missing character variables
- ✅ Missing variables from original in translation

---

## File Structure

After running the pipeline, your `game/tl/<language>/` directory will contain:

```
game/tl/romanian/
├── characters.json           # Character name mappings
├── Cell01_JM.rpy            # Original translation file
├── Cell01_JM.parsed.yaml    # Clean text for editing/translation
├── Cell01_JM.tags.json      # Tags and metadata
└── Cell01_JM.translated.rpy # Final output (after merge)
```

---

## Workflow Examples

### Example 1: New Game Setup

```powershell
# Step 1: Configure game
.\characters.ps1
# Select game, language, model
# Edit game/tl/romanian/characters.json manually

# Step 2: Extract all files
.\extract.ps1 -All

# Step 3: Translate
.\translate.ps1
# Select same game

# Step 4: Merge all
.\merge.ps1 -All

# Step 5: Test in game, then replace originals
```

### Example 2: Update Single File

```powershell
# Extract
.\extract.ps1 -Source "Cell01_JM.rpy"

# Manually edit Cell01_JM.parsed.yaml to fix translations

# Merge
.\merge.ps1 -Source "Cell01_JM"

# Review Cell01_JM.translated.rpy
```

### Example 3: Batch Re-translation

```powershell
# Extract all files (preserves existing translations)
.\extract.ps1 -All

# Translate only untranslated blocks
.\translate.ps1

# Merge all
.\merge.ps1 -All
```

---

## Configuration

### models/local_config.json

Stores game-specific configuration:

```json
{
  "games": {
    "Once.a.Porn.a.Time.2": {
      "name": "Once.a.Porn.a.Time.2",
      "path": "C:\\_oxo_\\games\\Once.a.Porn.a.Time.2",
      "target_language": "romanian",
      "source_language": "english",
      "model": "Aya-23-8B",
      "context_before": 3,
      "context_after": 1
    }
  },
  "current_game": "Once.a.Porn.a.Time.2"
}
```

### game/tl/<language>/characters.json

Maps character variables to display names:

```json
{
  "jm": {
    "name": "Jasmine",
    "gender": "female",
    "type": "main",
    "description": "Main quest character"
  },
  "u": {
    "name": "Prince",
    "gender": "male",
    "type": "protagonist",
    "description": "Player character"
  }
}
```

---

## Context Strategy

The translation engine uses asymmetric context (from `MODULARISATION_PLAN.md`):

- **Cell files** (character dialogue): 3 lines before, 1 line after
- **Room files** (environment): 2 lines before, 1 line after
- **Expedition files** (gameplay): 1 line before only
- **Common.rpy** (system): No context

This is configured in `models/local_config.json` per game.

---

## Troubleshooting

### "Configuration file not found"
**Solution:** Run `.\characters.ps1` first to set up the game.

### "No .parsed.yaml files found"
**Solution:** Run `.\extract.ps1 -All` first.

### "Validation errors found"
**Solution:** Review the error report. Common issues:
- Missing quotes in translation
- Unmatched `{color}` tags
- Missing `[variable]` placeholders

Fix in the `.parsed.yaml` file and re-run `.\merge.ps1`.

### "Python not found"
**Solution:** The scripts use the system Python. Install Python 3.8+ or run `.\setup.ps1` to create a venv.

---

## Advanced Features

### Manual Translation Workflow

1. Extract files: `.\extract.ps1 -All`
2. Send `.parsed.yaml` files to human translators
3. Translators edit YAML files directly (easy to read/edit)
4. Receive completed YAML files
5. Merge: `.\merge.ps1 -All`

### Git Integration

YAML files are git-friendly:

```bash
git diff Cell01_JM.parsed.yaml
```

Shows exactly which translations changed, without tag noise.

### Batch Processing

Process multiple games:

```powershell
# Game 1
.\characters.ps1  # Select Game 1
.\extract.ps1 -All
.\translate.ps1
.\merge.ps1 -All

# Game 2
.\characters.ps1  # Select Game 2
.\extract.ps1 -All
.\translate.ps1
.\merge.ps1 -All
```

---

## File Format Details

### .parsed.yaml Format

```yaml
# Cell01_JM.rpy - Parsed Translations
# Generated: 2025-12-27 10:30:00

"1-Jasmine":
  en: "See you later. Bye!"
  ro: "Ne vedem mai târziu. Ciao!"

"2-Narrator":
  en: "You don't have any mail!"
  ro: ""

"separator-1":
  type: separator

"3-Choice":
  en: "I'd like to show you Sherazade's unicorn horn"
  ro: ""
```

**Key points:**
- Composite keys: `"blockID-CharacterName"`
- `en`: English text (always present, tags removed)
- `ro`: Romanian translation (empty if untranslated)
- `separator` blocks preserve structure

### .tags.json Format

Contains complete metadata for reconstruction. See `src/models.py` for full structure.

---

## Next Steps

- [ ] Test the pipeline on a single file
- [ ] Extract all files for your game
- [ ] Review and edit `characters.json`
- [ ] Run full translation pipeline
- [ ] Test in-game
- [ ] Report any issues

---

## Support

For issues or questions:
1. Check validation error messages
2. Review this guide
3. Check `MODULARISATION_PLAN.md` for technical details
4. Inspect the generated YAML files manually
