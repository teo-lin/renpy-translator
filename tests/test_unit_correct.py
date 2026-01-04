"""
Unit test for the correction script (scripts/correct.py).

This test focuses on the PatternBasedCorrector to ensure that correction
rules are applied correctly to a file, testing the logic in isolation
without requiring a live model.
"""

import sys
import yaml
from pathlib import Path
import tempfile
import shutil

# Add src and scripts directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

# The script being tested is correct.py, but we import its classes
from correct import PatternBasedCorrector, CombinedCorrector, RenpyFileCorrector

# --- Test Data ---

# A simple set of correction rules for testing
TEST_CORRECTIONS_CONTENT = {
    "protected_words": ["Ceau"],
    "exact_replacements": {
        " ,": ",",
        " !": "!",
        " ?": "?"
    },
    "verb_conjugations": [
        {
            "pattern": "să merge",
            "replacement": "să meargă"
        }
    ]
}

# Dummy .rpy file content with correctable errors
TEST_RPY_CONTENT = """
# game/script.rpy:10
translate romanian dialogue_1:
    # s "Hello , how are you ?"
    s "Salut , ce mai faci ?"

# game/script.rpy:20
translate romanian dialogue_2:
    # s "We should go to the store ."
    s "Ar trebui să merge la magazin ."

# game/script.rpy:30
translate romanian dialogue_3:
    # s "Ceau! What's up !"
    s "Ceau ! Ce mai faci !"
"""

# Expected content after corrections are applied
EXPECTED_RPY_CONTENT = """
# game/script.rpy:10
translate romanian dialogue_1:
    # s "Hello , how are you ?"
    s "Salut, ce mai faci?"

# game/script.rpy:20
translate romanian dialogue_2:
    # s "We should go to the store ."
    s "Ar trebui să meargă la magazin ."

# game/script.rpy:30
translate romanian dialogue_3:
    # s "Ceau! What's up !"
    s "Ceau ! Ce mai faci!"
"""

def test_pattern_correction_flow():
    """
    Tests the PatternBasedCorrector flow by running it on a temporary
    .rpy file with a temporary set of correction rules.
    """
    print("\n" + "=" * 70)
    print("TEST: Pattern-Based Correction Flow")
    print("=" * 70)

    # Create a temporary directory for test files
    temp_dir = Path(tempfile.mkdtemp(prefix="test_correct_"))
    print(f"[SETUP] Created temporary directory: {temp_dir}")

    try:
        # 1. Create handcrafted input files
        corrections_yaml_path = temp_dir / "test_corrections.yaml"
        test_rpy_path = temp_dir / "test_script.rpy"

        with open(corrections_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(TEST_CORRECTIONS_CONTENT, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"[SETUP] Created: {corrections_yaml_path.name}")

        with open(test_rpy_path, 'w', encoding='utf-8') as f:
            f.write(TEST_RPY_CONTENT)
        print(f"[SETUP] Created: {test_rpy_path.name}")

        # 2. Instantiate correctors
        print("\n[RUN] Instantiating and running correctors...")
        pattern_corrector = PatternBasedCorrector(str(corrections_yaml_path))
        # We only need the pattern corrector for this test
        combined_corrector = CombinedCorrector(patterns_corrector=pattern_corrector, llm_corrector=None)
        file_corrector = RenpyFileCorrector(corrector=combined_corrector, dry_run=False)
        print("[OK] Correctors instantiated.")

        # 3. Run the correction process on the dummy file
        result_stats = file_corrector.correct_file(test_rpy_path)
        print("[OK] Correction process finished.")

        # 4. Assertions
        print("\n[ASSERT] Verifying correction results...")

        # Assert statistics returned by the corrector
        assert result_stats['corrections'] > 0, "Corrector should have made changes."
        print(f"[OK] Corrector reported {result_stats['corrections']} changes.")

        # Read the content of the modified file
        actual_content = test_rpy_path.read_text(encoding='utf-8').strip().replace('\r\n', '\n')
        expected_content = EXPECTED_RPY_CONTENT.strip().replace('\r\n', '\n')

        # Assert that the content matches the expected corrected version
        assert actual_content == expected_content, "Output RPY content does not match expected content."
        print("[OK] Output content matches expected golden file.")
        
        # Verify that the protected word "Ceau" was not affected by the space rule
        assert "Ceau !" in actual_content, "Protected word rule was not respected."
        print("[OK] Protected word 'Ceau' was correctly handled.")

        print("\n[PASS] Correction flow test completed successfully!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed with an exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 5. Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n[CLEANUP] Removed temporary directory: {temp_dir}")

def main():
    """Run the test suite."""
    success = test_pattern_correction_flow()
    if success:
        print("\n" + "="*70)
        print("[OK] ALL CORRECTION TESTS PASSED")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("[FAIL] CORRECTION TESTS FAILED")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
