# Test Suite

| Test | Config | Extract | Translate | Correct | Merge | Pipeline |
|------|--------|---------|-----------|---------|-------|----------|
| `test_e2e_aya23.py` | ✅ | ✅ | ✅ Aya-23 | | ✅ | ✅ Mod |
| `test_e2e_madlad.py` | ✅ | ✅ | ✅ Madlad | | ✅ | ✅ Mod |
| `test_e2e_seamlessm4t.py`| ✅ | ✅ | ✅ Seamless | | ✅ | ✅ Mod |
| `test_e2e_mbart.py` | ✅ | ✅ | ✅ MBART | | ✅ | ✅ Mod |
| `test_e2e_quickmt.py` | ✅ | ✅ | ✅ QuickMT | | ✅ | ✅ Mod |
| `test_e2e_example_game.py` | ✅ | ✅ | ✅ Any | | ✅ | ⚠️ Mod (PS) |
| `test_e2e_translate_aio.py` | | | ✅ Any | | | ⚠️ AIO |
| `test_e2e_translate_aio_uncensored.py`| | | ✅ Any | | | ⚠️ AIO |
| `test_unit_extract_merge.py` | | ✅ | | | ✅ | ✅ Mod |
| `test_unit_renpy_tags.py` | | ⚠️ Unit | | | ⚠️ Unit | ✅ Mod |
| `test_unit_config.py` | ✅ | | | | | ⚠️ Mod (PS) |
| `test_unit_extract.py`| | ✅ | | | | ✅ Mod |
| `test_unit_translate_modular.py` | | | ⚠️ Mock | | | ✅ Mod |
| `test_unit_correct.py` | | | | ✅ | | ✅ Mod |
| `test_unit_merge.py` | | | | | ✅ | ✅ Mod |

---

## Running & Debugging Tests

### Run All Tests
```powershell
# Run all tests with model selection prompt
.\2-test.ps1

# Run all tests with specific model (e.g., Aya-23 = model 2)
.\2-test.ps1 -Model 2
```

### Run Individual Tests
```powershell
# Run unit tests directly (no model needed)
.\venv\Scripts\python.exe .\tests\test_unit_config.py
.\venv\Scripts\python.exe .\tests\test_unit_extract.py
.\venv\Scripts\python.exe .\tests\test_unit_merge.py
.\venv\Scripts\python.exe .\tests\test_unit_correct.py
.\venv\Scripts\python.exe .\tests\test_unit_renpy_tags.py

# Run modular translation test (requires model, uses mock)
.\venv\Scripts\python.exe .\tests\test_unit_translate_modular.py

# E2E tests (need model files downloaded)
.\venv\Scripts\python.exe .\tests\test_e2e_aya23.py
```

### Common Issues

**Import errors with triton/torch/torchao** ✅ **FIXED**:
- **Problem**: E2E tests failed with `ImportError: cannot import name 'AttrsDescriptor'` due to package incompatibility
- **Solution**: Implemented lazy loading in `src/translators/__init__.py` and protected imports in translator modules
- **Result**: Tests now fail gracefully with helpful error messages instead of crashing
- **Remaining**: Tests using transformers (MADLAD, SeamlessM4T) still require compatible package versions for actual use
- See: https://github.com/pytorch/ao/issues/2919 and `tests/FIX_SUMMARY.md`

**Unicode encoding errors** ✅ **FIXED**: All emojis removed from `.py` files (kept only in `.md`).

**Path issues** ✅ **FIXED**: Tests use `from utils import` (not `from tests.utils import`).

**YAML/JSON test data**: Parsed YAML should contain **clean text without tags** (tags are stripped during extraction). Tags are stored separately in the JSON file and restored during merge.

**All translator implementations complete**: All working models (MBART, QuickMT, MADLAD, SeamlessM4T, Aya-23) have been implemented and tested.

**LLMic removed**: The LLMic-3B model was removed due to non-functional translation. See `models/MODELS.md` for details.

  These tests will skip with a helpful message if the translator module is not available.

---

## Shared Utilities

**`test_utils.py`** - Common functions used across tests:
- `discover_characters()` - Auto-discover characters from .rpy
- `count_translations()` - Count translations in .rpy
- `backup_file()`, `restore_file()`, `cleanup_files()` - File operations
- `validate_rpy_structure()` - Validate .rpy format
- `get_rpy_files()` - Get .rpy files in directory

---
