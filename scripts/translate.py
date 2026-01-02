"""
Modular Translation Pipeline Script

Translates .parsed.yaml files using batch translation with context awareness.
Uses configuration from current_config.json and character.json files.
Supports glossary and custom prompts with fallback hierarchy.

Usage:
    python translate.py --game <game_name>
    python translate.py  # Uses current_game from config
"""

import sys
import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import ParsedBlock, is_separator_block, parse_block_id
from translators.aya23_translator import Aya23Translator
from renpy_utils import show_progress


class ModularBatchTranslator:
    """
    Batch translator for parsed YAML files with custom context logic.

    - DIALOGUE blocks: Use context_before + context_after from surrounding blocks
    - CHOICE blocks: No dialogue context, only character info from characters.json
    """

    def __init__(
        self,
        translator,
        characters: Dict,
        target_lang_code: str,
        context_before: int = 3,
        context_after: int = 1
    ):
        """
        Initialize modular batch translator.

        Args:
            translator: Translation backend (Aya23Translator or MADLAD400Translator)
            characters: Character mapping from characters.json
            target_lang_code: Target language code (e.g., 'ro', 'es')
            context_before: Number of lines of context before current block (for dialogue)
            context_after: Number of lines of context after current block (for dialogue)
        """
        self.translator = translator
        self.characters = characters
        self.target_lang_code = target_lang_code
        self.context_before = context_before
        self.context_after = context_after

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

        print(f"\n  Processing: {parsed_yaml_path.name}")

        # Load files
        with open(parsed_yaml_path, 'r', encoding='utf-8') as f:
            parsed_blocks: Dict[str, ParsedBlock] = yaml.safe_load(f)

        with open(tags_json_path, 'r', encoding='utf-8-sig') as f:
            tags_file = json.load(f)

        metadata = tags_file['metadata']
        structure = tags_file['structure']
        block_order = structure['block_order']

        # Identify untranslated blocks
        untranslated_ids = self._identify_untranslated(parsed_blocks, self.target_lang_code)
        total_blocks = len([bid for bid in parsed_blocks if not is_separator_block(bid, parsed_blocks[bid])])

        print(f"    Total blocks: {total_blocks}")
        print(f"    Untranslated: {len(untranslated_ids)}")
        print(f"    Already done: {total_blocks - len(untranslated_ids)}")

        if not untranslated_ids:
            print("    [OK] All blocks already translated!")
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
            block_order
        )

        # Translate blocks with progress tracking
        print(f"    Translating {len(contexts)} blocks...")
        translated_count = 0
        failed_count = 0
        start_time = time.time()

        for idx, context_item in enumerate(contexts, start=1):
            block_id = context_item['block_id']
            char_name = context_item['character_name']
            text_to_translate = context_item['text']
            context_list = context_item['context']
            is_choice = context_item['is_choice']

            # Show progress
            show_progress(idx, len(contexts), start_time, prefix="    ")

            # Get speaker for context
            speaker = None if char_name in ['Narrator', 'Choice'] else char_name

            try:
                # Translate
                translation = self.translator.translate(
                    text=text_to_translate,
                    context=context_list if context_list else None,
                    speaker=speaker
                )

                # Debug: Log first 3 translations to verify assignment
                if translated_count < 3:
                    print(f"\n    [DEBUG] Block {block_id}")
                    print(f"            EN: {text_to_translate[:40]}...")
                    print(f"            RO: {translation[:40]}...")

                # Update block
                parsed_blocks[block_id][self.target_lang_code] = translation
                translated_count += 1

            except Exception as e:
                print(f"\n    [ERROR] Translation failed for {block_id}: {e}")
                failed_count += 1

        # Clear progress line
        print()

        # Save updated YAML
        try:
            self._save_yaml(parsed_blocks, output_yaml_path, metadata)
            print(f"    [OK] Saved to: {output_yaml_path.name}")

        except Exception as e:
            print(f"    [ERROR] Failed to save YAML file: {e}")
            import traceback
            traceback.print_exc()
            # Mark all translations as failed since they weren't saved
            failed_count += translated_count
            translated_count = 0

        # Return statistics
        stats = {
            'total': total_blocks,
            'translated': translated_count,
            'skipped': total_blocks - len(untranslated_ids),
            'failed': failed_count
        }

        print(f"    [OK] Translated: {stats['translated']}, Failed: {stats['failed']}")

        return stats

    def _identify_untranslated(self, parsed_blocks: Dict[str, ParsedBlock], lang_code: str) -> List[str]:
        """
        Identify blocks that need translation.

        A block needs translation if:
        - It's not a separator
        - The target language field is empty or whitespace-only
        """
        untranslated = []

        for block_id, block in parsed_blocks.items():
            # Skip separators
            if is_separator_block(block_id, block):
                continue

            # Check if translation is missing
            target_text = block.get(lang_code, '')
            if not target_text or not target_text.strip():
                untranslated.append(block_id)

        return untranslated

    def _extract_contexts(
        self,
        untranslated_ids: List[str],
        parsed_blocks: Dict[str, ParsedBlock],
        block_order: List[str]
    ) -> List[Dict]:
        """
        Extract context for each untranslated block.

        Context strategy:
        - DIALOGUE blocks: N lines before + M lines after
        - CHOICE blocks: No dialogue context (only character info from characters.json)
        """
        contexts: List[Dict] = []

        # Build index map: block_id -> position in order
        block_index = {block_id: idx for idx, block_id in enumerate(block_order)}

        for block_id in untranslated_ids:
            idx = block_index.get(block_id)
            if idx is None:
                continue

            # Parse block ID to get character name
            _, char_name = parse_block_id(block_id)

            # Check if this is a CHOICE block
            is_choice = char_name == 'Choice' or block_id.endswith('-Choice')

            # Get text to translate
            text_to_translate = parsed_blocks[block_id]['en']

            # Extract context based on block type
            if is_choice:
                # CHOICE blocks: No dialogue context
                # Only character info is used (passed via translator's character knowledge)
                context_list = []
            else:
                # DIALOGUE blocks: Use context from surrounding blocks
                context_list = self._extract_dialogue_context(
                    block_id, idx, parsed_blocks, block_order
                )

            contexts.append({
                'block_id': block_id,
                'character_name': char_name,
                'text': text_to_translate,
                'context': context_list,
                'is_choice': is_choice
            })

        return contexts

    def _extract_dialogue_context(
        self,
        block_id: str,
        idx: int,
        parsed_blocks: Dict[str, ParsedBlock],
        block_order: List[str]
    ) -> List[str]:
        """Extract dialogue context from surrounding blocks."""
        context_before: List[str] = []
        context_after: List[str] = []

        # Extract context before
        for i in range(idx - 1, max(-1, idx - self.context_before - 10), -1):
            if len(context_before) >= self.context_before:
                break

            prev_id = block_order[i]
            prev_block = parsed_blocks.get(prev_id)

            if not prev_block or is_separator_block(prev_id, prev_block):
                continue

            # Prefer translated context, fall back to English
            prev_text = prev_block.get(self.target_lang_code, '') or prev_block.get('en', '')
            if prev_text.strip():
                prev_char = parse_block_id(prev_id)[1]
                context_before.insert(0, f"{prev_char}: {prev_text}")

        # Extract context after
        for i in range(idx + 1, min(len(block_order), idx + self.context_after + 10)):
            if len(context_after) >= self.context_after:
                break

            next_id = block_order[i]
            next_block = parsed_blocks.get(next_id)

            if not next_block or is_separator_block(next_id, next_block):
                continue

            # Prefer translated context, fall back to English
            next_text = next_block.get(self.target_lang_code, '') or next_block.get('en', '')
            if next_text.strip():
                next_char = parse_block_id(next_id)[1]
                context_after.append(f"{next_char}: {next_text}")

        return context_before + context_after

    def _save_yaml(
        self,
        parsed_blocks: Dict[str, ParsedBlock],
        output_path: Path,
        metadata: dict
    ):
        """Save parsed blocks to YAML file with header."""
        from datetime import datetime

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create header
        header = (
            f"# {output_path.stem} - Parsed Translations\n"
            f"# Original extraction: {metadata.get('extracted_at', 'unknown')}\n"
            f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            f.flush()  # Ensure data is written to disk

        # Verify file was created and has content
        if not output_path.exists():
            raise IOError(f"File was not created: {output_path}")

        file_size = output_path.stat().st_size
        if file_size == 0:
            raise IOError(f"File was created but is empty: {output_path}")


def load_config(project_root: Path, game_name: Optional[str] = None) -> Dict:
    """Load game configuration from current_config.json."""
    config_file = project_root / "models" / "current_config.json"

    if not config_file.exists():
        print(f"ERROR: Configuration not found at {config_file}")
        print("Please run 1-config.ps1 first to set up your game.")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)

    # Determine which game to use
    if game_name:
        if game_name not in config.get('games', {}):
            print(f"ERROR: Game '{game_name}' not found in configuration.")
            print(f"Available games: {', '.join(config.get('games', {}).keys())}")
            sys.exit(1)
        game_config = config['games'][game_name]
    else:
        current_game = config.get('current_game')
        if not current_game:
            print("ERROR: No current_game set in configuration.")
            print("Please run 1-config.ps1 first.")
            sys.exit(1)
        game_config = config['games'][current_game]

    return game_config


