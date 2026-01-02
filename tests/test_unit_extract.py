"""
Test the src/extract.py Python module.

This test validates that the RenpyExtractor class correctly:
1. Extracts translation blocks from .rpy file content.
2. Separates clean text from tags.
3. Generates properly structured ParsedBlock and TagsFileContent objects.
4. Handles different block types (dialogue, narrator, strings) and tags.
"""

import sys
import json
import yaml
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extract import RenpyExtractor
from src.models import BlockType, FileStructureType, ParsedBlock, TagsFileContent
from src.renpy_utils import RenpyTagExtractor # Needed for RenpyExtractor init

# Project paths (used for temporary file creation)
test_output_dir = project_root / "temp_test_output"
test_output_dir.mkdir(exist_ok=True)

# Sample Ren'Py content for testing
TEST_RPY_CONTENT = """
# game/script.rpy:10
translate romanian chapter1_start_1234abcd:

    # "This is some narration."
    "Aceasta este o narațiune."

# game/script.rpy:20
translate romanian character_dialogue_efgh5678:

    # jm "Hello, [name]! {color=#FF0000}How are you?{/color}"
    jm "Salut, [name]! {color=#FF0000}Cum ești?{/color}"

# ----------------------------------------

# game/strings.rpy:5
old "{b}Chapter One{/b}"
new "{b}Capitolul Unu{/b}"
"""

# Test files
temp_rpy_file = test_output_dir / "test_extract.rpy"
temp_yaml_file = test_output_dir / "test_extract.parsed.yaml"
temp_json_file = test_output_dir / "test_extract.tags.json"


def setup_test_files():
    """Create a temporary .rpy file for extraction testing."""
    print(f"\n[SETUP] Creating temporary test file: {temp_rpy_file}")
    temp_rpy_file.write_text(TEST_RPY_CONTENT, encoding='utf-8')
    assert temp_rpy_file.exists()


def cleanup_test_files():
    """Remove all temporary files created during testing."""
    print(f"\n[CLEANUP] Removing temporary test files from {test_output_dir}")
    if temp_rpy_file.exists():
        temp_rpy_file.unlink()
    if temp_yaml_file.exists():
        temp_yaml_file.unlink()
    if temp_json_file.exists():
        temp_json_file.unlink()
    if test_output_dir.exists() and not list(test_output_dir.iterdir()): # Only remove if empty
        test_output_dir.rmdir()


