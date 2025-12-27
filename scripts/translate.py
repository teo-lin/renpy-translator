"""
Ren'Py Translation Pipeline using Aya-23-8B

Translates Ren'Py game files from English to any supported language while preserving:
- Ren'Py formatting tags: {color=...}, {size=...}, {/color}, etc.
- Variables: [name], [variable_name]
- Special characters and formatting

CRITICAL: Language Identifier Handling
- Automatically converts "translate english" to "translate <target_language>" in output
- Prevents Ren'Py "translation already exists" errors
- Ensures translation files use correct language declaration

Usage:
    python translate.py <input_file_or_dir> [--language LANG] [output_dir]

    If --language is not specified, the language is auto-detected from the path
    (e.g., "game/tl/romanian" → Romanian)
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict
import json
import time

# Fix Windows PATH for CUDA DLLs (required for llama-cpp-python)
if sys.platform == "win32":
    torch_lib = str(Path(__file__).parent.parent / "venv" / "Lib" / "site-packages" / "torch" / "lib")
    if os.path.exists(torch_lib) and torch_lib not in os.environ["PATH"]:
        os.environ["PATH"] = torch_lib + os.pathsep + os.environ["PATH"]

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from core import Aya23Translator


def detect_language_from_path(path: Path) -> str:
    """
    Auto-detect target language from path (e.g., "game/tl/romanian" → "Romanian")

    Returns capitalized language name (e.g., "Romanian", "Spanish", "French")
    """
    path_str = str(path).lower().replace('\\', '/')

    # Language mappings (path name → proper name)
    lang_map = {
        'romanian': 'Romanian',
        'spanish': 'Spanish',
        'french': 'French',
        'german': 'German',
        'italian': 'Italian',
        'portuguese': 'Portuguese',
        'russian': 'Russian',
        'turkish': 'Turkish',
        'czech': 'Czech',
        'polish': 'Polish',
        'ukrainian': 'Ukrainian',
        'bulgarian': 'Bulgarian',
        'chinese': 'Chinese',
        'japanese': 'Japanese',
        'korean': 'Korean',
        'vietnamese': 'Vietnamese',
        'thai': 'Thai',
        'indonesian': 'Indonesian',
        'arabic': 'Arabic',
        'hebrew': 'Hebrew',
        'persian': 'Persian',
        'hindi': 'Hindi',
        'bengali': 'Bengali',
    }

    # Check each language in path
    for path_lang, proper_lang in lang_map.items():
        if f'/{path_lang}/' in path_str or path_str.endswith(f'/{path_lang}') or path_str.endswith(f'{path_lang}'):
            return proper_lang

    # Default to Romanian if not detected
    return 'Romanian'


def show_progress(current, total, start_time, prefix=""):
    """Display simple progress bar with >>> characters and time labels"""
    percentage = (current / total) * 100 if total > 0 else 0
    elapsed = time.time() - start_time

    # Calculate ETA
    if current > 0 and elapsed > 0:
        rate = current / elapsed
        remaining = (total - current) / rate if rate > 0 else 0
    else:
        remaining = 0

    # Format time strings
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{int(elapsed)}s"
    remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s" if remaining >= 60 else f"{int(remaining)}s"

    # Create progress bar with >>> characters
    bar_width = 50
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = ">" * filled + " " * (bar_width - filled)

    # Display with labels
    print(f"\r{prefix}[{bar}] {current}/{total} ({percentage:.0f}%) | Elapsed: {elapsed_str} | ETA: {remaining_str}",
          end='', flush=True)


class RenpyTagExtractor:
    """Extract and restore Ren'Py tags and variables"""

    # Patterns for Ren'Py formatting
    TAG_PATTERN = re.compile(r'\{[^}]+\}')  # {color=#fff}, {/color}, etc.
    VAR_PATTERN = re.compile(r'\[[^\]]+\]')  # [name], [variable]

    @classmethod
    def extract_tags(cls, text: str) -> Tuple[str, List[Tuple[int, str]]]:
        """
        Extract tags and variables from text, return clean text and tag positions

        Returns:
            (clean_text, [(position, tag), ...])
        """
        tags = []
        clean_text = text

        # Find all tags and variables
        all_matches = []
        for match in cls.TAG_PATTERN.finditer(text):
            all_matches.append((match.start(), match.group()))
        for match in cls.VAR_PATTERN.finditer(text):
            all_matches.append((match.start(), match.group()))

        # Sort by position (reverse order for removal)
        all_matches.sort(key=lambda x: x[0], reverse=True)

        # Remove tags from text and store positions
        for pos, tag in all_matches:
            # Calculate position in words/chars for restoration
            before_tag = text[:pos]
            tags.insert(0, (len(before_tag), tag))
            clean_text = clean_text[:pos] + clean_text[pos + len(tag):]

        # Clean up extra spaces left after tag removal
        # Remove multiple consecutive spaces
        clean_text = re.sub(r' +', ' ', clean_text)
        # Remove spaces before punctuation
        clean_text = re.sub(r' +([.,!?;:])', r'\1', clean_text)

        return clean_text.strip(), tags

    @classmethod
    def restore_tags(cls, translated_text: str, tags: List[Tuple[int, str]], original_text: str) -> str:
        """
        Restore tags into translated text based on relative positions

        Strategy:
        - If text length is similar, use proportional positions
        - Place tags at word boundaries when possible
        - Never insert tags inside other tags
        """
        if not tags:
            return translated_text

        result = translated_text
        original_len = len(original_text)
        translated_len = len(translated_text)

        # Sort tags by position for insertion
        sorted_tags = sorted(tags, key=lambda x: x[0], reverse=True)

        for orig_pos, tag in sorted_tags:
            # Calculate proportional position
            if original_len > 0:
                ratio = orig_pos / original_len
                new_pos = int(ratio * translated_len)
            else:
                new_pos = 0

            # Clamp position to text bounds
            new_pos = max(0, min(new_pos, len(result)))

            # CRITICAL FIX: Ensure we don't insert inside another tag
            # Check if we're inside a tag (between { and } or [ and ])
            safe_pos = cls._find_safe_insertion_point(result, new_pos)

            # Insert tag
            result = result[:safe_pos] + tag + result[safe_pos:]

        return result

    @staticmethod
    def _find_safe_insertion_point(text: str, target_pos: int) -> int:
        """
        Find a safe position to insert a tag, ensuring we don't break existing tags

        Args:
            text: The text to insert into
            target_pos: The desired insertion position

        Returns:
            A safe position that won't break existing tags
        """
        # Clamp to text bounds
        target_pos = max(0, min(target_pos, len(text)))

        # Check if we're inside a tag at target_pos
        # Count unclosed braces/brackets before this position
        before_text = text[:target_pos]

        # Count { and } before target
        open_braces = before_text.count('{')
        close_braces = before_text.count('}')

        # Count [ and ] before target
        open_brackets = before_text.count('[')
        close_brackets = before_text.count(']')

        # If we're inside a tag, find the end of it
        if open_braces > close_braces:
            # We're inside {}, find the next }
            next_close = text.find('}', target_pos)
            if next_close != -1:
                return next_close + 1

        if open_brackets > close_brackets:
            # We're inside [], find the next ]
            next_close = text.find(']', target_pos)
            if next_close != -1:
                return next_close + 1

        # Position is safe
        return target_pos


