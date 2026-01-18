# VSCode Testing Setup Guide

**How to run tests from VSCode Testing UI**

---

## 1. Install Required Extension

Install the **Python extension** by Microsoft:

1. Open VSCode
2. Press `Ctrl+Shift+X` (Extensions view)
3. Search for "Python"
4. Install "Python" by Microsoft (ms-python.python)

**Extension ID:** `ms-python.python`

This extension includes built-in test discovery and running capabilities.

---

## 2. Configuration (Already Done ✅)

I've already configured everything for you:

### `.vscode/settings.json`
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": ["-v", "--tb=short"],
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.analysis.extraPaths": ["${workspaceFolder}/src"],
    "python.autoComplete.extraPaths": ["${workspaceFolder}/src"]
}
```

### `pytest.ini`
```ini
[pytest]
testpaths =
    tests
    src/poly_trans/tests
    src/poly_ren/tests
    src/poly_bench/tests

pythonpath = . src
```

---

## 3. Open Testing View

**Method 1 - Sidebar:**
1. Click the **Testing** icon in the left sidebar (flask/beaker icon)

**Method 2 - Command Palette:**
1. Press `Ctrl+Shift+P`
2. Type "Test: Focus on Test Explorer View"
3. Press Enter

**Method 3 - Keyboard:**
- Press `Ctrl+Shift+U` then `T`

---

## 4. Discover Tests

VSCode should automatically discover tests, but if not:

1. In the Testing view, click the **Refresh** button (circular arrow icon)
2. Or press `Ctrl+Shift+P` → "Test: Refresh Tests"

You should see a tree structure like:
```
└─ enro
   ├─ tests/
   │  ├─ test_unit_translate.py
   │  ├─ test_unit_extract.py
   │  ├─ test_unit_merge.py
   │  ├─ test_int_aya23.py
   │  └─ ...
   ├─ src/poly_trans/tests/
   │  ├─ test_unit_translate.py
   │  ├─ test_int_aya23.py
   │  └─ ...
   ├─ src/poly_ren/tests/
   │  └─ ...
   └─ src/poly_bench/tests/
      └─ ...
```

---

## 5. Run Tests

### Run All Tests
- Click the **Run All** button (▶▶ icon) at the top of Testing view

### Run Single Test File
- Hover over a test file → click the **▶ Run Test** button

### Run Single Test Function
- Expand a test file
- Hover over a test function → click **▶ Run Test**

### Run Tests with Right-Click
- Right-click any test/file/folder → "Run Test"

### Run Tests from Editor
- Open a test file
- Click the ▶ icon in the gutter next to any test function
- Or right-click → "Run Test"

---

## 6. View Test Results

**In Testing View:**
- ✅ Green checkmark = Passed
- ❌ Red X = Failed
- ⊘ Gray circle = Not run
- Click any test to see output

**In Editor:**
- Inline decorations show pass/fail next to test functions
- Click the decoration to see details

**Output Panel:**
- Bottom panel shows detailed test output
- Select "Python Test Log" from dropdown

---

## 7. Debug Tests

### Debug Single Test
1. Right-click a test → "Debug Test"
2. Or click the **🐛 Debug** icon next to a test

### Set Breakpoints
1. Open test file
2. Click in the gutter (left of line numbers) to set breakpoint
3. Run "Debug Test"
4. Debugger will pause at breakpoint

---

## 8. Filter Tests

**In Testing View toolbar:**
- Click the **filter** icon (funnel)
- Choose:
  - Show Only Failed Tests
  - Show Only Passed Tests
  - Show All Tests

**By Pattern:**
- Click the **...** menu → "Run Tests Matching Pattern"
- Enter pattern like `test_unit_*` or `test_int_*`

---

## 9. Test Organization

### Your Test Structure

```
C:\_____\_CODE\enro/
├─ tests/                      # Root tests (backward compatibility)
│  ├─ test_unit_translate.py   # Translation logic (uses old imports)
│  ├─ test_unit_extract.py     # Extraction logic
│  ├─ test_unit_merge.py       # Merge logic
│  ├─ test_unit_compare.py     # Comparison logic
│  ├─ test_int_aya23.py        # Aya23 model (uses old imports)
│  └─ ...
│
├─ src/poly_trans/tests/       # poly_trans standalone tests
│  ├─ test_unit_translate.py   # Translation logic (uses poly_trans.*)
│  ├─ test_int_aya23.py        # Aya23 model (uses poly_trans.*)
│  ├─ test_int_helsinkyRo.py   # Helsinki model
│  ├─ test_int_madlad400.py    # MADLAD model
│  ├─ test_int_mbartRo.py      # mBART model
│  └─ test_int_seamless96.py   # Seamless model
│
├─ src/poly_ren/tests/         # poly_ren tests
│  ├─ test_unit_extract.py
│  ├─ test_unit_merge.py
│  └─ test_unit_renpy_tags.py
│
└─ src/poly_bench/tests/       # poly_bench tests
   ├─ test_unit_compare.py
   ├─ test_e2e_compare.py
   └─ test_e2e_benchmark.py
