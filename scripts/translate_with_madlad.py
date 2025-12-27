"""
Ren'Py Translation Pipeline using MADLAD-400-3B

Translates Ren'Py game files from English to any of 400+ languages while preserving:
- Ren'Py formatting tags: {color=...}, {size=...}, {/color}, etc.
- Variables: [name], [variable_name]
- Special characters and formatting

Uses Google's MADLAD-400-3B model for translation.
Supports 400+ languages with language-agnostic design.

CRITICAL: Language Identifier Handling
- Automatically converts "translate english" to "translate <target_language>" in output
- Prevents Ren'Py "translation already exists" errors
- Ensures translation files use correct language declaration

Usage:
    python translate_with_madlad.py <input_file_or_dir> --language LANG [--lang-code CODE] [output_dir]

    Examples:
        python translate_with_madlad.py game/tl/romanian --language Romanian --lang-code ro
        python translate_with_madlad.py game/tl/spanish --language Spanish --lang-code es
        python translate_with_madlad.py game/tl/japanese --language Japanese --lang-code ja
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from renpy_utils import detect_language_from_path
from translation_pipeline import RenpyTranslationPipeline
from translators import MADLAD400Translator


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print("  python translate_with_madlad.py game/tl/romanian/ --language Romanian --lang-code ro")
        print("  python translate_with_madlad.py game/tl/spanish/ --language Spanish --lang-code es")
        print("  python translate_with_madlad.py game/tl/japanese/ --language Japanese --lang-code ja")
        sys.exit(1)

    # Parse arguments
    input_path = Path(sys.argv[1])
    target_language = None
    lang_code = None
    output_path_arg = None

    # Parse command-line arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--language' and i + 1 < len(sys.argv):
            target_language = sys.argv[i + 1]
            i += 2
        elif arg == '--lang-code' and i + 1 < len(sys.argv):
            lang_code = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            output_path_arg = arg
            i += 1
        else:
            i += 1

    # Auto-detect language from path if not specified
    if target_language is None or lang_code is None:
        detected_lang, detected_code = detect_language_from_path(input_path)
        if target_language is None:
            target_language = detected_lang
        if lang_code is None:
            lang_code = detected_code
        print(f"Auto-detected language: {target_language} ({lang_code})")

    # Default paths
    project_root = Path(__file__).parent.parent

    # Generic glossary fallback: <lang_code>_uncensored_glossary.json → <lang_code>_glossary.json → none
    glossary = None
    glossary_path = None
    for glossary_variant in [f"{lang_code}_uncensored_glossary.json", f"{lang_code}_glossary.json"]:
        candidate = project_root / "data" / glossary_variant
        if candidate.exists():
            with open(candidate, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
            glossary_path = candidate
            print(f"[OK] Using glossary: {glossary_variant}")
            break

    if not glossary_path:
        print(f"[WARNING] No glossary found for {target_language} ({lang_code})")

    # Initialize translator
    translator = MADLAD400Translator(
        target_language=target_language,
        lang_code=lang_code,
        glossary=glossary
    )

    # Initialize pipeline with translator
    pipeline = RenpyTranslationPipeline(translator)

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
