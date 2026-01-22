"""
Example usage of poly_trans standalone package.

This demonstrates how to use poly_trans programmatically to translate
YAML files with dialogue blocks.
"""

from pathlib import Path

# Import from installed poly_trans package
from poly_trans.translate import ModularBatchTranslator

# NOTE: This example assumes monorepo structure with models/ at root
# For standalone usage, provide your own model paths
repo_root = Path(__file__).parent.parent.parent.parent


def example_basic_translation():
    """Example: Basic translation with Aya23Translator"""

    # Import translator here to avoid loading CUDA DLLs at module import time
    from poly_trans.translators.aya23_translator import Aya23Translator

    # Paths (adjust to your setup)
    model_path = repo_root / "models" / "aya23" / "aya-23-8B-Q4_K_M.gguf"

    if not model_path.exists():
        print(f"Model not found: {model_path}")
        print("Please download the model first.")
        return

    # Initialize translator
    print("Initializing Aya23 translator...")
    translator = Aya23Translator(
        model_path=str(model_path),
        target_language="Romanian",
        glossary={
            "hello": "bună",
            "world": "lume"
        }
    )

    # Create batch translator
    batch_translator = ModularBatchTranslator(
        translator=translator,
        characters={},  # Character info (can be loaded from YAML)
        target_lang_code="ro",
        context_before=3,  # Use 3 lines before for context
        context_after=1    # Use 1 line after for context
    )

    # Example: Translate a file
    parsed_yaml = repo_root / "games" / "Once a Porn a Time 2" / "game" / "tl" / "romanian" / "TEST.parsed.yaml"
    tags_yaml = repo_root / "games" / "Once a Porn a Time 2" / "game" / "tl" / "romanian" / "TEST.tags.yaml"

    if parsed_yaml.exists() and tags_yaml.exists():
        print(f"\nTranslating: {parsed_yaml.name}")
        stats = batch_translator.translate_file(
            parsed_yaml_path=parsed_yaml,
            tags_yaml_path=tags_yaml
        )

        print(f"\nResults:")
        print(f"  Total blocks: {stats['total']}")
        print(f"  Translated: {stats['translated']}")
        print(f"  Skipped (already done): {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")
    else:
        print(f"\nTest files not found:")
        print(f"  {parsed_yaml}")
        print(f"  {tags_yaml}")
        print("\nCreate a test YAML file to try translation.")


def example_check_import():
    """Example: Check if poly_trans is properly installed"""

    import poly_trans
    from poly_trans.models import ParsedBlock, parse_block_id, is_separator_block
    from poly_trans.translate import ModularBatchTranslator

    print("poly_trans import check:")
    print(f"  Version: {poly_trans.__version__}")
    print(f"  Available: {poly_trans.__all__}")
    print(f"  ParsedBlock: {ParsedBlock}")
    print(f"  ModularBatchTranslator: {ModularBatchTranslator}")
    print("\nAll imports successful!")


if __name__ == "__main__":
    print("=" * 70)
    print("poly_trans Example Usage")
    print("=" * 70)

    # Check imports first
    print("\n1. Checking imports...")
    example_check_import()

    # Uncomment to run actual translation
    # print("\n2. Running translation example...")
    # example_basic_translation()

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
