"""
Translation Prompts for Aya-23-8B

This module loads prompt templates from data/ directory for easier customization.
Keeping prompts in separate files allows for easier editing, versioning, and A/B testing.

CRITICAL FILE STRUCTURE REQUIREMENTS:
- ALL translation files MUST use "translate <language>" declarations matching the target language
- NEVER use "translate english" in non-English translation files (causes conflicts)
- Each translation block format:
    translate <language> label_name_hash:
        # original text
        translated_text
"""

from pathlib import Path

# Determine project root (go up from src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load prompt templates once at module import
# Fallback hierarchy: translate_uncensored.txt → translate.txt
try:
    TRANSLATION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "translate_uncensored.txt").read_text(encoding='utf-8')
except FileNotFoundError:
    try:
        TRANSLATION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "translate.txt").read_text(encoding='utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Translation prompt template not found. Please create one of:\n"
            f"  - {PROJECT_ROOT / 'data' / 'prompts' / 'translate_uncensored.txt'}\n"
            f"  - {PROJECT_ROOT / 'data' / 'prompts' / 'translate.txt'}"
        )

# Fallback hierarchy: correct_uncensored.txt → correct.txt
try:
    CORRECTION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "correct_uncensored.txt").read_text(encoding='utf-8')
except FileNotFoundError:
    try:
        CORRECTION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "correct.txt").read_text(encoding='utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Correction prompt template not found. Please create one of:\n"
            f"  - {PROJECT_ROOT / 'data' / 'prompts' / 'correct_uncensored.txt'}\n"
            f"  - {PROJECT_ROOT / 'data' / 'prompts' / 'correct.txt'}"
        )


def create_translation_prompt(text: str, target_language: str = "Romanian",
                              glossary_instructions: str = "",
                              context_section: str = "", speaker_hint: str = "") -> str:
    """
    Create optimized prompt for translation with context awareness

    Args:
        text: English text to translate
        target_language: Target language name (e.g., "Romanian", "Spanish", "French")
        glossary_instructions: Optional glossary terms to enforce
        context_section: Optional previous dialogue context
        speaker_hint: Optional character/speaker identifier

    Returns:
        Complete translation prompt
    """
    return TRANSLATION_PROMPT_TEMPLATE.format(
        target_language=target_language,
        glossary_instructions=glossary_instructions,
        context_section=context_section,
        speaker_hint=speaker_hint,
        text=text
    )


def create_correction_prompt(text: str, target_language: str = "Romanian") -> str:
    """
    Create prompt for correcting grammar errors

    Args:
        text: Translated text with potential errors
        target_language: Language name (e.g., "Romanian", "Spanish", "French")

    Returns:
        Complete correction prompt
    """
    return CORRECTION_PROMPT_TEMPLATE.format(
        target_language=target_language,
        text=text
    )
