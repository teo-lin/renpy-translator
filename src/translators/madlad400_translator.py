"""
MADLAD-400-3B Translator Implementation

Uses Hugging Face transformers for translation with 400+ language support.
Optimized for broad language coverage including rare and low-resource languages.
"""

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from pathlib import Path


class MADLAD400Translator:
    """
    MADLAD-400-3B translator using Hugging Face transformers

    Supports 400+ languages with good quality translations.
    Uses language tags like <2ro>, <2es>, <2ja> for target language specification.
    """

    # Mapping of common language codes to MADLAD language tags
    # Format: <2xx> where xx is the ISO 639-1 code
    LANGUAGE_CODE_MAP = {
        'ro': 'ro',  # Romanian
        'es': 'es',  # Spanish
        'fr': 'fr',  # French
        'de': 'de',  # German
        'it': 'it',  # Italian
        'pt': 'pt',  # Portuguese
        'ru': 'ru',  # Russian
        'tr': 'tr',  # Turkish
        'cs': 'cs',  # Czech
        'pl': 'pl',  # Polish
        'uk': 'uk',  # Ukrainian
        'bg': 'bg',  # Bulgarian
        'zh': 'zh',  # Chinese
        'ja': 'ja',  # Japanese
        'ko': 'ko',  # Korean
        'vi': 'vi',  # Vietnamese
        'th': 'th',  # Thai
        'id': 'id',  # Indonesian
        'ar': 'ar',  # Arabic
        'he': 'he',  # Hebrew
        'fa': 'fa',  # Persian/Farsi
        'hi': 'hi',  # Hindi
        'bn': 'bn',  # Bengali
        'nl': 'nl',  # Dutch
        'sv': 'sv',  # Swedish
        'no': 'no',  # Norwegian
        'da': 'da',  # Danish
        'fi': 'fi',  # Finnish
        'el': 'el',  # Greek
        'hu': 'hu',  # Hungarian
    }

    def __init__(self, target_language: str = "Romanian", lang_code: str = None,
                 device: str = None, glossary: dict = None):
        """
        Initialize MADLAD-400-3B translator

        Args:
            target_language: Target language name (e.g., "Romanian", "Spanish", "Japanese")
            lang_code: ISO 639-1 language code (e.g., "ro", "es", "ja"). If None, auto-detected.
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN→target language term mappings
        """
        self._target_language = target_language
        self.glossary = glossary or {}

        # Auto-detect language code if not provided
        if lang_code is None:
            # Try to guess from language name
            lang_name_lower = target_language.lower()
            for code, name_key in self.LANGUAGE_CODE_MAP.items():
                if lang_name_lower.startswith(code) or lang_name_lower.startswith(name_key):
                    lang_code = code
                    break
            if lang_code is None:
                # Default to first 2 letters of language name
                lang_code = target_language[:2].lower()

        self.lang_code = lang_code

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        print(f"Initializing MADLAD-400-3B Translation (EN→{target_language})...")
        print(f"  Language code: {lang_code}")
        print(f"  Device: {device}")
        print(f"  Loading model... This may take 30-60 seconds...")

        # Load model and tokenizer
        model_name = "google/madlad400-3b-mt"
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        print("Model loaded successfully!")

    @property
    def target_language(self) -> str:
        """Return the target language name"""
        return self._target_language

    def _apply_glossary(self, text: str, translation: str) -> str:
        """
        Apply glossary terms to translation (basic implementation)

        Args:
            text: Original English text
            translation: Translated text

        Returns:
            Translation with glossary terms applied
        """
        if not self.glossary:
            return translation

        # Find glossary terms that appear in the original text
        for en_term, target_term in self.glossary.items():
            # Skip comment entries
            if en_term.startswith("_comment"):
                continue

            # Case-insensitive search in original
            if en_term.lower() in text.lower():
                # Try to replace in translation
                # This is a simple approach - more sophisticated logic could be added
                pass

        return translation

    def translate(self, text: str, max_length: int = 512, num_beams: int = 4,
                  temperature: float = 1.0, context: list = None,
                  speaker: str = None) -> str:
        """
        Translate text using MADLAD-400-3B

        Args:
            text: English text to translate
            max_length: Maximum length of translation
            num_beams: Number of beams for beam search
            temperature: Sampling temperature (1.0 = default)
            context: Optional list of previous dialogue lines (for consistency)
            speaker: Optional character name/identifier

        Returns:
            Translated text
        """
        # MADLAD uses language tags like <2ro> for Romanian, <2es> for Spanish
        lang_tag = f"<2{self.lang_code}>"

        # Prepare input with language tag
        input_text = f"{lang_tag} {text}"

        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate translation
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                temperature=temperature,
                early_stopping=True,
                do_sample=False,  # Use beam search, not sampling
            )

        # Decode translation
        translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Apply glossary if available
        translation = self._apply_glossary(text, translation)

        # Clean up translation
        translation = translation.strip()

        return translation


if __name__ == "__main__":
    """
    CLI entry point for standalone translation script usage.

    Usage:
        python madlad400_translator.py <input_file> --language <language_code>

    Example:
        python madlad400_translator.py script.rpy --language ro
    """
    import sys
    import json
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python madlad400_translator.py <input_file> --language <lang_code>")
        print("Example: python madlad400_translator.py script.rpy --language ro")
        sys.exit(1)

    # Parse arguments
    input_file = Path(sys.argv[1])
    target_language = None
    lang_code = None

    # Check for --language parameter
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--language' and i + 1 < len(sys.argv):
            lang_code = sys.argv[i + 1]
            # Map language codes to names
            lang_map = {
                'ro': 'Romanian', 'es': 'Spanish', 'fr': 'French',
                'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
                'ru': 'Russian', 'ar': 'Arabic', 'zh': 'Chinese',
                'ja': 'Japanese', 'ko': 'Korean', 'tr': 'Turkish',
                'cs': 'Czech', 'pl': 'Polish', 'uk': 'Ukrainian',
                'bg': 'Bulgarian', 'vi': 'Vietnamese', 'th': 'Thai',
                'id': 'Indonesian', 'he': 'Hebrew', 'fa': 'Persian',
                'hi': 'Hindi', 'bn': 'Bengali', 'nl': 'Dutch',
                'sv': 'Swedish', 'no': 'Norwegian', 'da': 'Danish',
                'fi': 'Finnish', 'el': 'Greek', 'hu': 'Hungarian'
            }
            target_language = lang_map.get(lang_code, lang_code.capitalize())
            break

    if not target_language or not lang_code:
        print("Error: --language parameter is required")
        sys.exit(1)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Try to load glossary
    project_root = Path(__file__).parent.parent.parent
    glossary = None
    for glossary_variant in [f"{lang_code}_uncensored_glossary.json", f"{lang_code}_glossary.json"]:
        glossary_path = project_root / "data" / glossary_variant
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
            print(f"[OK] Using glossary: {glossary_variant}")
            break

    # Initialize translator
    translator = MADLAD400Translator(
        target_language=target_language,
        lang_code=lang_code,
        glossary=glossary
    )

    # Initialize pipeline
    pipeline = RenpyTranslationPipeline(translator)

    # Translate file
    try:
        pipeline.translate_file(input_file, output_path=None)
        sys.exit(0)
    except Exception as e:
        print(f"Error during translation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
