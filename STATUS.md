# Enro - Ren'Py Translation System

**Last Updated:** 2026-01-03

---

## Current State

**Status:** ✅ Production Ready - 5/6 models working

**Models:**
- ✅ Aya-23-8B (llama.cpp) - 5.8GB VRAM
- ✅ MADLAD-400-3B (T5) - 4GB VRAM
- ✅ SeamlessM4T-v2 (Multimodal) - 5GB+ VRAM
- ✅ MBART-En-Ro (BART) - 2GB VRAM
- ✅ Helsinki-RO (OPUS-MT) - 1GB VRAM
- ❌ QuickMT-En-Ro - Not implemented

**Pipeline:**
```
1-config.ps1   → Discover games & characters
2-extract.ps1  → .rpy → .parsed.yaml + .tags.json
3-translate.ps1→ Translate .parsed.yaml
4-correct.ps1  → Grammar/pattern corrections
5-merge.ps1    → .parsed.yaml + .tags.json → .translated.rpy
```

---

## Dependency Map

### File Classification

**Pure Translation Logic (Generic):**
- `src/prompts.py` - Template management ✅
- `src/batch_translator.py` - Batch processing ✅
- `src/translators/*.py` - All 5 translator backends ✅
- `src/models.py` - Type definitions ⚠️ **MIXED - needs splitting**
- `src/core.py` - LEGACY ❌ **Delete in Phase 2**

**Ren'Py-Specific Logic:**
- `src/extract.py` - .rpy → YAML/JSON extraction
- `src/merger.py` - YAML/JSON → .rpy merging
- `src/renpy_utils.py` - Tag extraction, parsing ⚠️ **MIXED - needs splitting**
- `src/translation_pipeline.py` - Ren'Py translation pipeline ❌ **Optional, can delete**

**Scripts (Entry Points):**
- `scripts/translate.py` - Main translation orchestrator
- `scripts/correct.py` - Correction script (uses legacy core.py)
- `scripts/benchmark*.py` - Quality benchmarking (uses legacy core.py)

### Import Dependencies

```
Base Layer (no internal deps):
├── prompts.py ✅ Pure
├── models.py ⚠️ Mixed (generic + Ren'Py types)
└── renpy_utils.py ⚠️ Mixed (progress display + Ren'Py parsing)

Mid Layer (depends on base):
├── batch_translator.py → models ✅ Pure
├── extract.py → models, renpy_utils (Ren'Py)
├── merger.py → models, renpy_utils (Ren'Py)
├── translation_pipeline.py → renpy_utils ❌ Deletable
└── core.py (LEGACY) → prompts ❌ Delete

Translators (depends on base): ✅ All Pure
├── aya23_translator.py → prompts
├── helsinkyRo_translator.py
├── mbartRo_translator.py
├── madlad400_translator.py
└── seamless96_translator.py

Scripts (terminal nodes):
├── translate.py → models, aya23_translator, renpy_utils
├── correct.py → core (LEGACY) ⚠️ Blocks deletion
└── benchmark*.py → models, translators, renpy_utils ⚠️ Blocks deletion
```

---

## 🚨 Critical Findings from Dependency Analysis

### 1. **renpy_utils.py Contains Mixed Concerns**
**Problem:** Used by 7 files, contains BOTH generic and Ren'Py-specific code:
- **Generic:** `show_progress()` - UI utility (used by scripts)
- **Ren'Py-specific:** `RenpyTagExtractor`, parsing logic, regex patterns

**Impact:** Cannot move to `local-translator` as-is without importing Ren'Py logic.

**Solution:**
```python
# src/utils/ui.py (→ local-translator)
def show_progress(current, total, desc): ...

# src/renpy_utils.py (→ renpy-translator)
class RenpyTagExtractor: ...
# All Ren'Py parsing logic stays here
```

**Files affected:** 7 files import `renpy_utils`
- `translation_pipeline.py` (deletable)
- `extract.py`, `merger.py` (use tag extraction)
- `scripts/translate.py`, `scripts/benchmark*.py` (use show_progress)

---

### 2. **models.py Contains Mixed Types**
**Problem:** Contains BOTH generic and Ren'Py-specific type definitions:

**Generic types:**
- `BlockType` enum (dialogue, narrator, choice, etc.)
- `ParsedBlock` concept (block with text + metadata)

