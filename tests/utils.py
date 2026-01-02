"""
Common test utilities shared across test files

Provides reusable functions for:
- Character discovery
- File operations (backup, restore, cleanup)
- Translation counting
- Validation
"""

import re
import shutil
import sys
import unittest
from pathlib import Path
from typing import Dict, List, TypeVar, Type


# --- Existing Utility Functions (unchanged) ---

def discover_characters(tl_path: Path, game_path: Path) -> Dict[str, dict]:
    """
    Discover characters from .rpy files by scanning for dialogue patterns
    and extracting character names from script.rpy definitions.

    Args:
        tl_path: Path to translation directory (e.g., game/tl/romanian)
        game_path: Path to game root directory

    Returns:
        Dictionary mapping character variables to character info
    """
    character_vars = {}
    character_files = {}  # Track which files each character appears in

    # Step 1: Scan translation .rpy files for dialogue patterns
    rpy_files = list(tl_path.glob("*.rpy"))
    # Exclude backup and generated files
    rpy_files = [f for f in rpy_files if not f.name.endswith('.backup')
                 and not f.name.endswith('.translated.rpy')]

    for rpy_file in rpy_files:
        content = rpy_file.read_text(encoding='utf-8')
        file_name = rpy_file.stem

        # Find dialogue patterns: character_var "text"
        pattern = r'^\s*(\w+)\s+"[^"\\]*(?:\\.[^"\\]*)*"'
        matches = re.finditer(pattern, content, re.MULTILINE)

        for match in matches:
            char_var = match.group(1)

            # Skip keywords
            if char_var in ('translate', 'old', 'new'):
                continue

            # Add character if not seen before
            if char_var not in character_vars:
                character_vars[char_var] = {
                    'name': char_var.upper(),
                    'gender': 'neutral',
                    'type': 'supporting',
                    'description': ''
                }
                character_files[char_var] = []

            # Track this file for the character
            if file_name not in character_files[char_var]:
                character_files[char_var].append(file_name)

    # Step 2: Extract character names from script.rpy define statements
    script_files = list(game_path.rglob("script*.rpy"))
    script_files = [f for f in script_files if 'tl' not in f.parts]

    for script_file in script_files:
        content = script_file.read_text(encoding='utf-8')

        # Match: define var = Character('Name', ...) or Character(None)
        pattern = r'define\s+(\w+)\s*=\s*Character\((?:["\\](.+?)["\\]|None)\s*[,)]'
        matches = re.finditer(pattern, content)

        for match in matches:
            char_var = match.group(1)
            char_name = match.group(2) if match.group(2) else ''

            # Skip if we haven't seen this character in translations
            if char_var not in character_vars:
                continue

            # Handle special cases
            if char_var == 'narrator' or char_name == '':
                character_vars[char_var]['name'] = 'Narrator'
                character_vars[char_var]['type'] = 'narrator'
            # Detect protagonist (common patterns: mc, u, player)
            elif re.match(r'^(mc|u|player)$', char_var) or re.match(r'^\\[.*name.*\\]$', char_name):
                # Use proper name if not a placeholder
                if not re.match(r'^\\[.*\\]$', char_name) and char_name:
                    character_vars[char_var]['name'] = char_name
                else:
                    character_vars[char_var]['name'] = 'MainCharacter'
                character_vars[char_var]['type'] = 'protagonist'
            # Regular characters
            elif not re.match(r'^\?+$|\\[.*\\]$', char_name) and char_name:
                character_vars[char_var]['name'] = char_name
                character_vars[char_var]['type'] = 'main'

    # Step 3: Generate descriptions based on file appearances
    for char_var, files in character_files.items():
        if not files:
            continue

        file_types = []

        # Categorize file types
        cell_files = [f for f in files if f.startswith('Cell')]
        room_files = [f for f in files if f.startswith('Room')]
        exped_files = [f for f in files if f.startswith('Exped')]
        chara_files = [f for f in files if f.startswith('Chara')]

        if cell_files:
            file_types.append('Cell character')
        if room_files:
            file_types.append('Room character')
        if exped_files:
            file_types.append('Expedition character')
        if chara_files:
            file_types.append('Character definition')

        if file_types:
            description = f"{', '.join(file_types)} (appears in {len(files)} files)"
        else:
            description = f"Appears in: {', '.join(files[:3])}"

        character_vars[char_var]['description'] = description

    # Step 4: Add special narrator character (empty string)
    character_vars[''] = {
        'name': 'Narrator',
        'gender': 'neutral',
        'type': 'narrator',
        'description': 'Narration without character'
    }

    return character_vars


