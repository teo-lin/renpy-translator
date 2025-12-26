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
# Fallback hierarchy: translate_uncensored.txt → translate.txt → embedded template
try:
    TRANSLATION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "translate_uncensored.txt").read_text(encoding='utf-8')
except FileNotFoundError:
    try:
        TRANSLATION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "translate.txt").read_text(encoding='utf-8')
    except FileNotFoundError:
        # Fallback to embedded template if neither file exists
        TRANSLATION_PROMPT_TEMPLATE = """Translate this English dialogue to natural, colloquial {target_language}.{glossary_instructions}{context_section}{speaker_hint}

CRITICAL RULES:
1. Use natural {target_language} idioms and expressions, NOT literal word-for-word translations
2. Use appropriate formality level for casual dialogue (informal/familiar forms)
3. Match gender and number agreement based on dialogue context
4. Use glossary terms exactly as specified - maintain consistency
5. Follow proper {target_language} word order and grammar rules
6. Maintain proper spacing around variables: ", [name]!" not "[name]!"
7. **QUOTE HANDLING (CRITICAL FOR REN'PY SYNTAX):**
   - When you see nested quotes in English like ''quoted text'' (two single quotes)
   - You MUST use the same format in {target_language}: ''text''
   - Example: Use '' for nested quotes, NOT \" or unescaped "
8. **DO NOT TRANSLATE THESE:**
   - Game titles and proper nouns (keep capitalized words EXACTLY as-is)
   - Character names from glossary
   - Technical terms, variables like [name], {{{{color=...}}}} tags

GRAMMAR RULES:
9. Use correct verb conjugations and tenses for {target_language}
10. Apply proper diacritics and special characters for {target_language}
11. Ensure adjectives agree with nouns in gender/number as required

English: {text}
{target_language}:"""

# Fallback hierarchy: correct_uncensored.txt → correct.txt → embedded template
try:
    CORRECTION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "correct_uncensored.txt").read_text(encoding='utf-8')
except FileNotFoundError:
    try:
        CORRECTION_PROMPT_TEMPLATE = (PROJECT_ROOT / "data" / "prompts" / "correct.txt").read_text(encoding='utf-8')
    except FileNotFoundError:
        # Fallback to embedded template if neither file exists
        CORRECTION_PROMPT_TEMPLATE = """You are a {target_language} grammar expert. Correct ONLY the grammatical errors in this {target_language} text.

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. **QUOTE HANDLING (HIGHEST PRIORITY - PREVENTS SYNTAX ERRORS):**
   - ALL nested quotes MUST use '' (two single quotes), NEVER use \" or unescaped "
   - If you see unescaped " or \" inside a string, change them to '' immediately
2. Fix verb conjugations and tenses according to {target_language} grammar rules
3. Fix pronoun usage (reflexive, possessive, etc.) when grammatically required
4. Fix gender/number agreement (adjectives must match nouns)
5. Fix diacritics and special characters for {target_language}
6. Fix spelling errors

ABSOLUTE PROHIBITIONS - NEVER DO THESE:
1. NEVER change proper names (names of people, places, game titles) - keep capitalized words EXACTLY as-is
2. NEVER change punctuation (keep ..., ?!?, !!, etc. exactly as written) - EXCEPT fixing quotes to ''
3. NEVER remove or add words unless fixing grammar (keep meaning 100% identical)
4. NEVER change sentence structure unless grammatically wrong
5. NEVER add or remove spaces around ... or other punctuation
6. If text is already grammatically correct (and quotes use ''), return it UNCHANGED
7. Do NOT translate to other languages
8. Do NOT add explanations

{target_language} text to correct: {text}
Corrected {target_language}:"""


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
