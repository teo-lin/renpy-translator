"""
Test the src/merger.py Python module in isolation.

This test validates that the RenpyMerger class correctly:
1. Reads a .parsed.yaml (with translations) and a .tags.json file.
2. Reconstructs a .rpy file from these inputs.
3. Correctly restores text, character variables, and tags.
4. Matches an expected "golden" output file.
"""

import sys
import json
import yaml
from pathlib import Path
import tempfile
import shutil

# Add src directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from merger import RenpyMerger

# --- Test Data ---

# Handcrafted YAML file with translations
PARSED_YAML_CONTENT = """
dialogue-1:
  en: Hello, [name]!
  ro: Salut, [name]!
separator-1:
  type: separator
strings-1:
  en: '{b}Chapter 1{/b}'
  ro: '{b}Capitolul 1{/b}'
"""

# Handcrafted JSON file with metadata and tags
TAGS_JSON_CONTENT = """
{
  "metadata": {
    "source_file": "test.rpy",
    "target_language": "romanian",
    "source_language": "english",
    "extracted_at": "2025-12-28T12:00:00Z",
    "file_structure_type": "DIALOGUE_AND_STRINGS",
    "has_separator_lines": true,
    "total_blocks": 3,
    "untranslated_blocks": 0
  },
  "structure": {
    "block_order": [
      "dialogue-1",
      "separator-1",
      "strings-1"
    ],
    "string_section_start": 2,
    "string_section_header": "translate romanian strings:"
  },
  "blocks": {
    "dialogue-1": {
      "type": "dialogue",
      "label": "start_dialogue",
      "location": "game/script.rpy:10",
      "char_var": "s",
      "char_name": "Sylvie",
      "tags": [],
      "template": "# {location}\\ntranslate {language} {label}:\\n\\n    # {char_var} \\"{original}\\"\\n    {char_var} \\"{translation}\\"",
      "separator_content": null
    },
    "separator-1": {
      "type": "separator",
      "label": null,
      "location": null,
      "char_var": null,
      "char_name": null,
      "tags": [],
      "template": "",
      "separator_content": "# ----------------------------------------"
    },
    "strings-1": {
      "type": "string",
      "label": "strings",
      "location": "game/script.rpy:20",
      "char_var": null,
      "char_name": null,
      "tags": [
        {"pos": 0, "tag": "{b}", "type": "other"},
        {"pos": 9, "tag": "{/b}", "type": "close"}
      ],
      "template": "    # {location}\\n    old \\"{original}\\"\\n    new \\"{translation}\\"",
      "separator_content": null
    }
  },
  "character_map": {
    "s": "Sylvie"
  }
}
"""

# Expected output .rpy file content
EXPECTED_RPY_CONTENT = """# TODO: Translation updated at 2025-12-28

# game/script.rpy:10
translate romanian start_dialogue:

    # s "Hello, [name]!"
    s "Salut, [name]!"

# ----------------------------------------

translate romanian strings:

    # game/script.rpy:20
    old "{b}Chapter 1{/b}"
    new "{b}Capitolul 1{/b}"

"""

def test_merge_in_isolation():
    """
    Tests the RenpyMerger class with handcrafted input files.
    """
    print("\n" + "=" * 70)
    print("TEST: RenpyMerger in Isolation")
    print("=" * 70)

    # Create a temporary directory for test files
    temp_dir = Path(tempfile.mkdtemp(prefix="test_merge_"))
    print(f"[SETUP] Created temporary directory: {temp_dir}")

    try:
        # 1. Create handcrafted input files
        parsed_yaml_path = temp_dir / "test.parsed.yaml"
        tags_json_path = temp_dir / "test.tags.json"
        output_rpy_path = temp_dir / "test.output.rpy"

        with open(parsed_yaml_path, 'w', encoding='utf-8') as f:
            f.write(PARSED_YAML_CONTENT)
        print(f"[SETUP] Created: {parsed_yaml_path.name}")

        with open(tags_json_path, 'w', encoding='utf-8') as f:
            f.write(TAGS_JSON_CONTENT)
        print(f"[SETUP] Created: {tags_json_path.name}")

        # 2. Instantiate and run the merger
        print("\n[RUN] Instantiating and running RenpyMerger...")
        merger = RenpyMerger()
        success = merger.merge_file(
            parsed_yaml_path=parsed_yaml_path,
            tags_json_path=tags_json_path,
            output_rpy_path=output_rpy_path,
            validate=True
        )

        # 3. Assertions
        print("\n[ASSERT] Verifying merge results...")
        assert success, "Merger reported failure or validation errors."
        print("[OK] Merger returned success.")

        assert output_rpy_path.exists(), "Output .rpy file was not created."
        print(f"[OK] Output file created: {output_rpy_path.name}")

        actual_content = output_rpy_path.read_text(encoding='utf-8').strip().replace('\\r\\n', '\\n')
        expected_content = EXPECTED_RPY_CONTENT.strip().replace('\\r\\n', '\\n')

        assert actual_content == expected_content, "Output content does not match expected content."
        print("[OK] Output content matches expected golden file.")

        print("\n[PASS] Merge test completed successfully!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed with an exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 4. Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n[CLEANUP] Removed temporary directory: {temp_dir}")

def main():
    """Run the test suite."""
    success = test_merge_in_isolation()
    if success:
        print("\n" + "="*70)
        print("✅ ALL MERGE TESTS PASSED")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("❌ MERGE TESTS FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())

