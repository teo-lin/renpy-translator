"""
Ren'Py Translation Utilities

Common utilities for parsing and processing Ren'Py translation files.
Shared across all translation backends (Aya-23-8B, MADLAD-400-3B, etc.)
"""

import re
import time
from pathlib import Path
from typing import List, Tuple, Dict


from typing import List, Tuple, Dict, Optional, TypedDict


# Define a TypedDict for a Ren'Py translation block
class RenpyBlock(TypedDict):
    type: str # 'dialogue' or 'string'
    label: str
    original: str
    character_var: Optional[str] # For dialogue blocks
    current_translation: str
    start_pos: int
    end_pos: int
    full_match: str
    source_language: str # Language identifier from the 'translate' statement

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


def detect_language_from_path(path: Path) -> Tuple[str, str]:
    """
    Auto-detect target language from path (e.g., "game/tl/romanian" → ("Romanian", "ro"))

    Returns:
        Tuple of (language_name, language_code)
    """
    path_str = str(path).lower().replace('\\', '/')

    # Language mappings (path name → (proper name, code))
    lang_map = {
        'romanian': ('Romanian', 'ro'),
        'spanish': ('Spanish', 'es'),
        'french': ('French', 'fr'),
        'german': ('German', 'de'),
        'italian': ('Italian', 'it'),
        'portuguese': ('Portuguese', 'pt'),
        'russian': ('Russian', 'ru'),
        'turkish': ('Turkish', 'tr'),
        'czech': ('Czech', 'cs'),
        'polish': ('Polish', 'pl'),
        'ukrainian': ('Ukrainian', 'uk'),
        'bulgarian': ('Bulgarian', 'bg'),
        'chinese': ('Chinese', 'zh'),
        'japanese': ('Japanese', 'ja'),
        'korean': ('Korean', 'ko'),
        'vietnamese': ('Vietnamese', 'vi'),
        'thai': ('Thai', 'th'),
        'indonesian': ('Indonesian', 'id'),
        'arabic': ('Arabic', 'ar'),
        'hebrew': ('Hebrew', 'he'),
        'persian': ('Persian', 'fa'),
        'hindi': ('Hindi', 'hi'),
        'bengali': ('Bengali', 'bn'),
        'dutch': ('Dutch', 'nl'),
        'swedish': ('Swedish', 'sv'),
        'norwegian': ('Norwegian', 'no'),
        'danish': ('Danish', 'da'),
        'finnish': ('Finnish', 'fi'),
        'greek': ('Greek', 'el'),
        'hungarian': ('Hungarian', 'hu'),
    }

    # Check each language in path
    for path_lang, (proper_lang, code) in lang_map.items():
        if f'/{path_lang}/' in path_str or path_str.endswith(f'/{path_lang}') or path_str.endswith(f'{path_lang}'):
            return proper_lang, code

    # Default to Romanian if not detected
    return 'Romanian', 'ro'


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


def apply_post_processing(translation: str) -> str:
    """
    Apply common post-processing to translation output

    - Fix spacing around Ren'Py variables
    - Sanitize quotes to prevent Ren'Py syntax errors

    Args:
        translation: Raw translation text

    Returns:
        Post-processed translation
    """
    # Fix spacing around Ren'Py variables (do this AFTER restoring tags)
    # Ensure space before [variable]: "este[name]" → "este [name]"
    translation = re.sub(r'(\S)(\[[\w\s]+\])', r'\1 \2', translation)

    # CRITICAL: Sanitize quotes to prevent Ren'Py syntax errors
    # Replace any nested double quotes with two single quotes
    translation = translation.replace('"', "''")
    # Fix escaped quotes that might have slipped through
    translation = translation.replace('\\"', "''").replace('\\"', "''")
    translation = translation.replace("\\'", "'")

    return translation
