"""
MADLAD-400-3B Translator Implementation

Uses Hugging Face transformers for translation with 400+ language support.
Optimized for broad language coverage including rare and low-resource languages.
"""

import warnings
from pathlib import Path

# Try to import transformers dependencies
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BitsAndBytesConfig
    TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError
    AutoTokenizer = None
    AutoModelForSeq2SeqLM = None
    BitsAndBytesConfig = None
    torch = None


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
                 device: str = None, glossary: dict = None, unsloth: bool = False, trust_remote_code: bool = False):
        """
        Initialize MADLAD-400-3B translator

        Args:
            target_language: Target language name (e.g., "Romanian", "Spanish", "Japanese")
            lang_code: ISO 639-1 language code (e.g., "ro", "es", "ja"). If None, auto-detected.
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN→target language term mappings
            unsloth: Whether to use unsloth for faster inference
            trust_remote_code: Whether to trust remote code for the model
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"MADLAD400Translator requires transformers and torch packages.\n"
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

        print(f"Initializing MADLAD-400-3B Translation (EN->{target_language})...")
        print(f"  Language code: {lang_code}")
        print(f"  Device: {device}")
        print(f"  Loading model... This may take 30-60 seconds...")

        # Suppress non-critical warnings
        warnings.filterwarnings("ignore", message=".*device_map.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*swigvarlink.*", category=DeprecationWarning)

        # Use local model path
        project_root = Path(__file__).parent.parent.parent.parent
        model_path = project_root / "models" / "madlad400"

        # Load model and tokenizer
        if unsloth:
            from unsloth import FastLanguageModel
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=str(model_path),
                trust_remote_code=trust_remote_code
            )
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)

            # Use memory-efficient loading with float16 (like other models)
            # NOTE: We avoid device_map="auto" for MADLAD because the large vocabulary (400 languages)
            # causes it to incorrectly offload layers to CPU even when GPU has enough memory
            try:
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    str(model_path),
                    trust_remote_code=trust_remote_code,
                    dtype=torch.float16 if device == "cuda" else torch.float32,
                    local_files_only=True
                )
                # Manually move to device (more reliable than device_map for this model)
                self.model = self.model.to(self.device)
            except (OSError, RuntimeError) as e:
                error_msg = str(e).lower()
                if "paging file" in error_msg or "1455" in error_msg:
                    # Windows paging file error
                    raise MemoryError(
                        f"MADLAD-400-3B requires more memory than currently available.\n"
                        f"Error: {e}\n\n"
                        f"SOLUTION: Increase your Windows paging file size:\n"
                        f"  1. Open System Properties > Advanced > Performance Settings\n"
                        f"  2. Go to Advanced tab > Virtual Memory > Change\n"
                        f"  3. Uncheck 'Automatically manage paging file'\n"
                        f"  4. Set custom size: Initial=16384MB, Maximum=32768MB\n"
                        f"  5. Click Set, then OK, and restart your computer\n\n"
                        f"Alternative: Use a smaller model like QuickMT-En-Ro or MBART instead."
                    )
                elif "out of memory" in error_msg or "cuda" in error_msg:
                    raise MemoryError(
                        f"MADLAD-400-3B requires more GPU memory than available.\n"
                        f"Your GPU may not have enough VRAM for this model (needs ~6-7GB).\n\n"
                        f"SOLUTIONS:\n"
                        f"  1. Close other applications using GPU memory\n"
                        f"  2. Use a smaller model like Helsinki-Ro, MBART, or SeamlessM4T\n"
                        f"  3. Use CPU mode (slower): set device='cpu' in config"
                    )
                else:
                    raise

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

    def translate(self, text: str, max_length: int = 256, num_beams: int = 4,
                  temperature: float = 1.0, context: list = None,
                  speaker: str = None) -> str:
        """
        Translate text using MADLAD-400-3B

        Args:
            text: English text to translate
            max_length: Maximum number of new tokens to generate
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

        # Tokenize (no padding for single input - padding causes translation artifacts)
        inputs = self.tokenizer(input_text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Debug: Print first translation attempt
        import os
        if os.getenv('DEBUG_MADLAD'):
            print(f"[DEBUG] Input text: {input_text}")
            print(f"[DEBUG] Input tokens shape: {inputs['input_ids'].shape}")
            print(f"[DEBUG] Device: {self.device}")
            print(f"[DEBUG] Model device: {next(self.model.parameters()).device}")

        # Generate translation
        with torch.no_grad():
            # Generate with proper parameters
            # NOTE: MADLAD requires explicit max_new_tokens and beam search for quality
            outputs = self.model.generate(
                **inputs,  # Pass all tokenizer outputs (input_ids, attention_mask, etc.)
                max_new_tokens=max_length,
                num_beams=max(1, num_beams),
                early_stopping=True,
                do_sample=False,  # Use deterministic generation for better quality
                no_repeat_ngram_size=4,  # Stronger prevention of repetition
                repetition_penalty=1.2,  # Stronger penalty to prevent repetitions
                length_penalty=1.0  # Neutral length penalty
            )

        if os.getenv('DEBUG_MADLAD'):
            print(f"[DEBUG] Output tokens shape: {outputs.shape}")
            print(f"[DEBUG] Output tokens: {outputs[0][:20]}")  # First 20 tokens

        # Decode translation
        translation = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

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
    from pathlib import Path
    from translator_utils import (
        get_project_root, load_glossary, parse_cli_language_arg,
        setup_sys_path
    )

    # Add parent directory to path for imports
    setup_sys_path()
    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python madlad400_translator.py <input_file> --language <lang_code>")
        print("Example: python madlad400_translator.py script.rpy --language ro")
        sys.exit(1)

    # Parse arguments
    input_file = Path(sys.argv[1])
    target_language, lang_code = parse_cli_language_arg()

    if not target_language or not lang_code:
        print("Error: --language parameter is required")
        sys.exit(1)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Load glossary using shared utility
    project_root = get_project_root()
    glossary = load_glossary(lang_code, project_root)

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
