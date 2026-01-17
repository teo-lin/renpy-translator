# Plan: Decouple Translation System into Three Apps (Monorepo)

## Overview

Reorganize the current monolithic translation system into three independent Python packages within a single monorepo:
1. **poly-trans** (`src/poly-trans/`) - Core translation engine (publishable to PyPI)
2. **poly-ren** (`src/poly-ren/`) - Renpy-specific text extraction/merging
3. **poly-bench** (`src/poly-bench/`) - Model comparison CLI tool

**Architecture**: Monorepo with workspace configuration
- All packages in one repository (enro)
- Each package publishable separately to PyPI
- Shared development environment and tooling

**Strategy**: Two-phase approach
- **Phase 1**: Pure architectural split with NO logic changes
- **Phase 2**: Add improvements (modular contexts, style guides, etc.)

**Platform**: Windows/CUDA primary, each app must be runnable and testable individually

---

## PHASE 1: Split into 3 Apps (No Logic Changes)

### Goal

Extract three separate Python packages from the current codebase while preserving all existing functionality exactly as-is.

### 1.1 Create poly-trans Package

**Location:** `src/poly-trans/` (within enro monorepo)

**Package Structure:**
```
src/poly-trans/
├── __init__.py
├── __version__.py
├── translate.py            # From scripts/translate.py (ModularBatchTranslator)
├── models/
│   ├── __init__.py
│   ├── aya23_translator.py      # From src/translators/
│   ├── madlad400_translator.py  # From src/translators/
│   ├── helsinkyRo_translator.py # From src/translators/
│   ├── mbartRo_translator.py    # From src/translators/
│   └── seamless96_translator.py # From src/translators/
├── prompts.py              # From src/prompts.py
├── data/                   # From data/
│   ├── prompts/
│   │   ├── translate.txt
│   │   └── translate_uncensored.txt
│   ├── ro_glossary.yaml
│   ├── ro_uncensored_glossary.yaml
│   └── ro_benchmark.json
└── pyproject.toml          # Package-specific config (for PyPI publishing)
```

**Files to Copy:**
- `scripts/translate.py` → `src/poly-trans/translate.py`
  - Keep ModularBatchTranslator class exactly as-is
  - Keep all current context logic (3 before, 1 after)
- `src/translators/*.py` → `src/poly-trans/models/*.py`
  - Copy all 5 translator classes unchanged
- `src/prompts.py` → `src/poly-trans/prompts.py`
  - Keep prompt loading logic unchanged
- `data/` → `src/poly-trans/data/`
  - Copy entire data folder (prompts, glossaries, benchmark files)

**Old Files:**
- Keep original files in `src/translators/`, `scripts/`, `data/` during transition
- Can be archived/removed after Phase 1 validation

**Critical Files:**
- `src/poly-trans/translate.py:27-340` - ModularBatchTranslator class
- `src/poly-trans/models/aya23_translator.py:128-160` - Aya23 translation logic
- `src/poly-trans/prompts.py` - Prompt loading
- `src/poly-trans/data/prompts/translate.txt` - Translation prompts

