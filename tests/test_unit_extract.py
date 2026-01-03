"""
Test the new src/extract.py CLI with YAML configuration.

This test validates that the new extraction flow correctly:
1. Loads game configuration from current_config.yaml
2. Loads character map from characters.yaml
3. Extracts translation blocks via CLI interface
4. Generates properly structured .parsed.yaml and .tags.json files
5. Handles command-line arguments (--source, --all, --game-name)
"""

import sys
import json
import yaml
import subprocess
import shutil
from pathlib import Path

# Project paths
project_root = Path(__file__).parent.parent
test_game_dir = project_root / "temp_test_game"
test_tl_dir = test_game_dir / "game" / "tl" / "ro"

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


def setup_test_environment():
    """Create a complete test environment with game, configs, and files."""
    print(f"\n[SETUP] Creating test environment at {test_game_dir}")

    # Create directory structure
    test_tl_dir.mkdir(parents=True, exist_ok=True)

    # Create test .rpy file
    test_rpy_file = test_tl_dir / "test_script.rpy"
    test_rpy_file.write_text(TEST_RPY_CONTENT, encoding='utf-8')
    print(f"[SETUP] Created test .rpy file: {test_rpy_file}")

    # Create characters.yaml
    characters_yaml = test_tl_dir / "characters.yaml"
    characters_data = {
        "jm": {
            "name": "Jasmine",
            "gender": "female",
            "type": "main",
            "description": "Main character"
        },
        "narrator": {
            "name": "Narrator",
            "gender": "neutral",
            "type": "narrator",
            "description": "Narration"
        }
    }
    with open(characters_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(characters_data, f, allow_unicode=True, default_flow_style=False)
    print(f"[SETUP] Created characters.yaml: {characters_yaml}")

    # Create current_config.yaml
    config_yaml = project_root / "models" / "current_config.yaml"
    config_data = {
        "games": {
            "TestGame": {
                "name": "TestGame",
                "path": str(test_game_dir),
                "target_language": {
                    "name": "Romanian",
                    "code": "ro"
                },
                "source_language": "english",
                "model": "aya23",
                "context_before": 3,
                "context_after": 1
            }
        },
        "current_game": "TestGame"
    }

    # Backup existing config if it exists
    backup_config = None
    if config_yaml.exists():
        backup_config = config_yaml.read_text(encoding='utf-8')
        print(f"[SETUP] Backed up existing config")

    with open(config_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"[SETUP] Created current_config.yaml: {config_yaml}")

    return backup_config


def cleanup_test_environment(backup_config=None):
    """Remove all test files and restore original config."""
    print(f"\n[CLEANUP] Removing test environment")

    # Remove test game directory
    if test_game_dir.exists():
        shutil.rmtree(test_game_dir)
        print(f"[CLEANUP] Removed {test_game_dir}")

    # Restore original config
    config_yaml = project_root / "models" / "current_config.yaml"
    if backup_config:
        config_yaml.write_text(backup_config, encoding='utf-8')
        print(f"[CLEANUP] Restored original config")
    elif config_yaml.exists():
        config_yaml.unlink()
        print(f"[CLEANUP] Removed test config")


def test_cli_extraction_single_file():
    """Test CLI extraction of a single file."""
    print("\n" + "=" * 70)
    print("TEST: CLI Extraction - Single File")
    print("=" * 70)

    backup_config = None
    try:
        # 1. Setup test environment
        backup_config = setup_test_environment()

        # 2. Get virtual environment Python
        venv_python = project_root / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            print(f"[FAIL] Virtual environment not found at {venv_python}")
            print("       Please run x0-setup.ps1 first")
            return False

        # 3. Run extraction via CLI
        extract_script = project_root / "src" / "extract.py"
        print(f"\n[RUN] Executing: {venv_python} {extract_script} --source test_script.rpy")

        result = subprocess.run(
            [str(venv_python), str(extract_script), "--source", "test_script.rpy"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"[FAIL] Extraction failed with exit code {result.returncode}")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            return False

        print("[OK] Extraction completed successfully")

        # 4. Verify output files exist
        parsed_yaml = test_tl_dir / "test_script.parsed.yaml"
        tags_json = test_tl_dir / "test_script.tags.json"

        print(f"\n[VERIFY] Checking output files...")
        assert parsed_yaml.exists(), f"Parsed YAML not found: {parsed_yaml}"
        print(f"[OK] Found {parsed_yaml.name}")

        assert tags_json.exists(), f"Tags JSON not found: {tags_json}"
        print(f"[OK] Found {tags_json.name}")

        # 5. Validate parsed YAML content
        print(f"\n[VERIFY] Validating parsed YAML content...")
        with open(parsed_yaml, 'r', encoding='utf-8') as f:
            parsed_blocks = yaml.safe_load(f)

        assert isinstance(parsed_blocks, dict), "parsed_blocks should be a dictionary"
        assert len(parsed_blocks) == 3, f"Expected 3 parsed blocks, got {len(parsed_blocks)}"

        # Check narrator block
        narrator_block_id = "1-Narrator"
        assert narrator_block_id in parsed_blocks, f"Narrator block '{narrator_block_id}' not found"
        assert parsed_blocks[narrator_block_id]['en'] == "This is some narration."
        assert parsed_blocks[narrator_block_id]['ro'] == "Aceasta este o narațiune."
        print(f"[OK] Narrator block '{narrator_block_id}' validated")

        # Check dialogue block (tags removed in clean text)
        dialogue_block_id = "2-Jasmine"
        assert dialogue_block_id in parsed_blocks, f"Dialogue block '{dialogue_block_id}' not found"
        assert parsed_blocks[dialogue_block_id]['en'] == "Hello,! How are you?"
        assert parsed_blocks[dialogue_block_id]['ro'] == "Salut,! Cum ești?"
        print(f"[OK] Dialogue block '{dialogue_block_id}' validated (tags removed)")

        # Check string block (separator is block 3, so this is block 4)
        string_block_id = "4-Narrator"
        assert string_block_id in parsed_blocks, f"String block '{string_block_id}' not found"
        assert parsed_blocks[string_block_id]['en'] == "Chapter One"
        assert parsed_blocks[string_block_id]['ro'] == "Capitolul Unu"
        print(f"[OK] String block '{string_block_id}' validated (tags removed)")

        # 6. Validate tags JSON content
        print(f"\n[VERIFY] Validating tags JSON content...")
        with open(tags_json, 'r', encoding='utf-8') as f:
            tags_file = json.load(f)

        assert 'metadata' in tags_file
        assert 'structure' in tags_file
        assert 'blocks' in tags_file
        assert 'character_map' in tags_file

        # Check metadata
        assert tags_file['metadata']['total_blocks'] == 3
        print("[OK] Tags file metadata validated")

        # Check structure includes separator
        expected_order = [narrator_block_id, dialogue_block_id, 'separator-3', string_block_id]
        assert tags_file['structure']['block_order'] == expected_order
        print("[OK] Tags file structure validated")

        # Check character map was loaded
        assert tags_file['character_map']['jm'] == 'Jasmine'
        print("[OK] Character map validated")

        # Check dialogue block has tags preserved
        dialogue_tags = tags_file['blocks'][dialogue_block_id]['tags']
        assert len(dialogue_tags) == 3, f"Expected 3 tags, got {len(dialogue_tags)}"
        print(f"[OK] Dialogue block tags validated (3 tags preserved)")

        print("\n[OK] All CLI extraction tests passed!")
        return True

    except AssertionError as ae:
        print(f"[FAIL] Assertion Failed: {ae}")
        return False
    except subprocess.TimeoutExpired:
        print("[FAIL] Extraction timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(backup_config)


def test_cli_extraction_all_files():
    """Test CLI extraction of all files using --all flag."""
    print("\n" + "=" * 70)
    print("TEST: CLI Extraction - All Files")
    print("=" * 70)

    backup_config = None
    try:
        # 1. Setup test environment
        backup_config = setup_test_environment()

        # Create a second .rpy file
        test_rpy_file2 = test_tl_dir / "test_script2.rpy"
        test_rpy_file2.write_text(TEST_RPY_CONTENT, encoding='utf-8')
        print(f"[SETUP] Created second test file: {test_rpy_file2}")

        # 2. Get virtual environment Python
        venv_python = project_root / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            print(f"[FAIL] Virtual environment not found")
            return False

        # 3. Run extraction with --all flag
        extract_script = project_root / "src" / "extract.py"
        print(f"\n[RUN] Executing with --all flag")

        result = subprocess.run(
            [str(venv_python), str(extract_script), "--all"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"[FAIL] Extraction failed with exit code {result.returncode}")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            return False

        print("[OK] Extraction completed successfully")

        # 4. Verify both files were extracted
        parsed_yaml1 = test_tl_dir / "test_script.parsed.yaml"
        parsed_yaml2 = test_tl_dir / "test_script2.parsed.yaml"

        assert parsed_yaml1.exists(), f"First file not extracted: {parsed_yaml1}"
        assert parsed_yaml2.exists(), f"Second file not extracted: {parsed_yaml2}"
        print(f"[OK] Both files extracted successfully")

        print("\n[OK] All files extraction test passed!")
        return True

    except AssertionError as ae:
        print(f"[FAIL] Assertion Failed: {ae}")
        return False
    except subprocess.TimeoutExpired:
        print("[FAIL] Extraction timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_environment(backup_config)


def main():
    """Run all extraction tests."""
    print("\n" + "=" * 70)
    print("SRC/EXTRACT.PY CLI TEST SUITE (YAML)")
    print("=" * 70)

    tests = [
        ("CLI Extraction - Single File", test_cli_extraction_single_file),
        ("CLI Extraction - All Files", test_cli_extraction_all_files)
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "\033[92m[PASS]\033[0m" if result else "\033[91m[FAIL]\033[0m"
        print(f"{status} {test_name}")

    print(f"\nTests: {passed}/{total} passed")

    if passed == total:
        print("\n\033[92m[SUCCESS] All tests passed!\033[0m")
        print("\nThe new YAML-based extraction flow is working correctly:")
        print("  - Loads configuration from current_config.yaml")
        print("  - Loads character map from characters.yaml")
        print("  - Extracts via CLI with proper argument handling")
        print("  - Generates valid .parsed.yaml and .tags.json files")
        return 0
    else:
        print(f"\n\033[91m[FAILURE] {total - passed} test(s) failed.\033[0m")
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
