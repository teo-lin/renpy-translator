#!/usr/bin/env python3
"""
Ren'Py Translation Script - LLMic-3B Model

Translates Ren'Py game files from English to Romanian using the LLMic-3B model.
LLMic is a bilingual EN-RO model with best-in-class BLEU score (41.01 on WMT16).

Usage:
    python scripts/translate_with_llmic.py <rpy_file> [--language ro] [--glossary path/to/glossary.json]

Arguments:
    rpy_file: Path to the .rpy file to translate
    --language: Target language code (must be 'ro' for Romanian)
    --glossary: Optional path to glossary JSON file

Example:
    python scripts/translate_with_llmic.py game/script.rpy --language ro
"""

import sys
import json
import argparse
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "translators"))

from llmic_translator import LLMicTranslator
from translation_pipeline import RenpyTranslationPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Translate Ren'Py files using LLMic-3B (EN->RO)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/translate_with_llmic.py game/script.rpy --language ro
  python scripts/translate_with_llmic.py game/script.rpy --language ro --glossary data/ro_glossary.json
        """
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to .rpy file to translate"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="ro",
        help="Target language code (must be 'ro' for Romanian)"
    )

    parser.add_argument(
        "--glossary",
        type=Path,
        default=None,
        help="Path to glossary JSON file (optional)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (optional, defaults to overwriting input)"
    )

    args = parser.parse_args()

    # Validate language
    if args.language != "ro":
        print("Error: LLMic only supports Romanian translation (--language ro)")
        sys.exit(1)

    # Validate input file
    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Load glossary if provided
    glossary = None
    if args.glossary:
        if not args.glossary.exists():
            print(f"Warning: Glossary file not found: {args.glossary}")
        else:
            try:
                with open(args.glossary, 'r', encoding='utf-8') as f:
                    glossary = json.load(f)
                print(f"[OK] Loaded glossary: {args.glossary}")
            except Exception as e:
                print(f"Warning: Failed to load glossary: {e}")
    else:
        # Try to auto-detect glossary
        for glossary_variant in ["ro_uncensored_glossary.json", "ro_glossary.json"]:
            glossary_path = project_root / "data" / glossary_variant
            if glossary_path.exists():
                try:
                    with open(glossary_path, 'r', encoding='utf-8') as f:
                        glossary = json.load(f)
                    print(f"[OK] Auto-detected glossary: {glossary_variant}")
                    break
                except:
                    pass

    # Initialize translator
    print("\nInitializing LLMic-3B translator...")
    try:
        translator = LLMicTranslator(
            target_language="Romanian",
            lang_code=args.language,
            glossary=glossary
        )
    except Exception as e:
        print(f"Error initializing translator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Initialize pipeline
    pipeline = RenpyTranslationPipeline(translator)

    # Translate file
    print(f"\nTranslating: {args.input_file}")
    try:
        pipeline.translate_file(args.input_file, output_path=args.output)
        print("\n[SUCCESS] Translation completed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Translation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
