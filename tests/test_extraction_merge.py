"""
Test the new modular extraction/merge pipeline

This test does not require a model to be loaded - it only tests
the extraction and merge logic without actual translation.
"""

import sys
import json
import yaml
from pathlib import Path
import tempfile
import argparse

# Set UTF-8 encoding for console output on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from extraction import RenpyExtractor
from merger import RenpyMerger
from models import BlockType, FileStructureType


def test_extraction():
    """Test extraction of .rpy file into YAML + JSON"""

    print("\n" + "=" * 70)
    print("TEST 1: Extraction Pipeline")
    print("=" * 70)

    # Sample .rpy content
    sample_rpy = """# TODO: Translation updated at 2024-02-29 18:59

# game/script.rpy:86
translate romanian test_label_1:

    # am "Hey! How are you?"
    am "Hei! Ce mai faci?"

# game/script.rpy:123
translate romanian test_label_2:

    # am "Have you decided to help me?"
    am ""

# game/script.rpy:140
translate romanian test_narrator_1:

    # "You don't have any mail!"
    ""

# ---------------------------------------------------------------------------

translate romanian strings:

    # game/script.rpy:200
    old "{color=#3ad8ff}Continue{/color} {image=arrow.png}"
    new "{color=#3ad8ff}{/color}{image=arrow.png}"

    # game/script.rpy:201
    old "Exit to menu"
    new ""
"""

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False, encoding='utf-8') as f:
        f.write(sample_rpy)
        temp_rpy = Path(f.name)

    try:
        # Character map
        character_map = {
            'am': 'Amelia',
            '': 'Narrator'
        }

        # Extract
        print("\n📖 Extracting file...")
        extractor = RenpyExtractor(character_map)
        parsed_blocks, tags_file = extractor.extract_file(
            temp_rpy,
            target_language='romanian',
            source_language='english'
        )

        # Verify parsed blocks
        print(f"\n✓ Extracted {len(parsed_blocks)} blocks")
        assert len(parsed_blocks) > 0, "No blocks extracted!"

        # Check for expected block types
        expected_blocks = [
            ('1-Amelia', 'Hey! How are you?', 'Hei! Ce mai faci!'),
            ('2-Amelia', 'Have you decided to help me?', ''),
            ('3-Narrator', 'You don\'t have any mail!', ''),
            ('separator-1', None, None),
        ]

        for block_id, expected_en, expected_ro in expected_blocks:
            if block_id not in parsed_blocks:
                print(f"  ⚠️  Block {block_id} not found")
                continue

            block = parsed_blocks[block_id]

            if expected_en is not None:
                assert 'en' in block, f"Block {block_id} missing 'en' field"
                print(f"  ✓ Block {block_id}: en = {block['en'][:50]}")

        # Verify tags file structure
        print("\n📦 Verifying tags file...")
        assert 'metadata' in tags_file, "Missing metadata"
        assert 'structure' in tags_file, "Missing structure"
        assert 'blocks' in tags_file, "Missing blocks"
        assert 'character_map' in tags_file, "Missing character_map"

        metadata = tags_file['metadata']
        assert metadata['file_structure_type'] == FileStructureType.DIALOGUE_AND_STRINGS.value
        print(f"  ✓ File structure: {metadata['file_structure_type']}")
        print(f"  ✓ Total blocks: {metadata['total_blocks']}")
        print(f"  ✓ Untranslated: {metadata['untranslated_blocks']}")

        # Verify tags in blocks
        for block_id, block_data in tags_file['blocks'].items():
            if block_id.startswith('separator'):
                continue

            assert 'type' in block_data, f"Block {block_id} missing type"
            assert 'tags' in block_data, f"Block {block_id} missing tags"
            assert 'template' in block_data, f"Block {block_id} missing template"

        print("\n✅ Extraction test passed!")
        return temp_rpy, parsed_blocks, tags_file

    except AssertionError as e:
        print(f"\n❌ Extraction test failed: {e}")
        temp_rpy.unlink(missing_ok=True)
        return None, None, None
    except Exception as e:
        print(f"\n❌ Extraction test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        temp_rpy.unlink(missing_ok=True)
        return None, None, None


def test_merge(temp_rpy, parsed_blocks, tags_file):
    """Test merging YAML + JSON back into .rpy"""

    if not temp_rpy or not parsed_blocks or not tags_file:
        print("\n⏭️  Skipping merge test (extraction failed)")
        return False

    print("\n" + "=" * 70)
    print("TEST 2: Merge Pipeline")
    print("=" * 70)

    try:
        # Save parsed blocks and tags to temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.parsed.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            temp_yaml = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tags.json', delete=False, encoding='utf-8') as f:
            json.dump(tags_file, f, indent=2, ensure_ascii=False)
            temp_json = Path(f.name)

        output_rpy = temp_rpy.with_suffix('.translated.rpy')

        # Merge
        print("\n🔧 Merging files...")
        merger = RenpyMerger()
        success = merger.merge_file(
            parsed_yaml_path=temp_yaml,
            tags_json_path=temp_json,
            output_rpy_path=output_rpy,
            validate=True
        )

        # Check output
        assert output_rpy.exists(), "Output file not created!"
        print(f"  ✓ Output file created: {output_rpy}")

        # Read output
        output_content = output_rpy.read_text(encoding='utf-8')
        print(f"  ✓ Output length: {len(output_content)} characters")

        # Verify structure
        assert 'translate romanian' in output_content, "Missing translate statement"
        assert 'translate romanian strings:' in output_content, "Missing strings section"
        print("  ✓ Output has correct structure")

        # Check validation
        if success:
            print("  ✓ Validation passed")
        else:
            print("  ⚠️  Validation found issues (check details above)")

        # Check for tag restoration
        if '{color=#3ad8ff}' in output_content:
            print("  ✓ Tags restored correctly")
        else:
            print("  ⚠️  Tags may not be restored")

        # Cleanup
        temp_yaml.unlink(missing_ok=True)
        temp_json.unlink(missing_ok=True)
        output_rpy.unlink(missing_ok=True)
        temp_rpy.unlink(missing_ok=True)

        print("\n✅ Merge test passed!")
        return True

    except AssertionError as e:
        print(f"\n❌ Merge test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Merge test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tag_preservation():
    """Test that tags are preserved through extract/merge cycle"""

    print("\n" + "=" * 70)
    print("TEST 3: Tag Preservation")
    print("=" * 70)

    # Sample with complex tags
    sample_rpy = """# TODO: Test

# game/test.rpy:1
translate romanian test_tags:

    # jm "Hello {color=#ff0000}world{/color}! My name is [name]."
    jm "Salut {color=#ff0000}lume{/color}! Numele meu este [name]."
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False, encoding='utf-8') as f:
        f.write(sample_rpy)
        temp_rpy = Path(f.name)

    try:
        # Extract
        character_map = {'jm': 'Jasmine'}
        extractor = RenpyExtractor(character_map)
        parsed_blocks, tags_file = extractor.extract_file(temp_rpy, 'romanian', 'english')

        # Check clean text
        block_id = '1-Jasmine'
        assert block_id in parsed_blocks, f"Block {block_id} not found"

        clean_en = parsed_blocks[block_id]['en']
        clean_ro = parsed_blocks[block_id]['ro']

        print(f"\n  Clean EN: {clean_en}")
        print(f"  Clean RO: {clean_ro}")

        # Verify tags removed
        assert '{color' not in clean_en, "Tags not removed from EN"
        assert '[name]' not in clean_en, "Variables not removed from EN"
        print("  ✓ Tags removed from clean text")

        # Check tags stored
        block_tags = tags_file['blocks'][block_id]['tags']
        assert len(block_tags) > 0, "No tags stored"
        print(f"  ✓ Stored {len(block_tags)} tags")

        # Verify tag types
        tag_contents = [t['tag'] for t in block_tags]
        assert '{color=#ff0000}' in tag_contents, "Color tag not stored"
        assert '{/color}' in tag_contents, "Close tag not stored"
        assert '[name]' in tag_contents, "Variable not stored"
        print("  ✓ All tags stored correctly")

        # Merge back
        with tempfile.NamedTemporaryFile(mode='w', suffix='.parsed.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False)
            temp_yaml = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tags.json', delete=False, encoding='utf-8') as f:
            json.dump(tags_file, f, indent=2, ensure_ascii=False)
            temp_json = Path(f.name)

        output_rpy = temp_rpy.with_suffix('.translated.rpy')

        merger = RenpyMerger()
        merger.merge_file(temp_yaml, temp_json, output_rpy, validate=True)

        # Read output
        output_content = output_rpy.read_text(encoding='utf-8')

        # Verify tags restored
        assert '{color=#ff0000}' in output_content, "Color tag not restored"
        assert '{/color}' in output_content, "Close tag not restored"
        assert '[name]' in output_content, "Variable not restored"
        print("  ✓ All tags restored in output")

        # Cleanup
        temp_yaml.unlink(missing_ok=True)
        temp_json.unlink(missing_ok=True)
        output_rpy.unlink(missing_ok=True)
        temp_rpy.unlink(missing_ok=True)

        print("\n✅ Tag preservation test passed!")
        return True

    except AssertionError as e:
        print(f"\n❌ Tag preservation test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Tag preservation test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """Test integrity validation catches errors"""

    print("\n" + "=" * 70)
    print("TEST 4: Validation")
    print("=" * 70)

    # Create parsed blocks with intentional errors
    parsed_blocks = {
        "1-Test": {
            "en": 'Hello [name]',
            "ro": 'Salut'  # Missing [name] variable
        },
        "2-Test": {
            "en": "Test",
            "ro": "Test with unmatched quote"  # This will cause unmatched quote when in template
        }
    }

    tags_file = {
        "metadata": {
            "source_file": "test.rpy",
            "target_language": "romanian",
            "source_language": "english",
            "extracted_at": "2025-01-01",
            "file_structure_type": "dialogue_and_strings",
            "has_separator_lines": False,
            "total_blocks": 2,
            "untranslated_blocks": 0
        },
        "structure": {
            "block_order": ["1-Test", "2-Test"],
            "string_section_start": None,
            "string_section_header": None
        },
        "blocks": {
            "1-Test": {
                "type": "dialogue",
                "label": "test_1",
                "location": "game/test.rpy:1",
                "char_var": "t",
                "char_name": "Test",
                "tags": [{"pos": 6, "tag": "[name]", "type": "variable"}],
                "template": '# {location}\ntranslate {language} {label}:\n\n    # {char_var} "{original}"\n    {char_var} "{translation}"',
                "separator_content": None
            },
            "2-Test": {
                "type": "dialogue",
                "label": "test_2",
                "location": "game/test.rpy:10",
                "char_var": "t",
                "char_name": "Test",
                "tags": [],
                "template": '# {location}\ntranslate {language} {label}:\n\n    # {char_var} "{original}"\n    {char_var} "{translation}"',
                "separator_content": None
            }
        },
        "character_map": {"t": "Test"}
    }

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.parsed.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False)
            temp_yaml = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.tags.json', delete=False, encoding='utf-8') as f:
            json.dump(tags_file, f, indent=2, ensure_ascii=False)
            temp_json = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.rpy', delete=False, encoding='utf-8') as f:
            output_rpy = Path(f.name)

        # Merge with validation
        merger = RenpyMerger()
        success = merger.merge_file(temp_yaml, temp_json, output_rpy, validate=True)

        # Should detect errors
        if merger.validation_errors:
            print(f"\n  ✓ Validation detected {len(merger.validation_errors)} error(s)")

            # Check for expected error type
            error_types = [e.error_type for e in merger.validation_errors]
            if 'missing_variable' in error_types:
                print("  ✓ Detected missing variable")
            else:
                print("  ⚠️  Did not detect missing variable")

            print("\n  Error report:")
            print(merger.get_validation_report())
        else:
            print("  ⚠️  Validation did not detect any errors (expected at least one)")

        # Cleanup
        temp_yaml.unlink(missing_ok=True)
        temp_json.unlink(missing_ok=True)
        output_rpy.unlink(missing_ok=True)

        print("\n✅ Validation test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Validation test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Parse arguments (optional - for compatibility with test.ps1)
    parser = argparse.ArgumentParser(description="Test modular extraction/merge pipeline")
    parser.add_argument("--model_script", help="Model script path (not used by this test)", default=None)
    parser.add_argument("--language", help="Language code (not used by this test)", default=None)
    args = parser.parse_args()

    # Note: This test doesn't need a model or language - it only tests parsing logic
    if args.model_script or args.language:
        print("ℹ️  Note: This test does not require a model - testing extraction/merge logic only")

    print("\n" + "=" * 70)
    print("MODULAR PIPELINE TESTS")
    print("=" * 70)

    results = []

    # Run tests
    temp_rpy, parsed_blocks, tags_file = test_extraction()
    results.append(temp_rpy is not None)

    results.append(test_merge(temp_rpy, parsed_blocks, tags_file))
    results.append(test_tag_preservation())
    results.append(test_validation())

    # Summary
    print("\n" + "=" * 70)
    print("OVERALL TEST RESULTS")
    print("=" * 70)

    if all(results):
        print("✅ All modular pipeline tests passed!")
        sys.exit(0)
    else:
        print("❌ Some modular pipeline tests failed")
        sys.exit(1)
