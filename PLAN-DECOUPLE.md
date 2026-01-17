# Plan: Decouple Translation System into Three Apps

## Overview

Split the current monolithic translation system into three independent Python packages:
1. **poly-trans** (`c:\_____\_CODE\poly-trans`) - Core translation engine (publishable to PyPI)
2. **poly-ren** (`c:\_____\_CODE\poly-ren`) - Renpy-specific text extraction/merging
3. **poly-bench** (`c:\_____\_CODE\poly-bench`) - Model comparison CLI tool

**Strategy**: Two-phase approach
- **Phase 1**: Pure architectural split with NO logic changes
- **Phase 2**: Add improvements (modular contexts, style guides, etc.)

**Platform**: Windows/CUDA primary, each app must be runnable and testable individually

---

## PHASE 1: Split into 3 Apps (No Logic Changes)

### Goal

Extract three separate Python packages from the current codebase while preserving all existing functionality exactly as-is.

### 1.1 Create poly-trans Package (local_translator)

**Location:** `c:\_____\_CODE\poly-trans`

**Package Structure:**
```
poly-trans/
├── pyproject.toml              # Python packaging config
├── setup.py                    # Backward compatibility
├── README.md
├── LICENSE
├── local_translator/           # Python package name
│   ├── __init__.py
│   ├── __version__.py
│   ├── translate.py            # From enro/scripts/translate.py (ModularBatchTranslator)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── aya23_translator.py      # From enro/src/translators/
│   │   ├── madlad400_translator.py  # From enro/src/translators/
│   │   ├── helsinkyRo_translator.py # From enro/src/translators/
│   │   ├── mbartRo_translator.py    # From enro/src/translators/
│   │   └── seamless96_translator.py # From enro/src/translators/
│   └── prompts.py              # From enro/src/prompts.py
├── data/                       # From enro/data/
│   ├── prompts/
│   │   ├── translate.txt
│   │   └── translate_uncensored.txt
│   ├── ro_glossary.yaml
│   ├── ro_uncensored_glossary.yaml
│   └── ro_benchmark.json
├── scripts/                    # PowerShell wrappers (keep for Windows)
│   └── translate.ps1
└── tests/
    └── test_translators.py
```

**Files to Move from enro:**
- `scripts/translate.py` → `poly-trans/local_translator/translate.py`
  - Keep ModularBatchTranslator class exactly as-is
  - Keep all current context logic (3 before, 1 after)
- `src/translators/*.py` → `poly-trans/local_translator/models/*.py`
  - Copy all 5 translator classes unchanged
- `src/prompts.py` → `poly-trans/local_translator/prompts.py`
  - Keep prompt loading logic unchanged
- `data/` → `poly-trans/data/`
  - Move entire data folder (prompts, glossaries, benchmark files)

