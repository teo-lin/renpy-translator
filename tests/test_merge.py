"""
Test the merge operation on the Example game

This test runs the full modular pipeline on the Example game:
- Step 1: Backup original file(s)
- Step 2: Setup (create characters.json if needed)
- Step 3: Extract (.rpy → .parsed.yaml + .tags.json)
- Step 4: Translate (fill in missing translations)
- Step 5: Merge (.parsed.yaml + .tags.json → .translated.rpy)
- Step 6: Verify output and cleanup

Usage:
    python tests/test_merge.py              # Process all .rpy files (default)
    python tests/test_merge.py --file 1     # Process specific file by number
"""

import sys
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple
import argparse

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from extraction import RenpyExtractor
from merger import RenpyMerger

# Project paths
project_root = Path(__file__).parent.parent
example_dir = project_root / "games" / "Example" / "game" / "tl" / "romanian"
python_exe = project_root / "venv" / "Scripts" / "python.exe"

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Test merge operation on Example game.")
parser.add_argument("--model_script", type=str, required=False, help="Path to the Python translation script to use (optional).")
parser.add_argument("--language", type=str, default="ro", help="Target language code (e.g., 'ro').")
parser.add_argument("--file", type=int, help="Process specific file by number (1-based index). Default: process all files")
args = parser.parse_args()

target_language = args.language


def get_rpy_files() -> List[Path]:
    """Get list of .rpy files in the Example game directory"""
    if not example_dir.exists():
        print(f"[FAIL] Example directory not found at {example_dir}")
        return []

    rpy_files = sorted(example_dir.glob("*.rpy"))
    # Exclude backup and generated files
    rpy_files = [f for f in rpy_files if not f.name.endswith('.backup')
                 and not f.name.endswith('.translated.rpy')]

    return rpy_files


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


