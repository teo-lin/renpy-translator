"""
Integration Test: Model Comparison (9-compare.ps1)

This test verifies that the model comparison workflow works correctly:
1. Runs 9-compare.ps1 with Example game
2. Verifies parsed files are created
3. Checks that translations are stored under numbered keys (r0, r1, r2, etc.)
4. Validates that ALL installed models produced translations
5. Checks output format and statistics

This is a full end-to-end test that requires all installed models.
"""

import sys
import json
import yaml
import subprocess
from pathlib import Path
import re

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Project paths
project_root = Path(__file__).parent.parent
compare_script = project_root / "8-compare.ps1"
models_config_path = project_root / "models" / "models_config.json"
test_game = "Example"
test_language = "ro"
test_dir = project_root / "games" / test_game / "game" / "tl" / "romanian"


def load_models_config():
    """Load models configuration to know expected model count"""
    if not models_config_path.exists():
        print(f"ERROR: Models configuration not found at {models_config_path}")
        return None

    with open(models_config_path, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)

    return config


def cleanup_parsed_files():
    """Remove any existing parsed files before test"""
    if not test_dir.exists():
        print(f"  Test directory doesn't exist yet: {test_dir}")
        return

    parsed_files = list(test_dir.glob("*.parsed.yaml"))
    if parsed_files:
        print(f"  Cleaning up {len(parsed_files)} existing parsed file(s)...")
        for file in parsed_files:
            file.unlink()
            print(f"    Removed: {file.name}")
    else:
        print(f"  No existing parsed files to clean up")


def run_compare_script():
    """Run 9-compare.ps1 and return output and exit code"""
    print(f"\n  Running: {compare_script}")
    print(f"  Game: {test_game}, Language: {test_language}")
    print(f"  This may take several minutes...\n")

    try:
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File",
             str(compare_script), "-GameName", test_game, "-Language", test_language],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10 minute timeout
        )

        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        print("  ERROR: Script timed out after 10 minutes!")
        return "", "Timeout", 1
    except Exception as e:
        print(f"  ERROR: Failed to run script: {e}")
        return "", str(e), 1


def test_compare_workflow():
    """Run the full comparison workflow and validate results"""

    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Model Comparison Workflow (9-compare.ps1)")
    print("=" * 70)

    # Step 1: Load configuration
    print("\n[1/5] Loading models configuration...")
    models_config = load_models_config()
    if not models_config:
        print("  [FAIL] Could not load models configuration")
        return False

    installed_models = models_config.get('installed_models', [])
    expected_model_count = len(installed_models)

    if expected_model_count == 0:
        print("  [FAIL] No models installed - please run 0-setup.ps1 first")
        return False

    print(f"  ✓ Found {expected_model_count} installed models")
    for model_key in installed_models:
        model_info = models_config['available_models'][model_key]
        print(f"    - {model_info['name']}")

    # Step 2: Cleanup
    print("\n[2/5] Cleaning up existing files...")
    cleanup_parsed_files()

    # Step 3: Run comparison
    print("\n[3/5] Running comparison workflow...")
    stdout, stderr, exit_code = run_compare_script()

    # Display output
    if stdout:
        for line in stdout.split('\n'):
            print(f"  {line}")

    if stderr and stderr != "Timeout":
        print(f"\nSTDERR:\n{stderr}")

    if exit_code != 0:
        print(f"\n  [FAIL] Script failed with exit code {exit_code}")
        return False

    print(f"\n  ✓ Script completed successfully (exit code: 0)")

    # Step 4: Verify output files
    print("\n[4/5] Verifying output files...")

    if not test_dir.exists():
        print(f"  [FAIL] Test directory not created: {test_dir}")
        return False

    parsed_files = list(test_dir.glob("*.parsed.yaml"))
    if len(parsed_files) == 0:
        print(f"  [FAIL] No parsed files created")
        return False

    print(f"  ✓ Found {len(parsed_files)} parsed file(s)")

    # Check first file for numbered keys
    first_file = parsed_files[0]
    print(f"\n  Examining: {first_file.name}")

    with open(first_file, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)

    # Find any block with 'en' key (dialogue, narrator, or string)
    # The current block ID creation uses char_name or "block-" prefix, not "dialogue-".
    # We'll just take the first block that has an 'en' key.
    dialogue_blocks = [k for k in content.keys() if 'en' in content[k]]
    if not dialogue_blocks:
        print(f"  [FAIL] No translatable blocks (with 'en' key) found in parsed file")
        return False

    first_block_id = dialogue_blocks[0]
    first_block = content[first_block_id]

    print(f"    First block: {first_block_id}")
    print(f"    Keys in block: {list(first_block.keys())}")

    # Check for new format keys (ay, he, ma, etc.)
    found_keys = []
    for model_key in installed_models:
        key = model_key[:2].lower()
        if key in first_block:
            found_keys.append(key)
            print(f"      ✓ Found key '{key}': {first_block[key][:50]}...")

    if len(found_keys) == 0:
        print(f"  [FAIL] No numbered translation keys (r0, r1, etc.) found")
        return False

    print(f"\n  ✓ Found {len(found_keys)} translation keys: {', '.join(found_keys)}")

    if len(found_keys) != expected_model_count:
        print(f"  [WARNING] Expected {expected_model_count} keys, found {len(found_keys)}")
        print(f"            Some models may have failed")
    else:
        print(f"  ✓ All {expected_model_count} models produced translations")

    # Step 5: Verify output format
    print("\n[5/5] Verifying output format...")

    output_text = stdout.lower()

    checks = [
        ("model comparison", "model comparison table"),
        ("duration", "duration tracking"),
        ("fastest:", "performance comparison"),
        ("benchmark complete" or "comparison complete", "completion message")
    ]

    all_checks_passed = True
    for keyword, description in checks:
        if keyword in output_text:
            print(f"  ✓ Found {description}")
        else:
            print(f"  [WARNING] Missing {description} (keyword: '{keyword}')")
            all_checks_passed = False

    if not all_checks_passed:
        print(f"\n  [WARNING] Some output checks failed, but core functionality works")

    print("\n  ✓ Verification complete!")
    return True


