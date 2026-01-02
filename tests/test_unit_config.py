"""
Test script for character extraction from Example game
Verifies that 1-config.ps1 properly generates characters.json with:
- Correct character variables discovered from .rpy files
- Character names extracted from script.rpy definitions
- Auto-generated descriptions based on file appearances
"""

import json
import os
import sys
import shutil
import subprocess
from pathlib import Path

def test_unit_config():
    """Test that 1-config.ps1 creates characters.json correctly"""

    # Paths
    project_root = Path(__file__).parent.parent
    characters_file = project_root / "games" / "Example" / "game" / "tl" / "romanian" / "characters.json"
    backup_file = characters_file.with_suffix(".json.backup")
    stage_script = project_root / "1-config.ps1"

    print("=" * 70)
    print("TEST: Character Discovery & Generation")
    print("=" * 70)
    print()

    # Step 1: Backup existing file if it exists
    print("[1/5] Backing up existing characters.json (if exists)...")
    if characters_file.exists():
        shutil.copy2(characters_file, backup_file)
        print(f"   [OK] Backed up to: {backup_file.name}")
        characters_file.unlink()
        print(f"   [OK] Deleted existing file")
    else:
        print("   [OK] No existing file to backup")
    print()

    # Step 2: Run 1-config.ps1 to generate characters.json
    print("[2/5] Running 1-config.ps1 to generate characters.json...")
    try:
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy", "Bypass",
                "-File", str(stage_script),
                "-GamePath", str(project_root / "games" / "Example"),
                "-Language", "romanian",
                "-Model", "Aya-23-8B"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"   [FAIL] Script failed with exit code {result.returncode}")
            print(f"   STDERR: {result.stderr}")
            return False

        print("   [OK] 1-config.ps1 executed successfully")
    except Exception as e:
        print(f"   [FAIL] Error running 1-config.ps1: {e}")
        return False
    print()

    # Step 3: Verify file was created
    print("[3/5] Verifying characters.json was created...")
    if not characters_file.exists():
        print(f"   [FAIL] File was not created: {characters_file}")
        return False
    print(f"   [OK] File created: {characters_file}")
    print()

    # Step 4: Load and validate content
    print("[4/5] Validating characters.json content...")
    try:
        with open(characters_file, 'r', encoding='utf-8-sig') as f:
            characters = json.load(f)
    except Exception as e:
        print(f"   [FAIL] Error loading JSON: {e}")
        return False

    print(f"   [OK] Found {len(characters)} characters in characters.json")
    print()

    # Expected characters from Example game
    expected = {
        "narrator": {
            "name": "Narrator",  # From: define narrator = Character(None)
            "type": "narrator"
        },
        "mc": {
            "name": "MainCharacter",  # From: define mc = Character("[player_name]", ...)
            "type": "protagonist"
        },
        "sarah": {
            "name": "Sarah",  # From: define sarah = Character("Sarah", ...)
            "type": "main"
        },
        "alex": {
            "name": "Alex",  # From: define alex = Character("Alex", ...)
            "type": "main"
        }
    }

    # Test each expected character
    print("[5/5] Testing character data...")
    passed = 0
    failed = 0

    for char_var, expected_data in expected.items():
        if char_var not in characters:
            print(f"   [FAIL] Character '{char_var}' not found in characters.json")
            failed += 1
            continue

        char = characters[char_var]

        # Check name
        if char.get("name") != expected_data["name"]:
            print(f"   [FAIL] {char_var}.name = '{char.get('name')}', expected '{expected_data['name']}'")
            failed += 1
        else:
            print(f"   [PASS] {char_var}.name = '{char.get('name')}'")
            passed += 1

        # Check type
        if char.get("type") != expected_data["type"]:
            print(f"   [FAIL] {char_var}.type = '{char.get('type')}', expected '{expected_data['type']}'")
            failed += 1
        else:
            print(f"   [PASS] {char_var}.type = '{char.get('type')}'")
            passed += 1

        # Check description exists
        if char.get("description"):
            print(f"   [PASS] {char_var}.description = '{char.get('description')}'")
            passed += 1
        else:
            print(f"   [WARN] {char_var}.description is empty")

    print()

    # Cleanup: Remove characters.json (restore backup if it existed)
    print("[Cleanup] Cleaning up characters.json...")
    if backup_file.exists():
        # Restore original file
        shutil.copy2(backup_file, characters_file)
        backup_file.unlink()
        print("   [OK] Original file restored")
    else:
        # No backup existed, remove the generated file
        if characters_file.exists():
            characters_file.unlink()
            print("   [OK] Generated file removed")
    print()

    # Summary
    total = passed + failed
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Assertions: {passed}/{total} passed")

    if failed == 0:
        print()
        print("\033[92m[SUCCESS] All tests passed!\033[0m")
        print()
        print("1-config.ps1 successfully:")
        print("  - Generated characters.json from scratch")
        print("  - Discovered all character variables from .rpy files")
        print("  - Extracted character names from script.rpy")
        print("  - Set correct character types")
        return True
    else:
        print()
        print(f"\033[91m[FAILURE] {failed} tests failed.\033[0m")
        return False

if __name__ == "__main__":
    success = test_unit_config()
    sys.exit(0 if success else 1)