class RenpyTranslationParser:
    """Parse and write Ren'Py translation files"""

    # CRITICAL: Capture language identifier to ensure correct output
    # When reading "translate english" source, must output "translate romanian"
    TRANSLATE_BLOCK_PATTERN = re.compile(
        r'# game/[^\n]+\n'  # Comment with file location
        r'translate (\w+) (\w+):\s*\n'  # translate <language> <label_name>:
        r'\s*# (.+)\n'  # Original text comment
        r'\s*(\w+) "(.*)"'  # character_var "translation"
    )

    # String blocks inside "translate <language> strings:" sections
    STRING_BLOCK_PATTERN = re.compile(
        r'# game/[^\n]+\n'  # Comment with file location
        r'\s*old "(.+)"\s*\n'  # old "original text"
        r'\s*new "(.*)"'  # new "translation"
    )

    # Pattern to match "translate <language> strings:" declarations
    STRING_SECTION_PATTERN = re.compile(r'translate (\w+) strings:')

    @staticmethod
    def extract_dialogue(text: str) -> str:
        """
        Extract dialogue text from a line like 'am "Hello!"'
        Returns just 'Hello!'
        """
        # Match pattern: character_var "dialogue text"
        match = re.search(r'\w+\s+"(.+)"', text)
        if match:
            return match.group(1)
        # Fallback: return the original text
        return text

    @classmethod
    def parse_file(cls, file_path: Path) -> List[Dict]:
        """
        Parse Ren'Py translation file and extract all translation blocks

        Returns:
            List of dicts with: {
                'type': 'dialogue' or 'string',
                'label': str,
                'original': str,
                'character_var': str (for dialogue) or None,
                'current_translation': str,
                'start_pos': int,
                'end_pos': int,
                'full_match': str
            }
        """
        content = file_path.read_text(encoding='utf-8')
        blocks = []

        # Parse dialogue blocks
        for match in cls.TRANSLATE_BLOCK_PATTERN.finditer(content):
            source_language = match.group(1)  # Capture source language (e.g., "english")
            label = match.group(2)
            original = match.group(3)
            character_var = match.group(4)
            current_translation = match.group(5)

            blocks.append({
                'type': 'dialogue',
                'source_language': source_language,
                'label': label,
                'original': original,
                'character_var': character_var,
                'current_translation': current_translation,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'full_match': match.group(0)
            })

        # Parse string blocks (UI/menu text)
        for match in cls.STRING_BLOCK_PATTERN.finditer(content):
            original = match.group(1)
            current_translation = match.group(2)

            blocks.append({
                'type': 'string',
                'label': f'string_{match.start()}',  # Unique label based on position
                'original': original,
                'character_var': None,
                'current_translation': current_translation,
                'start_pos': match.start(),
                'end_pos': match.end(),
                'full_match': match.group(0)
            })

        # Sort by position in file
        blocks.sort(key=lambda x: x['start_pos'])

        return blocks

    @classmethod
    def create_translation_block(cls, block: Dict, translation: str, target_language: str = "romanian") -> str:
        """
        Recreate translation block with new translation and correct language identifier

        Args:
            block: Block dict with 'full_match', 'type', etc.
            translation: New translation text
            target_language: Target language identifier (e.g., "romanian", "spanish")

        CRITICAL: Always outputs "translate <target_language>" regardless of source language
        This fixes the bug where target language files incorrectly had "translate english"
        """
        full_match = block['full_match']

        # Replace source language with target language (e.g., "translate english" → "translate romanian")
        if block['type'] == 'dialogue' and 'source_language' in block:
            full_match = full_match.replace(
                f"translate {block['source_language']} ",
                f"translate {target_language} ",
                1  # Only replace first occurrence
            )

        lines = full_match.split('\n')

        if block['type'] == 'dialogue':
            # Update the translation line (last line) for dialogue
            lines[-1] = f'    {block["character_var"]} "{translation}"'
        else:  # string type
            # Update the translation line (last line) for strings
            lines[-1] = f'    new "{translation}"'

        return '\n'.join(lines)


