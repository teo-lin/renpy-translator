# Test Suite

## Quick Reference

### 🚀 End-to-End Tests (Full Pipeline)

| Test | Pipeline | Model | Speed |
|------|----------|-------|-------|
| `test_e2e_aya23.py` | Config → Extract → Translate → Merge | Aya-23-8B (real) | Slow |
| `test_e2e_madlad.py` | Config → Extract → Translate → Merge | MADLAD-400 (real) | Slow |
| `test_merge.py` | Config → Extract → *Fake* → Merge | None (hardcoded) | Fast |

### ⚡ Unit Tests (Individual Components)

| Test | What It Tests | Model |
|------|---------------|-------|
| `test_translate_modular.py` | ModularBatchTranslator (context, glossary) | Mock |
| `test_extraction_merge.py` | RenpyExtractor + RenpyMerger | None |
| `test_renpy_tags.py` | Tag extraction/restoration | None |

### 🔧 Legacy Tests (Old AIO Pipeline)

| Test | What It Tests | Model |
|------|---------------|-------|
| `test_translate_aio.py` | Old all-in-one translation pipeline | Aya-23/MADLAD |
| `test_translate_aio_uncensored.py` | Old pipeline (uncensored prompts) | Aya-23/MADLAD |
| `test_example_game.py` | Runs external translation script | Configurable |

### 🛠️ Other Tests

| Test | What It Tests |
|------|---------------|
| `test_characters.py` | PowerShell `3-config.ps1` character discovery |
| `test_extract_script.py` | PowerShell `4-extract.ps1` extraction script |
| `test_utils.py` | Shared test utilities (not a test) |

---

## Running Tests

### Recommended Tests (Modular Pipeline)

```bash
# Fast - no model required
python tests/test_merge.py                    # Integration test
python tests/test_translate_modular.py        # Translation unit tests
python tests/test_extraction_merge.py         # Extract/merge unit tests

# Slow - model required
python tests/test_e2e_aya23.py                # Full e2e with Aya-23
python tests/test_e2e_madlad.py               # Full e2e with MADLAD
```

### Legacy Tests (Old Pipeline)

```bash
python tests/test_translate_aio.py --model_script scripts/aya23_translator.py
python tests/test_characters.py
```

---

## Test Categories

### ✅ **E2E Tests** - Full pipeline validation
- `test_e2e_aya23.py` - Full modular pipeline with real Aya-23 model
- `test_e2e_madlad.py` - Full modular pipeline with real MADLAD model
- `test_merge.py` - Full modular pipeline with fake translations (fast)

### 🧪 **Unit Tests** - Component isolation
- `test_translate_modular.py` - Translation module (MockTranslator)
- `test_extraction_merge.py` - Extract/merge modules
- `test_renpy_tags.py` - Tag processing

### 📦 **Legacy Tests** - Old pipeline (pre-modular)
- `test_translate_aio.py` - All-in-one translation (deprecated)
- `test_translate_aio_uncensored.py` - Uncensored variant (deprecated)
- `test_example_game.py` - External script runner

### ⚙️ **Integration Tests** - PowerShell scripts
- `test_characters.py` - Tests `3-config.ps1`
- `test_extract_script.py` - Tests `4-extract.ps1`

---

## Test Comparison Matrix

| Test | Config | Extract | Translate | Merge | Real Model | New Pipeline |
|------|--------|---------|-----------|-------|------------|--------------|
| `test_e2e_aya23.py` | ✅ | ✅ | ✅ Aya-23 | ✅ | ✅ | ✅ |
| `test_e2e_madlad.py` | ✅ | ✅ | ✅ MADLAD | ✅ | ✅ | ✅ |
| `test_merge.py` | ✅ | ✅ | ⚠️ Fake | ✅ | ❌ | ✅ |
| `test_translate_modular.py` | ❌ | ❌ | ✅ Mock | ❌ | ❌ | ✅ |
| `test_extraction_merge.py` | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| `test_translate_aio.py` | ❌ | ❌ | ✅ Real | ❌ | ✅ | ❌ Old |

---

## Shared Utilities

**`test_utils.py`** - Common functions used across tests:
- `discover_characters()` - Auto-discover characters from .rpy
- `count_translations()` - Count translations in .rpy
- `backup_file()`, `restore_file()`, `cleanup_files()` - File operations
- `validate_rpy_structure()` - Validate .rpy format
- `get_rpy_files()` - Get .rpy files in directory

---

## Quick Start

### Run Fast Tests (No Model)
```bash
python tests/test_merge.py
python tests/test_translate_modular.py
```

### Run Full E2E (Requires Model)
```bash
python tests/test_e2e_aya23.py
```

### Test Specific File
```bash
python tests/test_e2e_aya23.py --file 1
python tests/test_merge.py --file 2
```

---

## Documentation

For detailed information about E2E tests, see [`README_E2E_TESTS.md`](README_E2E_TESTS.md)