**Package Config (src/poly-trans/pyproject.toml):**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "poly-trans"
version = "1.0.0"
dependencies = [
    "pyyaml>=6.0",
    "torch>=2.0.0",
    "transformers>=4.30.0",
    "llama-cpp-python>=0.2.0",
    "sentencepiece>=0.1.99",
]
```

**API:** Keep current file-based API (load YAML, translate, save YAML) - no new interfaces yet

**Testing:**
- Install in editable mode: `pip install -e .` (from repo root with workspace config)
- Import: `from src.poly_trans.translate import ModularBatchTranslator`
- Both old and new code paths should work during transition

---

### 1.2 Create poly-ren Package

**Location:** `src/poly-ren/` (within enro monorepo)

**Package Structure:**
```
src/poly-ren/
├── __init__.py
├── extract.py              # From src/extract.py
├── merge.py                # From src/merge.py
├── models.py               # From src/models.py
├── renpy_utils.py          # From src/renpy_utils.py
├── cli.py                  # Python CLI (new)
└── pyproject.toml          # Package-specific config (for PyPI publishing)
```

**Files to Copy:**
- `src/extract.py` → `src/poly-ren/extract.py` (unchanged)
- `src/merge.py` → `src/poly-ren/merge.py` (unchanged)
- `src/models.py` → `src/poly-ren/models.py` (unchanged)
- `src/renpy_utils.py` → `src/poly-ren/renpy_utils.py` (unchanged)

**New Files to Create:**
- `src/poly-ren/cli.py` - Python CLI
  - Provide Python entry points for extract/merge/translate
  - Import from `src.poly_trans` (monorepo import)

**Old Files:**
- Keep original files in `src/` during transition
- Can be archived/removed after Phase 1 validation

**Critical Files:**
- `src/poly-ren/extract.py:27-195` - RenpyExtractor class
- `src/poly-ren/merge.py:19-230` - RenpyMerger class
- `src/poly-ren/renpy_utils.py:9-118` - RenpyTagExtractor class

**Package Config (src/poly-ren/pyproject.toml):**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "poly-ren"
version = "1.0.0"
dependencies = [
    "pyyaml>=6.0",
    # For monorepo: imports from src.poly_trans
    # For PyPI release: "poly-trans>=1.0.0"
]
```

**Testing:**
- Install in editable mode: `pip install -e .` (from repo root)
- Import: `from src.poly_ren.extract import RenpyExtractor`
- Import poly-trans: `from src.poly_trans.translate import ModularBatchTranslator`

---

### 1.3 Create poly-bench Package

**Location:** `src/poly-bench/` (within enro monorepo)

**Package Structure:**
```
src/poly-bench/
├── __init__.py
├── compare.py              # From scripts/compare.py
├── benchmark.py            # From scripts/benchmark.py
├── cli.py                  # Python CLI (new)
└── pyproject.toml          # Package-specific config (for PyPI publishing)
```

**Files to Copy:**
- `scripts/compare.py` → `src/poly-bench/compare.py`
  - Keep model comparison logic unchanged
  - Update imports to use `src.poly_trans`
- `scripts/benchmark.py` → `src/poly-bench/benchmark.py`
  - Keep BLEU scoring logic unchanged
  - Update imports to use `src.poly_trans`

**New Files to Create:**
- `src/poly-bench/cli.py` - Python CLI
  - Provide Python entry points for compare/benchmark
  - Import from `src.poly_trans` (monorepo import)

**Old Files:**
- Keep original files in `scripts/` during transition
- PowerShell scripts (8-compare.ps1, 9-benchmark.ps1) remain at root
- Can be updated to call new code paths

**Critical Files:**
- `src/poly-bench/compare.py` - Speed comparison orchestration
- `src/poly-bench/benchmark.py` - BLEU quality scoring

**Package Config (src/poly-bench/pyproject.toml):**
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "poly-bench"
version = "1.0.0"
dependencies = [
    "pyyaml>=6.0",
    "nltk>=3.8",
    # For monorepo: imports from src.poly_trans
    # For PyPI release: "poly-trans>=1.0.0"
]
```

**Note:** Uses benchmark data from `src/poly-trans/data/ro_benchmark.json`

**Testing:**
- Install in editable mode: `pip install -e .` (from repo root)
- Import: `from src.poly_bench.compare import compare_models`
- Import poly-trans: `from src.poly_trans.translate import ModularBatchTranslator`


---

### 1.4 Update Import Paths

**In src/poly-trans/:**
- No external imports from other packages
- Self-contained translation engine
- Internal imports: `from .models.aya23_translator import Aya23Translator`

**In src/poly-ren/:**
```python
# Before (current monolith):
from src.translators.aya23_translator import Aya23Translator
from scripts.translate import ModularBatchTranslator

# After (monorepo):
from src.poly_trans.models.aya23_translator import Aya23Translator
from src.poly_trans.translate import ModularBatchTranslator
```

**In src/poly-bench/:**
```python
# Before:
from src.translators.aya23_translator import Aya23Translator

