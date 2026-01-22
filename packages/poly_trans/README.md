# poly_trans

Local neural translation engine with context awareness and glossary support.

## Description

Standalone translation package supporting 5 neural models (Aya23, MADLAD400, Helsinki, mBART, SeamlessM4T) with contextual translation, glossary support, and prompt customization.

**Input:** YAML files with untranslated dialogue blocks
**Output:** Same YAML files with translations added
**Method:** Line-by-line translation with surrounding context

## Setup

### Installation

```bash
# From monorepo root
cd C:\_____\_CODE\enro
pip install -e src/poly_trans

# Or install dependencies directly
pip install -r requirements.txt
```

### Dependencies

- Python >=3.9
- PyYAML >=6.0
- PyTorch >=2.0.0
- Transformers >=4.30.0
- llama-cpp-python >=0.2.0
- sentencepiece >=0.1.99

## Usage

### Programmatic API

```python
from poly_trans.translate import ModularBatchTranslator
from poly_trans.translators.aya23_translator import Aya23Translator

# Initialize translator
translator = Aya23Translator(
    model_path="path/to/aya-23-8B.gguf",
    target_language="Romanian",
    glossary={"hello": "bună"},
    prompt_template="Translate to {target_language}: {text}"
)

# Create batch translator
batch_translator = ModularBatchTranslator(
    translator=translator,
    characters={},  # Character info dict
    target_lang_code="ro",
    context_before=3,  # Lines of context before
    context_after=1    # Lines of context after
)

# Translate a YAML file
stats = batch_translator.translate_file(
    parsed_yaml_path="path/to/game.parsed.yaml",
    tags_yaml_path="path/to/game.tags.yaml"
)

print(f"Translated: {stats['translated']} blocks")
```

### Available Translators

```python
# Import specific translators as needed
from poly_trans.translators.aya23_translator import Aya23Translator
from poly_trans.translators.madlad400_translator import MADLAD400Translator
from poly_trans.translators.helsinkyRo_translator import HelsinkiRoTranslator
from poly_trans.translators.mbartRo_translator import MBartRoTranslator
from poly_trans.translators.seamless96_translator import SeamlessM4Tv2Translator
```

## Configuration

### Prompts

Edit YAML files in `data/prompts/`:
- `aya23.yaml` - Aya23 model prompts
- `madlad400.yaml` - MADLAD400 prompts
- `helsinkyRo.yaml` - Helsinki prompts
- etc.

### Glossaries

Edit YAML files in `data/glossaries/`:
```yaml
# data/glossaries/ro_glossary.yaml
hello: bună
world: lume
```

### Models

Models are configured via `models/models_config.yaml` (monorepo root).

## Input Format

poly_trans expects `.parsed.yaml` files:

```yaml
1-Character1:
  en: "Hello, how are you?"
  ro: ""  # Empty = needs translation

2-Character2:
  en: "I'm fine, thanks!"
  ro: ""
```

After translation:

```yaml
1-Character1:
  en: "Hello, how are you?"
  ro: "Bună, ce mai faci?"

2-Character2:
  en: "I'm fine, thanks!"
  ro: "Sunt bine, mulțumesc!"
```

## Test

```bash
# From monorepo root
cd C:\_____\_CODE\enro

# Test imports
python -c "from poly_trans.translate import ModularBatchTranslator; print('OK')"

# Run unit tests (from repo root)
pytest tests/test_unit_translate.py
```

## Debug

### Check Imports

```python
import sys
sys.path.insert(0, 'src')
import poly_trans
print(poly_trans.__version__)  # Should print: 1.0.0
```

### Check CUDA

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA devices: {torch.cuda.device_count()}")
```

### Enable Verbose Logging

```python
translator = Aya23Translator(
    model_path="...",
    target_language="Romanian",
    verbose=True  # Enable verbose output
)
```

## Notes

- **Context-aware:** Uses surrounding dialogue lines for better translations
- **Resumable:** Skips already-translated blocks (checks if target language field has content)
- **In-place:** Modifies input YAML files directly
- **Windows/CUDA primary:** Optimized for Windows with CUDA, expandable to Mac/Linux

## Package Structure

```
poly_trans/
  ├── __init__.py          # Package exports
  ├── translate.py         # Main translation logic
  ├── models.py            # Data types (ParsedBlock, etc.)
  ├── utils.py             # Utility functions
  ├── prompts.py           # Prompt management
  ├── translators/         # Translator implementations
  │   ├── aya23_translator.py
  │   ├── madlad400_translator.py
  │   ├── helsinkyRo_translator.py
  │   ├── mbartRo_translator.py
  │   └── seamless96_translator.py
  └── data/                # Prompts, glossaries, benchmarks
      ├── prompts/
      ├── glossaries/
      └── benchmarks/
```
