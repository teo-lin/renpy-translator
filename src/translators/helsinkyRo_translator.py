"""
QuickMT-En-Ro Translator Implementation

Uses Hugging Face transformers for fast English to Romanian translation.
Lightweight model optimized for speed.
"""

import warnings
from pathlib import Path

# Try to import transformers dependencies
try:
    import torch
    from transformers import MarianMTModel, MarianTokenizer
    TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError
    MarianMTModel = None
    MarianTokenizer = None
    torch = None


class QuickMTTranslator:
    """
    QuickMT translator using Hugging Face transformers

    Lightweight Marian MT model for fast English-Romanian translation.
    """

    def __init__(self, model_path: str = None, target_language: str = "Romanian",
                 lang_code: str = "ro", device: str = None, glossary: dict = None):
        """
        Initialize QuickMT translator

        Args:
            model_path: Path to local model or HuggingFace model ID
            target_language: Target language name
            lang_code: Language code (default: "ro" for Romanian)
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN->target language term mappings
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"QuickMTTranslator requires transformers and torch packages.\n"
                f"Original error: {IMPORT_ERROR}"
            )

        self._target_language = target_language
        self.lang_code = lang_code
        self.glossary = glossary or {}

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Use local model path if not provided
        project_root = Path(__file__).parent.parent.parent
        if model_path is None:
            model_path = project_root / "models" / "helsinkiRo"
        else:
            model_path = Path(model_path)

        self.model_path = str(model_path)

        print(f"Initializing QuickMT Translation (EN->{target_language})...")
        print(f"  Language code: {lang_code}")
        print(f"  Device: {device}")
        print(f"  Model: {model_path}")
        print(f"  Loading model... This may take 10-30 seconds...")

        # Suppress sacremoses warning (it's optional and not needed for basic translation)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*sacremoses.*")
            # Load tokenizer and model from local path
            self.tokenizer = MarianTokenizer.from_pretrained(model_path)

        # Use memory-efficient loading
        self.model = MarianMTModel.from_pretrained(
            model_path,
            low_cpu_mem_usage=True,
            device_map="auto",
            dtype=torch.float16 if device == "cuda" else torch.float32
        )

        self.model.eval()
        print("Model loaded successfully!")

    @property
    def target_language(self) -> str:
        """Return the target language name"""
        return self._target_language

    def translate(self, text: str, max_length: int = 256, num_beams: int = 4,
                  context: list = None, speaker: str = None) -> str:
        """
        Translate text using QuickMT

        Args:
            text: English text to translate
            max_length: Maximum number of new tokens to generate
            num_beams: Number of beams for beam search (default 4)
            context: Optional list of previous dialogue lines (for consistency)
            speaker: Optional character name/identifier

        Returns:
            Translated text
        """
        # Tokenize input
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate translation
        with torch.no_grad():
            generated_tokens = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                num_beams=num_beams,
                early_stopping=True
            )

        # Decode translation
        translation = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

        # Clean up translation
        translation = translation.strip()

        return translation


if __name__ == "__main__":
    """
    CLI entry point for standalone translation script usage.

    Usage:
        python quickmt_translator.py <input_file> --language ro

    Example:
        python quickmt_translator.py script.rpy --language ro
    """
    import sys
    import json
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python quickmt_translator.py <input_file> --language ro")
        sys.exit(1)

    # Parse arguments
    input_file = Path(sys.argv[1])
    lang_code = None

    # Check for --language parameter
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == '--language' and i + 1 < len(sys.argv):
            lang_code = sys.argv[i + 1]
            break

    if lang_code != 'ro':
        print("Error: QuickMT-En-Ro only supports Romanian translation (--language ro)")
        sys.exit(1)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Try to load glossary
    project_root = Path(__file__).parent.parent.parent
    glossary = None
    for glossary_variant in ["ro_uncensored_glossary.json", "ro_glossary.json"]:
        glossary_path = project_root / "data" / glossary_variant
        if glossary_path.exists():
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
            print(f"[OK] Using glossary: {glossary_variant}")
            break

    # Initialize translator
    translator = QuickMTTranslator(
        target_language="Romanian",
        lang_code="ro",
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