```

### Test Types

**Unit Tests (Fast - Mocked):**
- `test_unit_*.py` - Use mock translators
- Run in < 1 second
- Test logic only

**Integration Tests (Slow - Real Models):**
- `test_int_*.py` - Load real 3-8GB AI models
- Run in 10-30 seconds each
- Test actual model inference

**E2E Tests:**
- `test_e2e_*.py` - End-to-end workflows
- Variable runtime

---

## 10. Running Specific Test Types

### Run Only Unit Tests (Fast)
1. In Testing view, expand to see test files
2. Run only `test_unit_*.py` files
3. Or use pattern filter: `test_unit_*`

### Run Only Integration Tests (Slow)
1. Expand to see test files
2. Run only `test_int_*.py` files
3. Or use pattern filter: `test_int_*`

### Run Tests for Specific Package
- Click the folder icon (e.g., `src/poly_trans/tests/`)
- Click "Run Test" to run all tests in that package

---

## 11. Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Test Explorer | `Ctrl+Shift+U` then `T` |
| Run All Tests | No default (set custom) |
| Run Test at Cursor | No default (set custom) |
| Debug Test at Cursor | No default (set custom) |
| Show Test Output | `Ctrl+Shift+U` |

**To Set Custom Shortcuts:**
1. `Ctrl+K Ctrl+S` (Keyboard Shortcuts)
2. Search for "Test: Run All Tests"
3. Click the + icon to set a keybinding

---

## 12. Troubleshooting

### Tests Not Discovered

**Solution 1: Refresh Tests**
- Click refresh button in Testing view
- Or `Ctrl+Shift+P` → "Test: Refresh Tests"

**Solution 2: Check Python Interpreter**
- Bottom-left corner should show: `Python 3.12.7 ('venv': venv)`
- If not, click it and select: `.\venv\Scripts\python.exe`

**Solution 3: Check pytest is Installed**
```bash
.\venv\Scripts\python -m pip list | findstr pytest
```

**Solution 4: Reload Window**
- `Ctrl+Shift+P` → "Developer: Reload Window"

### Import Errors in Tests

**The tests use `sys.path.insert(0, str(Path(__file__).parent.parent.parent))` to add src to path. This works because pytest.ini has:**
```ini
pythonpath = . src
```

**If imports still fail:**
1. Check `.vscode/settings.json` has:
   ```json
   "python.analysis.extraPaths": ["${workspaceFolder}/src"]
   ```
2. Reload window

### Tests Run But Fail

**Check Test Output:**
1. Click on failed test in Testing view
2. Read error message in output panel
3. Look for import errors, missing models, etc.

**Integration Tests Require Models:**
- `test_int_aya23.py` needs `models/aya23/aya-23-8B-Q4_K_M.gguf`
- `test_int_helsinkyRo.py` needs Helsinki model in Hugging Face cache
- etc.

---

## 13. Tips

### Hide Test Output Panel
- Click the **X** in output panel when not needed
- It auto-shows when running tests

### Continuous Testing (Auto-Run on Save)
Already enabled via:
```json
"python.testing.autoTestDiscoverOnSaveEnabled": true
```

Tests are discovered automatically when you save test files.

### Test Status in Status Bar
- Bottom status bar shows test summary (e.g., "12 passed, 1 failed")
- Click it to open Testing view

### Run from Terminal (Alternative)
```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_unit_translate.py

# Run with pattern
pytest -k "test_unit"

# Run from package directory
pytest src/poly_trans/tests/
```

---

## Quick Start Checklist

- [x] Install Python extension
- [x] Configuration added to `.vscode/settings.json`
- [x] Configuration added to `pytest.ini`
- [ ] Open Testing view (`Ctrl+Shift+U` then `T`)
- [ ] Click "Refresh Tests" button
- [ ] See test tree structure
- [ ] Click "Run All Tests" or run individual tests
- [ ] View results in Testing view

---

**That's it!** You should now be able to run all tests from the VSCode UI.

**Recommended Workflow:**
1. Open Testing view
2. Run unit tests first (fast)
3. If unit tests pass, run integration tests (slow)
4. Fix failures by clicking on failed test and reading output
5. Re-run failed tests after fixing

**For poly_trans standalone verification:**
- Run tests in `src/poly_trans/tests/`
- These now use proper `poly_trans.*` imports
- Integration tests actually load real models
