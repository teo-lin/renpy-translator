"""
End-to-End Test: Full Modular Pipeline with MADLAD-400-3B Model

This test runs the complete modular translation pipeline with the actual MADLAD-400 model:
- Step 1: Config (discover characters from .rpy files → characters.json)
- Step 2: Extract (.rpy → .parsed.yaml + .tags.json)
- Step 3: Translate (ModularBatchTranslator + MADLAD400Translator)
- Step 4: Merge (.parsed.yaml + .tags.json → .translated.rpy)
- Step 5: Validate and cleanup

Usage:
    python tests/test_e2e_madlad.py
    python tests/test_e2e_madlad.py --file 1    # Process specific file by number
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Tuple
import argparse

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "translators"))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "tests"))

from extract import RenpyExtractor
from merger import RenpyMerger
from madlad400_translator import MADLAD400Translator
from translate_modular import ModularBatchTranslator
from tests.utils import (
    discover_characters, count_translations, backup_file,
    restore_file, cleanup_files, validate_rpy_structure, get_rpy_files
)

# Test configuration
example_dir = project_root / "games" / "Example" / "game" / "tl" / "romanian"
model_path = project_root / "models" / "madlad400-3b-mt-GGUF" / "madlad400-3b-mt-q4_k_m.gguf"


def test_single_file_e2e(rpy_file: Path, character_map: dict) -> Tuple[bool, dict]:
    """
    Test the full e2e pipeline on a single .rpy file with MADLAD-400 model.

    Args:
        rpy_file: Path to .rpy file to test
        character_map: Character mapping dictionary

    Returns:
        Tuple of (success: bool, stats: dict)
    """
    print("\n" + "=" * 70)
    print(f"TEST: {rpy_file.name}")
    print("=" * 70)

    # File paths
    backup_path = rpy_file.with_suffix(".rpy.backup")
    parsed_yaml = rpy_file.parent / f"{rpy_file.stem}.parsed.yaml"
    tags_json = rpy_file.parent / f"{rpy_file.stem}.tags.json"
    translated_rpy = rpy_file.parent / f"{rpy_file.stem}.translated.rpy"

    stats = {
        'file': rpy_file.name,
        'initial_count': 0,
        'translations_added': 0,
        'final_count': 0,
        'success': False
    }

    # Step 1: Backup original file
    print("\n[1/5] Backing up original file...")
    if not rpy_file.exists():
        print(f"[FAIL] File not found at {rpy_file}")
        return False, stats

    backup_path = backup_file(rpy_file)
    print(f"[OK] Backed up to: {backup_path.name}")

    # Count initial translations
    initial_count = count_translations(rpy_file)
    stats['initial_count'] = initial_count
    print(f"[OK] Initial translations: {initial_count}")

    try:
        # Step 2: Extract
        print("\n[2/5] Extracting .rpy file...")

        extractor = RenpyExtractor(character_map)
        parsed_blocks, tags_file = extractor.extract_file(
            rpy_file,
            target_language='romanian',
            source_language='english'
        )

        # Save parsed YAML
        with open(parsed_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # Save tags JSON
        with open(tags_json, 'w', encoding='utf-8') as f:
            json.dump(tags_file, f, indent=2, ensure_ascii=False)

        print(f"[OK] Extracted {len(parsed_blocks)} blocks")
        print(f"[OK] Created: {parsed_yaml.name}")
        print(f"[OK] Created: {tags_json.name}")

        # Step 3: Translate with MADLAD-400 model
        print("\n[3/5] Translating with MADLAD-400 model...")
        print(f"[INFO] Loading model from: {model_path.name}")

        # Check if model exists
        if not model_path.exists():
            print(f"[FAIL] Model not found: {model_path}")
            print("[INFO] Please download the MADLAD-400-3B model first")
            return False, stats

        # Initialize MADLAD-400 translator
        translator = MADLAD400Translator(
            model_path=str(model_path),
            target_language='Romanian'
        )

        # Create batch translator
        batch_translator = ModularBatchTranslator(
            translator=translator,
            characters=character_map,
            target_lang_code='ro',
            context_before=3,
            context_after=1
        )

        # Translate file
        translation_stats = batch_translator.translate_file(
            parsed_yaml_path=parsed_yaml,
            tags_json_path=tags_json,
            output_yaml_path=None  # Overwrite in place
        )

        stats['translations_added'] = translation_stats['translated']
        print(f"[OK] Translated {translation_stats['translated']} blocks")
        print(f"[OK] Skipped {translation_stats['skipped']} blocks (already translated)")
        print(f"[OK] Failed {translation_stats['failed']} blocks")

        # Step 4: Merge
        print("\n[4/5] Merging YAML + JSON back to .rpy...")

        merger = RenpyMerger()
        success = merger.merge_file(
            parsed_yaml_path=parsed_yaml,
            tags_json_path=tags_json,
            output_rpy_path=translated_rpy,
            validate=True
        )

        if not success:
            print("[FAIL] Merge failed or validation errors found")
            if merger.validation_errors:
                print("\nValidation errors:")
                print(merger.get_validation_report())
            return False, stats

        print(f"[OK] Merge completed successfully")
        print(f"[OK] Created: {translated_rpy.name}")

        # Step 5: Validate output
        print("\n[5/5] Validating output...")

        if not translated_rpy.exists():
            print("[FAIL] Translated file was not created")
            return False, stats

        final_count = count_translations(translated_rpy)
        stats['final_count'] = final_count
        print(f"[OK] Final translations in output: {final_count}")

        # Verify we added translations
        expected_count = initial_count + stats['translations_added']
        if final_count < expected_count:
            print(f"[WARN] Expected at least {expected_count} translations, got {final_count}")

        # Validate structure
        validation_results = validate_rpy_structure(translated_rpy)
        all_checks_passed = True

        for check_name, passed in validation_results.items():
            if passed:
                print(f"[OK] {check_name.replace('_', ' ').title()} ✓")
            else:
                print(f"[WARN] {check_name.replace('_', ' ').title()} ✗")

        # Restore original file and cleanup
        print("\n[Cleanup] Restoring original file and cleaning up...")

        restore_file(rpy_file, backup_path)
        print("[OK] Original file restored")

        # Clean up all generated files
        cleanup_files([parsed_yaml, tags_json, translated_rpy])
        print("[OK] All generated files cleaned up")

        # Final summary
        print("\n" + "=" * 70)
        print("[OK] TEST PASSED!")
        print(f"  - Initial translations: {initial_count}")
        print(f"  - Translations added: {stats['translations_added']}")
        print(f"  - Final translations: {final_count}")
        print(f"  - Pipeline: Config → Extract → Translate (MADLAD-400) → Merge ✓")
        print("=" * 70)

        stats['success'] = True
        return True, stats

    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Try to restore and cleanup
        try:
            restore_file(rpy_file, backup_path)
            cleanup_files([parsed_yaml, tags_json, translated_rpy])
            print("\n[OK] Cleanup completed")
        except:
            pass

        return False, stats


def test_e2e_pipeline() -> bool:
    """
    Test the full e2e pipeline with MADLAD-400 model.

    Returns:
        True if test passed, False otherwise
    """
    print("\n" + "=" * 70)
    print("  E2E TEST: MADLAD-400-3B Modular Pipeline")
    print("=" * 70)

    # Check if model exists
    if not model_path.exists():
        print(f"\n[SKIP] Model not found: {model_path}")
        print("[INFO] Please download the MADLAD-400-3B model to run this test")
        print("[INFO] Expected location: models/madlad400-3b-mt-GGUF/madlad400-3b-mt-q4_k_m.gguf")
        return False

    # Get .rpy files to test
    rpy_files = get_rpy_files(example_dir)

    if not rpy_files:
        print(f"[FAIL] No .rpy files found in {example_dir}")
        return False

    # Parse arguments for file selection
    parser = argparse.ArgumentParser(description="E2E test with MADLAD-400 model")
    parser.add_argument("--file", type=int, help="Process specific file by number (1-based index)")
    args = parser.parse_args()

    if args.file is not None:
        file_num = args.file
        if 1 <= file_num <= len(rpy_files):
            files_to_process = [rpy_files[file_num - 1]]
            print(f"\nProcessing file {file_num}: {files_to_process[0].name}")
        else:
            print(f"[FAIL] Invalid file number: {file_num}. Must be 1-{len(rpy_files)}")
            return False
    else:
        # Default: process first file only (for speed)
        files_to_process = rpy_files[:1]
        print(f"\nProcessing first file: {files_to_process[0].name}")
        print(f"[INFO] Use --file N to test a specific file (1-{len(rpy_files)})")

    # Step 1: Generate character map
    print("\n[1/2] Config: Discovering and generating character map...")
    characters_json = example_dir / "characters.json"
    game_path = example_dir.parent.parent

    character_map = discover_characters(example_dir, game_path)

    # Save characters.json
    with open(characters_json, 'w', encoding='utf-8') as f:
        json.dump(character_map, f, indent=2, ensure_ascii=False)

    print(f"[OK] Generated characters.json with {len(character_map)} characters")

    # Step 2: Test each file
    print("\n[2/2] Running e2e tests...")
    all_results = []
    all_stats = []

    for i, rpy_file in enumerate(files_to_process, start=1):
        print(f"\n{'=' * 70}")
        print(f"File {i}/{len(files_to_process)}: {rpy_file.name}")
        print(f"{'=' * 70}")

        success, stats = test_single_file_e2e(rpy_file, character_map)
        all_results.append(success)
        all_stats.append(stats)

    # Clean up characters.json
    cleanup_files([characters_json])
    print(f"\n[Cleanup] Removed: {characters_json.name}")

    # Print summary
    print("\n" + "=" * 70)
    print("OVERALL TEST SUMMARY")
    print("=" * 70)

    passed = sum(all_results)
    failed = len(all_results) - passed

    print(f"\nFiles tested: {len(all_results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if all_stats:
        print("\nDetailed Results:")
        for stats in all_stats:
            status = "[PASS]" if stats['success'] else "[FAIL]"
            print(f"  {status} {stats['file']}")
            print(f"         Initial: {stats['initial_count']} | "
                  f"Added: {stats['translations_added']} | "
                  f"Final: {stats['final_count']}")

    print("\n" + "=" * 70)
    if all(all_results):
        print("[OK] ALL TESTS PASSED!")
        print("=" * 70)
        return True
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = test_e2e_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
