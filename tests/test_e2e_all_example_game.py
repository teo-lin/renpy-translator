"""
End-to-End Test: Complete Example Game Translation Pipeline

This test runs the full PowerShell workflow on the Example game:
- 1-config.ps1: Configure game and discover characters
- 2-extract.ps1: Extract .rpy → .parsed.yaml + .tags.json
- 3-translate.ps1: Translate using configured model
- 4-correct.ps1: Post-translation corrections
- 5-merge.ps1: Merge translations back to .rpy

This tests the actual user-facing workflow scripts.
"""

import sys
import subprocess
from pathlib import Path

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "tests"))

from utils import (
    count_translations, backup_file, restore_file,
    cleanup_files, get_rpy_files
)

# Test configuration
example_dir = project_root / "games" / "Example" / "game" / "tl" / "romanian"
model_path = project_root / "models" / "aya23" / "aya-23-8B-Q4_K_M.gguf"


def run_powershell_script(script_name: str, timeout: int = 300) -> tuple[bool, str, str]:
    """
    Run a PowerShell script and return success status, stdout, stderr.

    Args:
        script_name: Name of the .ps1 script (e.g., "1-config.ps1")
        timeout: Timeout in seconds (default 5 minutes)

    Returns:
        Tuple of (success, stdout, stderr)
    """
    script_path = project_root / script_name

    try:
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_root)
        )

        return (result.returncode == 0, result.stdout, result.stderr)

    except subprocess.TimeoutExpired:
        return (False, "", f"Timeout after {timeout}s")
    except Exception as e:
        return (False, "", str(e))


def test_e2e_example_game_translation() -> bool:
    """
    Test the full e2e PowerShell pipeline on the Example game.

    Returns:
        True if test passed, False otherwise
    """
    print("\n" + "=" * 70)
    print("  E2E TEST: Example Game Full Pipeline")
    print("=" * 70)

    # Check if model exists
    if not model_path.exists():
        print(f"\n[SKIP] Model not found: {model_path}")
        print("[INFO] Please download the Aya-23-8B model to run this test")
        return False

    # Get all .rpy files in the Example game
    rpy_files = get_rpy_files(example_dir)

    if not rpy_files:
        print(f"[FAIL] No .rpy files found in {example_dir}")
        return False

    print(f"\nFound {len(rpy_files)} file(s) to translate:")
    for rpy_file in rpy_files:
        print(f"  - {rpy_file.name}")

    # Backup all files
    print("\n[Setup] Backing up original files...")
    backups = []
    for rpy_file in rpy_files:
        backup_path = backup_file(rpy_file)
        backups.append((rpy_file, backup_path))
        print(f"  [OK] Backed up: {rpy_file.name}")

    # Count initial translations
    print("\n[Setup] Counting initial translations...")
    initial_counts = {}
    total_initial = 0
    for rpy_file in rpy_files:
        count = count_translations(rpy_file)
        initial_counts[rpy_file.name] = count
        total_initial += count
        print(f"  {rpy_file.name}: {count} translations")
    print(f"  Total initial translations: {total_initial}")

    try:
        # Step 1: Run 1-config.ps1
        print("\n" + "=" * 70)
        print("[1/5] Running: 1-config.ps1")
        print("=" * 70)
        success, stdout, stderr = run_powershell_script("1-config.ps1", timeout=60)

        if not success:
            print(f"[FAIL] 1-config.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            return False

        print("[OK] Config completed")

        # Step 2: Run 2-extract.ps1
        print("\n" + "=" * 70)
        print("[2/5] Running: 2-extract.ps1")
        print("=" * 70)
        success, stdout, stderr = run_powershell_script("2-extract.ps1", timeout=120)

        if not success:
            print(f"[FAIL] 2-extract.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            return False

        print("[OK] Extract completed")

        # Step 3: Run 3-translate.ps1
        print("\n" + "=" * 70)
        print("[3/5] Running: 3-translate.ps1")
        print("=" * 70)
        success, stdout, stderr = run_powershell_script("3-translate.ps1", timeout=600)  # 10 min for translation

        if not success:
            print(f"[FAIL] 3-translate.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            return False

        print("[OK] Translate completed")

        # Step 4: Run 4-correct.ps1
        print("\n" + "=" * 70)
        print("[4/5] Running: 4-correct.ps1")
        print("=" * 70)
        success, stdout, stderr = run_powershell_script("4-correct.ps1", timeout=300)

        if not success:
            print(f"[FAIL] 4-correct.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            return False

        print("[OK] Correct completed")

        # Step 5: Run 5-merge.ps1
        print("\n" + "=" * 70)
        print("[5/5] Running: 5-merge.ps1")
        print("=" * 70)
        success, stdout, stderr = run_powershell_script("5-merge.ps1", timeout=120)

        if not success:
            print(f"[FAIL] 5-merge.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            return False

        print("[OK] Merge completed")

        # Verify new translations
        print("\n" + "=" * 70)
        print("[Verify] Checking translations were added...")
        print("=" * 70)

        final_counts = {}
        total_final = 0
        total_added = 0

        for rpy_file in rpy_files:
            count = count_translations(rpy_file)
            final_counts[rpy_file.name] = count
            total_final += count
            added = count - initial_counts[rpy_file.name]
            total_added += added
            print(f"  {rpy_file.name}: {initial_counts[rpy_file.name]} → {count} (+{added})")

        print(f"  Total final translations: {total_final} (+{total_added})")

        # Final summary
        print("\n" + "=" * 70)
        if total_added > 0:
            print("[OK] TEST PASSED!")
            print(f"  - Files processed: {len(rpy_files)}")
            print(f"  - Initial translations: {total_initial}")
            print(f"  - Final translations: {total_final}")
            print(f"  - New translations added: {total_added}")
            print(f"  - Pipeline: Config → Extract → Translate → Correct → Merge ✓")
            print("=" * 70)
            return True
        else:
            print("[FAIL] TEST FAILED!")
            print("  - No new translations were added")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Always restore original files
        print("\n" + "=" * 70)
        print("[Cleanup] Restoring original files...")
        print("=" * 70)

        for rpy_file, backup_path in backups:
            if backup_path.exists():
                restore_file(rpy_file, backup_path)
                print(f"  [OK] Restored: {rpy_file.name}")

        # Clean up generated files
        print("\n[Cleanup] Removing generated files...")
        for rpy_file in rpy_files:
            cleanup_files([
                rpy_file.parent / f"{rpy_file.stem}.parsed.yaml",
                rpy_file.parent / f"{rpy_file.stem}.tags.json",
                rpy_file.parent / f"{rpy_file.stem}.translated.rpy",
            ])

        cleanup_files([
            example_dir / "characters.json",
            example_dir.parent.parent / "characters.json"  # May be in game root
        ])

        print("[OK] Cleanup completed")


if __name__ == "__main__":
    try:
        success = test_e2e_example_game_translation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
