# Ren'Py Translation System

Translate **any Ren'Py visual novel** into **major languages** using Aya-23-8B (local, private) using consumer grade laptop GPU (tested with RTX 3060, Windows)

**Game-Agnostic:** Works with any Ren'Py game - simply point it at your game's translation directory.

**Language-Agnostic:** Supports translation to any language supported by Aya-23-8B (23 languages including Romanian, Spanish, French, German, Italian, Portuguese, Russian, Arabic, Chinese, Japanese, Korean, and more).

## Features

✅ **Local Translation** - No cloud services, complete privacy
✅ **Preserves Ren'Py Formatting** - Keeps `{color=...}`, `{size=...}`, `[variables]` intact
✅ **Glossary Support** - Consistent terminology across your translations
✅ **Grammar Correction** - Optional post-processing for improved quality
✅ **Quality Benchmarking** - BLEU score testing against reference translations
✅ **Batch Processing** - Translate entire games automatically
✅ **Full GPU Acceleration** - Fast translation with CUDA support

## Requirements

- Python 3.12.7
- NVIDIA GPU with 6GB+ VRAM (CUDA 12.4) - tested with RTX3060 on Windows. Uses all available GPU layers.
- ~8GB disk space

## Quick Start

```powershell
# Step 1: Generate translation files using Ren'Py
renpy.exe "path\to\game" generate-translations <language>

# Step 2: Translate files with Aya-23-8B
.\translate.ps1 "path\to\game\game\tl\<language>"

# Step 3 (Optional): Correct grammar/conjugation errors
.\correct.ps1 "path\to\game\game\tl\<language>"
```

**Example (Romanian):**
```powershell
renpy.exe "path\to\game" generate-translations romanian
.\translate.ps1 "path\to\game\game\tl\romanian"
.\correct.ps1 "path\to\game\game\tl\romanian"
```

**Note:** You can also call the Python scripts directly: `python scripts\translate.py ...`

## Installation

### Automated Setup (Recommended)

Run the automated setup script to install everything:

```powershell
# Run setup script (downloads model, tools, and installs dependencies)
.\setup.ps1

# Optional: Skip certain steps
.\setup.ps1 -SkipModel      # Skip model download
.\setup.ps1 -SkipTools      # Skip Ren'Py/tools download
.\setup.ps1 -SkipPython     # Skip Python environment setup
```

**What it installs:**
- ✅ Python virtual environment with all dependencies
- ✅ Aya-23-8B model (4.8GB) from HuggingFace
- ✅ Ren'Py SDK (for generate-translations command)
- ✅ rpaExtract.exe (extract RPA archives)
- ✅ UnRen (decompile Ren'Py games)

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
- [rpaExtract](https://github.com/Lattyware/rpaextract)
- [UnRen](https://github.com/sam-m888/unren-forpy3)

## Scripts

### Translation Script: `scripts\translate.py`

Translates Ren'Py files from English to target language using Aya-23-8B.

**Features:**
- Preserves Ren'Py tags (`{color=...}`, `{size=...}`) and variables (`[variable_name]`)
- Uses glossary for consistent terminology (optional)
- Context-aware translation for better dialogue quality
- ~2-3 seconds per sentence with GPU acceleration

**Usage:**
```powershell
# Translate single file
python scripts\translate.py "path\to\file.rpy"

# Translate entire directory
python scripts\translate.py "path\to\game\game\tl\<language>"
```

### Correction Script: `scripts\correct.py`

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

Place in `data\<language>_glossary.json` (e.g., `data\ro_glossary.json`, `data\es_glossary.json`)

**Template:** See `data/ro_glossary.json` for an example with UI elements, character stats, and common game terms.

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

Aya-23-8B supports 23 languages:
- **European:** Romanian, Spanish, French, German, Italian, Portuguese, Russian, Turkish, Czech, Polish, Ukrainian, Bulgarian
- **Asian:** Chinese (Simplified/Traditional), Japanese, Korean, Vietnamese, Thai, Indonesian
- **Middle Eastern:** Arabic, Hebrew, Persian
- **Other:** Hindi, Bengali

**Note:** Translation quality varies by language. Romanian, Spanish, French, and German have the best support.

## Performance

- **Speed:** ~2-3 seconds/sentence (full GPU acceleration)
- **GPU Config:** ALL layers offloaded (-1), uses ~5.8GB VRAM
- **Quality:** SOTA multilingual model (January 2025)
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
python scripts\translate.py "data\test.rpy"
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
├── scripts/               # User-facing CLI tools
│   ├── translate.py       # Batch translation script
│   ├── correct.py         # Grammar correction script
│   └── benchmark.py       # BLEU benchmark script
├── tests/                 # Automated tests
│   ├── test_end_to_end.py
│   └── test_renpy_tags.py
├── data/                  # Prompts, glossaries, benchmarks, and correction rules
│   ├── prompts/
│   │   ├── translate.txt         # Translation prompt template (customizable)
│   │   └── correct.txt           # Correction prompt template (customizable)
│   ├── ro_glossary.json          # Example SFW glossary template
│   ├── ro_benchmark.json         # Example benchmark data template
│   └── ro_uncensored_corrections.json # Example correction rules (gitignored)
├── models/                # Downloaded models (gitignored)
├── tools/                 # External tools (gitignored)
├── renpy/                 # Ren'Py SDK (gitignored)
│   └── tools_config.json  # External tools configuration
├── requirements.txt       # Python dependencies
├── setup.ps1              # Automated setup script
├── translate.ps1          # PowerShell launcher for translate.py
├── correct.ps1            # PowerShell launcher for correct.py
└── benchmark.ps1          # PowerShell launcher for benchmark.py

```

## Contributing

See [DEV-NOTES.md](DEV-NOTES.md) for development history and technical implementation details.

## License

MIT License - Use for any purpose, including commercial projects.

---

## Acknowledgments

- **Model:** [Aya-23-8B](https://huggingface.co/CohereForAI/aya-23-8B) by Cohere For AI
- **Quantization:** [bartowski's GGUF conversion](https://huggingface.co/bartowski/aya-23-8B-GGUF)
- **Framework:** [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
