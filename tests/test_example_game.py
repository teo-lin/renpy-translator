import sys
import shutil
import subprocess
from pathlib import Path
import argparse # Import argparse

# Project paths
project_root = Path(__file__).parent.parent
example_file = project_root / "games" / "Example" / "game" / "tl" / "romanian" / "Cell01_Academy.rpy"
backup_file = example_file.with_suffix(".rpy.backup")
python_exe = project_root / "venv" / "Scripts" / "python.exe"

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Test example game translation workflow.")
parser.add_argument("--model_script", type=str, required=True, help="Path to the Python translation script to use.")
parser.add_argument("--language", type=str, required=True, help="Target language code (e.g., 'ro').")
args = parser.parse_args()

# Use the model script from arguments
translate_script = Path(args.model_script)
target_language = args.language

# --- DEBUGGING PRINTS ---
print(f"\nDEBUG: sys.argv = {sys.argv}")
print(f"DEBUG: args.model_script = {args.model_script}")
print(f"DEBUG: translate_script (resolved Path) = {translate_script}")
print(f"DEBUG: translate_script.exists() = {translate_script.exists()}")
print(f"DEBUG: python_exe = {python_exe}")
# --- END DEBUGGING PRINTS ---

def count_translations(file_path):
    """Count how many non-empty translations exist in the file"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    count = 0
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip comments
        if not stripped or stripped.startswith('#'):
            continue

        # Skip "old" lines (source text, not translations)
        if stripped.startswith('old '):
            continue

        # Count character dialogue lines with non-empty translations
        # Format: character_var "translation text"
        if '"' in stripped and '""' not in stripped:
            # Check if it's a character line (starts with identifier) or "new" line
            if stripped.startswith('new ') or (not stripped.startswith('translate') and ' "' in stripped):
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

    if initial_count != 4:
        print(f"[FAIL] WARNING: Expected 4 initial translations, found {initial_count}")

    # Step 3: Run translation
    print("\n[3/5] Running translation...")
    print(f"Command: {python_exe} {translate_script} {example_file} --language {target_language}")

    try:
        result = subprocess.run(
            [str(python_exe), str(translate_script), str(example_file), "--language", target_language],
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

    # Step 5: Restore original file and cleanup
    print("\n[5/5] Restoring original file and cleaning up...")
    shutil.copy2(backup_file, example_file)
    backup_file.unlink()  # Delete backup
    print("[OK] Original file restored")

    # Clean up any generated files
    example_dir = example_file.parent
    cleanup_files = [
        example_dir / "Cell01_Academy.parsed.yaml",
        example_dir / "Cell01_Academy.tags.json",
        example_dir / "Cell01_Academy.translated.rpy",
        example_dir / "characters.json"
    ]

    for cleanup_file in cleanup_files:
        if cleanup_file.exists():
            cleanup_file.unlink()
            print(f"[OK] Removed: {cleanup_file.name}")

    print("[OK] Example game restored to original state")

    # Final summary
    print("\n" + "=" * 70)
    print("[OK] TEST PASSED!")
    print(f"  - Started with: {initial_count} translations")
    print(f"  - Ended with: {final_count} translations")
    print(f"  - Added: {added} new translations")
    print(f"  - All generated files cleaned up")
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

        # Try to restore backup and cleanup if it exists
        if backup_file.exists():
            print("\nRestoring backup file and cleaning up...")
            shutil.copy2(backup_file, example_file)
            backup_file.unlink()
            print("[OK] Backup restored")

            # Clean up any generated files
            example_dir = example_file.parent
            cleanup_files = [
                example_dir / "Cell01_Academy.parsed.yaml",
                example_dir / "Cell01_Academy.tags.json",
                example_dir / "Cell01_Academy.translated.rpy",
                example_dir / "characters.json"
            ]

            for cleanup_file in cleanup_files:
                if cleanup_file.exists():
                    cleanup_file.unlink()
                    print(f"[OK] Removed: {cleanup_file.name}")

        sys.exit(1)