def load_resources(project_root: Path, game_config: Dict, target_lang_code: str):
    """
    Load glossary, corrections, and prompt template with fallback hierarchy.

    Returns: (glossary, corrections, prompt_template)
    """
    # Load glossary with fallback
    glossary = None
    for glossary_variant in [f"{target_lang_code}_uncensored_glossary.json", f"{target_lang_code}_glossary.json"]:
        glossary_path = project_root / "data" / glossary_variant
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8-sig') as f:
                glossary = json.load(f)
            print(f"[OK] Using glossary: {glossary_variant}")
            break

    if not glossary:
        print(f"[WARNING] No glossary found for language code '{target_lang_code}'")

    # Load corrections with fallback (for future use)
    corrections = None
    for corrections_variant in [f"{target_lang_code}_uncensored_corrections.json", f"{target_lang_code}_corrections.json"]:
        corrections_path = project_root / "data" / corrections_variant
        if corrections_path.exists():
            with open(corrections_path, 'r', encoding='utf-8-sig') as f:
                corrections = json.load(f)
            print(f"[OK] Using corrections: {corrections_variant}")
            break

    # Load prompt template with fallback
    prompt_template = None
    for prompt_variant in ["translate_uncensored.txt", "translate.txt"]:
        prompt_path = project_root / "data" / "prompts" / prompt_variant
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            print(f"[OK] Using prompt: {prompt_variant}")
            break

    if not prompt_template:
        print("[WARNING] No prompt template found, using default")

    return glossary, corrections, prompt_template


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Translate parsed YAML files using modular pipeline')
    parser.add_argument('--game', type=str, help='Game name (uses current_game from config if not specified)')
    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent

    # Load configuration
    print("\n" + "=" * 70)
    print("  Modular Translation Pipeline")
    print("=" * 70)
    print("\nLoading configuration...")
    game_config = load_config(project_root, args.game)

    game_name = game_config['name']
    game_path = Path(game_config['path'])
    target_language_obj = game_config['target_language'] # This is the full language object
    model_name = game_config['model']
    context_before = game_config.get('context_before', 3)
    context_after = game_config.get('context_after', 1)

    target_language_code = target_language_obj['Code']
    target_language_name = target_language_obj['Name']

    print(f"  Game: {game_name}")
    print(f"  Language: {target_language_name} ({target_language_code})")
    print(f"  Model: {model_name}")
    print(f"  Context: {context_before} before, {context_after} after")

    # Map language name to code
    lang_code_map = {
        'romanian': 'ro', 'spanish': 'es', 'french': 'fr',
        'german': 'de', 'italian': 'it', 'portuguese': 'pt',
        'russian': 'ru', 'turkish': 'tr', 'czech': 'cs',
        'polish': 'pl', 'ukrainian': 'uk', 'bulgarian': 'bg',
        'chinese': 'zh', 'japanese': 'ja', 'korean': 'ko',
        'vietnamese': 'vi', 'thai': 'th', 'indonesian': 'id',
        'arabic': 'ar', 'hebrew': 'he', 'hindi': 'hi'
    }
    # Use the extracted code directly, no need for lang_code_map.get with .lower()
    # unless mapping to a *different* code (which is not the case here)
    target_lang_code = lang_code_map.get(target_language_name.lower(), target_language_code)

    # Load resources (glossary, corrections, prompts)
    print("\nLoading resources...")
    glossary, corrections, prompt_template = load_resources(project_root, game_config, target_lang_code)

    # Load characters.json
    tl_dir = game_path / "game" / "tl" / target_language_name.lower()
    characters_file = tl_dir / "characters.json"

    characters = {}
    if characters_file.exists():
        with open(characters_file, 'r', encoding='utf-8-sig') as f:
            characters = json.load(f)
        print(f"[OK] Loaded {len(characters)} characters from characters.json")
    else:
        print(f"[WARNING] No characters.json found at {characters_file}")

    # Determine model path based on model name
    # Load model configuration from models_config.json
    models_config_path = project_root / "models" / "models_config.json"
    with open(models_config_path, 'r', encoding='utf-8-sig') as f:
        all_models_config = json.load(f)['available_models']

    model_config = all_models_config.get(model_name)

    if not model_config:
        print(f"ERROR: Model '{model_name}' not found in models_config.json")
        sys.exit(1)

    model_path = project_root / model_config['destination']

    if not model_path.exists():
        print(f"ERROR: Model file not found: {model_path}")
        sys.exit(1)

    # Initialize translator
    print("\n" + "=" * 70)
    print("  Initializing Translator")
    print("=" * 70)

    translator = Aya23Translator(
        model_path=str(model_path),
        target_language=target_language_name.capitalize(),
        prompt_template=prompt_template,
        glossary=glossary
    )

    # Initialize batch translator
    batch_translator = ModularBatchTranslator(
        translator=translator,
        characters=characters,
        target_lang_code=target_lang_code,
        context_before=context_before,
        context_after=context_after
    )

    # Find all .parsed.yaml files
    print("\n" + "=" * 70)
    print("  Scanning for Files")
    print("=" * 70)

    parsed_files = list(tl_dir.glob("*.parsed.yaml"))

    if not parsed_files:
        print(f"\nERROR: No .parsed.yaml files found in {tl_dir}")
        print("Please run 2-extract.ps1 first to extract translation files.")
        sys.exit(1)

    print(f"\nFound {len(parsed_files)} file(s) to process")

    # Translate all files
    print("\n" + "=" * 70)
    print("  Translating Files")
    print("=" * 70)

    total_stats = {
        'files': 0,
        'total_blocks': 0,
        'translated_blocks': 0,
        'skipped_blocks': 0,
        'failed_blocks': 0
    }

    overall_start = time.time()

    for file_idx, parsed_file in enumerate(parsed_files, 1):
        # Show overall progress
        if len(parsed_files) > 1:
            print()
            show_progress(file_idx - 1, len(parsed_files), overall_start, prefix="Overall: ")
            print(f"\n[File {file_idx}/{len(parsed_files)}]")

        # Find corresponding tags.json file
        # Remove .parsed.yaml and replace with .tags.json
        base_name = parsed_file.name.removesuffix('.parsed.yaml')
        tags_file = parsed_file.parent / f"{base_name}.tags.json"
        if not tags_file.exists():
            print(f"\n  [WARNING] Skipping {parsed_file.name} - no matching .tags.json file")
            print(f"             Expected: {tags_file.name}")
            continue

        # Translate file
        stats = batch_translator.translate_file(
            parsed_yaml_path=parsed_file,
            tags_json_path=tags_file,
            output_yaml_path=None  # Overwrite in place
        )

        total_stats['files'] += 1
        total_stats['total_blocks'] += stats['total']
        total_stats['translated_blocks'] += stats['translated']
        total_stats['skipped_blocks'] += stats['skipped']
        total_stats['failed_blocks'] += stats['failed']

    # Final summary
    print("\n" + "=" * 70)
    print("  TRANSLATION COMPLETE")
    print("=" * 70)
    print(f"  Files processed:     {total_stats['files']}")
    print(f"  Total blocks:        {total_stats['total_blocks']}")
    print(f"  Translated:          {total_stats['translated_blocks']}")
    print(f"  Already done:        {total_stats['skipped_blocks']}")
    print(f"  Failed:              {total_stats['failed_blocks']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
