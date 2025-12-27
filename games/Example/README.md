# Example Ren'Py Game - Translation Demo

This is a **minimal example Ren'Py visual novel** used for testing translation workflows.

## Structure

```
Example/
├── README.md                    # This file
└── game/
    ├── script.rpy              # Source Ren'Py script (English)
    └── tl/
        └── romanian/
            ├── script.rpy      # Romanian translation file
            ├── characters.json # Character mappings (for modular pipeline)
            └── script.rpy.backup # Backup (created by tests)
```

## What's Included

This example contains **20 dialogue blocks + 6 string blocks (menu choices)** featuring:

### Characters
- **narrator** - Story narration
- **mc** (Main Character) - The player character with variable name `[player_name]`
- **sarah** - A friendly student who shows the player around
- **alex** - Sarah's best friend

### Ren'Py Features Demonstrated

1. **Basic dialogue** - Simple conversational text
2. **Variables** - `[player_name]` dynamic substitution
3. **Formatting tags**:
   - `{b}bold{/b}` - Bold text
   - `{color=#ff69b4}colored{/color}` - Colored text
   - `{size=18}sized{/size}` - Custom font size
4. **Scene headers** - Location and time indicators
5. **Multi-line conversations** - Natural dialogue flow

## Story Summary

A new student arrives at an academy and meets Sarah, who gives them a tour. They visit the library, have lunch at the cafeteria, and meet Sarah's friend Alex. A welcoming introduction to campus life.

## Usage

### Option 1: Original Pipeline (All-in-One)

Translate directly using the original pipeline:

```powershell
# Using interactive launcher (recommended)
.\translate.ps1

# Or directly with Python
python src\translators\aya23_translator.py games\Example\game\tl\romanian\script.rpy --language ro
```

### Option 2: Modular Pipeline (Extract → Translate → Merge)

Use the new modular pipeline for better control:

```powershell
# Step 1: Extract clean text and tags
.\extract.ps1 -Source "script.rpy"
# Creates: script.parsed.yaml (human-editable) and script.tags.json (metadata)

# Step 2: Translate (or manually edit the YAML file)
.\translate.ps1
# Updates: script.parsed.yaml with translations

# Step 3: Merge back to .rpy format
.\merge.ps1 -Source "script"
# Creates: script.translated.rpy (with tags restored and validation)
```

**Benefits of modular approach:**
- Human review between steps
- Edit YAML files manually
- Git-friendly diffs
- Integrity validation before final output

### Automated Test

Run the automated test that translates and verifies:

```powershell
# Run test (automatically restores original after)
venv\Scripts\python.exe tests\test_example_game.py

# Or use the test runner
.\test.ps1
```

The test will:
1. Back up the original file (3 sample translations)
2. Translate the remaining 17 empty strings
3. Verify translations were added
4. Restore the file to its original state

### File State

The Romanian translation file (`game/tl/romanian/script.rpy`) contains:
- **Total blocks:** 26 (20 dialogue + 6 string/menu choices)
- **Translated:** 4 blocks (3 dialogue + 1 string) ≈ 15%
- **Untranslated:** 22 blocks (17 dialogue + 5 strings) ≈ 85%

This mix allows testing:
- Skipping already-translated blocks
- Processing untranslated blocks
- Preserving existing translations
- Handling both dialogue and string block types

After running translation, all 26 blocks will be filled. The automated test restores it back to the original state (4 translated) for the next run.

## Notes

- All Ren'Py tags (`{b}`, `{color=...}`, etc.) are preserved exactly
- Variables in square brackets `[player_name]` remain untranslated
- The file is a real Ren'Py translation file format
- Comments show the original English text for reference
