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

import sys
import os
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from renpy_utils import detect_language_from_path
from translation_pipeline import RenpyTranslationPipeline
from translators.aya23_translator import Aya23Translator


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
        target_language, _ = detect_language_from_path(input_path)
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

    # Load prompt template with fallback
    prompt_template = None
    prompt_template_path = project_root / "data" / "prompts" / "translate_uncensored.txt"
    if not prompt_template_path.exists():
        prompt_template_path = project_root / "data" / "prompts" / "translate.txt"

    if prompt_template_path.exists():
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

    # Initialize translator
    translator = Aya23Translator(
        model_path=str(model_path),
        target_language=target_language,
        prompt_template=prompt_template,
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
