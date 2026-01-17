# poly_ren

Renpy-specific text extraction and merging tools.

## Description

Handles extraction of translatable text from Renpy game files (.rpy), tag preservation, and merging translated text back into game files.

## Setup

```bash
# Install dependencies
pip install -r ../../requirements.txt

# Or install as package
pip install -e .
```

## Configure

No configuration required. Extraction/merging is file-based.

## Run

### Extract
```bash
# Python CLI
python cli.py extract <input_dir> <output_yaml>

# Or programmatically
from src.poly_ren.extract import RenpyExtractor
extractor = RenpyExtractor()
blocks = extractor.extract_from_directory("game/tl")
```

### Merge
```bash
# Python CLI
python cli.py merge <translation_yaml> <output_dir>

# Or programmatically
from src.poly_ren.merge import RenpyMerger
merger = RenpyMerger()
merger.merge_translations("translations.yaml", "game/tl/language")
```

## Test

```bash
# Run poly_ren tests
pytest ../../tests/test_unit_extract.py
pytest ../../tests/test_unit_merge.py
pytest ../../tests/test_unit_renpy_tags.py
```

## Debug

Check extracted YAML structure or enable verbose output in extractor/merger classes.
