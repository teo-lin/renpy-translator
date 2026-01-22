"""
Shared utilities for all translators

Common functionality used across Aya23, MADLAD400, Seamless96, Helsinki, mBART translators
to reduce code duplication and maintain consistency.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


def get_project_root() -> Path:
    """
    DEPRECATED: This function assumes a monorepo structure and should not be used.

    For standalone usage, pass project_root explicitly to functions that need it.

    Raises:
        RuntimeError: Always - use explicit paths instead
    """
    raise RuntimeError(
        "get_project_root() is deprecated. "
        "Pass project_root explicitly to load_glossary(), load_prompt_template(), etc."
    )


def load_glossary(lang_code: str, project_root: Optional[Path] = None) -> Optional[Dict]:
    """
    Load glossary for a language with fallback hierarchy.

    Tries to load in this order:
    1. {lang_code}_uncensored_glossary.yaml
    2. {lang_code}_glossary.yaml

    Args:
        lang_code: Language code (e.g., 'ro', 'es', 'fr')
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Dictionary with glossary terms or None if no glossary found
    """
    if project_root is None:
        project_root = get_project_root()

    glossary_variants = [
        f"{lang_code}_uncensored_glossary.yaml",
        f"{lang_code}_glossary.yaml"
    ]

    for glossary_variant in glossary_variants:
        glossary_path = project_root / "data" / glossary_variant
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary = yaml.safe_load(f)
            print(f"[OK] Using glossary: {glossary_variant}")
            return glossary

    return None


def get_language_code_map() -> Dict[str, str]:
    """
    Get mapping of language codes to language names.

    Returns:
        Dictionary mapping language codes to names
    """
    return {
        'ro': 'Romanian',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'tr': 'Turkish',
        'cs': 'Czech',
        'pl': 'Polish',
        'uk': 'Ukrainian',
        'bg': 'Bulgarian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'vi': 'Vietnamese',
        'th': 'Thai',
        'id': 'Indonesian',
        'ar': 'Arabic',
        'he': 'Hebrew',
        'fa': 'Persian',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'da': 'Danish',
        'fi': 'Finnish',
        'el': 'Greek',
        'hu': 'Hungarian'
    }


def parse_cli_language_arg() -> Tuple[Optional[str], Optional[str]]:
    """
    Parse --language argument from command line.

    Returns:
        Tuple of (language_name, language_code) or (None, None) if not found
    """
    import sys

    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--language' and i + 1 < len(sys.argv):
            lang_code = sys.argv[i + 1]
            lang_map = get_language_code_map()
            lang_name = lang_map.get(lang_code, lang_code.capitalize())
            return lang_name, lang_code

    return None, None


def load_prompt_template(lang_code: str, project_root: Optional[Path] = None) -> Optional[str]:
    """
    Load prompt template for a language with fallback hierarchy.

    Tries to load in this order:
    1. prompts/{lang_code}_uncensored_prompt.txt
    2. prompts/{lang_code}_prompt.txt

    Args:
        lang_code: Language code (e.g., 'ro', 'es', 'fr')
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Prompt template string or None if no template found
    """
    if project_root is None:
        project_root = get_project_root()

    prompt_variants = [
        f"prompts/{lang_code}_uncensored_prompt.txt",
        f"prompts/{lang_code}_prompt.txt"
    ]

    for prompt_variant in prompt_variants:
        prompt_path = project_root / "data" / prompt_variant
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            print(f"[OK] Using prompt template: {prompt_variant}")
            return prompt_template

    return None


def load_models_config(project_root: Optional[Path] = None) -> Dict:
    """
    Load models configuration from models_config.yaml.

    Args:
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Dictionary with models configuration
    """
    if project_root is None:
        project_root = get_project_root()

    config_path = project_root / "models" / "models_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Models configuration not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_current_config(project_root: Optional[Path] = None) -> Dict:
    """
    Load current configuration from current_config.yaml.

    Args:
        project_root: Project root path (auto-detected if not provided)

    Returns:
        Dictionary with current configuration
    """
    if project_root is None:
        project_root = get_project_root()

    config_path = project_root / "models" / "current_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Current configuration not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def setup_sys_path():
    """
    Add parent directory to sys.path for imports.
    Useful for CLI entry points that need to import from src/.
    """
    import sys
    parent_dir = str(get_project_root() / "src")
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