# After (monorepo):
from src.poly_trans.models.aya23_translator import Aya23Translator
from src.poly_trans.translate import ModularBatchTranslator
```

**For PyPI Publishing:**
When publishing to PyPI, imports change to:
```python
# poly-ren and poly-bench after PyPI publish:
from poly_trans.models.aya23_translator import Aya23Translator
from poly_trans.translate import ModularBatchTranslator
```

---

### 1.5 Root Workspace Configuration

**Create root pyproject.toml** (for monorepo workspace):
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "enro-workspace"
version = "1.0.0"
requires-python = ">=3.9"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = "."
testpaths = ["tests", "src/poly-trans", "src/poly-ren", "src/poly-bench"]
```

**Configuration and Data Files:**

**Copied to src/poly-trans/data/:**
- `data/prompts/` → `src/poly-trans/data/prompts/`
- `data/ro_glossary.yaml` → `src/poly-trans/data/ro_glossary.yaml`
- `data/ro_uncensored_glossary.yaml` → `src/poly-trans/data/ro_uncensored_glossary.yaml`
- `data/ro_benchmark.json` → `src/poly-trans/data/ro_benchmark.json`

**Keep at root:**
- `models/models_config.yaml` - Model file paths/configurations
- `models/current_config.yaml` - Current game configuration
- `data/` - Original data folder (keep during transition)
- Game-specific data (characters.yaml, etc.)

**Path Resolution:**
- All three packages can access `models/` and `data/` via relative paths from repo root
- poly-trans has its own copy in `src/poly-trans/data/` for standalone use

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

1. Create root workspace config: `pyproject.toml`
2. Create directory structure: `src/poly-trans/` and `src/poly-trans/models/`
3. Copy files:
   - `src/translators/*.py` → `src/poly-trans/models/`
   - `scripts/translate.py` → `src/poly-trans/translate.py`
   - `src/prompts.py` → `src/poly-trans/prompts.py`
   - `data/` → `src/poly-trans/data/`
4. Create `src/poly-trans/__init__.py` and `src/poly-trans/__version__.py`
5. Create `src/poly-trans/pyproject.toml` with dependencies
6. Test import: `from src.poly_trans.translate import ModularBatchTranslator`
7. Test local install: `pip install -e .` from repo root
8. Verify translation produces identical output to old code

### Week 2: poly-ren

1. Create directory structure: `src/poly-ren/`
2. Copy files:
   - `src/extract.py` → `src/poly-ren/extract.py`
   - `src/merge.py` → `src/poly-ren/merge.py`
   - `src/models.py` → `src/poly-ren/models.py`
   - `src/renpy_utils.py` → `src/poly-ren/renpy_utils.py`
3. Create `src/poly-ren/__init__.py`
4. Create `src/poly-ren/cli.py` (Python CLI)
5. Update imports to use `src.poly_trans`
6. Create `src/poly-ren/pyproject.toml`
7. Test imports: `from src.poly_ren.extract import RenpyExtractor`
8. Update PowerShell wrappers to call new code paths (optional)
9. Verify extract → translate → merge workflow works identically

### Week 3: poly-bench

1. Create directory structure: `src/poly-bench/`
2. Copy files:
   - `scripts/compare.py` → `src/poly-bench/compare.py`
   - `scripts/benchmark.py` → `src/poly-bench/benchmark.py`
3. Create `src/poly-bench/__init__.py`
4. Create `src/poly-bench/cli.py` (Python CLI)
5. Update imports to use `src.poly_trans`
6. Create `src/poly-bench/pyproject.toml`
7. Test imports: `from src.poly_bench.compare import compare_models`
8. Update PowerShell scripts to call new code paths (optional)
9. Verify comparison and benchmark produce same results

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

**Files to Copy (Phase 1):**