**Ren'Py-specific types:**
- `RenpyBlock` - Raw .rpy block structure
- `TaggedBlock` - Ren'Py tag metadata
- `TagsFileContent` - .tags.json structure

**Impact:** Cannot move to `local-translator` with Ren'Py types included.

**Solution:**
```python
# local_translator/models.py (generic)
@dataclass
class TranslationBlock:
    id: str
    text: str
    block_type: str  # 'dialogue', 'narrator', etc.
    metadata: Dict[str, Any]
    speaker: Optional[str] = None

# renpy_translator/models.py (Ren'Py-specific)
from local_translator.models import TranslationBlock

@dataclass
class RenpyBlock(TranslationBlock):
    tags: List[Tag]
    original_template: str
    character_var: str
```

**Files affected:** 5 files import `models`
- `batch_translator.py` (generic)
- `extract.py`, `merger.py` (Ren'Py-specific)
- `scripts/translate.py`, `scripts/benchmark*.py`

---

### 3. **translation_pipeline.py is Optional/Deletable**
**Finding:** Only used in `__main__` blocks of translators for standalone testing.

**NOT used by:**
- Main workflow (`scripts/translate.py`)
- Extract/merge pipeline
- Any production code

**Recommendation:** DELETE in Phase 2, replace with proper unit tests.

---

### 4. **core.py Blocks Phase 2 Cleanup**
**Finding:** Legacy Aya23Translator still used by:
- `scripts/correct.py` (line 213)
- `scripts/benchmark.py` (line 46)

**Blocker:** Must migrate these scripts BEFORE deleting `core.py`.

**Solution:** Update scripts to use `translators/aya23_translator.py` instead.

---

### 5. **No Circular Dependencies** ✅
**Good news:** Clean hierarchical structure:
- Base → Mid → Scripts
- No file imports create cycles
- Safe to refactor

---

## Decoupling Plan - Two Repos

### Goal
Split into two packages:
1. **local-translator** - Generic translation engine (reusable)
2. **renpy-translator** - Ren'Py adapter (uses local-translator)

---

### Phase 1: In-Place Splits (Week 1) 🎯

**Goal:** Prepare files for clean extraction by splitting mixed concerns.

#### Week 1A: Config Split (2 days)

**Current Problem:**
```json
// games/current_config.json - WRONG! Mixed concerns
{
  "game_path": "...",           // Game-specific
  "target_language": "ro",      // Translation-specific
  "selected_model": "aya23"     // Model-specific
}
```

**Solution:**
```yaml
# games/<game_name>/config.yaml (game-specific)
game_name: "the_question"
game_path: "C:\\_____\\_CODE\\enro\\games\\the_question"
source_language: "en"
target_language: "ro"
characters:
  e: "Eileen"

# config/translation.yaml (translation settings)
selected_model: "aya23"
target_language: "ro"
glossary: "data/glossaries/ro.yaml"
corrections: "data/corrections/ro.yaml"

# config/models.yaml (model metadata)
models:
  aya23:
    name: "Aya-23-8B"
    path: "models/aya-23-8B-Q4_K_M.gguf"
    memory: "5.8GB"
    backend: "llama-cpp"
```

**Tasks:**
- [ ] Create `config/` directory
- [ ] Create `config/translation.yaml`
- [ ] Create `config/models.yaml`
- [ ] Create `games/<game>/config.yaml` for each game
- [ ] Convert all JSON → YAML
- [ ] Update loader functions in scripts
- [ ] Test full pipeline
- [ ] Keep backward compatibility wrapper (read old JSON if new YAML missing)

---

#### Week 1B: renpy_utils.py Split (2 days)

**Problem:** Mixed generic UI and Ren'Py-specific logic.

**Solution:**
```python
# src/utils/__init__.py (NEW)
# Empty

# src/utils/ui.py (NEW - generic, → local-translator)
def show_progress(current: int, total: int, desc: str = "", width: int = 50) -> None:
    """Display progress bar (generic, no Ren'Py deps)"""
    ...

# src/renpy_utils.py (KEEP - Ren'Py-specific, → renpy-translator)
class RenpyTagExtractor:
    """Extract/restore Ren'Py tags"""
    ...

class RenpyTranslationParser:
    """Parse .rpy translation files"""
    ...

# All regex patterns, Ren'Py-specific logic stays here
```

**Tasks:**
- [ ] Create `src/utils/` directory
- [ ] Create `src/utils/ui.py`
- [ ] Move `show_progress()` from `renpy_utils.py` → `utils/ui.py`
- [ ] Update imports in all files:
  - `from src.renpy_utils import show_progress` → `from src.utils.ui import show_progress`
  - Keep `from src.renpy_utils import RenpyTagExtractor` as-is
- [ ] Test all scripts (translate.py, benchmark*.py)
- [ ] Verify extract.py, merger.py still work

**Files to update:**
- `scripts/translate.py` (line 25)
- `scripts/benchmark_translate.py` (line 29)
- Any other scripts using `show_progress()`

---

#### Week 1C: models.py Split (1 day)

**Problem:** Mixed generic and Ren'Py-specific types.

**Solution:**
```python
# src/models_generic.py (NEW - generic, → local-translator)
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

class BlockType(Enum):
    DIALOGUE = "dialogue"
    NARRATOR = "narrator"
    CHOICE = "choice"
    STRING = "string"

@dataclass
class TranslationBlock:
    """Generic translation block (engine-agnostic)"""
    id: str
    text: str
    block_type: BlockType
    metadata: Dict[str, Any]
    speaker: Optional[str] = None

# src/models.py (KEEP - Ren'Py-specific, → renpy-translator)
from src.models_generic import TranslationBlock, BlockType
from typing import TypedDict, List, Dict, Any

class RenpyBlock(TypedDict):
    """Ren'Py-specific block with tags"""
    type: str
    character_var: str
    text: str
    original_line: str

class TaggedBlock(TypedDict):
    """Block with tag metadata for .tags.json"""
    id: str
    type: str
    original_text: str
    tags: List[Dict[str, Any]]
    template: str
```

**Tasks:**
- [ ] Create `src/models_generic.py`
- [ ] Move generic types to `models_generic.py`
- [ ] Update `src/models.py` to import from `models_generic.py`
- [ ] Update imports in files:
  - `batch_translator.py` → import from `models_generic`
  - `extract.py`, `merger.py` → keep importing from `models`
- [ ] Test extract/merge/translate pipeline

**Files to update:**
- `src/batch_translator.py` (line 16-19)
- `scripts/translate.py` (line 23)
- `scripts/benchmark_translate.py` (line 23)

---

### Phase 2: Cleanup & Legacy Removal (Week 2)

**Goal:** Remove legacy code, prepare for extraction.

**Tasks:**
- [ ] Migrate `scripts/correct.py` from `core.py` to `translators/aya23_translator.py`
- [ ] Migrate `scripts/benchmark.py` from `core.py` to `translators/aya23_translator.py`
- [ ] Delete `src/core.py` (no longer used)
- [ ] Delete `src/translation_pipeline.py` (optional, not used by main workflow)
- [ ] Convert remaining JSON files to YAML:
  - `data/ro_glossary.json` → `data/glossaries/ro.yaml`
  - `data/ro_corrections.json` → `data/corrections/ro.yaml`
  - `data/en_corrections.json` → `data/corrections/en.yaml`
- [ ] Update all scripts to load YAML instead of JSON
- [ ] Test full pipeline (config → extract → translate → correct → merge)

---

### Phase 3: Extract local-translator Package (Week 3)

**Goal:** Create standalone `local-translator` package.

**Create package structure:**
```
local-translator/
├── pyproject.toml
├── README.md
├── LICENSE
├── local_translator/
│   ├── __init__.py
│   ├── translators/
│   │   ├── __init__.py
│   │   ├── base.py              # Interface/protocol
│   │   ├── aya23.py             # From src/translators/aya23_translator.py
│   │   ├── madlad400.py
│   │   ├── mbart.py
│   │   ├── helsinki.py
│   │   └── seamless.py
│   ├── models.py                # From src/models_generic.py
│   ├── prompts.py               # From src/prompts.py
│   ├── batch_translator.py      # From src/batch_translator.py
│   └── utils/
│       ├── __init__.py
│       └── ui.py                # From src/utils/ui.py
├── config/
│   └── models.yaml              # From config/models.yaml
├── data/
│   ├── prompts/
│   │   ├── translate.txt
│   │   └── correct.txt
│   ├── glossaries/
│   │   ├── ro.yaml
│   │   ├── es.yaml
│   │   └── fr.yaml
│   └── corrections/
│       ├── ro.yaml
│       └── es.yaml
└── tests/
    ├── test_translators/
    │   ├── test_aya23.py
    │   ├── test_madlad400.py
    │   └── ...
    └── test_batch_translator.py
```

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "local-translator"
version = "1.0.0"
description = "Local AI-powered game translation engine"
authors = [{name = "Your Name", email = "you@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "pyyaml>=6.0",
    "llama-cpp-python>=0.2.0",
    "torch>=2.0.0",
    "transformers>=4.30.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black", "mypy"]
```

**Tasks:**
- [ ] Create new repo: `local-translator`
- [ ] Copy files from enro (see structure above)
- [ ] Rename imports: `src.translators.aya23_translator` → `local_translator.translators.aya23`
- [ ] Remove all Ren'Py dependencies
- [ ] Create `pyproject.toml`
- [ ] Create README.md with usage examples
- [ ] Test package installation: `pip install -e .`
- [ ] Run all tests in isolation
- [ ] Verify no Ren'Py imports remain

---

### Phase 4: Refactor renpy-translator (Week 4)

**Goal:** Use `local-translator` as dependency.

**Structure:**
```
renpy-translator/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── renpy_translator/
│   ├── __init__.py
│   ├── extract.py             # From src/extract.py
│   ├── merge.py               # From src/merger.py
│   ├── renpy_utils.py         # From src/renpy_utils.py (cleaned)
│   ├── models.py              # From src/models.py (Ren'Py-specific)
│   └── validator.py           # NEW - validation logic
├── scripts/
│   ├── config.py
│   ├── extract.py
│   ├── translate.py           # Uses local_translator
│   ├── correct.py
│   └── merge.py
├── launchers/                  # PowerShell UI
│   ├── 0-setup.ps1
│   ├── 1-config.ps1
│   ├── 2-extract.ps1
│   ├── 3-translate.ps1
│   ├── 4-correct.ps1
│   ├── 5-merge.ps1
│   └── 8-test.ps1
├── renpy_sdk/                  # Ren'Py SDK
├── config/
│   └── renpy.yaml             # Ren'Py-specific settings
├── games/                      # User games (gitignored)
└── tests/
    ├── test_extract.py
    ├── test_merge.py
    └── test_e2e/
```

**requirements.txt:**
```
local-translator>=1.0.0
pyyaml>=6.0
```

**requirements-dev.txt:**
```
-e ../local-translator  # Use local version for development
pyyaml>=6.0
pytest>=7.0
```

**Tasks:**
- [ ] Add `local-translator` to requirements.txt
- [ ] Install: `pip install -r requirements.txt`
- [ ] Update imports:
  - `from src.translators.aya23_translator import Aya23Translator` → `from local_translator.translators.aya23 import Aya23Translator`
  - `from src.utils.ui import show_progress` → `from local_translator.utils.ui import show_progress`
  - `from src.models_generic import TranslationBlock` → `from local_translator.models import TranslationBlock`
- [ ] Remove duplicated files (translators, prompts.py, batch_translator.py, utils/ui.py)
- [ ] Keep Ren'Py-specific files (extract.py, merge.py, renpy_utils.py, models.py)
- [ ] Test full pipeline end-to-end
- [ ] Update PowerShell launchers if needed

---

## What Goes Where?

### ✅ local-translator (Generic Translation Engine)

**From current enro:**
- `src/translators/*.py` → `local_translator/translators/`
- `src/prompts.py` → `local_translator/prompts.py`
- `src/batch_translator.py` → `local_translator/batch_translator.py`
- `src/models_generic.py` → `local_translator/models.py` (renamed)
- `src/utils/ui.py` → `local_translator/utils/ui.py`
- `data/prompts/` → `local_translator/data/prompts/`
- `data/glossaries/` → `local_translator/data/glossaries/`
- `data/corrections/` → `local_translator/data/corrections/`
- `config/models.yaml` → `local_translator/config/models.yaml`

**NOT included:**
- ❌ Ren'Py-specific logic
- ❌ Extract/merge code
- ❌ Tag handling
- ❌ .rpy parsing

---

### ✅ renpy-translator (Ren'Py Adapter)

**Keep from current enro:**
- `src/extract.py` → `renpy_translator/extract.py`
- `src/merger.py` → `renpy_translator/merge.py`
- `src/renpy_utils.py` → `renpy_translator/renpy_utils.py`
- `src/models.py` → `renpy_translator/models.py`
- `scripts/*.py` → `renpy_translator/scripts/`
- `*.ps1` → `renpy_translator/launchers/`
- `renpy/` → `renpy_translator/renpy_sdk/`
- `tests/test_*extract*.py`, `test_*merge*.py` → `renpy_translator/tests/`
- `config/translation.yaml` → User config
- `games/` → User games

**Depends on:**
- ✅ `local-translator` (via pip install)

---

## Publishing to PyPI

### Steps

```bash
# 1. Create free account at https://pypi.org/account/register/
# (No verification, instant approval)

# 2. Install tools
pip install build twine

# 3. Build package (in local-translator/)
python -m build
# Creates: dist/local_translator-1.0.0.tar.gz and .whl

# 4. Upload to PyPI
twine upload dist/*
# Enter PyPI username/password

# Done! Now anyone can: pip install local-translator
```

**Alternative (No PyPI):** Use local install
```bash
# In renpy-translator/requirements.txt
-e ../local-translator  # Development mode
```

---

## Distribution Strategy

### Option A: Developer Install
```bash
git clone https://github.com/user/renpy-translator.git
cd renpy-translator
pip install -r requirements.txt  # Gets local-translator from PyPI
```

### Option B: End User (Bundled Release)
```
Download: renpy-translator-v1.0.zip
Contents:
  ├── renpy_translator/
  ├── venv/ (pre-installed with local-translator)
  └── launchers/*.ps1

Usage: Unzip and run .\launchers\0-setup.ps1
```

**Recommendation:** Provide both. Developers use A, end users use B.

---

## Migration Checklist

### Week 1A: Config Split
- [ ] Create `config/` directory
- [ ] Create `config/translation.yaml`
- [ ] Create `config/models.yaml`
- [ ] Create `games/<game>/config.yaml` for each game
- [ ] Convert JSON → YAML
- [ ] Update loader functions
- [ ] Test full pipeline

### Week 1B: renpy_utils.py Split
- [ ] Create `src/utils/ui.py`
- [ ] Move `show_progress()` from renpy_utils
- [ ] Update imports in 7 files
- [ ] Test all scripts

### Week 1C: models.py Split
- [ ] Create `src/models_generic.py`
- [ ] Move generic types
- [ ] Update imports in 5 files
- [ ] Test pipeline

### Week 2: Cleanup
- [ ] Migrate correct.py from core.py
- [ ] Migrate benchmark.py from core.py
- [ ] Delete core.py
- [ ] Delete translation_pipeline.py
- [ ] Convert remaining JSON → YAML
- [ ] Test full pipeline

### Week 3: Extract local-translator
- [ ] Create local-translator repo
- [ ] Copy files (see Phase 3)
- [ ] Create pyproject.toml
- [ ] Test: `pip install -e .`
- [ ] Run tests in isolation

### Week 4: Integrate
- [ ] Add local-translator to requirements
- [ ] Update imports in renpy-translator
- [ ] Remove duplicated files
- [ ] Test end-to-end
- [ ] Create bundled release

### Week 5: Polish
- [ ] Documentation for both repos
- [ ] Publish to PyPI (optional)
- [ ] Create release bundles
- [ ] Update README files

---

## Key Decisions

### 1. File Formats
**Decision: Full YAML**
- All configs: YAML
- All glossaries/corrections: YAML
- Extracted translations: YAML (already done)
- Exception: External JSON from APIs (convert internally)

### 2. Package Distribution
**Decision: PyPI + Bundled Releases**
- Publish `local-translator` to PyPI (free, no approval)
- Distribute `renpy-translator`:
  - Source on GitHub (developers)
  - Bundled ZIP with venv (end users)

### 3. Dependency Management
**Decision: pip with requirements.txt**
```
# requirements.txt (PyPI)
local-translator>=1.0.0

# requirements-dev.txt (local dev)
-e ../local-translator
```

---

## Benefits

**For local-translator:**
- ✅ Reusable in Unity, Godot, web apps
- ✅ No game engine dependencies
- ✅ Easy to test in isolation
- ✅ Can be published to PyPI

**For renpy-translator:**
- ✅ Focused on Ren'Py logic only
- ✅ Smaller, cleaner codebase
- ✅ Easy to maintain
- ✅ Clear separation of concerns

**For users:**
- ✅ "Just works" (auto-installs dependencies)
- ✅ Can use local-translator for other projects
- ✅ Updates to models don't require renpy-translator changes