def count_translations(file_path: Path) -> int:
    """
    Count how many non-empty translations exist in a .rpy file.

    Args:
        file_path: Path to .rpy file

    Returns:
        Number of non-empty translations found
    """
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    count = 0
    for line in lines:
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Skip "old" lines (source text, not translations)
        if stripped.startswith('old '):
            continue

        # Count character dialogue lines with non-empty translations
        # Format: character_var "translation text"
        if '"' in stripped and '""' not in stripped:
            # Check if it's a character line (starts with identifier) or "new" line
            if stripped.startswith('new ') or (not stripped.startswith('translate') and ' "' in stripped):
                count += 1

    return count


def backup_file(file_path: Path) -> Path:
    """
    Create a backup of a file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def restore_file(file_path: Path, backup_path: Path):
    """
    Restore a file from its backup.

    Args:
        file_path: Original file path
        backup_path: Backup file path
    """
    if backup_path.exists():
        shutil.copy2(backup_path, file_path)
        backup_path.unlink()


def cleanup_files(files: List[Path]):
    """
    Delete a list of files if they exist.

    Args:
        files: List of file paths to delete
    """
    for file_path in files:
        if file_path.exists():
            file_path.unlink()


def validate_rpy_structure(file_path: Path) -> Dict[str, bool]:
    """
    Validate that a .rpy file has expected structure elements.

    Args:
        file_path: Path to .rpy file to validate

    Returns:
        Dictionary mapping check names to pass/fail status
    """
    content = file_path.read_text(encoding='utf-8')

    checks = {
        'has_translate_statements': 'translate ' in content,
        'has_strings_section': 'translate ' in content and 'strings:' in content,
        'has_color_tags': '{color=' in content or '{/color}' in content,
        'has_variables': '[' in content and ']' in content,
        'has_bold_tags': '{b}' in content or '{/b}' in content,
    }

    return checks


def get_rpy_files(directory: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """
    Get list of .rpy files in a directory, excluding certain patterns.

    Args:
        directory: Directory to search
        exclude_patterns: List of patterns to exclude (e.g., ['.backup', '.translated.rpy'])

    Returns:
        List of .rpy file paths
    """
    if exclude_patterns is None:
        exclude_patterns = ['.backup', '.translated.rpy']

    rpy_files = sorted(directory.glob("*.rpy"))

    # Exclude files matching patterns
    filtered_files = []
    for f in rpy_files:
        should_exclude = False
        for pattern in exclude_patterns:
            if f.name.endswith(pattern):
                should_exclude = True
                break
        if not should_exclude:
            filtered_files.append(f)

    return filtered_files


# --- New Base Test Class ---

_TranslatorType = TypeVar('_TranslatorType')

class BaseTranslatorIntegrationTest(unittest.TestCase):
    """
    Base class for translator integration tests.
    Handles common setup like path configuration and provides a template
    for translator initialization.
    """
    project_root = Path(__file__).parent.parent
    translator: _TranslatorType = None # Type hint for the translator instance

    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment: add project paths to sys.path.
        Derived classes should call super().setUpClass() and then initialize
        their specific translator.
        """
        print(f"\nSetting up test environment for {cls.__name__}...")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up resources after all tests in this class have run.
        Derived classes should call super().tearDownClass() and then clean up
        their specific translator if necessary.
        """
        print(f"Tearing down test environment for {cls.__name__}.")
        if cls.translator:
            del cls.translator
            cls.translator = None

    def _get_model_path(self, model_subdir: str, model_filename: str) -> Path:
        """
        Helper method to construct model paths.
        """
        return self.project_root / "models" / model_subdir / model_filename

    def _assert_translation(self, english_text: str, expected_romanian: str):
        """
        Helper method for common translation assertion.
        """
        print(f"Translating: '{english_text}'")
        translation = self.translator.translate(english_text)
        # Handle Unicode characters on Windows console (cp1252 encoding)
        try:
            print(f"Received translation: '{translation}'")
        except UnicodeEncodeError:
            # Use ASCII representation for characters that can't be printed
            print("Received translation:", ascii(translation))
        self.assertEqual(translation, expected_romanian)