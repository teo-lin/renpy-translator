"""
Test script for character extraction from Example game
Verifies that characters.json is properly generated with:
- Correct character variables discovered from .rpy files
- Character names extracted from script.rpy definitions
- Auto-generated descriptions based on file appearances
"""

import json
import os
import sys

def test_characters():
    """Test character extraction for Example game"""

    # Path to characters.json
    characters_file = r"games\Example\game\tl\romanian\characters.json"

    # Check if file exists
    if not os.path.exists(characters_file):
        print(f"[FAIL] FAIL: {characters_file} not found")
        print("   Run: .\\characters.ps1 and select Example game")
        return False

    # Load characters.json (handle UTF-8 BOM)
    with open(characters_file, 'r', encoding='utf-8-sig') as f:
        characters = json.load(f)

    print(f"[OK] Found {len(characters)} characters in characters.json")
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
            "type": "main"  # Auto-detected as main (can be manually changed to supporting)
        }
    }

    # Test each expected character
    passed = 0
    failed = 0

    for char_var, expected_data in expected.items():
        if char_var not in characters:
            print(f"[FAIL] FAIL: Character '{char_var}' not found in characters.json")
            failed += 1
            continue

        char = characters[char_var]

        # Check name
        if char.get("name") != expected_data["name"]:
            print(f"[FAIL] FAIL: {char_var}.name = '{char.get('name')}', expected '{expected_data['name']}'")
            failed += 1
        else:
            print(f"[OK] PASS: {char_var}.name = '{char.get('name')}'")
            passed += 1

        # Check type
        if char.get("type") != expected_data["type"]:
            print(f"[FAIL] FAIL: {char_var}.type = '{char.get('type')}', expected '{expected_data['type']}'")
            failed += 1
        else:
            print(f"[OK] PASS: {char_var}.type = '{char.get('type')}'")
            passed += 1

        # Check description exists and is not empty
        description = char.get("description", "")
        if description:
            print(f"[OK] PASS: {char_var}.description = '{description}'")
            passed += 1
        else:
            print(f"[WARN] WARN: {char_var}.description is empty")

        # Check gender is set
        if "gender" in char:
            print(f"[OK] INFO: {char_var}.gender = '{char.get('gender')}'")

        print()

    # Summary
    total = passed + failed
    print("=" * 60)
    print(f"Test Results: {passed}/{total} passed")

    if failed == 0:
        print("[PASS] ALL TESTS PASSED")
        return True
    else:
        print(f"[FAIL] {failed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = test_characters()
    sys.exit(0 if success else 1)