**PowerShell Wrappers:**
- Keep existing PowerShell scripts as thin wrappers
- Create Python CLI alongside (don't replace)
- Both should work independently for Windows testing

**Critical Files:**
- `poly-trans/local_translator/translate.py:27-340` - ModularBatchTranslator class
- `poly-trans/local_translator/models/aya23_translator.py:128-160` - Aya23 translation logic
- `poly-trans/local_translator/prompts.py` - Prompt loading
- `poly-trans/data/prompts/translate.txt` - Translation prompts

**Dependencies (pyproject.toml):**
```toml
dependencies = [
    "pyyaml>=6.0",
    "torch>=2.0.0",
    "transformers>=4.30.0",
    "llama-cpp-python>=0.2.0",
    "sentencepiece>=0.1.99",
]
```

**API:** Keep current file-based API (load YAML, translate, save YAML) - no new interfaces yet

**Testing on Windows:**
- Install locally: `pip install -e c:\_____\_CODE\poly-trans`
- Run PowerShell wrapper: `.\scripts\translate.ps1`
- Run Python CLI: `python -m local_translator.translate`
- Both should produce identical results

---

### 1.2 Create poly-ren Package (renpy_translator)

**Location:** `c:\_____\_CODE\poly-ren`

**Package Structure:**
```
poly-ren/
├── pyproject.toml
├── README.md
├── renpy_translator/           # Python package name
│   ├── __init__.py
│   ├── extract.py              # From enro/src/extract.py
│   ├── merge.py                # From enro/src/merge.py
│   ├── models.py               # From enro/src/models.py
│   ├── renpy_utils.py          # From enro/src/renpy_utils.py
│   └── cli.py                  # Python CLI
├── scripts/                    # PowerShell wrappers (keep for Windows)
│   ├── extract.ps1
│   ├── merge.ps1
│   └── translate.ps1
└── tests/
    ├── test_extract.py
    ├── test_merge.py
    └── fixtures/
```

**Files to Move from enro:**
- `src/extract.py` → `poly-ren/renpy_translator/extract.py` (unchanged)
- `src/merge.py` → `poly-ren/renpy_translator/merge.py` (unchanged)
- `src/models.py` → `poly-ren/renpy_translator/models.py` (unchanged)
- `src/renpy_utils.py` → `poly-ren/renpy_translator/renpy_utils.py` (unchanged)

**New Files to Create:**
- `poly-ren/renpy_translator/cli.py` - Python CLI
  - Provide Python entry points for extract/merge/translate
  - Call `local_translator` functions via import
- `poly-ren/scripts/*.ps1` - PowerShell wrappers (keep existing)
  - Keep current PowerShell workflow scripts
  - Update to call Python CLI underneath
  - Don't delete - needed for Windows testing

**Critical Files:**
- `poly-ren/renpy_translator/extract.py:27-195` - RenpyExtractor class
- `poly-ren/renpy_translator/merge.py:19-230` - RenpyMerger class
- `poly-ren/renpy_translator/renpy_utils.py:9-118` - RenpyTagExtractor class

**Dependencies (pyproject.toml):**
```toml
dependencies = [
    "pyyaml>=6.0",
    # For local development: pip install -e c:\_____\_CODE\poly-trans
    # For PyPI release: "local-translator>=1.0.0"
]
```

**Note:** During Phase 1, install poly-trans locally with `-e` flag. After PyPI publish, use package dependency.

**Testing on Windows:**
- Install locally: `pip install -e c:\_____\_CODE\poly-ren`
- Also install poly-trans: `pip install -e c:\_____\_CODE\poly-trans`
- Run PowerShell: `.\scripts\extract.ps1 game.rpy`
- Run Python CLI: `python -m renpy_translator extract game.rpy`

---

### 1.3 Create poly-bench Package (translation_model_comparer)

**Location:** `c:\_____\_CODE\poly-bench`

**Package Structure:**
```
poly-bench/
├── pyproject.toml
├── README.md
├── translation_model_comparer/ # Python package name
│   ├── __init__.py
│   ├── compare.py              # From enro/scripts/compare.py
│   ├── benchmark.py            # From enro/scripts/benchmark.py
│   └── cli.py                  # Python CLI
├── scripts/                    # PowerShell wrappers (keep for Windows)
│   ├── compare.ps1
│   └── benchmark.ps1
└── tests/
    └── test_benchmark.py
```

**Files to Move from enro:**
- `scripts/compare.py` → `poly-bench/translation_model_comparer/compare.py`
  - Keep model comparison logic unchanged
  - Update imports to use local_translator
- `scripts/benchmark.py` → `poly-bench/translation_model_comparer/benchmark.py`
  - Keep BLEU scoring logic unchanged
  - Update imports to use local_translator

**New Files to Create:**
- `poly-bench/translation_model_comparer/cli.py` - Python CLI
  - Provide Python entry points for compare/benchmark
- `poly-bench/scripts/compare.ps1` - PowerShell wrapper (from enro/8-compare.ps1)
  - Keep existing PowerShell logic
  - Update to call Python CLI
- `poly-bench/scripts/benchmark.ps1` - PowerShell wrapper (from enro/9-benchmark.ps1)
  - Keep existing PowerShell logic
  - Don't delete - needed for Windows

**Critical Files:**
- `poly-bench/translation_model_comparer/compare.py` - Speed comparison orchestration
- `poly-bench/translation_model_comparer/benchmark.py` - BLEU quality scoring

**Dependencies (pyproject.toml):**
```toml
dependencies = [
    "pyyaml>=6.0",
    "nltk>=3.8",
    # For local development: pip install -e c:\_____\_CODE\poly-trans
    # For PyPI release: "local-translator>=1.0.0"
]
```

**Note:** poly-bench uses benchmark data from poly-trans/data/ro_benchmark.json

**Testing on Windows:**
- Install locally: `pip install -e c:\_____\_CODE\poly-bench`
- Also install poly-trans: `pip install -e c:\_____\_CODE\poly-trans`
- Run PowerShell: `.\scripts\compare.ps1`
- Run Python CLI: `python -m translation_model_comparer compare`

---

### 1.4 Update Import Paths

**In poly-trans/local_translator:**
- No external imports from other packages
- Self-contained translation engine

**In poly-ren/renpy_translator:**
```python
# Before (in current enro monolith):
from src.translators.aya23_translator import Aya23Translator
from scripts.translate import ModularBatchTranslator

# After:
from local_translator.models.aya23_translator import Aya23Translator
from local_translator.translate import ModularBatchTranslator
```

**In poly-bench/translation_model_comparer:**
```python
# Before:
from src.translators.aya23_translator import Aya23Translator

# After:
from local_translator.models.aya23_translator import Aya23Translator
```

---

### 1.5 Configuration and Data Files

**Moved to poly-trans:**
- `data/prompts/translate.txt` → `poly-trans/data/prompts/translate.txt`
- `data/prompts/translate_uncensored.txt` → `poly-trans/data/prompts/translate_uncensored.txt`
- `data/ro_glossary.yaml` → `poly-trans/data/ro_glossary.yaml`
- `data/ro_uncensored_glossary.yaml` → `poly-trans/data/ro_uncensored_glossary.yaml`
- `data/ro_benchmark.json` → `poly-trans/data/ro_benchmark.json`

**Keep in enro project:**
- `models/models_config.yaml` - Model file paths/configurations
- `models/current_config.yaml` - Current game configuration
- Game-specific data (characters.yaml, etc.)

**Path Resolution:**
- poly-trans loads data from its own `data/` folder
- poly-trans loads model configs from enro `models/models_config.yaml` (absolute path or env var)
- poly-ren and poly-bench load data via poly-trans package

---

### 1.6 Testing Strategy for Phase 1

**Validation Checklist:**
1. Extract functionality still works identically
2. Translation produces same output as before
3. Merge reconstructs .rpy files correctly
4. Model comparison gives same speed results
5. Benchmark gives same BLEU scores

**Test Approach:**
1. Run full workflow on test game with OLD code → save outputs
2. Run full workflow with NEW split packages → compare outputs
3. Outputs must be byte-identical (or diff only in timestamps)

---

## PHASE 2: Improvements (After Split is Complete)

### Goal

Add new features and improvements to the decoupled architecture.

### 2.1 Modular Context System in poly-trans

**Add to local_translator/translate.py:**

**New Context Types:**
1. **Chapter summary** (auto-generated, editable)
2. **Previous/next lines** (for dialogue, as currently exists)
3. **User-provided context** (optional override)

**Implementation:**
- Create `local_translator/context.py` module
- Add `generate_chapter_summary()` function
- Add `extract_dialogue_context()` (from current code)
- Add `merge_contexts()` to combine all context types

**YAML API Extension:**
```yaml
blocks:
  - id: "1-Alice"
    text: "Hello!"
    contexts:
      chapter_summary: "Auto-generated or user-provided"
      dialogue_before: ["Bob: Hi there"]
      dialogue_after: ["Alice: How are you?"]
      user_provided: "Optional custom context"
```

---

### 2.2 Structured Style Guides

**Add to local_translator/translate.py:**

**Style Guide Fields:**
```yaml
metadata:
  style_guide:
    tone: informal          # formal | informal | neutral
    pronouns: tu            # tu | vous | mixed
    slang_level: moderate   # none | light | moderate | heavy
    formality: casual       # casual | professional | literary
    gender_neutral: true    # true | false
```

**Implementation:**
- Add `StyleGuide` class in `local_translator/style.py`
- Update prompt templates to include style instructions
- Pass style guide to translator models

---

### 2.3 Enhanced YAML API

**Full Input Format:**
```yaml
metadata:
  source_language: english
  target_language: romanian
  model: aya23
  style_guide:
    tone: informal
    pronouns: tu
    slang_level: moderate

config:
  auto_summarize: true      # Auto-generate chapter summaries
  context_before: 3         # Dialogue context lines
  context_after: 1
  temperature: 0.2

glossary:
  term1: translation1
  term2: translation2

blocks:
  - id: "1-Alice"
    text: "Hello, how are you?"
    speaker: Alice
    contexts:
      chapter_summary: "Optional user override"
      user_provided: "Additional context"
```

**Output Format:**
```yaml
metadata:
  translated_at: "2026-01-17T14:30:00Z"
  total_blocks: 10
  successful: 10
  failed: 0

results:
  - id: "1-Alice"
    source: "Hello, how are you?"
    translation: "Bună, ce mai faci?"
    contexts_used:
      chapter_summary: true
      dialogue_context: true
```

---

### 2.4 Publishing to PyPI

**For poly-trans/local_translator only** (first release):

1. Create PyPI account
2. Build package: `python -m build`
3. Upload to TestPyPI: `python -m twine upload --repository testpypi dist/*`
4. Test install: `pip install --index-url https://test.pypi.org/simple/ local-translator`
5. Upload to PyPI: `python -m twine upload dist/*`

**Version: 1.0.0** (initial release with current functionality)
**Version: 1.1.0** (after Phase 2 improvements)

---

### 2.5 Extensibility Enhancements

**Plugin System for Models:**
- Create `local_translator/models/base.py` with abstract `BaseTranslator`
- Allow loading custom models from external packages
- Register models via entry points

**Strategy Pattern:**
- Create `local_translator/strategies/base.py`
- Implement different translation strategies:
  - `line_context.py` (current approach)
  - `line_summary.py` (with chapter summaries)
  - `adaptive.py` (auto-select based on content)

---

## Implementation Order

### Week 1: Setup & poly-trans

1. Create directory: `c:\_____\_CODE\poly-trans`
2. Set up package structure with `local_translator/` subfolder
3. Move files from enro:
   - `src/translators/*.py` → `poly-trans/local_translator/models/`
   - `scripts/translate.py` → `poly-trans/local_translator/translate.py`
   - `src/prompts.py` → `poly-trans/local_translator/prompts.py`
   - `data/` → `poly-trans/data/`
4. Create `pyproject.toml` with dependencies
5. Create PowerShell wrapper: `poly-trans/scripts/translate.ps1`
6. Test local install: `pip install -e c:\_____\_CODE\poly-trans`
7. Test PowerShell wrapper on Windows
8. Verify translation produces identical output to enro

### Week 2: poly-ren

1. Create directory: `c:\_____\_CODE\poly-ren`
2. Set up package structure with `renpy_translator/` subfolder
3. Move files from enro:
   - `src/extract.py` → `poly-ren/renpy_translator/extract.py`
   - `src/merge.py` → `poly-ren/renpy_translator/merge.py`
   - `src/models.py` → `poly-ren/renpy_translator/models.py`
   - `src/renpy_utils.py` → `poly-ren/renpy_translator/renpy_utils.py`
4. Create `poly-ren/renpy_translator/cli.py` (Python CLI)
5. Copy PowerShell wrappers from enro to `poly-ren/scripts/`
6. Update imports to use `local_translator` from poly-trans
7. Create `pyproject.toml`
8. Test install: `pip install -e c:\_____\_CODE\poly-ren`
9. Test PowerShell wrappers on Windows
10. Verify extract → translate → merge workflow works identically

### Week 3: poly-bench

1. Create directory: `c:\_____\_CODE\poly-bench`
2. Set up package structure with `translation_model_comparer/` subfolder
3. Move files from enro:
   - `scripts/compare.py` → `poly-bench/translation_model_comparer/compare.py`
   - `scripts/benchmark.py` → `poly-bench/translation_model_comparer/benchmark.py`
4. Create `poly-bench/translation_model_comparer/cli.py` (Python CLI)
5. Copy PowerShell scripts from enro:
   - `8-compare.ps1` → `poly-bench/scripts/compare.ps1`
   - `9-benchmark.ps1` → `poly-bench/scripts/benchmark.ps1`
6. Update imports to use `local_translator` from poly-trans
7. Create `pyproject.toml`
8. Test install: `pip install -e c:\_____\_CODE\poly-bench`
9. Test PowerShell wrappers on Windows
10. Verify comparison and benchmark produce same results as enro

### Week 4: Validation & Testing

1. Run full test suite comparing old vs new outputs
2. Fix any regressions
3. Document migration process
4. Archive old code

### Week 5-6: Phase 2 Improvements

1. Implement modular context system
2. Add structured style guides
3. Create enhanced YAML API
4. Update documentation
5. Publish local_translator v1.1.0 to PyPI

---

## Critical Files Reference

**Files to Move (Phase 1):**

**From enro → poly-trans:**
- `scripts/translate.py:27-340` → `poly-trans/local_translator/translate.py`
- `src/translators/aya23_translator.py` → `poly-trans/local_translator/models/`
- `src/translators/madlad400_translator.py` → `poly-trans/local_translator/models/`
- `src/translators/helsinkyRo_translator.py` → `poly-trans/local_translator/models/`
- `src/translators/mbartRo_translator.py` → `poly-trans/local_translator/models/`
- `src/translators/seamless96_translator.py` → `poly-trans/local_translator/models/`
- `src/prompts.py` → `poly-trans/local_translator/prompts.py`
- `data/` → `poly-trans/data/`

**From enro → poly-ren:**
- `src/extract.py` → `poly-ren/renpy_translator/extract.py`
- `src/merge.py` → `poly-ren/renpy_translator/merge.py`
- `src/models.py` → `poly-ren/renpy_translator/models.py`
- `src/renpy_utils.py` → `poly-ren/renpy_translator/renpy_utils.py`
- PowerShell scripts → `poly-ren/scripts/`

**From enro → poly-bench:**
- `scripts/compare.py` → `poly-bench/translation_model_comparer/compare.py`
- `scripts/benchmark.py` → `poly-bench/translation_model_comparer/benchmark.py`
- `8-compare.ps1` → `poly-bench/scripts/compare.ps1`
- `9-benchmark.ps1` → `poly-bench/scripts/benchmark.ps1`

**Files to Create (Phase 1):**

**poly-trans:**
- `poly-trans/pyproject.toml`
- `poly-trans/local_translator/__init__.py`
- `poly-trans/local_translator/__version__.py`
- `poly-trans/scripts/translate.ps1` (PowerShell wrapper)

**poly-ren:**
- `poly-ren/pyproject.toml`
- `poly-ren/renpy_translator/__init__.py`
- `poly-ren/renpy_translator/cli.py` (Python CLI)
- Updated PowerShell wrappers in `poly-ren/scripts/`

**poly-bench:**
- `poly-bench/pyproject.toml`
- `poly-bench/translation_model_comparer/__init__.py`
- `poly-bench/translation_model_comparer/cli.py` (Python CLI)
- Updated PowerShell wrappers in `poly-bench/scripts/`

**Files to Create (Phase 2):**
- `poly-trans/local_translator/context.py`
- `poly-trans/local_translator/style.py`
- `poly-trans/local_translator/strategies/base.py`
- `poly-trans/local_translator/strategies/line_context.py`
- `poly-trans/local_translator/strategies/line_summary.py`

---

## Success Criteria

**Phase 1 Complete When:**
- All three packages install independently at their new locations
- Full workflow runs identically to current system
- All tests pass
- No functionality lost
- Both PowerShell and Python CLIs work on Windows

**Phase 2 Complete When:**
- Modular context system working
- Style guides integrated
- YAML API documented
- local_translator published to PyPI
- Documentation updated

---

## Directory Structure Summary

```
c:\_____\_CODE\
├── enro/                       # Original project (eventually deprecated)
├── poly-trans/                 # Core translator (publishable to PyPI)
│   ├── local_translator/       # Python package
│   ├── data/                   # Prompts, glossaries, benchmarks
│   └── scripts/                # PowerShell wrappers
├── poly-ren/                   # Renpy translator
│   ├── renpy_translator/       # Python package
│   └── scripts/                # PowerShell wrappers
└── poly-bench/                 # Model comparer
    ├── translation_model_comparer/  # Python package
    └── scripts/                # PowerShell wrappers
```

---

## Notes

- All packages use YAML exclusively (no JSON)
- Windows/CUDA primary target, but Python-based for cross-platform expandability
- **PowerShell wrappers kept alongside Python CLIs** - don't delete, needed for Windows
- Both PowerShell and Python entry points must work independently
- Data folder moved to poly-trans (prompts, glossaries, benchmark)
- Model configs (`models_config.yaml`) stay in enro for now
- Publishing only for poly-trans/local_translator (others may be published later)
- Each app must be runnable and testable individually on Windows