class RenpyTranslationPipeline:
    """End-to-end translation pipeline for Ren'Py files"""

    def __init__(self, model_path: str, target_language: str = "Romanian", glossary_path: str = None):
        """
        Initialize pipeline

        Args:
            model_path: Path to Aya-23-8B GGUF model
            target_language: Target language name (e.g., "Romanian", "Spanish", "French")
            glossary_path: Optional path to glossary JSON
        """
        print(f"Initializing Ren'Py Translation Pipeline (EN→{target_language})...")
        self.translator = Aya23Translator(model_path, target_language=target_language)
        self.target_language = target_language

        self.glossary = {}
        if glossary_path and Path(glossary_path).exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                self.glossary = json.load(f)
            print(f"[OK] Loaded glossary with {len(self.glossary)} terms")

    @staticmethod
    def _get_dialogue_context(current_block: Dict, all_blocks: List[Dict], max_context: int = 3) -> List[str]:
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
            skip_empty: Skip blocks that already have translations

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

        # Filter blocks
        to_translate = [b for b in blocks if not skip_empty or b['current_translation'] == '']
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

            # Translate clean text with context
            translation = self.translator.translate(
                clean_text,
                glossary=self.glossary,
                context=context,
                speaker=speaker
            )

            # Restore tags
            final_translation = RenpyTagExtractor.restore_tags(
                translation, tags, clean_text
            )

            # Fix spacing around Ren'Py variables (do this AFTER restoring tags)
            # Ensure space before [variable]: "este[name]" → "este [name]"
            final_translation = re.sub(r'(\S)(\[[\w\s]+\])', r'\1 \2', final_translation)
            # Remove unwanted letters after variables: "[name]u" → "[name]"
            final_translation = re.sub(r'(\[[\w\s]+\])([a-zA-Z]+)', lambda m: m.group(1) + (' ' + m.group(2) if m.group(2) not in ['u', 'a', 'i'] else ''), final_translation)

            # CRITICAL: Sanitize quotes to prevent Ren'Py syntax errors
            # Replace any nested double quotes with two single quotes
            final_translation = final_translation.replace('"', "''")
            # Fix escaped quotes that might have slipped through
            final_translation = final_translation.replace('\\"', "''").replace('\\"', "''")
            final_translation = final_translation.replace("\\'", "'")

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

        print(f"    [OK] Translated {len(to_translate)} blocks" + " " * 20)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
        print(f"  Saved to: {output_path}")

        return {
            'total': len(blocks),
            'translated': len(to_translate),
            'skipped': skipped
        }

    def translate_directory(self, input_dir: Path, output_dir: Path,
                           pattern: str = "*.rpy") -> Dict:
        """
        Translate all .rpy files in a directory

        Args:
            input_dir: Input directory
            output_dir: Output directory (mirrors structure)
            pattern: File pattern to match

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

            stats = self.translate_file(input_file, output_file)

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


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print("  python translate.py game/tl/romanian/")
        print("  python translate.py game/tl/spanish/ --language Spanish")
        print("  python translate.py game/tl/romanian/ game/tl/romanian_translated/")
        sys.exit(1)

    # Parse arguments
    input_path = Path(sys.argv[1])
    target_language = None
    output_path_arg = None

    # Check for --language parameter
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--language' and i + 1 < len(sys.argv):
            target_language = sys.argv[i + 1]
        elif not arg.startswith('--') and arg != target_language:
            output_path_arg = arg

    # Auto-detect language from path if not specified
    if target_language is None:
        target_language = detect_language_from_path(input_path)
        print(f"Auto-detected language: {target_language}")

    # Default paths
    project_root = Path(__file__).parent.parent
    model_path = project_root / "models" / "aya-23-8B-GGUF" / "aya-23-8B-Q4_K_M.gguf"

    # Map language names to ISO codes
    lang_code_map = {
        'Romanian': 'ro',
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de',
        'Italian': 'it',
        'Portuguese': 'pt'
    }
    lang_code = lang_code_map.get(target_language, target_language.lower()[:2])

    # Generic glossary fallback: uncensored → censored → none
    glossary_path = None
    for glossary_variant in [f"{lang_code}_uncensored_glossary.json", f"{lang_code}_glossary.json"]:
        candidate = project_root / "data" / glossary_variant
        if candidate.exists():
            glossary_path = candidate
            print(f"[OK] Using glossary: {glossary_variant}")
            break

    if not glossary_path:
        print(f"[WARNING] No glossary found for {target_language} ({lang_code})")

    # Initialize pipeline
    pipeline = RenpyTranslationPipeline(str(model_path), target_language, str(glossary_path) if glossary_path else None)

    # Translate
    if input_path.is_file():
        # Single file
        output_path = Path(output_path_arg) if output_path_arg else None
        pipeline.translate_file(input_path, output_path)
    else:
        # Directory
        output_dir = Path(output_path_arg) if output_path_arg else input_path.parent / target_language.lower()
        pipeline.translate_directory(input_path, output_dir)


if __name__ == "__main__":
    main()
