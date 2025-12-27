# Example Ren'Py Game - Translation Demo

This is a mock Ren'Py game used to demonstrate the translation system.

## Structure

```
Example/
└── game/
    └── tl/
        └── romanian/
            └── script.rpy     # Romanian translations (3 samples + 17 empty)
```

## What's Included

This example contains **20 dialogue lines** featuring:

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

### Manual Translation

You can translate the file manually:

```powershell
# Using interactive launcher (recommended)
.\translate.ps1

# Or directly with Python
venv\Scripts\python.exe scripts\translate_with_aya23.py games\Example\game\tl\romanian
```

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

The Romanian file contains:
- **3 translated strings** - Sample translations to show the format
- **17 empty strings** - Ready to be filled by the translation system

After running translation, all 20 strings will be filled. The automated test restores it back to 3 samples for the next run.

## Notes

- All Ren'Py tags (`{b}`, `{color=...}`, etc.) are preserved exactly
- Variables in square brackets `[player_name]` remain untranslated
- The file is a real Ren'Py translation file format
- Comments show the original English text for reference
