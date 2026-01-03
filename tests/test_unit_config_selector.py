"""
Unit tests for scripts/config_selector.py

Tests the user selection functions:
- select_item: Single item selection with auto-selection
- select_multiple_items: Multiple item selection
- select_languages_single_row: Language selection with row display
"""

import sys
import io
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from config_selector import select_item, select_multiple_items, select_languages_single_row


def test_select_item_auto_select_single():
    """Test auto-selection when only one item is available"""
    print("\n[TEST] select_item - Auto-select single item")

    items = [{'name': 'OnlyOption', 'code': 'only'}]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Capture stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    result = select_item("Test Selection", items, formatter, "item")

    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()

    assert result == items[0], "Should return the only item"
    assert "Auto-selecting" in output, "Should show auto-selection message"
    print("   [PASS] Auto-selected single item correctly")
    return True


def test_select_item_user_selection():
    """Test user selection from multiple items"""
    print("\n[TEST] select_item - User selects from multiple items")

    items = [
        {'name': 'Option1', 'code': 'opt1'},
        {'name': 'Option2', 'code': 'opt2'},
        {'name': 'Option3', 'code': 'opt3'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: select option 2
    with patch('builtins.input', return_value='2'):
        result = select_item("Test Selection", items, formatter, "item")

    assert result == items[1], "Should return the second item"
    print("   [PASS] User selection (option 2) works correctly")
    return True


def test_select_item_quit():
    """Test user quitting selection"""
    print("\n[TEST] select_item - User quits selection")

    items = [
        {'name': 'Option1', 'code': 'opt1'},
        {'name': 'Option2', 'code': 'opt2'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: quit
    with patch('builtins.input', return_value='q'):
        try:
            select_item("Test Selection", items, formatter, "item")
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 0, "Should exit with code 0"
            print("   [PASS] Quit functionality works correctly")
            return True


def test_select_item_invalid_then_valid():
    """Test handling invalid input followed by valid input"""
    print("\n[TEST] select_item - Invalid input handling")

    items = [
        {'name': 'Option1', 'code': 'opt1'},
        {'name': 'Option2', 'code': 'opt2'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate: invalid input "abc", then valid "1"
    with patch('builtins.input', side_effect=['abc', '1']):
        result = select_item("Test Selection", items, formatter, "item")

    assert result == items[0], "Should return first item after retry"
    print("   [PASS] Invalid input handling works correctly")
    return True


def test_select_multiple_items_all():
    """Test selecting all items"""
    print("\n[TEST] select_multiple_items - Select all")

    items = [
        {'name': 'Item1', 'code': 'i1'},
        {'name': 'Item2', 'code': 'i2'},
        {'name': 'Item3', 'code': 'i3'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: select all
    with patch('builtins.input', return_value='a'):
        result = select_multiple_items("Test Selection", items, formatter, "item")

    assert result == items, "Should return all items"
    assert len(result) == 3, "Should have 3 items"
    print("   [PASS] Select all works correctly")
    return True


def test_select_multiple_items_specific():
    """Test selecting specific items (1,3)"""
    print("\n[TEST] select_multiple_items - Select specific items")

    items = [
        {'name': 'Item1', 'code': 'i1'},
        {'name': 'Item2', 'code': 'i2'},
        {'name': 'Item3', 'code': 'i3'},
        {'name': 'Item4', 'code': 'i4'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: select items 1 and 3
    with patch('builtins.input', return_value='1,3'):
        result = select_multiple_items("Test Selection", items, formatter, "item")

    assert len(result) == 2, "Should return 2 items"
    assert result[0] == items[0], "First item should be Item1"
    assert result[1] == items[2], "Second item should be Item3"
    print("   [PASS] Select specific items (1,3) works correctly")
    return True


def test_select_multiple_items_duplicates():
    """Test that duplicate selections are handled (1,2,1 -> 1,2)"""
    print("\n[TEST] select_multiple_items - Duplicate handling")

    items = [
        {'name': 'Item1', 'code': 'i1'},
        {'name': 'Item2', 'code': 'i2'},
        {'name': 'Item3', 'code': 'i3'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: 1,2,1 (duplicate 1)
    with patch('builtins.input', return_value='1,2,1'):
        result = select_multiple_items("Test Selection", items, formatter, "item")

    assert len(result) == 2, "Should return 2 unique items"
    assert result[0] == items[0], "First item should be Item1"
    assert result[1] == items[1], "Second item should be Item2"
    print("   [PASS] Duplicate selection handled correctly")
    return True


def test_select_multiple_items_quit():
    """Test quitting from multiple selection"""
    print("\n[TEST] select_multiple_items - Quit")

    items = [
        {'name': 'Item1', 'code': 'i1'},
        {'name': 'Item2', 'code': 'i2'}
    ]

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    # Simulate user input: quit
    with patch('builtins.input', return_value='Q'):
        try:
            select_multiple_items("Test Selection", items, formatter, "item")
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 0, "Should exit with code 0"
            print("   [PASS] Quit works correctly")
            return True


def test_select_languages_single_row_all():
    """Test selecting all languages in single row display"""
    print("\n[TEST] select_languages_single_row - Select all")

    languages = [
        {'name': 'Romanian', 'code': 'ro'},
        {'name': 'Spanish', 'code': 'es'},
        {'name': 'French', 'code': 'fr'}
    ]

    def formatter(lang, num):
        return f"[{num}] {lang['name']}"

    # Simulate user input: select all
    with patch('builtins.input', return_value='A'):
        result = select_languages_single_row("Select Languages", languages, formatter, "language")

    assert result == languages, "Should return all languages"
    assert len(result) == 3, "Should have 3 languages"
    print("   [PASS] Select all languages works correctly")
    return True


def test_select_languages_single_row_specific():
    """Test selecting specific languages (1,3)"""
    print("\n[TEST] select_languages_single_row - Select specific")

    languages = [
        {'name': 'Romanian', 'code': 'ro'},
        {'name': 'Spanish', 'code': 'es'},
        {'name': 'French', 'code': 'fr'},
        {'name': 'German', 'code': 'de'}
    ]

    def formatter(lang, num):
        return f"[{num}] {lang['name']}"

    # Simulate user input: 1,3
    with patch('builtins.input', return_value='1,3'):
        result = select_languages_single_row("Select Languages", languages, formatter, "language")

    assert len(result) == 2, "Should return 2 languages"
    assert result[0]['code'] == 'ro', "First should be Romanian"
    assert result[1]['code'] == 'fr', "Second should be French"
    print("   [PASS] Select specific languages works correctly")
    return True


def test_select_item_empty_list():
    """Test error handling for empty item list"""
    print("\n[TEST] select_item - Empty list handling")

    items = []

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    try:
        select_item("Test Selection", items, formatter, "item")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No items to select" in str(e), "Should have appropriate error message"
        print("   [PASS] Empty list raises ValueError correctly")
        return True


def test_select_multiple_items_empty_list():
    """Test error handling for empty item list in multiple selection"""
    print("\n[TEST] select_multiple_items - Empty list handling")

    items = []

    def formatter(item, num):
        return f"[{num}] {item['name']}"

    try:
        select_multiple_items("Test Selection", items, formatter, "item")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No items to select" in str(e), "Should have appropriate error message"
        print("   [PASS] Empty list raises ValueError correctly")
        return True


def run_all_tests():
    """Run all config_selector tests"""
    print("=" * 70)
    print("UNIT TESTS: config_selector.py")
    print("=" * 70)

    tests = [
        ("Auto-select single item", test_select_item_auto_select_single),
        ("User selection", test_select_item_user_selection),
        ("Quit selection", test_select_item_quit),
        ("Invalid input handling", test_select_item_invalid_then_valid),
        ("Select all items", test_select_multiple_items_all),
        ("Select specific items", test_select_multiple_items_specific),
        ("Duplicate handling", test_select_multiple_items_duplicates),
        ("Quit multiple selection", test_select_multiple_items_quit),
        ("Select all languages", test_select_languages_single_row_all),
        ("Select specific languages", test_select_languages_single_row_specific),
        ("Empty list (select_item)", test_select_item_empty_list),
        ("Empty list (select_multiple)", test_select_multiple_items_empty_list),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"   [FAIL] {test_name}")
        except Exception as e:
            failed += 1
            print(f"   [FAIL] {test_name}: {e}")

    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests: {passed}/{passed + failed} passed")
    print()

    if failed == 0:
        print("\033[92m[SUCCESS] All config_selector tests passed!\033[0m")
        return True
    else:
        print(f"\033[91m[FAILURE] {failed} test(s) failed.\033[0m")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
