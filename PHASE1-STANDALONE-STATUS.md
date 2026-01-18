# Phase 1: Standalone Package Status

**Date:** January 17, 2026
**Status:** ⚠️ Packages are NOT standalone

---

## Summary

The three packages (poly_trans, poly_ren, poly_bench) were created in Phase 1 as an **architectural split with NO logic changes** per the plan. They are **NOT standalone** and still depend on the shared `src/` directory structure.

This is **correct per Phase 1 requirements** but the READMEs were misleading.

---

## poly_trans Status: ❌ NOT Standalone

### Missing Dependencies

**poly_trans/translate.py imports:**
```python
from models import ParsedBlock, is_separator_block, parse_block_id
from translators.aya23_translator import Aya23Translator
from renpy_utils import show_progress
```

**What's missing in poly_trans:**
- ❌ `models.py` - Contains ParsedBlock TypedDict and helper functions (exists only in `src/models.py`)
- ❌ `renpy_utils.py` - Contains show_progress function (exists only in `src/renpy_utils.py`)
- ⚠️ Import path mismatch: imports `translators.aya23_translator` but translators are in `poly_trans/models/`

**What poly_trans HAS:**
- ✅ `translate.py` - Main translation logic
- ✅ `prompts.py` - Prompt management
- ✅ `models/` - All 5 translator implementations
- ✅ `data/` - Prompts, glossaries, benchmarks

### Why It Doesn't Work

```python
# README example (DOES NOT WORK):
from src.poly_trans.translate import ModularBatchTranslator

translator = ModularBatchTranslator(
    model_key="aya23",  # ❌ No such parameter
    target_language="Romanian"  # ❌ Wrong signature
)
```

**Actual signature:**
```python
def __init__(
    self,
    translator,      # ❌ Requires pre-initialized translator object
    characters: Dict,  # ❌ Requires characters dict
    target_lang_code: str,
    context_before: int = 3,
    context_after: int = 1
):
```

---

## poly_ren Status: ⚠️ Partially Standalone

### Dependencies

**poly_ren files import:**
```python
from models import RenpyBlock, ParsedBlock, TaggedBlock  # ❌ from src/models.py
```

**Missing:**
- ❌ `models.py` - Needs TypedDicts

**What poly_ren HAS:**
- ✅ `extract.py` - Extraction logic
- ✅ `merge.py` - Merge logic
- ✅ `renpy_utils.py` - Copied locally (has its own version!)

### Tests

- ✅ Tests work from package directory (`src/poly_ren/tests/`)
- ⚠️ Only because they import from parent `src/models.py`

---

## poly_bench Status: ❌ NOT Standalone

### Dependencies

**poly_bench/compare.py imports:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ParsedBlock, is_separator_block  # ❌ from src/models.py
from compare import BenchmarkTranslator  # ❌ from scripts/compare.py
```

**Missing:**
- ❌ `models.py`
- ❌ All translator implementations (depends on poly_trans or src/translators)

---

## Why This Happened

Per the **Phase 1 plan**:
> "Phase 1: Pure architectural split with NO logic changes"
> "First, split in 3 apps, no logic changes. After the split we add improvements..."

**This is CORRECT behavior:**
- We copied files to new locations
- We did NOT refactor imports or dependencies
- Packages share code via parent `src/` directory
- This is a **monorepo** with shared dependencies

---

## What Needs To Happen (Phase 2)

### Option A: Keep as Monorepo (Recommended)

Packages remain in monorepo, share common code via `src/`:

```
src/
  ├── models.py          # Shared TypedDicts
  ├── renpy_utils.py     # Shared utilities
  ├── poly_trans/        # Translation engine
  ├── poly_ren/          # Renpy extraction/merge
  └── poly_bench/        # Benchmarking
```

**Pros:**
- Matches current structure
- Easy development workflow
- DRY (Don't Repeat Yourself)

**Cons:**
- Can't publish poly_trans to PyPI standalone

### Option B: Make poly_trans Truly Standalone (For PyPI)

Copy dependencies into poly_trans:

```
poly_trans/
  ├── translate.py
  ├── models.py          # Copy from src/models.py (only needed types)
  ├── utils.py           # Copy show_progress from renpy_utils.py
  ├── translators/       # Rename from models/
  │   ├── aya23.py
  │   └── ...
  ├── data/
  └── prompts.py
```

Update imports:
```python
from poly_trans.models import ParsedBlock
from poly_trans.utils import show_progress
from poly_trans.translators.aya23 import Aya23Translator
```

**Pros:**
- Publishable to PyPI
- Truly standalone

**Cons:**
- Code duplication (models.py exists in 2 places)
- More maintenance burden

---

## Current Workaround

All packages work correctly when run from the **monorepo root**:

```bash
# From C:\_____\_CODE\enro/
python src/poly_trans/translate.py --game test
python src/poly_ren/extract.py
python src/poly_bench/compare.py
```

Tests in root `tests/` directory work:
```bash
pytest tests/test_unit_extract.py  # ✅ Works
pytest tests/test_unit_translate.py  # ✅ Works
pytest tests/test_unit_compare.py  # ✅ Works
```

---

## Recommendation

**For now (Phase 1 complete):**
1. Update READMEs to accurately reflect current state
2. Document that packages require monorepo structure
3. Document actual usage patterns (not standalone examples)

**For Phase 2:**
- **If goal is PyPI publishing:** Make poly_trans standalone (Option B)
- **If goal is monorepo development:** Keep shared dependencies (Option A)

User should decide which direction to take.

---

**Status:** ⚠️ Phase 1 Complete (architectural split done, but NOT standalone)
**Action Required:** Update READMEs to match reality
**Decision Needed:** Phase 2 direction (standalone vs monorepo)
