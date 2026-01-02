

## Troubleshooting

### Line Ending and Encoding Issues (CRLF/LF)

**Affected File Types:**

Different file types require different line endings:

| File Type | Required | Why | Impact if Wrong |
|-----------|----------|-----|-----------------|
| `.ps1` (PowerShell) | **CRLF** | Windows PowerShell parser requirement | Parse errors, "unexpected token" |
| `.bat`, `.cmd` (Batch) | **CRLF** | Windows command interpreter | Script failure, commands not recognized |
| `.sh` (Shell) | **LF** | Unix/Linux shell requirement | Script fails with `\r: command not found` |
| `.py` (Python) | **LF** (preferred) | Cross-platform standard | Usually works but non-standard |
| `.rpy` (Ren'Py) | **LF** | Cross-platform game engine | May cause parsing issues |

**Symptoms:**
- **PowerShell (.ps1)**: "unexpected token" or "missing terminator" errors
- **Shell scripts (.sh)**: `/bin/bash^M: bad interpreter` or `\r: command not found`
- **Batch files (.bat)**: Commands not recognized or script stops unexpectedly
- Scripts worked before but fail after git operations
- Error mentions valid code as having syntax errors

**Cause:**
Mixed line endings (LF vs CRLF) or UTF-8 encoding issues. This can happen when:
- Git converts line endings inconsistently
- Files have UTF-8 emojis/special characters without a BOM (PowerShell only)
- `.gitattributes` settings conflict with actual file content
- Files edited on different operating systems (Windows vs Linux/Mac)

**Solution:**

1. **Check current line endings:**
```powershell
# View git's line ending configuration
git config core.autocrlf
git ls-files --eol 1-config.ps1

# Check actual file encoding
file 1-config.ps1
```

2. **Fix line endings for all PowerShell scripts:**
```powershell
# Option 1: Using Python (recommended)
python -c "
import glob
for file in glob.glob('*.ps1') + glob.glob('scripts/*.ps1'):
    with open(file, 'rb') as f:
        content = f.read()
    # Remove non-ASCII characters (emojis, special chars)
    text = content.decode('utf-8', errors='ignore')
    text_ascii = ''.join(c if ord(c) < 128 else '' for c in text)
    # Normalize to CRLF
    text_ascii = text_ascii.replace('\r\n', '\n').replace('\n', '\r\n')
    with open(file, 'wb') as f:
        f.write(text_ascii.encode('ascii'))
print('Fixed all .ps1 files')
"

# Option 2: Renormalize git index
git add --renormalize *.ps1 scripts/*.ps1
git status  # Check what changed
```

3. **Prevent future issues:**
```powershell
# Ensure .gitattributes is configured (already set in this repo)
cat .gitattributes
# Should show: *.ps1 text eol=crlf

# Normalize all tracked files
git add --renormalize .
git status

# Commit the normalized files
git commit -m "Normalize line endings"
```

4. **Avoid non-ASCII characters in PowerShell:**
- Don't use emojis in PowerShell scripts (use `[OK]` instead of `✅`)
- Don't use Unicode box-drawing characters
- If you must use Unicode, add UTF-8 BOM to the file

**Prevention - Pre-Commit Hook:**

This repository includes a pre-commit hook at `.git/hooks/pre-commit` that automatically validates line endings for all file types.

**Installation:**
```bash
# The hook is already installed if you cloned this repo
# To manually install/update:
chmod +x .git/hooks/pre-commit
```

**What it checks:**
- - **PowerShell (.ps1)**: Blocks non-ASCII characters, warns about LF
- - **Batch files (.bat, .cmd)**: Warns about LF line endings
- - **Shell scripts (.sh)**: **Blocks CRLF** (will break on Unix/Linux)
- ⚠️ **Python (.py)**: Warns about CRLF (LF is standard)
- 💡 Suggests fixes with helpful error messages

**Testing the hook:**
```bash
# This will be blocked:
echo 'Write-Host "✅ Success"' > test.ps1
git add test.ps1
git commit -m "test"
# Output: ERROR: test.ps1 contains non-ASCII characters

# This will succeed:
echo 'Write-Host "[OK] Success"' > test.ps1
git add test.ps1
git commit -m "test"
```

**Git Configuration:**
This repository uses `.gitattributes` to enforce correct line endings:

```gitattributes
# Windows-specific files (CRLF required)
*.ps1 text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf

# Unix/Linux files (LF required)
*.sh text eol=lf

# Cross-platform files (LF standard)
*.py text eol=lf
*.rpy text eol=lf
*.md text
*.json text
```

Plus `core.autocrlf=true` for automatic conversion on Windows.

**One-Time Setup After Cloning:**
```bash
# Normalize all files to prevent issues
git add --renormalize .
git commit -m "Normalize line endings"
```

### CUDA DLL Not Found

**Root Cause:** CPU-only torch installed instead of CUDA-enabled torch. The `llama.dll` from llama-cpp-python requires CUDA runtime DLLs (cublas, cudart, etc.) that only come with CUDA-enabled torch.

**Fix:** The setup script now automatically detects CPU-only torch and reinstalls with CUDA support. Simply re-run:

```powershell
.\setup.ps1
```

**Manual Fix (if needed):**
```powershell
# Uninstall CPU-only torch
venv\Scripts\python.exe -m pip uninstall -y torch torchvision

# Install CUDA-enabled torch
venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### Out of Memory

If you run out of VRAM, reduce GPU layers:

```python
# In src\core.py, change:
translator = Aya23Translator(model_path, n_gpu_layers=30)  # Instead of -1
```

### Poor Translation Quality

1. Check if language is well-supported by Aya-23-8B
2. Add domain-specific terms to your glossary
3. Use grammar correction with `--llm-only` for better results
4. Run benchmarks to measure quality against reference translations
5. Consider fine-tuning the model with your training data




## Troubleshooting

### "Configuration file not found"
**Solution:** Run `.\1-config.ps1` first to set up the game.

### "No .parsed.yaml files found"
**Solution:** Run `.\4-2-extract.ps1 -All` first.

### "Validation errors found"
**Solution:** Review the error report. Common issues:
- Missing quotes in translation
- Unmatched `{color}` tags
- Missing `[variable]` placeholders

Fix in the `.parsed.yaml` file and re-run `.\7-5-merge.ps1`.

### "Python not found"
**Solution:** The scripts use the system Python. Install Python 3.8+ or run `.\setup.ps1` to create a venv.

---
