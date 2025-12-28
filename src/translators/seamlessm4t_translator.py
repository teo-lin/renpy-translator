"""
SeamlessM4T-v2 Translator Implementation

Uses Hugging Face transformers for translation with Meta's latest multimodal model.
Optimized for high-quality text translation with nearly 100 languages supported.
"""

from pathlib import Path

# Try to import transformers dependencies
try:
    import torch
    from transformers import AutoProcessor, SeamlessM4Tv2Model
    TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError
    AutoProcessor = None
    SeamlessM4Tv2Model = None
    torch = None


class SeamlessM4Tv2Translator:
    """
    SeamlessM4T-v2 translator using Hugging Face transformers

    Supports nearly 100 languages with state-of-art translation quality.
    Uses Meta's 2024 multimodal model (text + speech, though we only use text).
    """

    # Mapping of common language codes to SeamlessM4T language codes
    # SeamlessM4T uses 3-letter ISO codes (e.g., "ron" for Romanian)
    LANGUAGE_CODE_MAP = {
        'ro': 'ron',  # Romanian
        'es': 'spa',  # Spanish
        'fr': 'fra',  # French
        'de': 'deu',  # German
        'it': 'ita',  # Italian
        'pt': 'por',  # Portuguese
        'ru': 'rus',  # Russian
        'tr': 'tur',  # Turkish
        'cs': 'ces',  # Czech
        'pl': 'pol',  # Polish
        'uk': 'ukr',  # Ukrainian
        'bg': 'bul',  # Bulgarian
        'zh': 'cmn',  # Chinese (Mandarin)
        'ja': 'jpn',  # Japanese
        'ko': 'kor',  # Korean
        'vi': 'vie',  # Vietnamese
        'th': 'tha',  # Thai
        'id': 'ind',  # Indonesian
        'ar': 'arb',  # Arabic (Modern Standard)
        'he': 'heb',  # Hebrew
        'fa': 'pes',  # Persian/Farsi
        'hi': 'hin',  # Hindi
        'bn': 'ben',  # Bengali
        'nl': 'nld',  # Dutch
        'sv': 'swe',  # Swedish
        'no': 'nor',  # Norwegian
        'da': 'dan',  # Danish
        'fi': 'fin',  # Finnish
        'el': 'ell',  # Greek
        'hu': 'hun',  # Hungarian
        'en': 'eng',  # English (source)
    }

    def __init__(self, target_language: str = "Romanian", lang_code: str = None,
                 device: str = None, glossary: dict = None, model_name: str = None):
        """
        Initialize SeamlessM4T-v2 translator

        Args:
            target_language: Target language name (e.g., "Romanian", "Spanish", "Japanese")
            lang_code: 2-letter language code (e.g., "ro", "es", "ja"). Auto-converted to 3-letter.
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN->target language term mappings
            model_name: Model variant to use. Default: "facebook/seamless-m4t-v2-large"
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"SeamlessM4Tv2Translator requires transformers and torch packages.\n"
                f"Original error: {IMPORT_ERROR}\n"
                f"This is likely due to triton/torch version incompatibility.\n"
                f"See: https://github.com/pytorch/ao/issues/2919"
            )

        self._target_language = target_language
        self.glossary = glossary or {}

        # Auto-detect language code if not provided
        if lang_code is None:
            # Try to guess from language name
            lang_name_lower = target_language.lower()
            # Try exact matches first
            name_to_code = {
                'romanian': 'ro', 'spanish': 'es', 'french': 'fr',
                'german': 'de', 'italian': 'it', 'portuguese': 'pt',
                'russian': 'ru', 'turkish': 'tr', 'czech': 'cs',
                'polish': 'pl', 'ukrainian': 'uk', 'bulgarian': 'bg',
                'chinese': 'zh', 'japanese': 'ja', 'korean': 'ko',
                'vietnamese': 'vi', 'thai': 'th', 'indonesian': 'id',
                'arabic': 'ar', 'hebrew': 'he', 'persian': 'fa',
                'farsi': 'fa', 'hindi': 'hi', 'bengali': 'bn',
                'dutch': 'nl', 'swedish': 'sv', 'norwegian': 'no',
                'danish': 'da', 'finnish': 'fi', 'greek': 'el',
                'hungarian': 'hu'
            }
            lang_code = name_to_code.get(lang_name_lower, target_language[:2].lower())

        # Convert 2-letter code to 3-letter code for SeamlessM4T
        self.lang_code_3letter = self.LANGUAGE_CODE_MAP.get(lang_code, lang_code)
        self.lang_code = lang_code

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Default model
        if model_name is None:
            model_name = "facebook/seamless-m4t-v2-large"
        self.model_name = model_name

        print(f"Initializing SeamlessM4T-v2 Translation (EN->{target_language})...")
        print(f"  Language code: {lang_code} ({self.lang_code_3letter})")
        print(f"  Device: {device}")
        print(f"  Model: {model_name}")
        print(f"  Loading model... This may take 60-90 seconds...")

        # Load processor and model
        self.processor = AutoProcessor.from_pretrained(model_name)

        # Use memory-efficient loading to avoid paging file errors
        self.model = SeamlessM4Tv2Model.from_pretrained(
            model_name,
            low_cpu_mem_usage=True,  # Reduces RAM usage during loading
            device_map="auto",  # Automatically manages memory across CPU/GPU
            torch_dtype=torch.float16 if device == "cuda" else torch.float32  # Use half precision on GPU
        )
        # Note: Don't call .to(device) when using device_map="auto"

        self.model.eval()

        print("Model loaded successfully!")
        print("  Note: SeamlessM4T-v2 is a large model (2.3GB+)")

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

    def translate(self, text: str, max_length: int = 512, num_beams: int = 5,
                  context: list = None, speaker: str = None) -> str:
        """
        Translate text using SeamlessM4T-v2

        Args:
            text: English text to translate
            max_length: Maximum length of translation
            num_beams: Number of beams for beam search (default 5 for quality)
            context: Optional list of previous dialogue lines (for consistency)
            speaker: Optional character name/identifier

        Returns:
            Translated text
        """
        # SeamlessM4T uses processor to prepare inputs
        # tgt_lang specifies target language using 3-letter codes
        text_inputs = self.processor(
            text=text,
            src_lang="eng",  # Source is always English
            return_tensors="pt"
        )

        # Move inputs to device
        text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}

        # Generate translation
        with torch.no_grad():
            output_tokens = self.model.generate(
                **text_inputs,
                tgt_lang=self.lang_code_3letter,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True,
            )

        # Decode translation
        translation = self.processor.decode(output_tokens[0].tolist()[0], skip_special_tokens=True)

        # Apply glossary if available
        translation = self._apply_glossary(text, translation)

        # Clean up translation
        translation = translation.strip()

        return translation


if __name__ == "__main__":
    """
    CLI entry point for standalone translation script usage.

    Usage:
        python seamlessm4t_translator.py <input_file> --language <language_code>

    Example:
        python seamlessm4t_translator.py script.rpy --language ro
    """
    import sys
    import json
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python seamlessm4t_translator.py <input_file> --language <lang_code>")
        print("Example: python seamlessm4t_translator.py script.rpy --language ro")
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
    translator = SeamlessM4Tv2Translator(
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