def test_single_file(rpy_file: Path, character_map: dict) -> Tuple[bool, dict]:
    """
    Test the merge pipeline on a single .rpy file.

    Returns:
        Tuple of (success: bool, stats: dict)
    """
    print("\n" + "=" * 70)
    print(f"TEST: {rpy_file.name}")
    print("=" * 70)

    # File paths
    backup_file = rpy_file.with_suffix(".rpy.backup")
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
    print("\n[1/6] Backing up original file...")
    if not rpy_file.exists():
        print(f"[FAIL] File not found at {rpy_file}")
        return False, stats

    shutil.copy2(rpy_file, backup_file)
    print(f"[OK] Backed up to: {backup_file.name}")

    # Count initial translations
    initial_count = count_translations(rpy_file)
    stats['initial_count'] = initial_count
    print(f"[OK] Initial translations: {initial_count}")

    try:
        # Step 2: Character map already provided
        print("\n[2/6] Using provided character map...")
        print(f"[OK] Character map has {len(character_map)} characters")

        # Step 3: Extract
        print("\n[3/6] Extracting .rpy file...")

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

        # Step 4: Translate (manually fill in some translations)
        print("\n[4/6] Adding sample translations to YAML...")

        # Add translations to untranslated blocks
        translations_added = 0
        for block_id, block in parsed_blocks.items():
            if block.get('type') == 'separator':
                continue

            # Only translate blocks that don't have Romanian text
            if 'ro' in block and (not block['ro'] or block['ro'].strip() == ''):
                en_text = block.get('en', '')

                # Add simple test translations
                # In a real scenario, this would come from the translation model
                if 'new student' in en_text.lower():
                    block['ro'] = 'Oh, salut! Ești studentul nou?'
                    translations_added += 1
                elif 'transferred here' in en_text.lower():
                    block['ro'] = 'Da, tocmai m-am transferat aici. Încântat de cunoștință!'
                    translations_added += 1
                elif 'show you around' in en_text.lower():
                    block['ro'] = 'Sunt Sarah. Lasă-mă să-ți arăt campusul.'
                    translations_added += 1
                elif 'wonderful' in en_text.lower():
                    block['ro'] = 'Ar fi {b}minunat{/b}, mulțumesc!'
                    translations_added += 1
                elif 'library' in en_text.lower() and 'studying' in en_text.lower():
                    block['ro'] = 'Aceasta este biblioteca. Vei petrece mult timp aici studiind.'
                    translations_added += 1

                # Stop after adding 5 sample translations
                if translations_added >= 5:
                    break

        # Save updated YAML
        with open(parsed_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        stats['translations_added'] = translations_added
        print(f"[OK] Added {translations_added} sample translations")

        # Step 5: Merge
        print("\n[5/6] Merging YAML + JSON back to .rpy...")

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
            return False

        print(f"[OK] Merge completed successfully")
        print(f"[OK] Created: {translated_rpy.name}")

        # Verify output
        if not translated_rpy.exists():
            print("[FAIL] Translated file was not created")
            return False, stats

        final_count = count_translations(translated_rpy)
        stats['final_count'] = final_count
        print(f"[OK] Final translations in output: {final_count}")

        expected_count = initial_count + translations_added
        if final_count < expected_count:
            print(f"[FAIL] Expected at least {expected_count} translations, got {final_count}")
            return False, stats

        # Verify structure
        output_content = translated_rpy.read_text(encoding='utf-8')

        checks = [
            ('translate romanian', 'Translation statements'),
            ('translate romanian strings:', 'Strings section'),
            ('{color=', 'Color tags preserved'),
            ('[player_name]', 'Variables preserved'),
            ('{b}', 'Bold tags preserved'),
        ]

        all_checks_passed = True
        for check_str, check_name in checks:
            if check_str in output_content:
                print(f"[OK] {check_name} ✓")
            else:
                print(f"[FAIL] {check_name} ✗")
                all_checks_passed = False

        if not all_checks_passed:
            print("[FAIL] Some structure checks failed")
            return False, stats

        # Step 6: Restore original file and cleanup
        print("\n[6/6] Restoring original file and cleaning up...")

        shutil.copy2(backup_file, rpy_file)
        backup_file.unlink()
        print("[OK] Original file restored")

        # Clean up all generated files
        cleanup_files = [
            parsed_yaml,
            tags_json,
            translated_rpy
        ]

        for cleanup_file in cleanup_files:
            if cleanup_file.exists():
                cleanup_file.unlink()
                print(f"[OK] Removed: {cleanup_file.name}")

        print("[OK] All generated files cleaned up")

        # Final summary
        print("\n" + "=" * 70)
        print("[OK] TEST PASSED!")
        print(f"  - Initial translations: {initial_count}")
        print(f"  - Translations added: {translations_added}")
        print(f"  - Final translations: {final_count}")
        print(f"  - Pipeline steps: Extract → Translate → Merge ✓")
        print(f"  - All generated files cleaned up ✓")
        print("=" * 70)

        stats['success'] = True
        return True, stats

    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Try to restore and cleanup
        try:
            if backup_file.exists():
                shutil.copy2(backup_file, rpy_file)
                backup_file.unlink()
                print("\n[OK] Backup restored")

            for cleanup_file in [parsed_yaml, tags_json, translated_rpy]:
                if cleanup_file.exists():
                    cleanup_file.unlink()
        except:
            pass

        return False, stats


def test_merge_pipeline(files_to_process: List[Path]) -> bool:
    """
    Test the merge pipeline on one or more files.

    Args:
        files_to_process: List of .rpy files to test

    Returns:
        True if all tests passed, False otherwise
    """
    print("\n" + "=" * 70)
    print(f"TEST: Merge Pipeline on {len(files_to_process)} file(s)")
    print("=" * 70)

    # Step 1: Setup characters.json (shared for all files)
    print("\n[Setup] Creating characters.json...")
    characters_json = example_dir / "characters.json"

    character_map = {
        'narrator': {
            'name': 'Narrator',
            'gender': 'neutral',
            'type': 'narrator',
            'description': 'Story narrator'
        },
        'mc': {
            'name': 'Player',
            'gender': 'male',
            'type': 'protagonist',
            'description': 'Main character (player)'
        },
        'sarah': {
            'name': 'Sarah',
            'gender': 'female',
            'type': 'main',
            'description': 'Student guide'
        },
        'alex': {
            'name': 'Alex',
            'gender': 'neutral',
            'type': 'side',
            'description': 'Sarah\'s friend'
        }
    }

    # Save characters.json
    with open(characters_json, 'w', encoding='utf-8') as f:
        json.dump(character_map, f, indent=2, ensure_ascii=False)

    print(f"[OK] Created characters.json with {len(character_map)} characters")

    # Test each file
    all_results = []
    all_stats = []

    for i, rpy_file in enumerate(files_to_process, start=1):
        print(f"\n{'=' * 70}")
        print(f"File {i}/{len(files_to_process)}: {rpy_file.name}")
        print(f"{'=' * 70}")

        success, stats = test_single_file(rpy_file, character_map)
        all_results.append(success)
        all_stats.append(stats)

    # Clean up characters.json
    if characters_json.exists():
        characters_json.unlink()
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
        # Get list of available .rpy files
        rpy_files = get_rpy_files()

        if not rpy_files:
            print("[FAIL] No .rpy files found in Example game directory")
            sys.exit(1)

        # Determine which files to process
        if args.file is not None:
            # Process specific file by number
            file_num = args.file
            if 1 <= file_num <= len(rpy_files):
                files_to_process = [rpy_files[file_num - 1]]
                print(f"\nProcessing file {file_num}: {files_to_process[0].name}")
            else:
                print(f"[FAIL] Invalid file number: {file_num}. Must be 1-{len(rpy_files)}")
                print(f"\nAvailable files:")
                for i, f in enumerate(rpy_files, start=1):
                    print(f"  [{i}] {f.name}")
                sys.exit(1)
        else:
            # Default: process all files
            files_to_process = rpy_files
            print(f"\nProcessing all {len(files_to_process)} file(s)")

        # Run the test
        success = test_merge_pipeline(files_to_process)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
