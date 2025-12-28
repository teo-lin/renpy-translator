"""
Test Ren'Py tag extraction and restoration logic
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import the tag extractor from scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from renpy_utils import RenpyTagExtractor
from renpy_utils import RenpyTranslationParser


def test_tag_extraction():
    """Test tag extraction from various Ren'Py formatted strings"""

    test_cases = [
        # (original, expected_clean, expected_tags_count)
        (
            "Hello {color=#fff}world{/color}!",
            "Hello world!",
            2
        ),
        (
            "My name is [name]",
            "My name is",
            1
        ),
        (
            "{size=20}{color=#797979}02/2023{/color}{/size}",
            "02/2023",
            4
        ),
        (
            "See you later [name]!",
            "See you later!",
            1
        ),
        (
            "{color=#ff0000}Red text{/color} and {color=#00ff00}green text{/color}",
            "Red text and green text",
            4
        ),
        (
            "Plain text without tags",
            "Plain text without tags",
            0
        ),
        (
            "{b}Bold{/b} and {i}italic{/i} with [variable]",
            "Bold and italic with",
            5
        ),
    ]

    print("Testing Tag Extraction")
    print("=" * 70)

    all_passed = True

    for i, (original, expected_clean, expected_tag_count) in enumerate(test_cases, 1):
        clean_text, tags = RenpyTagExtractor.extract_tags(original)

        passed = (
            clean_text == expected_clean and
            len(tags) == expected_tag_count
        )

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\nTest {i}: {status}")
        print(f"  Original:  {original}")
        print(f"  Clean:     {clean_text}")
        print(f"  Expected:  {expected_clean}")
        print(f"  Tags:      {len(tags)} (expected {expected_tag_count})")

        if tags:
            print(f"  Tag list:  {[tag for _, tag in tags]}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tag extraction tests passed!")
    else:
        print("✗ Some tag extraction tests failed")

    return all_passed


def test_tag_restoration():
    """Test tag restoration after translation simulation"""

    test_cases = [
        # (original, simulated_translation, should_contain_tags)
        (
            "Hello {color=#fff}world{/color}!",
            "Salut lume!",
            ["{color=#fff}", "{/color}"]
        ),
        (
            "My name is [name]",
            "Numele meu este",
            ["[name]"]
        ),
        (
            "{size=20}Big text{/size}",
            "Text mare",
            ["{size=20}", "{/size}"]
        ),
    ]

    print("\n\nTesting Tag Restoration")
    print("=" * 70)

    all_passed = True

    for i, (original, translation, expected_tags) in enumerate(test_cases, 1):
        # Extract tags
        clean_original, tags = RenpyTagExtractor.extract_tags(original)

        # Restore tags
        restored = RenpyTagExtractor.restore_tags(translation, tags, clean_original)

        # Check if all expected tags are present
        tags_present = all(tag in restored for tag in expected_tags)

        passed = tags_present
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"\nTest {i}: {status}")
        print(f"  Original:     {original}")
        print(f"  Translation:  {translation}")
        print(f"  Restored:     {restored}")
        print(f"  Expected tags: {expected_tags}")
        print(f"  All present:  {tags_present}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ All tag restoration tests passed!")
    else:
        print("✗ Some tag restoration tests failed")

    return all_passed


def test_renpy_parser():
    """Test Ren'Py file parsing"""
    from renpy_utils import RenpyTranslationParser

    # Sample Ren'Py translation content
    sample_content = """# TODO: Translation updated at 2024-02-29 18:59

# game/script.rpy:86
translate english test_label_1:

    # am "Hey!"
    am ""

# game/script.rpy:123
translate english test_label_2:

    # am "Have you decided to help me? Really?"
    am ""

# game/script.rpy:125
translate english test_label_3:

    # am "Thank you thank you thank you!"
    am "Mulțumesc mulțumesc mulțumesc!"
"""

    # Write to temp file
    temp_file = Path(__file__).parent / "test_temp.rpy"
    temp_file.write_text(sample_content, encoding='utf-8')

    print("\n\nTesting Ren'Py File Parser")
    print("=" * 70)

    try:
        blocks = RenpyTranslationParser.parse_file(temp_file)

        print(f"\nParsed {len(blocks)} translation blocks:")

        for block in blocks:
            print(f"\n  Label: {block['label']}")
            print(f"  Original: {block['original']}")
            print(f"  Character: {block['character_var']}")
            print(f"  Translation: '{block['current_translation']}'")

        # Verify parsing
        expected_count = 3
        passed = len(blocks) == expected_count

        print("\n" + "=" * 70)
        if passed:
            print(f"✓ Parser test passed! Found {expected_count} blocks as expected")
        else:
            print(f"✗ Parser test failed! Expected {expected_count} blocks, found {len(blocks)}")

        return passed

    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()


if __name__ == "__main__":
    results = []

    results.append(test_tag_extraction())
    results.append(test_tag_restoration())
    results.append(test_renpy_parser())

    print("\n\n" + "=" * 70)
    print("OVERALL TEST RESULTS")
    print("=" * 70)

    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