def test_extraction_logic():
    """Test the RenpyExtractor's core extraction and parsing logic."""
    print("\n" + "=" * 70)
    print("TEST: RenpyExtractor Core Logic")
    print("=" * 70)

    try:
        # 1. Setup: Create test .rpy file
        setup_test_files()

        # 2. Instantiate Extractor (using a dummy character map)
        extractor = RenpyExtractor(character_map={'jm': 'Jasmine'})
        print("[OK] RenpyExtractor instantiated.")

        # 3. Perform extraction
        parsed_blocks, tags_file = extractor.extract_file(
            temp_rpy_file,
            target_language="romanian",
            source_language="english"
        )
        print("[OK] Extraction performed.")

        # 4. Assertions on parsed_blocks (YAML equivalent)
        print("\n[ASSERT] Validating parsed_blocks...")
        assert isinstance(parsed_blocks, dict), "parsed_blocks should be a dictionary"
        assert len(parsed_blocks) == 3, f"Expected 3 parsed blocks, got {len(parsed_blocks)}"

        # Check narrator block
        narrator_block_id = "1-Narrator"
        assert narrator_block_id in parsed_blocks, f"Narrator block '{narrator_block_id}' not found."
        assert parsed_blocks[narrator_block_id]['en'] == "This is some narration."
        assert parsed_blocks[narrator_block_id]['ro'] == "Aceasta este o narațiune."
        print(f"[OK] Narrator block '{narrator_block_id}' validated.")

        # Check dialogue block (tags should be removed in parsed_blocks)
        dialogue_block_id = "2-Jasmine"
        assert dialogue_block_id in parsed_blocks, f"Dialogue block '{dialogue_block_id}' not found."
        assert parsed_blocks[dialogue_block_id]['en'] == "Hello,! How are you?", \
            f"EN mismatch: got {repr(parsed_blocks[dialogue_block_id]['en'])}"
        assert parsed_blocks[dialogue_block_id]['ro'] == "Salut,! Cum ești?", \
            f"RO mismatch: got {repr(parsed_blocks[dialogue_block_id]['ro'])}"
        print(f"[OK] Dialogue block '{dialogue_block_id}' validated (tags removed).")

        # Check string block (index 4 because block 3 is the separator, tags removed)
        string_block_id = "4-Narrator"
        assert string_block_id in parsed_blocks, f"String block '{string_block_id}' not found."
        assert parsed_blocks[string_block_id]['en'] == "Chapter One", \
            f"EN mismatch: got {repr(parsed_blocks[string_block_id]['en'])}"
        assert parsed_blocks[string_block_id]['ro'] == "Capitolul Unu", \
            f"RO mismatch: got {repr(parsed_blocks[string_block_id]['ro'])}"
        print(f"[OK] String block '{string_block_id}' validated (tags removed).")

        # 5. Assertions on tags_file (JSON equivalent)
        print("\n[ASSERT] Validating tags_file...")
        assert isinstance(tags_file, dict), "tags_file should be a dictionary"
        assert 'metadata' in tags_file and 'structure' in tags_file and 'blocks' in tags_file

        # Check metadata
        assert tags_file['metadata']['file_structure_type'] == FileStructureType.DIALOGUE_AND_STRINGS.value
        assert tags_file['metadata']['total_blocks'] == 3
        print("[OK] tags_file metadata validated.")

        # Check structure (including separator)
        expected_order = [narrator_block_id, dialogue_block_id, 'separator-3', string_block_id]
        assert tags_file['structure']['block_order'] == expected_order, \
            f"Expected {expected_order}, got {tags_file['structure']['block_order']}"
        print("[OK] tags_file structure validated.")

        # Check a tagged block (dialogue block with tags)
        tagged_dialogue_block = tags_file['blocks'][dialogue_block_id]
        assert tagged_dialogue_block['type'] == BlockType.DIALOGUE.value, \
            f"Expected {BlockType.DIALOGUE.value}, got {tagged_dialogue_block['type']}"
        assert tagged_dialogue_block['char_var'] == 'jm'
        assert tagged_dialogue_block['char_name'] == 'Jasmine'
        # Original: "Hello, [name]! {color=#FF0000}How are you?{/color}"
        # Tags: [name], {color=#FF0000}, {/color} = 3 tags
        assert len(tagged_dialogue_block['tags']) == 3, \
            f"Expected 3 tags ([name], color, /color), got {len(tagged_dialogue_block['tags'])}"
        print(f"[OK] tags_file dialogue block '{dialogue_block_id}' validated.")

        print("\n[OK] All extraction logic tests passed!")
        return True

    except AssertionError as ae:
        print(f"[FAIL] Assertion Failed: {ae}")
        return False
    except Exception as e:
        print(f"[FAIL] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 6. Cleanup
        cleanup_test_files()


def main():
    """Run the extraction test."""
    print("\n" + "=" * 70)
    print("SRC/EXTRACT.PY TEST SUITE")
    print("=" * 70)

    test_name = "Python RenpyExtractor Logic"
    result = test_extraction_logic()

    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    status = "\033[92m[PASS]\033[0m" if result else "\033[91m[FAIL]\033[0m"
    print(f"{status} {test_name}")

    if result:
        print("\n\033[92m[SUCCESS] All tests passed!\033[0m")
        return 0
    else:
        print("\n\033[91m[FAILURE] Some tests failed.\033[0m")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
