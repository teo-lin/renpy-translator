# Ren'Py Translation System

Translate **any Ren'Py visual novel** into **400+ languages** using state-of-the-art local AI models (Aya-23-8B or MADLAD-400-3B) on consumer grade laptop GPU (tested with RTX 3060, Windows)

**Game-Agnostic:** Works with any Ren'Py game - simply point it at your game's translation directory.

**Language-Agnostic:** Supports translation to:
- **23 major languages** via Aya-23-8B (Romanian, Spanish, French, German, Italian, Portuguese, Russian, Arabic, Chinese, Japanese, Korean, and more)
- **400+ languages** via MADLAD-400-3B (includes all Aya-23 languages plus hundreds more)

## Features

✅ **Dual Model Support** - Choose between Aya-23-8B (23 languages) or MADLAD-400-3B (400+ languages)
✅ **Local Translation** - No cloud services, complete privacy
✅ **Preserves Ren'Py Formatting** - Keeps `{color=...}`, `{size=...}`, `[variables]` intact
✅ **Glossary Support** - Consistent terminology across your translations
✅ **Grammar Correction** - Optional post-processing for improved quality (Aya-23-8B)
✅ **Quality Benchmarking** - BLEU score testing against reference translations
✅ **Batch Processing** - Translate entire games automatically
✅ **Full GPU Acceleration** - Fast translation with CUDA support

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
```

The tests verify:
- ✅ Game structure independence
- ✅ EN→target language conversion workflow
- ✅ Translation pipeline with Aya-23-8B
- ✅ Tag preservation (`{color=...}`, `[variables]`)
- ✅ Glossary usage
- ✅ Output format validation

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
│   ├── core.py            # Aya23Translator class
│   └── prompts.py         # Translation/correction prompts
├── scripts/               # Translation engine scripts (called by launchers)
│   ├── translate_with_aya23.py     # Aya-23-8B translation engine
│   ├── translate_with_madlad.py    # MADLAD-400-3B translation engine
│   ├── correct_with_aya23.py       # Aya-23-8B grammar correction engine
│   └── benchmark.py       # BLEU benchmark script
├── tests/                 # Automated tests
│   ├── test_end_to_end.py
│   └── test_renpy_tags.py
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
├── models/                # Downloaded models (gitignored)
├── tools/                 # External tools (gitignored)
├── renpy/                 # Ren'Py SDK (gitignored)
│   └── tools_config.json  # External tools configuration
├── requirements.txt       # Python dependencies
├── setup.ps1              # Automated setup script
├── translate.ps1          # Interactive launcher (selects model, language, game)
├── correct.ps1            # Interactive launcher for grammar correction
└── benchmark.ps1          # PowerShell launcher for benchmark.py

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
