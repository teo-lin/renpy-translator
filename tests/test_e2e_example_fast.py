"""
End-to-End Test: Complete Example Game Translation Pipeline (Fast variant)

Same pipeline as test_e2e_example.py but uses NLLB-200 (39s for 70 blocks,
no GPU VRAM pressure) and patterns-only correction to avoid loading a second
LLM. Runs ~4-5x faster than the aya23 + LLM-correction variant.

- 1-config.ps1: Configure game and discover characters
- 2-extract.ps1: Extract .rpy -> .parsed.yaml + .tags.yaml
- 3-translate.ps1: Translate using NLLB-200
- 4-correct.ps1: Pattern-based corrections only (no LLM)
- 5-merge.ps1: Merge translations back to .rpy
"""

import sys
import subprocess
from pathlib import Path
import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "tests"))

from utils import (
    count_translations, backup_file, restore_file,
    cleanup_files, get_rpy_files
)

# Test configuration
game_name = "Example"
game_path = project_root / "games" / game_name
example_dir = game_path / "game" / "tl" / "romanian"
model_path = project_root / "models" / "nllb200"

target_language_code = "ro"
target_language_name = "Romanian"
target_language_folder = "romanian"
model_key = "nllb200"


def run_powershell_script(script_name: str, args: list = None, timeout: int = 300) -> tuple[bool, str, str]:
    if args is None:
        args = []

    script_path = project_root / script_name

    try:
        command = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + args
        result = subprocess.run(
            command,
            cwd=str(project_root),
            text=True,
            timeout=timeout,
        )
        success = result.returncode == 0
        return success, None, None

    except subprocess.TimeoutExpired:
        return (False, "", f"Timeout after {timeout}s")
    except Exception as e:
        return (False, "", str(e))


@pytest.mark.e2e
@pytest.mark.slow
def test_e2e_example_game_translation_fast():
    """
    Full e2e pipeline on the Example game using NLLB-200 + patterns-only
    correction. Validates pipeline correctness without the LLM correction
    overhead.
    """
    print("\n" + "=" * 70)
    print("  E2E TEST: Example Game Full Pipeline (NLLB-200, fast)")
    print("=" * 70)

    if not model_path.exists():
        print(f"\n[SKIP] Model not found: {model_path}")
        pytest.skip(f"Model not found: {model_path}")

    rpy_files = get_rpy_files(example_dir)

    if not rpy_files:
        print(f"[FAIL] No .rpy files found in {example_dir}")
        assert False, "Test step failed"

    print(f"\nFound {len(rpy_files)} file(s) to translate:")
    for rpy_file in rpy_files:
        print(f"  - {rpy_file.name}")

    print("\n[Setup] Backing up original files...")
    backups = []
    for rpy_file in rpy_files:
        backup_path = backup_file(rpy_file)
        backups.append((rpy_file, backup_path))
        print(f"  [OK] Backed up: {rpy_file.name}")

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
        # Step 1: Configure
        print("\n" + "=" * 70)
        print("[1/5] Running: 1-config.ps1")
        print("=" * 70)
        success, _, stderr = run_powershell_script("1-config.ps1", args=[
            "-GamePath", str(game_path),
            "-Language", target_language_code,
            "-Model", model_key,
        ], timeout=60)
        if not success:
            print(f"[FAIL] 1-config.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            assert False, "Test step failed"
        print("[OK] Config completed")

        # Step 2: Extract
        print("\n" + "=" * 70)
        print("[2/5] Running: 2-extract.ps1")
        print("=" * 70)
        success, _, stderr = run_powershell_script("2-extract.ps1", args=[
            "-GameName", game_name,
            "-All",
        ], timeout=120)
        if not success:
            print(f"[FAIL] 2-extract.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            assert False, "Test step failed"
        print("[OK] Extract completed")

        # Step 3: Translate (NLLB-200, ~40s for Example game)
        print("\n" + "=" * 70)
        print("[3/5] Running: 3-translate.ps1 (NLLB-200)")
        print("=" * 70)
        success, _, stderr = run_powershell_script("3-translate.ps1", args=[
            "-GameName", game_name,
            "-All",
            "-Model", model_key,
        ], timeout=180)
        if not success:
            print(f"[FAIL] 3-translate.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            assert False, "Test step failed"
        print("[OK] Translate completed")

        # Step 4: Correct (patterns only — no LLM load)
        print("\n" + "=" * 70)
        print("[4/5] Running: 4-correct.ps1 (Patterns Only)")
        print("=" * 70)
        success, _, stderr = run_powershell_script("4-correct.ps1", args=[
            "-GameName", game_name,
            "-LanguageName", target_language_code,
            "-ModeName", "Patterns Only",
            "-Yes",
        ], timeout=60)
        if not success:
            print(f"[FAIL] 4-correct.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            assert False, "Test step failed"
        print("[OK] Correct completed")

        # Step 5: Merge
        print("\n" + "=" * 70)
        print("[5/5] Running: 5-merge.ps1")
        print("=" * 70)
        success, _, stderr = run_powershell_script("5-merge.ps1", args=[
            "-GameName", game_name,
            "-All",
        ], timeout=120)
        if not success:
            print(f"[FAIL] 5-merge.ps1 failed")
            if stderr:
                print(f"STDERR: {stderr}")
            assert False, "Test step failed"
        print("[OK] Merge completed")

        # Verify
        print("\n" + "=" * 70)
        print("[Verify] Checking translations were added...")
        print("=" * 70)

        translated_rpy_files = [
            rpy_file.parent / f"{rpy_file.stem}.translated.rpy"
            for rpy_file in rpy_files
        ]

        total_final = 0
        total_added = 0
        for translated_rpy_file in translated_rpy_files:
            count = count_translations(translated_rpy_file)
            total_final += count
            total_added += count
            print(f"  {translated_rpy_file.name}: 0 -> {count} (+{count})")

        print(f"  Total final translations: {total_final} (+{total_added})")

        print("\n" + "=" * 70)
        if total_added > 0:
            print("[OK] TEST PASSED!")
            print(f"  - Files processed: {len(rpy_files)}")
            print(f"  - Initial translations: {total_initial}")
            print(f"  - Final translations: {total_final}")
            print(f"  - New translations added: {total_added}")
            print(f"  - Pipeline: Config -> Extract -> Translate -> Correct -> Merge [OK]")
            print("=" * 70)
        else:
            print("[FAIL] TEST FAILED! No new translations were added.")
            print("=" * 70)
            assert False, "Test step failed"

    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        assert False, "Test step failed"

    finally:
        print("\n" + "=" * 70)
        print("[Cleanup] Restoring original files...")
        print("=" * 70)
        for rpy_file, backup_path in backups:
            if backup_path.exists():
                restore_file(rpy_file, backup_path)
                print(f"  [OK] Restored: {rpy_file.name}")

        print("\n[Cleanup] Removing generated files...")
        for rpy_file in rpy_files:
            cleanup_files([
                rpy_file.parent / f"{rpy_file.stem}.parsed.yaml",
                rpy_file.parent / f"{rpy_file.stem}.tags.yaml",
                rpy_file.parent / f"{rpy_file.stem}.translated.rpy",
                rpy_file.parent / f"{rpy_file.stem}.corrections.txt",
            ])

        cleanup_files([
            example_dir / "characters.yaml",
            example_dir.parent.parent / "characters.yaml",
        ])

        print("[OK] Cleanup completed")


if __name__ == "__main__":
    try:
        test_e2e_example_game_translation_fast()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
