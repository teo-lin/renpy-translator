"""
Test the extract.ps1 PowerShell script using the Example game

This test validates that the extraction PowerShell script correctly:
1. Extracts translation files into YAML and JSON formats
2. Generates properly structured output files
3. Handles characters and tags correctly
"""

import sys
import json
import subprocess
from pathlib import Path
import yaml

# Project paths
project_root = Path(__file__).parent.parent
example_game = project_root / "games" / "Example"
example_tl = example_game / "game" / "tl" / "romanian"
test_file = "Cell01_Academy.rpy"
test_file_path = example_tl / test_file

# Output paths
yaml_output = example_tl / "Cell01_Academy.parsed.yaml"
json_output = example_tl / "Cell01_Academy.tags.json"

# PowerShell script
extract_script = project_root / "extract.ps1"


def cleanup_output_files():
    """Remove any existing output files"""
    if yaml_output.exists():
        yaml_output.unlink()
    if json_output.exists():
        json_output.unlink()


def test_prerequisites():
    """Verify all required files exist"""
    print("\n" + "=" * 70)
    print("TEST: Prerequisites Check")
    print("=" * 70)

    checks = [
        (example_game.exists(), f"Example game directory: {example_game}"),
        (test_file_path.exists(), f"Test file: {test_file_path}"),
        (extract_script.exists(), f"Extract script: {extract_script}"),
        ((example_tl / "characters.json").exists(), f"Characters config: {example_tl / 'characters.json'}")
    ]

    all_passed = True
    for passed, description in checks:
        status = "[PASS]" if passed else "[FAIL]"
        color = "\033[92m" if passed else "\033[91m"
        print(f"{color}{status}\033[0m {description}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n[FAIL] Prerequisites check failed!")
        return False

    print("\n[OK] All prerequisites satisfied")
    return True


def configure_example_game():
    """Add Example game to configuration if not present"""
    print("\n" + "=" * 70)
    print("TEST: Configure Example Game")
    print("=" * 70)

    config_path = project_root / "models" / "local_config.json"

    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)

        # Check if Example game already configured
        if 'games' in config and 'Example' in config['games']:
            print("[OK] Example game already configured")
            return True

        # Add Example game configuration
        if 'games' not in config:
            config['games'] = {}

        config['games']['Example'] = {
            "name": "Example",
            "path": str(example_game),
            "target_language": "romanian",
            "source_language": "english",
            "model": "Aya-23-8B",
            "context_before": 3,
            "context_after": 1
        }

        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)

        print("[OK] Example game added to configuration")
        return True

    except Exception as e:
        print(f"[FAIL] Error configuring Example game: {e}")
        return False


