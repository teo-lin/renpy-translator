"""
Test the example game translation workflow

This test:
1. Backs up the original example game file (3 strings translated)
2. Runs translation on the remaining empty strings
3. Verifies new translations were added
4. Restores the original file for next test run
"""

import sys
import shutil
import subprocess
from pathlib import Path

# Project paths
project_root = Path(__file__).parent.parent
example_file = project_root / "games" / "Example" / "game" / "tl" / "romanian" / "script.rpy"
backup_file = example_file.with_suffix(".rpy.backup")
python_exe = project_root / "venv" / "Scripts" / "python.exe"
translate_script = project_root / "scripts" / "translate.py"


def count_translations(file_path):
    """Count how many non-empty translations exist in the file"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    count = 0
    for i, line in enumerate(lines):
        # Look for character lines with non-empty strings
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '"' in stripped:
            # Extract what's in quotes
            if '""' not in stripped:  # Not an empty translation
                count += 1

    return count


def test_example_game_translation():
    """Test translating the example game"""
    print("\n" + "=" * 70)
    print("TEST: Example Game Translation Workflow")
    print("=" * 70)

    # Step 1: Backup original file
    print("\n[1/5] Backing up original file...")
    if not example_file.exists():
        print(f"[FAIL] Example file not found at {example_file}")
        return False

    shutil.copy2(example_file, backup_file)
    print(f"[OK] Backed up to: {backup_file.name}")

    # Step 2: Count initial translations
    print("\n[2/5] Counting initial translations...")
    initial_count = count_translations(example_file)
    print(f"[OK] Initial translations: {initial_count}")

    if initial_count != 3:
        print(f"[FAIL] WARNING: Expected 3 initial translations, found {initial_count}")

    # Step 3: Run translation
    print("\n[3/5] Running translation...")
    print(f"Command: {python_exe} {translate_script} {example_file}")

    try:
        result = subprocess.run(
            [str(python_exe), str(translate_script), str(example_file)],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes timeout
        )

        if result.returncode != 0:
            print(f"[FAIL] FAILED: Translation failed with exit code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False

        print("[OK] Translation completed successfully")

    except subprocess.TimeoutExpired:
        print("[FAIL] FAILED: Translation timed out after 3 minutes")
        return False
    except Exception as e:
        print(f"[FAIL] FAILED: {e}")
        return False

    # Step 4: Verify new translations
    print("\n[4/5] Verifying translations were added...")
    final_count = count_translations(example_file)
    print(f"[OK] Final translations: {final_count}")

    added = final_count - initial_count
    print(f"[OK] New translations added: {added}")

    if added <= 0:
        print("[FAIL] FAILED: No new translations were added")
        return False

    if final_count < 15:  # Should have at least 15 out of 20 translated
        print(f"[FAIL] WARNING: Expected more translations, only got {final_count}")

    # Step 5: Restore original file
    print("\n[5/5] Restoring original file for next test run...")
    shutil.copy2(backup_file, example_file)
    backup_file.unlink()  # Delete backup
    print("[OK] Original file restored (3 sample translations)")

    # Final summary
    print("\n" + "=" * 70)
    print("[OK] TEST PASSED!")
    print(f"  - Started with: {initial_count} translations")
    print(f"  - Ended with: {final_count} translations")
    print(f"  - Added: {added} new translations")
    print(f"  - File restored to original state")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = test_example_game_translation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Try to restore backup if it exists
        if backup_file.exists():
            print("\nRestoring backup file...")
            shutil.copy2(backup_file, example_file)
            backup_file.unlink()
            print("[OK] Backup restored")

        sys.exit(1)