**To src/poly-trans/:**
- `scripts/translate.py:27-340` → `src/poly-trans/translate.py`
- `src/translators/aya23_translator.py` → `src/poly-trans/models/`
- `src/translators/madlad400_translator.py` → `src/poly-trans/models/`
- `src/translators/helsinkyRo_translator.py` → `src/poly-trans/models/`
- `src/translators/mbartRo_translator.py` → `src/poly-trans/models/`
- `src/translators/seamless96_translator.py` → `src/poly-trans/models/`
- `src/prompts.py` → `src/poly-trans/prompts.py`
- `data/` → `src/poly-trans/data/`

**To src/poly-ren/:**
- `src/extract.py` → `src/poly-ren/extract.py`
- `src/merge.py` → `src/poly-ren/merge.py`
- `src/models.py` → `src/poly-ren/models.py`
- `src/renpy_utils.py` → `src/poly-ren/renpy_utils.py`

**To src/poly-bench/:**
- `scripts/compare.py` → `src/poly-bench/compare.py`
- `scripts/benchmark.py` → `src/poly-bench/benchmark.py`

**Original Files:**
- Keep all original files in place during transition
- Can archive after Phase 1 validation

**Files to Create (Phase 1):**

**Root:**
- `pyproject.toml` (workspace config)

**src/poly-trans/:**
- `src/poly-trans/__init__.py`
- `src/poly-trans/__version__.py`
- `src/poly-trans/models/__init__.py`
- `src/poly-trans/pyproject.toml`

**src/poly-ren/:**
- `src/poly-ren/__init__.py`
- `src/poly-ren/cli.py` (Python CLI)
- `src/poly-ren/pyproject.toml`

**src/poly-bench/:**
- `src/poly-bench/__init__.py`
- `src/poly-bench/cli.py` (Python CLI)
- `src/poly-bench/pyproject.toml`

**Files to Create (Phase 2):**
- `src/poly-trans/context.py`
- `src/poly-trans/style.py`
- `src/poly-trans/strategies/base.py`
- `src/poly-trans/strategies/line_context.py`
- `src/poly-trans/strategies/line_summary.py`

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
enro/  (monorepo root at c:\_____\_CODE\enro)
├── src/
│   ├── poly-trans/             # Core translator package (publishable to PyPI)
│   │   ├── __init__.py
│   │   ├── __version__.py
│   │   ├── translate.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── aya23_translator.py
│   │   │   ├── madlad400_translator.py
│   │   │   ├── helsinkyRo_translator.py
│   │   │   ├── mbartRo_translator.py
│   │   │   └── seamless96_translator.py
│   │   ├── prompts.py
│   │   ├── data/               # Prompts, glossaries, benchmarks
│   │   └── pyproject.toml
│   ├── poly-ren/               # Renpy translator package
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── merge.py
│   │   ├── models.py
│   │   ├── renpy_utils.py
│   │   ├── cli.py
│   │   └── pyproject.toml
│   ├── poly-bench/             # Model comparer package
│   │   ├── __init__.py
│   │   ├── compare.py
│   │   ├── benchmark.py
│   │   ├── cli.py
│   │   └── pyproject.toml
│   ├── translators/            # Old files (keep during transition)
│   ├── extract.py              # Old files (keep during transition)
│   ├── merge.py                # Old files (keep during transition)
│   └── ...
├── scripts/                    # PowerShell wrappers (existing)
│   ├── translate.ps1
│   ├── 8-compare.ps1
│   └── 9-benchmark.ps1
├── models/                     # Model configurations
├── data/                       # Original data (keep during transition)
├── tests/                      # Integration tests
├── pyproject.toml              # Root workspace config
├── README.md
└── .git
```

---

## Notes

- **Monorepo architecture**: All three packages in one repository (enro)
- All packages use YAML exclusively (no JSON)
- Windows/CUDA primary target, but Python-based for cross-platform expandability
- **PowerShell wrappers** remain at repo root - can be updated to call new code paths
- Original files kept in place during transition for safety
- Data folder copied to `src/poly-trans/data/` (original stays at root)
- Model configs (`models_config.yaml`) stay at root
- Each package can be published separately to PyPI
- Monorepo imports: `from src.poly_trans import ...`
- PyPI imports (after publishing): `from poly_trans import ...`