def run_extraction():
    """Run the extract.ps1 script on the test file"""
    print("\n" + "=" * 70)
    print("TEST: Running Extraction Script")
    print("=" * 70)

    # Build PowerShell command
    ps_command = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(extract_script),
        "-Source", test_file,
        "-GameName", "Example"
    ]

    print(f"\n[Run] Command: {' '.join(ps_command)}")

    try:
        result = subprocess.run(
            ps_command,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"\n[FAIL] Script failed with exit code {result.returncode}")
            print(f"\nSTDOUT:\n{result.stdout}")
            print(f"\nSTDERR:\n{result.stderr}")
            return False

        print("\n[OK] Extraction completed successfully")
        if result.stdout:
            print(f"\nOutput:\n{result.stdout}")

        return True

    except subprocess.TimeoutExpired:
        print("\n[FAIL] Extraction timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"\n[FAIL] Error running extraction: {e}")
        return False


def validate_yaml_output():
    """Validate the YAML output file structure and content"""
    print("\n" + "=" * 70)
    print("TEST: YAML Output Validation")
    print("=" * 70)

    if not yaml_output.exists():
        print(f"[FAIL] YAML output not found: {yaml_output}")
        return False

    print(f"[OK] YAML file exists: {yaml_output.name}")

    try:
        with open(yaml_output, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            print("[FAIL] YAML data is not a dictionary of blocks")
            return False

        print(f"[OK] YAML contains {len(data)} blocks")

        # Check structure of first block
        if len(data) > 0:
            required_fields = ['en', 'ro']
            first_block_id = list(data.keys())[0]
            first_block = data[first_block_id]

            print(f"[OK] First block ID: {first_block_id}")

            all_fields_present = True
            for field in required_fields:
                if field not in first_block:
                    print(f"[FAIL] Missing required field: {field}")
                    all_fields_present = False
                else:
                    print(f"[OK] Field present: {field}")

            if not all_fields_present:
                return False

        # Check for specific content
        translated_blocks = {k: v for k, v in data.items() if v.get('ro')}
        untranslated_blocks = {k: v for k, v in data.items() if not v.get('ro')}

        print(f"\n[Info] Translated blocks: {len(translated_blocks)}")
        print(f"[Info] Untranslated blocks: {len(untranslated_blocks)}")

        # Check for Romanian content
        romanian_found = any("Bine ai venit" in v.get('ro', '') for v in data.values())
        if romanian_found:
            print("[OK] Found Romanian translations")
        else:
            print("[WARN] No Romanian translations found")

        return True

    except yaml.YAMLError as e:
        print(f"[FAIL] YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading YAML: {e}")
        return False


def validate_json_output():
    """Validate the JSON output file structure and content"""
    print("\n" + "=" * 70)
    print("TEST: JSON Output Validation")
    print("=" * 70)

    if not json_output.exists():
        print(f"[FAIL] JSON output not found: {json_output}")
        return False

    print(f"[OK] JSON file exists: {json_output.name}")

    try:
        with open(json_output, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        # Check required top-level keys
        required_keys = ['metadata', 'structure', 'blocks']
        all_keys_present = True

        for key in required_keys:
            if key not in data:
                print(f"[FAIL] Missing required key: {key}")
                all_keys_present = False
            else:
                print(f"[OK] Key present: {key}")

        if not all_keys_present:
            return False

        # Check metadata content
        metadata = data.get('metadata', {})
        print(f"\n[Info] Metadata:")
        print(f"  - Target language: {metadata.get('target_language')}")
        print(f"  - Total blocks: {metadata.get('total_blocks')}")
        print(f"  - Untranslated blocks: {metadata.get('untranslated_blocks')}")
        print(f"  - File structure: {metadata.get('file_structure_type')}")

        # Check structure content
        structure = data.get('structure', {})
        block_order = structure.get('block_order', [])
        print(f"\n[Info] Block order: {len(block_order)} blocks")

        # Check blocks content
        blocks = data.get('blocks', {})
        print(f"[Info] Blocks: {len(blocks)} blocks")

        if blocks:
            # Check first block structure
            first_block_id = list(blocks.keys())[0]
            first_block = blocks[first_block_id]
            print(f"\n[Info] First block ({first_block_id}):")
            for key in ['label', 'character', 'tags']:
                if key in first_block:
                    print(f"  - {key}: {first_block[key]}")

        return True

    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading JSON: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("EXTRACT.PS1 TEST SUITE - Example Game")
    print("=" * 70)

    tests = [
        ("Prerequisites", test_prerequisites),
        ("Configuration", configure_example_game),
        ("Cleanup", lambda: (cleanup_output_files(), True)[1]),
        ("Extraction", run_extraction),
        ("YAML Validation", validate_yaml_output),
        ("JSON Validation", validate_json_output),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if not result:
                print(f"\n[FAIL] Test '{test_name}' failed. Stopping test suite.")
                break
        except Exception as e:
            print(f"\n[FAIL] Test '{test_name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            break

    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "\033[92m[PASS]\033[0m" if result else "\033[91m[FAIL]\033[0m"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n\033[92m[SUCCESS] All tests passed!\033[0m")
        print(f"\nOutput files generated:")
        print(f"  - {yaml_output}")
        print(f"  - {json_output}")
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