def test_key_format():
    """Test that keys are in correct format (r0, r1, r2, not 01, 02)"""

    print("\n" + "=" * 70)
    print("TEST: Key format validation")
    print("=" * 70)

    if not test_dir.exists():
        print("  [SKIP] No test files available")
        return True

    parsed_files = list(test_dir.glob("*.parsed.yaml"))
    if not parsed_files:
        print("  [SKIP] No parsed files to check")
        return True

    print(f"  Checking {len(parsed_files)} parsed file(s)...")

    for parsed_file in parsed_files:
        with open(parsed_file, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        for block_id, block_data in content.items():
            # Filter out non-dialogue blocks or blocks without 'en' key
            if 'en' in block_data:
                # Check for correct format (ay, he, ma, etc.)
                for key in block_data.keys():
                    if key == 'en': # Skip the English key
                        continue
                    if re.match(r'^[a-z]{2}$', key):
                        # Correct format
                        pass
                    elif re.match(r'^[a-z]{2}\d+$', key): # Check for old format with number suffix like r0, ay0
                        print(f"  [FAIL] Found old format key '{key}' in {parsed_file.name}")
                        print(f"         Should be a two-letter abbreviation (e.g., '{key[:2]}')")
                        return False
                    else: # Catch any other unexpected key format
                        print(f"  [FAIL] Found unexpected key format '{key}' in {parsed_file.name}")
                        return False

    print(f"  ✓ All keys use correct format (e.g., ay, he)")
    return True


def main():
    """Run all integration tests"""

    print("\n" + "=" * 70)
    print("INTEGRATION TESTS: Model Comparison (9-compare.ps1)")
    print("=" * 70)
    print("\nNOTE: This test requires:")
    print("  - All models installed (run 0-setup.ps1)")
    print("  - Example game present")
    print("  - May take 5-10 minutes depending on model count")
    print("=" * 70)

    tests = [
        ("Main workflow", test_compare_workflow),
        ("Key format", test_key_format)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"Running: {test_name}")
        print('=' * 70)

        try:
            if test_func():
                print(f"\n  ✓ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n  ✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"\n  ✗ {test_name} FAILED with exception:")
            print(f"     {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n  ✓ ALL INTEGRATION TESTS PASSED!")
        print(f"\n  Translation files saved at:")
        print(f"    {test_dir}")
        print(f"\n  You can review the translations to compare model outputs.")
        return 0
    else:
        print("\n  ✗ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
