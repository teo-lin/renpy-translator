"""
Batch Translation Engine

Handles batch translation of parsed YAML files using various translation backends.
Supports context extraction and intelligent untranslated block identification.
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    # Try relative import (when used as package)
    from .models import ParsedBlock, TagsFileContent, is_separator_block, parse_block_id
except ImportError:
    # Fall back to absolute import (when run standalone or from tests)
    from models import ParsedBlock, TagsFileContent, is_separator_block, parse_block_id


@dataclass
class TranslationContext:
    """Context for a translation block."""
    block_id: str
    character_name: str
    text_to_translate: str
    context_before: List[str]
    context_after: List[str]


class BatchTranslator:
    """Batch translation manager for parsed YAML files."""

    def __init__(
        self,
        translator,
        context_before: int = 3,
        context_after: int = 1
    ):
        """
        Initialize batch translator.

        Args:
            translator: Translation backend (Aya23Translator or MADLAD400Translator)
            context_before: Number of lines of context before current block
            context_after: Number of lines of context after current block
        """
        self.translator = translator
        self.context_before = context_before
        self.context_after = context_after

    # ========================================================================
    # MAIN TRANSLATION METHOD
    # ========================================================================

    def translate_file(
        self,
        parsed_yaml_path: Path,
        tags_json_path: Path,
        output_yaml_path: Optional[Path] = None
    ) -> Dict[str, int]:
        """
        Translate untranslated blocks in a parsed YAML file.

        Args:
            parsed_yaml_path: Path to .parsed.yaml file
            tags_json_path: Path to .tags.json file
            output_yaml_path: Path to output YAML (default: overwrite input)

        Returns:
            Dict with statistics: {'total', 'translated', 'skipped', 'failed'}
        """
        if output_yaml_path is None:
            output_yaml_path = parsed_yaml_path

        print(f"📖 Loading files for translation...")

        # Load files
        with open(parsed_yaml_path, 'r', encoding='utf-8') as f:
            parsed_blocks: Dict[str, ParsedBlock] = yaml.safe_load(f)

        with open(tags_json_path, 'r', encoding='utf-8') as f:
            tags_file: TagsFileContent = json.load(f)

        metadata = tags_file['metadata']
        structure = tags_file['structure']
        tagged_blocks = tags_file['blocks']
        character_map = tags_file['character_map']

        # Identify untranslated blocks (in Python, not LLM)
        untranslated_ids = self._identify_untranslated(parsed_blocks)
        total_blocks = len([bid for bid in parsed_blocks if not is_separator_block(bid, parsed_blocks[bid])])

        print(f"📦 Total blocks: {total_blocks}")
        print(f"📝 Untranslated blocks: {len(untranslated_ids)}")
        print(f"✅ Already translated: {total_blocks - len(untranslated_ids)}")

        if not untranslated_ids:
            print("✨ All blocks are already translated!")
            return {
                'total': total_blocks,
                'translated': 0,
                'skipped': total_blocks,
                'failed': 0
            }

        # Extract context for each untranslated block
        contexts = self._extract_contexts(
            untranslated_ids,
            parsed_blocks,
            tagged_blocks,
            structure['block_order']
        )

        # Translate blocks
        print(f"\n🚀 Starting translation...")
        translated_count = 0
        failed_count = 0

        for idx, context in enumerate(contexts, start=1):
            print(f"\n[{idx}/{len(contexts)}] Translating block: {context.block_id}")

            # Get character name for context
            char_name = context.character_name
            speaker = char_name if char_name not in ['Narrator', 'Choice'] else None

            # Format context for translator
            context_list = context.context_before + context.context_after

            try:
                # Translate
                translation = self.translator.translate(
                    text=context.text_to_translate,
                    context=context_list if context_list else None,
                    speaker=speaker
                )

                # Update block
                parsed_blocks[context.block_id]['ro'] = translation
                translated_count += 1

                print(f"  ✅ Translated: {translation[:60]}...")

            except Exception as e:
                print(f"  ❌ Translation failed: {e}")
                failed_count += 1

        # Save updated YAML
        print(f"\n💾 Saving translated file to: {output_yaml_path}")
        self._save_yaml(parsed_blocks, output_yaml_path, metadata)

        # Return statistics
        stats = {
            'total': total_blocks,
            'translated': translated_count,
            'skipped': total_blocks - len(untranslated_ids),
            'failed': failed_count
        }

        print(f"\n📊 Translation complete!")
        print(f"   Total blocks: {stats['total']}")
        print(f"   Translated: {stats['translated']}")
        print(f"   Already done: {stats['skipped']}")
        print(f"   Failed: {stats['failed']}")

        return stats

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _identify_untranslated(self, parsed_blocks: Dict[str, ParsedBlock]) -> List[str]:
        """
        Identify blocks that need translation.

        A block needs translation if:
        - It's not a separator
        - The 'ro' field is empty or whitespace-only
        """
        untranslated = []

        for block_id, block in parsed_blocks.items():
            # Skip separators
            if is_separator_block(block_id, block):
                continue

            # Check if translation is missing
            ro_text = block.get('ro', '')
            if not ro_text or not ro_text.strip():
                untranslated.append(block_id)

        return untranslated

    def _extract_contexts(
        self,
        untranslated_ids: List[str],
        parsed_blocks: Dict[str, ParsedBlock],
        tagged_blocks: Dict[str, 'TaggedBlock'],
        block_order: List[str]
    ) -> List[TranslationContext]:
        """
        Extract context for each untranslated block.

        Context includes:
        - N lines before (already translated preferred)
        - M lines after (already translated preferred)
        - Character name
        """
        contexts: List[TranslationContext] = []

        # Build index map: block_id -> position in order
        block_index = {block_id: idx for idx, block_id in enumerate(block_order)}

        for block_id in untranslated_ids:
            idx = block_index.get(block_id)
            if idx is None:
                continue

            # Get character name
            _, char_name = parse_block_id(block_id)

            # Get text to translate
            text_to_translate = parsed_blocks[block_id]['en']

            # Extract context before
            context_before: List[str] = []
            for i in range(idx - 1, max(-1, idx - self.context_before - 10), -1):
                if len(context_before) >= self.context_before:
                    break

                prev_id = block_order[i]
                prev_block = parsed_blocks.get(prev_id)

                if not prev_block or is_separator_block(prev_id, prev_block):
                    continue

                # Prefer translated context
                prev_text = prev_block.get('ro', '') or prev_block.get('en', '')
                if prev_text.strip():
                    prev_char = parse_block_id(prev_id)[1]
                    context_before.insert(0, f"{prev_char}: {prev_text}")

            # Extract context after
            context_after: List[str] = []
            for i in range(idx + 1, min(len(block_order), idx + self.context_after + 10)):
                if len(context_after) >= self.context_after:
                    break

                next_id = block_order[i]
                next_block = parsed_blocks.get(next_id)

                if not next_block or is_separator_block(next_id, next_block):
                    continue

                # Prefer translated context
                next_text = next_block.get('ro', '') or next_block.get('en', '')
                if next_text.strip():
                    next_char = parse_block_id(next_id)[1]
                    context_after.append(f"{next_char}: {next_text}")

            contexts.append(TranslationContext(
                block_id=block_id,
                character_name=char_name,
                text_to_translate=text_to_translate,
                context_before=context_before,
                context_after=context_after
            ))

        return contexts

    def _save_yaml(
        self,
        parsed_blocks: Dict[str, ParsedBlock],
        output_path: Path,
        metadata: dict
    ):
        """Save parsed blocks to YAML file with header."""
        from datetime import datetime

        header = (
            f"# {output_path.stem} - Parsed Translations\n"
            f"# Original extraction: {metadata.get('extracted_at', 'unknown')}\n"
            f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
