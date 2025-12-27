"""
Base Translation Pipeline for Ren'Py Files

Provides a reusable pipeline for translating Ren'Py files with any translation backend.
Handles file parsing, context extraction, post-processing, and file writing.
"""

import time
from pathlib import Path
from typing import List, Dict
from abc import ABC, abstractmethod

from renpy_utils import (
    RenpyTranslationParser,
    RenpyTagExtractor,
    RenpyBlock,
    show_progress,
    apply_post_processing
)


class BaseTranslator(ABC):
    """Abstract base class for translation backends"""

    @abstractmethod
    def translate(self, text: str, **kwargs) -> str:
        """
        Translate text from English to target language

        Args:
            text: Clean English text (tags already removed)
            **kwargs: Backend-specific options (context, speaker, etc.)

        Returns:
            Translated text
        """
        pass

    @property
    @abstractmethod
    def target_language(self) -> str:
        """Return the target language name (e.g., 'Romanian', 'Spanish')"""
        pass


class RenpyTranslationPipeline:
    """
    Reusable translation pipeline for Ren'Py files

    Works with any translator backend that implements BaseTranslator interface.
    Handles all common tasks: parsing, context extraction, tag preservation, post-processing.
    """

    def __init__(self, translator: BaseTranslator):
        """
        Initialize pipeline with a translator backend

        Args:
            translator: Any translator implementing BaseTranslator interface
        """
        self.translator = translator
        self.target_language = translator.target_language

    @staticmethod
    def _get_dialogue_context(current_block: Dict, all_blocks: List[Dict],
                              max_context: int = 3) -> List[str]:
        """
        Get surrounding dialogue context for a dialogue block

        For dialogue blocks, we want context from nearby dialogue in the same file,
        NOT from menu options or unrelated dialogue.

        Args:
            current_block: The block we're translating
            all_blocks: All blocks from the file
            max_context: Maximum number of context lines (before + after)

        Returns:
            List of context strings in format ["speaker: text", ...]
        """
        if current_block['type'] != 'dialogue':
            return None

        context = []
        current_pos = current_block['start_pos']

        # Find dialogue blocks near this one (within a reasonable distance)
        # A reasonable distance is ~5000 characters (roughly same scene)
        nearby_dialogue = []
        for block in all_blocks:
            if block['type'] == 'dialogue' and block['start_pos'] != current_pos:
                distance = abs(block['start_pos'] - current_pos)
                if distance < 5000:  # Same scene threshold
                    nearby_dialogue.append((distance, block['start_pos'], block))

        # Sort by position in file
        nearby_dialogue.sort(key=lambda x: x[1])

        # Get context: up to max_context/2 before and after
        context_before = []
        context_after = []

        for _, pos, block in nearby_dialogue:
            if pos < current_pos:
                context_before.append(block)
            elif pos > current_pos:
                context_after.append(block)

        # Take the closest ones
        context_before = context_before[-(max_context // 2):]
        context_after = context_after[:(max_context // 2 + max_context % 2)]

        # Build context strings
        for block in context_before + context_after:
            speaker = block.get('character_var', 'unknown')
            text = RenpyTranslationParser.extract_dialogue(block['original'])
            # Remove tags for cleaner context
            clean_text, _ = RenpyTagExtractor.extract_tags(text)
            if clean_text.strip():
                context.append(f"{speaker}: {clean_text}")

        return context if context else None

    def translate_file(self, input_path: Path, output_path: Path = None,
                       skip_empty: bool = True) -> Dict:
        """
        Translate a single Ren'Py translation file

        Args:
            input_path: Input .rpy file
            output_path: Output .rpy file (overwrites if exists, None = same as input)
            skip_empty: Skip blocks that already have non-empty translations

        Returns:
            Statistics dict
        """
        if output_path is None:
            output_path = input_path

        print(f"\nProcessing: {input_path.name}")

        # Parse file
        blocks = RenpyTranslationParser.parse_file(input_path)
        print(f"  Found {len(blocks)} translation blocks")

        if not blocks:
            print("  No translation blocks found, skipping")
            return {'total': 0, 'translated': 0, 'skipped': 0}

        # Filter blocks - ONLY skip if translation is non-empty
        if skip_empty:
            to_translate = [b for b in blocks if not b['current_translation'] or b['current_translation'].strip() == '']
        else:
            to_translate = blocks

        skipped = len(blocks) - len(to_translate)

        if skipped > 0:
            print(f"  Skipping {skipped} blocks with existing translations")

        if not to_translate:
            print("  Nothing to translate")
            return {'total': len(blocks), 'translated': 0, 'skipped': skipped}

        print(f"  Translating {len(to_translate)} blocks...")

        # Translate each block and store results
        translations = {}
        start_time = time.time()

        for i, block in enumerate(to_translate):
            original_text = block['original']

            if block['type'] == 'dialogue':
                # Extract just the dialogue text (remove character prefix)
                dialogue_text = RenpyTranslationParser.extract_dialogue(original_text)
            else:
                # For strings, use the text as-is
                dialogue_text = original_text

            # Extract tags
            clean_text, tags = RenpyTagExtractor.extract_tags(dialogue_text)

            # Skip empty texts
            if not clean_text.strip():
                continue

            # Get speaker character code (only for dialogue)
            speaker = block['character_var'] if block['type'] == 'dialogue' else None

            # Show progress
            show_progress(i + 1, len(to_translate), start_time, prefix="  ")

            # Get context based on block type
            context = None
            if block['type'] == 'dialogue':
                # For dialogue: get surrounding dialogue from the same file location
                context = self._get_dialogue_context(block, blocks, max_context=3)

            # Translate clean text with context (using the translator backend)
            translation = self.translator.translate(
                clean_text,
                context=context,
                speaker=speaker
            )

            # Restore tags
            final_translation = RenpyTagExtractor.restore_tags(
                translation, tags, clean_text
            )

            # Apply common post-processing
            final_translation = apply_post_processing(final_translation)

            # Store translation for this block
            translations[block['label']] = final_translation

        # Clear progress line and show completion
        print()  # Newline after progress bar
        print(f"    [OK] Translated {len(translations)} blocks")

        # Update content by processing blocks in reverse order
        # This prevents position invalidation
        content = input_path.read_text(encoding='utf-8')

        # CRITICAL: Replace "translate <source_lang> strings:" with "translate <target_lang> strings:"
        # This fixes the bug where string sections had wrong language identifier
        target_lang_lower = self.target_language.lower()
        content = RenpyTranslationParser.STRING_SECTION_PATTERN.sub(
            f'translate {target_lang_lower} strings:',
            content
        )

        for block in reversed(to_translate):
            if block['label'] not in translations:
                continue

            final_translation = translations[block['label']]
            new_block = RenpyTranslationParser.create_translation_block(
                block, final_translation, target_language=self.target_language.lower()
            )
            content = (
                content[:block['start_pos']] +
                new_block +
                content[block['end_pos']:]
            )

        print(f"    [OK] Updated {len(translations)} blocks" + " " * 20)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
        print(f"  Saved to: {output_path}")

        return {
            'total': len(blocks),
            'translated': len(translations),
            'skipped': skipped
        }

    def translate_directory(self, input_dir: Path, output_dir: Path,
                           pattern: str = "*.rpy", skip_empty: bool = True) -> Dict:
        """
        Translate all .rpy files in a directory

        Args:
            input_dir: Input directory
            output_dir: Output directory (mirrors structure)
            pattern: File pattern to match
            skip_empty: Skip blocks with existing translations

        Returns:
            Overall statistics
        """
        input_files = list(input_dir.rglob(pattern))

        if not input_files:
            print(f"No files matching '{pattern}' found in {input_dir}")
            return {'files': 0, 'total_blocks': 0, 'translated_blocks': 0}

        print(f"\nFound {len(input_files)} files to translate")
        print("=" * 70)

        total_stats = {'files': 0, 'total_blocks': 0, 'translated_blocks': 0, 'skipped_blocks': 0}
        dir_start_time = time.time()

        for file_idx, input_file in enumerate(input_files):
            # Show overall progress for multi-file translation
            if len(input_files) > 1:
                print()
                show_progress(file_idx, len(input_files), dir_start_time, prefix="Overall: ")
                print(f"\n[File {file_idx + 1}/{len(input_files)}]", flush=True)

            # Calculate output path (mirror directory structure)
            rel_path = input_file.relative_to(input_dir)
            output_file = output_dir / rel_path

            stats = self.translate_file(input_file, output_file, skip_empty=skip_empty)

            total_stats['files'] += 1
            total_stats['total_blocks'] += stats['total']
            total_stats['translated_blocks'] += stats['translated']
            total_stats['skipped_blocks'] += stats['skipped']

        print("\n" + "=" * 70)
        print("TRANSLATION COMPLETE")
        print(f"  Files processed: {total_stats['files']}")
        print(f"  Blocks found: {total_stats['total_blocks']}")
        print(f"  Blocks translated: {total_stats['translated_blocks']}")
        print(f"  Blocks skipped: {total_stats['skipped_blocks']}")

        return total_stats
