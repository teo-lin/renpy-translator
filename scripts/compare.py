"""
Benchmark Translation Script

Translates ALL blocks in .parsed.yaml files for benchmarking purposes.
Unlike normal translation, this:
- Translates ALL blocks regardless of existing translations
- Saves translations under numbered keys (r0, r1, r2, etc.) for comparison

Usage:
    python compare.py --game <game_name> --model <model_key> --key <key_id>
    Example: python compare.py --game Example --model aya23 --key r0
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
from translators.helsinkyRo_translator import QuickMTTranslator
from translators.madlad400_translator import MADLAD400Translator
from translators.mbartRo_translator import MBARTTranslator
from translators.seamless96_translator import SeamlessM4Tv2Translator
from renpy_utils import show_progress


class BenchmarkTranslator:
    """
    Benchmark translator that translates ALL blocks and saves to numbered keys.
    """

    def __init__(
        self,
        translator,
        characters: Dict,
        save_key: str,  # e.g., "01", "02", "03"
        context_before: int = 3,
        context_after: int = 1
    ):
        self.translator = translator
        self.characters = characters
        self.save_key = save_key
        self.context_before = context_before
        self.context_after = context_after

    def translate_file(
        self,
        parsed_yaml_path: Path,
        tags_json_path: Path,
        output_yaml_path: Optional[Path] = None
    ) -> Dict[str, int]:
        """
        Translate ALL blocks in a parsed YAML file.

        Args:
            parsed_yaml_path: Path to .parsed.yaml file
            tags_json_path: Path to .tags.json file
            output_yaml_path: Path to output YAML (default: overwrite input)

        Returns:
            Dict with statistics: {'total', 'translated', 'failed'}
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

        # Get ALL translatable blocks (not just untranslated ones)
        all_block_ids = [bid for bid in parsed_blocks if not is_separator_block(bid, parsed_blocks[bid])]
        total_blocks = len(all_block_ids)

        print(f"    Total blocks to translate: {total_blocks}")

        if not all_block_ids:
            print("    [OK] No blocks to translate!")
            return {
                'total': 0,
                'translated': 0,
                'failed': 0
            }

        # Extract context for each block
        contexts = self._extract_contexts(
            all_block_ids,
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

                # Update block with numbered key
                parsed_blocks[block_id][self.save_key] = translation
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
            failed_count += translated_count
            translated_count = 0

        # Return statistics
        stats = {
            'total': total_blocks,
            'translated': translated_count,
            'failed': failed_count
        }

        print(f"    [OK] Translated: {stats['translated']}, Failed: {stats['failed']}")

        return stats

    def _extract_contexts(
        self,
        block_ids: List[str],
        parsed_blocks: Dict[str, ParsedBlock],
        block_order: List[str]
    ) -> List[Dict]:
        """Extract context for each block."""
        contexts: List[Dict] = []

        # Build index map: block_id -> position in order
        block_index = {block_id: idx for idx, block_id in enumerate(block_order)}

        for block_id in block_ids:
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
                context_list = []
            else:
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

        # Extract context before (use English only for consistency)
        for i in range(idx - 1, max(-1, idx - self.context_before - 10), -1):
            if len(context_before) >= self.context_before:
                break

            prev_id = block_order[i]
            prev_block = parsed_blocks.get(prev_id)

            if not prev_block or is_separator_block(prev_id, prev_block):
                continue

            prev_text = prev_block.get('en', '')
            if prev_text.strip():
                prev_char = parse_block_id(prev_id)[1]
                context_before.insert(0, f"{prev_char}: {prev_text}")

        # Extract context after (use English only for consistency)
        for i in range(idx + 1, min(len(block_order), idx + self.context_after + 10)):
            if len(context_after) >= self.context_after:
                break

            next_id = block_order[i]
            next_block = parsed_blocks.get(next_id)

            if not next_block or is_separator_block(next_id, next_block):
                continue

            next_text = next_block.get('en', '')
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
            f"# {output_path.stem} - Benchmark Translations\n"
            f"# Original extraction: {metadata.get('extracted_at', 'unknown')}\n"
            f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "\n"
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(parsed_blocks, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            f.flush()

        # Verify file was created and has content
        if not output_path.exists():
            raise IOError(f"File was not created: {output_path}")

        file_size = output_path.stat().st_size
        if file_size == 0:
            raise IOError(f"File was created but is empty: {output_path}")


def load_config(project_root: Path, game_name: str) -> Dict:
    """Load game configuration from current_config.json."""
    config_file = project_root / "models" / "current_config.json"

    if not config_file.exists():
        print(f"ERROR: Configuration not found at {config_file}")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)

    if game_name not in config.get('games', {}):
        print(f"ERROR: Game '{game_name}' not found in configuration.")
        sys.exit(1)

    return config['games'][game_name]


def load_resources(project_root: Path, target_lang_code: str):
    """Load glossary and prompt template."""
    # Load glossary with fallback
    glossary = None
    for glossary_variant in [f"{target_lang_code}_uncensored_glossary.json", f"{target_lang_code}_glossary.json"]:
        glossary_path = project_root / "data" / glossary_variant
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8-sig') as f:
                glossary = json.load(f)
            print(f"[OK] Using glossary: {glossary_variant}")
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

    return glossary, prompt_template


def initialize_translator(model_key: str, model_path: Path, target_language: str, glossary: dict, prompt_template: str):
    """Initialize the appropriate translator based on model key."""
    # Map model keys to translator classes
    translator_map = {
        'aya23': Aya23Translator,
        'helsinkiRo': QuickMTTranslator,
        'madlad400': MADLAD400Translator,
        'mbartRo': MBARTTranslator,
        'seamlessm96': SeamlessM4Tv2Translator,
    }

    translator_class = translator_map.get(model_key)
    if not translator_class:
        print(f"ERROR: Unknown model key: {model_key}")
        sys.exit(1)

    # Initialize translator with appropriate parameters
    if model_key == 'aya23':
        # Aya23 uses GGUF model file
        return translator_class(
            model_path=str(model_path),
            target_language=target_language,
            prompt_template=prompt_template,
            glossary=glossary
        )
    elif model_key in ['helsinkiRo', 'mbartRo']:
        # HuggingFace models - use model directory, not file
        return translator_class(
            model_path=str(model_path),
            target_language=target_language,
            glossary=glossary
        )
    elif model_key == 'madlad400':
        # MADLAD400 doesn't use model_path parameter
        return translator_class(
            target_language=target_language,
            glossary=glossary,
            trust_remote_code=True
        )
    elif model_key == 'seamlessm96':
        # SeamlessM4Tv2 uses model directory
        return translator_class(
            model_name=str(model_path),
            target_language=target_language,
            glossary=glossary
        )
    else:
        # Default initialization
        return translator_class(
            target_language=target_language
        )


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Benchmark translation - translate ALL blocks')
    parser.add_argument('--game', type=str, required=True, help='Game name')
    parser.add_argument('--model', type=str, required=True, help='Model key (e.g., aya23, helsinkiRo)')
    parser.add_argument('--key', type=str, required=True, help='Save key (e.g., r0, r1, r2)')
    args = parser.parse_args()

    # Setup paths
    project_root = Path(__file__).parent.parent

    # Load configuration
    print("\n" + "=" * 70)
    print(f"  Benchmark Translation - Model: {args.model}, Key: {args.key}")
    print("=" * 70)
    print("\nLoading configuration...")
    game_config = load_config(project_root, args.game)

    game_name = game_config['name']
    game_path = Path(game_config['path'])
    target_language_obj = game_config['target_language']
    context_before = game_config.get('context_before', 3)
    context_after = game_config.get('context_after', 1)

    target_language_code = target_language_obj['Code']
    target_language_name = target_language_obj['Name']

    print(f"  Game: {game_name}")
    print(f"  Language: {target_language_name} ({target_language_code})")
    print(f"  Model: {args.model}")
    print(f"  Save key: {args.key}")

    # Load model configuration
    models_config_path = project_root / "models" / "models_config.json"
    with open(models_config_path, 'r', encoding='utf-8-sig') as f:
        all_models_config = json.load(f)['available_models']

    model_config = all_models_config.get(args.model)
    if not model_config:
        print(f"ERROR: Model '{args.model}' not found in models_config.json")
        sys.exit(1)

    model_path = project_root / model_config['destination']
    if model_config['file'] is None:  # Directory-based model
        if not model_path.is_dir():
            print(f"ERROR: Model directory not found: {model_path}")
            sys.exit(1)
    else:  # File-based model
        if not model_path.is_file():
            print(f"ERROR: Model file not found: {model_path}")
            sys.exit(1)

    # Load resources
    print("\nLoading resources...")
    glossary, prompt_template = load_resources(project_root, target_language_code)

    # Load characters.json
    tl_dir = game_path / "game" / "tl" / target_language_name.lower()
    characters_file = tl_dir / "characters.json"

    characters = {}
    if characters_file.exists():
        with open(characters_file, 'r', encoding='utf-8-sig') as f:
            characters = json.load(f)
        print(f"[OK] Loaded {len(characters)} characters")

    # Initialize translator
    print("\n" + "=" * 70)
    print("  Initializing Translator")
    print("=" * 70)

    translator = initialize_translator(
        args.model,
        model_path,
        target_language_name.capitalize(),
        glossary,
        prompt_template
    )

    # Initialize benchmark translator
    benchmark_translator = BenchmarkTranslator(
        translator=translator,
        characters=characters,
        save_key=args.key,
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
        base_name = parsed_file.name.removesuffix('.parsed.yaml')
        tags_file = parsed_file.parent / f"{base_name}.tags.json"
        if not tags_file.exists():
            print(f"\n  [WARNING] Skipping {parsed_file.name} - no matching .tags.json file")
            continue

        # Translate file
        stats = benchmark_translator.translate_file(
            parsed_yaml_path=parsed_file,
            tags_json_path=tags_file,
            output_yaml_path=None
        )

        total_stats['files'] += 1
        total_stats['total_blocks'] += stats['total']
        total_stats['translated_blocks'] += stats['translated']
        total_stats['failed_blocks'] += stats['failed']

    # Calculate total duration
    total_duration = time.time() - overall_start

    # Final summary
    print("\n" + "=" * 70)
    print("  BENCHMARK TRANSLATION COMPLETE")
    print("=" * 70)
    print(f"  Model:               {args.model}")
    print(f"  Key:                 {args.key}")
    print(f"  Files processed:     {total_stats['files']}")
    print(f"  Total blocks:        {total_stats['total_blocks']}")
    print(f"  Translated:          {total_stats['translated_blocks']}")
    print(f"  Failed:              {total_stats['failed_blocks']}")
    print(f"  Duration:            {total_duration:.2f} seconds")
    print("=" * 70)

    # Return duration for PowerShell to capture
    print(f"\nBENCHMARK_DURATION:{total_duration:.2f}")


if __name__ == "__main__":
    main()
