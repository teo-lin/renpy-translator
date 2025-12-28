# Test Suite

| Test | Config | Extract | Translate | Merge | Pipeline |
|------|--------|---------|-----------|-------|----------|
| `test_e2e_aya23.py` | ✅ | ✅ | ✅ Aya-23 | ✅ | ✅ New |
| `test_e2e_madlad.py` | ✅ | ✅ | ✅ Madlad | ✅ | ✅ New |
| `test_e2e_orion14b.py` | ✅ | ✅ | ✅ Orion14B | ✅ | ✅ New |
| `test_e2e_seamlessm4t.py`| ✅ | ✅ | ✅ Seamless | ✅ | ✅ New |
| `test_e2e_example_game.py` | ✅ | ✅ | ✅ Real | ✅ | ✅ (PS) |
| `test_e2e_translate_aio.py` | | | ✅ Real | | ❌ Old |
| `test_e2e_translate_aio_uncensored.py`| | | ✅ Real | | ❌ Old |
| `test_u_config.py` | ✅ | | | | ✅ (PS) |
| `test_u_extract.py`| | ✅ | | | ✅ New |
| `test_u_translate_modular.py` | | | ⚠️ Mock | | ✅ New |
| `test_u_merge.py` | | | | ✅ | ✅ New |
| `test_u_renpy_tags.py` | | ✅ | | ✅ | ✅ New |

---

## Shared Utilities

**`test_utils.py`** - Common functions used across tests:
- `discover_characters()` - Auto-discover characters from .rpy
- `count_translations()` - Count translations in .rpy
- `backup_file()`, `restore_file()`, `cleanup_files()` - File operations
- `validate_rpy_structure()` - Validate .rpy format
- `get_rpy_files()` - Get .rpy files in directory

---
