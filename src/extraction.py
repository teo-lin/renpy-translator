"""
Ren'Py Translation File Extractor

Extracts translation blocks from .rpy files and separates clean text from tags.
Outputs two files:
- .parsed.yaml: Human-readable clean text for translation
- .tags.json: Machine-readable metadata and tags for reconstruction
"""

import re
import json
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

try:
    # Try relative import (when used as package)
    from .models import (
        BlockType, FileStructureType, CharacterType,
        RenpyBlock, ParsedBlock, TaggedBlock, TagInfo,
        ParsedFileMetadata, FileStructure, TagsFileContent,
        get_character_display_name, create_block_id
    )
    from .renpy_utils import RenpyTagExtractor
except ImportError:
    # Fall back to absolute import (when run standalone or from tests)
    from models import (
        BlockType, FileStructureType, CharacterType,
        RenpyBlock, ParsedBlock, TaggedBlock, TagInfo,
        ParsedFileMetadata, FileStructure, TagsFileContent,
        get_character_display_name, create_block_id
    )
    from renpy_utils import RenpyTagExtractor


class RenpyExtractor:
    """Extract and parse Ren'Py translation files."""

    # ========================================================================
    # REGEX PATTERNS
    # ========================================================================

    # Dialogue block: has character variable
    # # game/Cell01_JM.rpy:6256
    # translate romanian QuestChap2_Jasmine01_18_3deb0746:
    #
    #     # jm "See you later [name]. Bye!"
    #     jm "Translation here"
    DIALOGUE_PATTERN = re.compile(
        r'# (game/[^\n]+)\n'  # Location comment
        r'translate (\w+) (\w+):\s*\n'  # translate <language> <label>:
        r'\s*\n'  # Empty line
        r'\s*# (\w+) "([^"\\]*(?:\\.[^"\\]*)*)"\s*\n'  # Original with char_var
        r'\s*(\w+) "([^"\\]*(?:\\.[^"\\]*)*)"'  # Translation with char_var
    , re.MULTILINE | re.DOTALL)

    # Narrator block: NO character variable (just quoted text)
    # # game/Room_01.rpy:106
    # translate romanian room01_mail01_92caf0b8:
    #
    #     # "You don't have any mail!"
    #     ""
    NARRATOR_PATTERN = re.compile(
        r'# (game/[^\n]+)\n'  # Location comment
        r'translate (\w+) (\w+):\s*\n'  # translate <language> <label>:
        r'\s*\n'  # Empty line
        r'\s*# "([^"\\]*(?:\\.[^"\\]*)*)"\s*\n'  # Original (no char_var)
        r'\s*"([^"\\]*(?:\\.[^"\\]*)*)"'  # Translation (no char_var)
    , re.MULTILINE | re.DOTALL)

    # String block (inside "translate <lang> strings:" section)
    # # game/Cell01_JM.rpy:184
    # old "{color=#3ad8ff}Text here{/color}"
    # new "Translation"
    STRING_PATTERN = re.compile(
        r'# (game/[^\n]+)\n'  # Location comment
        r'\s*old "([^"\\]*(?:\\.[^"\\]*)*)"\s*\n'  # old "original"
        r'\s*new "([^"\\]*(?:\\.[^"\\]*)*)"'  # new "translation"
    , re.MULTILINE | re.DOTALL)

    # Separator line
    SEPARATOR_PATTERN = re.compile(
        r'^(# -+)$',
        re.MULTILINE
    )

    # Strings section header
    STRINGS_SECTION_PATTERN = re.compile(
        r'translate (\w+) strings:',
        re.MULTILINE
    )

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(self, character_map: Optional[Dict[str, str]] = None):
        """
        Initialize extractor.

        Args:
            character_map: Optional mapping of char_var -> display name
        """
        self.character_map = character_map or {}
        self.tag_extractor = RenpyTagExtractor()

    # ========================================================================
    # MAIN EXTRACTION METHOD
    # ========================================================================

    def extract_file(
        self,
        rpy_file_path: Path,
        target_language: str = "romanian",
        source_language: str = "english"
    ) -> Tuple[Dict[str, ParsedBlock], TagsFileContent]:
        """
        Extract translation blocks from a .rpy file.

        Args:
            rpy_file_path: Path to the .rpy file
            target_language: Target language code (e.g., "romanian")
            source_language: Source language code (e.g., "english")

        Returns:
            Tuple of (parsed_blocks, tags_file_content)
            - parsed_blocks: Dict[block_id, ParsedBlock] for YAML output
            - tags_file_content: Complete tags.json structure
        """
        print(f"📖 Reading file: {rpy_file_path}")

        # Read file content
        with open(rpy_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Detect file structure
        file_structure_type = self._detect_file_structure(content)
        print(f"📋 File structure: {file_structure_type.value}")

        # Parse blocks
        blocks = self._parse_blocks(content, target_language)
        print(f"📦 Found {len(blocks)} blocks")

        # Detect separator lines
        has_separators = bool(self.SEPARATOR_PATTERN.search(content))

        # Extract separators and add to blocks
        if has_separators:
            blocks.extend(self._extract_separators(content))
            print(f"🔀 Found {len([b for b in blocks if b['type'] == 'separator'])} separator lines")

        # Sort blocks by position to preserve order
        blocks.sort(key=lambda b: b.get('start_pos', 0))

        # Build parsed blocks and tags
        parsed_blocks: Dict[str, ParsedBlock] = {}
        tagged_blocks: Dict[str, TaggedBlock] = {}
        block_order: List[str] = []
        string_section_start: Optional[int] = None

        for idx, block in enumerate(blocks, start=1):
            block_type = block['type']

            if block_type == 'separator':
                # Separator block
                block_id = f"separator-{idx}"
                parsed_blocks[block_id] = {"type": "separator"}
                tagged_blocks[block_id] = {
                    "type": BlockType.SEPARATOR,
                    "label": None,
                    "location": None,
                    "char_var": None,
                    "char_name": None,
                    "tags": [],
                    "template": "",
                    "separator_content": block['content']
                }
                block_order.append(block_id)
                continue

            # Get character info
            char_var = block.get('character_var')
            char_name = get_character_display_name(char_var, self.character_map)

            # Check if this is the start of strings section
            if block_type == 'string' and string_section_start is None:
                string_section_start = idx - 1  # 0-based index

            # Extract tags from original text
            original_text = block['original']
            clean_en, tags = self.tag_extractor.extract_tags(original_text)

            # Extract tags from current translation (if exists)
            current_translation = block['current_translation']
            clean_ro = ""
            if current_translation and current_translation.strip():
                clean_ro, _ = self.tag_extractor.extract_tags(current_translation)

            # Create block ID
            block_id = create_block_id(idx, char_name)
            block_order.append(block_id)

            # Add to parsed blocks (YAML)
            parsed_blocks[block_id] = {
                "en": clean_en,
                "ro": clean_ro
            }

            # Convert tags to TagInfo format
            tag_list: List[TagInfo] = [
                {"pos": pos, "tag": tag, "type": self._classify_tag(tag)}
                for pos, tag in tags
            ]

            # Build reconstruction template
            template = self._build_template(block)

            # Add to tagged blocks (JSON)
            tagged_blocks[block_id] = {
                "type": BlockType(block_type),
                "label": block.get('label'),
                "location": block.get('location'),
                "char_var": char_var,
                "char_name": char_name,
                "tags": tag_list,
                "template": template,
                "separator_content": None
            }

        # Build metadata
        metadata: ParsedFileMetadata = {
            "source_file": str(rpy_file_path),
            "target_language": target_language,
            "source_language": source_language,
            "extracted_at": datetime.now().isoformat(),
            "file_structure_type": file_structure_type.value,
            "has_separator_lines": has_separators,
            "total_blocks": len(blocks),
            "untranslated_blocks": len([b for b in blocks if not b.get('current_translation', '').strip()])
        }

        # Build structure
        structure: FileStructure = {
            "block_order": block_order,
            "string_section_start": string_section_start,
            "string_section_header": f"translate {target_language} strings:" if string_section_start is not None else None
        }

        # Build tags file content
        tags_file: TagsFileContent = {
            "metadata": metadata,
            "structure": structure,
            "blocks": tagged_blocks,
            "character_map": self.character_map
        }

        return parsed_blocks, tags_file

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _detect_file_structure(self, content: str) -> FileStructureType:
        """Detect if file is strings-only or has dialogue blocks."""
        # Check if file starts with "translate <lang> strings:"
        first_translate = re.search(r'translate \w+ (\w+)', content)
        if first_translate and first_translate.group(1) == 'strings':
            return FileStructureType.STRINGS_ONLY

        # Check for dialogue blocks
        if self.DIALOGUE_PATTERN.search(content) or self.NARRATOR_PATTERN.search(content):
            return FileStructureType.DIALOGUE_AND_STRINGS

        # Default to strings only
        return FileStructureType.STRINGS_ONLY

    def _parse_blocks(self, content: str, target_language: str) -> List[RenpyBlock]:
        """Parse all translation blocks from file content."""
        blocks: List[RenpyBlock] = []

        # Parse dialogue blocks
        for match in self.DIALOGUE_PATTERN.finditer(content):
            location, lang, label, char_var_orig, original, char_var_trans, translation = match.groups()
            blocks.append({
                'type': 'dialogue',
                'label': label,
                'location': location,
                'character_var': char_var_trans,
                'original': original,
                'current_translation': translation,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'full_match': match.group(0)
            })

        # Parse narrator blocks
        for match in self.NARRATOR_PATTERN.finditer(content):
            location, lang, label, original, translation = match.groups()
            blocks.append({
                'type': 'narrator',
                'label': label,
                'location': location,
                'character_var': None,
                'original': original,
                'current_translation': translation,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'full_match': match.group(0)
            })

        # Parse string blocks
        for match in self.STRING_PATTERN.finditer(content):
            location, original, translation = match.groups()
            blocks.append({
                'type': 'string',
                'label': 'strings',
                'location': location,
                'character_var': None,
                'original': original,
                'current_translation': translation,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'full_match': match.group(0)
            })

        return blocks

    def _extract_separators(self, content: str) -> List[RenpyBlock]:
        """Extract separator lines from content."""
        separators: List[RenpyBlock] = []
        for match in self.SEPARATOR_PATTERN.finditer(content):
            separators.append({
                'type': 'separator',
                'content': match.group(1),
                'start_pos': match.start(),
                'end_pos': match.end()
            })
        return separators

    def _classify_tag(self, tag: str) -> Optional[str]:
        """Classify tag type for easier debugging."""
        if tag.startswith('{color'):
            return 'color'
        elif tag.startswith('{size'):
            return 'size'
        elif tag.startswith('{font'):
            return 'font'
        elif tag.startswith('{cps'):
            return 'cps'
        elif tag.startswith('{/'):
            return 'close'
        elif tag.startswith('{image'):
            return 'image'
        elif tag.startswith('[') and tag.endswith(']'):
            return 'variable'
        else:
            return 'other'

    def _build_template(self, block: RenpyBlock) -> str:
        """Build reconstruction template for a block."""
        block_type = block['type']

        if block_type == 'dialogue':
            return (
                "# {location}\n"
                "translate {language} {label}:\n"
                "\n"
                "    # {char_var} \"{original}\"\n"
                "    {char_var} \"{translation}\""
            )
        elif block_type == 'narrator':
            return (
                "# {location}\n"
                "translate {language} {label}:\n"
                "\n"
                "    # \"{original}\"\n"
                "    \"{translation}\""
            )
        elif block_type == 'string':
            return (
                "    # {location}\n"
                "    old \"{original}\"\n"
                "    new \"{translation}\""
            )
        else:
            return ""

    # ========================================================================
    # SAVE METHODS
    # ========================================================================

    def save_parsed_yaml(self, parsed_blocks: Dict[str, ParsedBlock], output_path: Path):
        """Save parsed blocks to YAML file."""
        print(f"💾 Saving parsed YAML to: {output_path}")

        # Add header comment
        header = (
            f"# {output_path.stem} - Parsed Translations\n"
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def save_tags_json(self, tags_file: TagsFileContent, output_path: Path):
        """Save tags file to JSON."""
        print(f"💾 Saving tags JSON to: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tags_file, f, indent=2, ensure_ascii=False)
