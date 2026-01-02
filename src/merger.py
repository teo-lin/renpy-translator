"""
Ren'Py Translation File Merger

Merges translated YAML files back into .rpy format using tags metadata.
Performs integrity validation to ensure syntax correctness.
"""

import re
import json
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    # Try relative import (when used as package)
    from .models import (
        ParsedBlock, TaggedBlock, TagInfo, TagsFileContent,
        FileStructureType, is_separator_block
    )
    from .renpy_utils import RenpyTagExtractor
except ImportError:
    # Fall back to absolute import (when run standalone or from tests)
    from models import (
        ParsedBlock, TaggedBlock, TagInfo, TagsFileContent,
        FileStructureType, is_separator_block
    )
    from renpy_utils import RenpyTagExtractor


@dataclass
class ValidationError:
    """Represents a validation error found during integrity check."""
    block_id: str
    error_type: str
    message: str
    line_number: Optional[int] = None


class RenpyMerger:
    """Merge translated YAML files back into .rpy format."""

    def __init__(self):
        """Initialize merger."""
        self.tag_extractor = RenpyTagExtractor()
        self.validation_errors: List[ValidationError] = []

    # ========================================================================
    # MAIN MERGE METHOD
    # ========================================================================

    def merge_file(
        self,
        parsed_yaml_path: Path,
        tags_json_path: Path,
        output_rpy_path: Path,
        validate: bool = True
    ) -> bool:
        """
        Merge YAML + JSON back into .rpy file.

        Args:
            parsed_yaml_path: Path to .parsed.yaml file
            tags_json_path: Path to .tags.json file
            output_rpy_path: Path to output .rpy file
            validate: Whether to run integrity validation

        Returns:
            True if successful, False if validation errors found
        """
        print(f"Loading files for merge...")

        # Load files
        with open(parsed_yaml_path, 'r', encoding='utf-8') as f:
            parsed_blocks: Dict[str, ParsedBlock] = yaml.safe_load(f)

        with open(tags_json_path, 'r', encoding='utf-8') as f:
            tags_file: TagsFileContent = json.load(f)

        metadata = tags_file['metadata']
        structure = tags_file['structure']
        tagged_blocks = tags_file['blocks']

        print(f"Loaded {len(parsed_blocks)} blocks")
        print(f"File structure: {metadata['file_structure_type']}")

        # Build output content
        output_lines: List[str] = []

        # Add header comment
        output_lines.append(f"# TODO: Translation updated at {metadata['extracted_at'][:10]}")
        output_lines.append("")

        # Determine structure type
        file_structure = FileStructureType(metadata['file_structure_type'])

        if file_structure == FileStructureType.STRINGS_ONLY:
            # File starts directly with strings section
            # Only append header if it exists
            if structure['string_section_header']:
                output_lines.append(structure['string_section_header'])
                output_lines.append("")

        # Process blocks in order
        block_order = structure['block_order']
        in_strings_section = file_structure == FileStructureType.STRINGS_ONLY
        string_section_start = structure.get('string_section_start')

        for idx, block_id in enumerate(block_order):
            # Check if we've reached strings section
            if not in_strings_section and string_section_start is not None and idx == string_section_start:
                in_strings_section = True
                output_lines.append("")
                output_lines.append(structure['string_section_header'])
                output_lines.append("")

            # Get block data
            parsed_block = parsed_blocks.get(block_id)
            tagged_block = tagged_blocks.get(block_id)

            if not parsed_block or not tagged_block:
                print(f"Warning: Missing data for block {block_id}")
                continue

            # Handle separator blocks
            if is_separator_block(block_id, parsed_block):
                separator_content = tagged_block.get('separator_content', '# -----------')
                output_lines.append("")
                output_lines.append(separator_content)
                output_lines.append("")
                continue

            # Get clean translations
            clean_en = parsed_block.get('en', '')
            clean_ro = parsed_block.get('ro', '')

            # Restore tags to both original and translation
            tags = tagged_block['tags']
            tag_list = [(tag['pos'], tag['tag']) for tag in tags]

            original_with_tags = self.tag_extractor.restore_tags(clean_en, tag_list, clean_en)
            translation_with_tags = self.tag_extractor.restore_tags(clean_ro, tag_list, clean_en)

            # Build block using template
            template = tagged_block['template']
            block_content = self._fill_template(
                template,
                language=metadata['target_language'],
                label=tagged_block.get('label', ''),
                location=tagged_block.get('location', ''),
                char_var=tagged_block.get('char_var', ''),
                original=original_with_tags,
                translation=translation_with_tags
            )

            output_lines.append(block_content)
            output_lines.append("")

        # Join output
        output_content = '\n'.join(output_lines)

        # Validate if requested
        if validate:
            print("Running integrity validation...")
            self.validation_errors = self.validate_content(output_content, block_order, parsed_blocks, tagged_blocks)

            if self.validation_errors:
                print(f"Found {len(self.validation_errors)} validation errors:")
                for error in self.validation_errors[:10]:  # Show first 10
                    print(f"   - {error.block_id}: {error.message}")
                print(f"\nFile will be saved, but please review errors!")
            else:
                print("Validation passed!")

        # Write output file
        print(f"Writing to: {output_rpy_path}")
        with open(output_rpy_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        return len(self.validation_errors) == 0

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _fill_template(
        self,
        template: str,
        language: str,
        label: str,
        location: str,
        char_var: str,
        original: str,
        translation: str
    ) -> str:
        """Fill a block template with values."""
        return template.format(
            language=language,
            label=label,
            location=location,
            char_var=char_var,
            original=original,
            translation=translation
        )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def validate_content(
        self,
        content: str,
        block_order: List[str],
        parsed_blocks: Dict[str, ParsedBlock],
        tagged_blocks: Dict[str, TaggedBlock]
    ) -> List[ValidationError]:
        """
        Validate merged content for syntax errors.

        Checks for:
        - Unmatched quotes
        - Unmatched braces/brackets
        - Missing character variables
        - Missing variables from original in translation
        """
        errors: List[ValidationError] = []

        # Split content into lines for line-based errors
        lines = content.split('\n')

        # 1. Check for unmatched quotes in each line
        for line_num, line in enumerate(lines, start=1):
            # Skip comment lines and labels
            if line.strip().startswith('#') or line.strip().endswith(':'):
                continue

            # Count quotes (excluding escaped quotes)
            quote_count = len(re.findall(r'(?<!\\)"', line))
            if quote_count % 2 != 0:
                errors.append(ValidationError(
                    block_id="unknown",
                    error_type="unmatched_quote",
                    message=f"Unmatched quote on line {line_num}: {line[:50]}",
                    line_number=line_num
                ))

        # 2. Check for unmatched braces/brackets in entire file
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            errors.append(ValidationError(
                block_id="file",
                error_type="unmatched_brace",
                message=f"Unmatched braces: {open_braces} open, {close_braces} close"
            ))

        open_brackets = content.count('[')
        close_brackets = content.count(']')
        if open_brackets != close_brackets:
            errors.append(ValidationError(
                block_id="file",
                error_type="unmatched_bracket",
                message=f"Unmatched brackets: {open_brackets} open, {close_brackets} close"
            ))

        # 3. Check each block for missing variables
        for block_id in block_order:
            if is_separator_block(block_id, parsed_blocks.get(block_id, {})):
                continue

            parsed = parsed_blocks.get(block_id)
            tagged = tagged_blocks.get(block_id)

            if not parsed or not tagged:
                continue

            # Find variables in original and translation
            original_vars = set(re.findall(r'\[(\w+)\]', parsed.get('en', '')))
            trans_vars = set(re.findall(r'\[(\w+)\]', parsed.get('ro', '')))

            # Check if translation is missing variables from original
            missing_vars = original_vars - trans_vars
            if missing_vars and parsed.get('ro', '').strip():  # Only check if translation exists
                errors.append(ValidationError(
                    block_id=block_id,
                    error_type="missing_variable",
                    message=f"Translation missing variables: {', '.join(missing_vars)}"
                ))

        # 4. Check for missing character variables in dialogue blocks
        for block_id in block_order:
            tagged = tagged_blocks.get(block_id)
            if not tagged:
                continue

            if tagged['type'] == 'dialogue' and not tagged.get('char_var'):
                errors.append(ValidationError(
                    block_id=block_id,
                    error_type="missing_char_var",
                    message="Dialogue block missing character variable"
                ))

        return errors

    def get_validation_report(self) -> str:
        """Get a formatted validation error report."""
        if not self.validation_errors:
            return "No validation errors found!"

        report = [f"Found {len(self.validation_errors)} validation errors:\n"]

        # Group errors by type
        errors_by_type: Dict[str, List[ValidationError]] = {}
        for error in self.validation_errors:
            errors_by_type.setdefault(error.error_type, []).append(error)

        for error_type, errors in errors_by_type.items():
            report.append(f"\n{error_type.upper().replace('_', ' ')} ({len(errors)} errors):")
            for error in errors[:5]:  # Show first 5 of each type
                report.append(f"  - {error.block_id}: {error.message}")
            if len(errors) > 5:
                report.append(f"  ... and {len(errors) - 5} more")

        return '\n'.join(report)
