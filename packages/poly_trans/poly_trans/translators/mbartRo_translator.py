"""
MBART-En-Ro Translator Implementation

Uses Hugging Face transformers for translation with Facebook's MBART model.
Optimized for English to Romanian translation.
"""

from pathlib import Path

# Try to import transformers dependencies
try:
    import torch
    from transformers import MBartForConditionalGeneration, MBartTokenizer
    TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError
    MBartForConditionalGeneration = None
    MBartTokenizer = None
    torch = None


class MBARTTranslator:
    """
    MBART translator using Hugging Face transformers

    Facebook's multilingual BART model fine-tuned for English-Romanian translation.
    """

    def __init__(self, model_path: str = None, target_language: str = "Romanian",
                 lang_code: str = "ro", device: str = None, glossary: dict = None):
        """
        Initialize MBART translator

        Args:
            model_path: Path to local model or HuggingFace model ID
            target_language: Target language name
            lang_code: Language code (default: "ro" for Romanian)
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN->target language term mappings
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"MBARTTranslator requires transformers and torch packages.\n"
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
        project_root = Path(__file__).parent.parent.parent.parent
        if model_path is None:
            model_path = project_root / "models" / "mbartRo"
        else:
            model_path = Path(model_path)

        self.model_path = str(model_path)

        print(f"Initializing MBART Translation (EN->{target_language})...")
        print(f"  Language code: {lang_code}")
        print(f"  Device: {device}")
        print(f"  Model: {model_path}")
        print(f"  Loading model... This may take 30-60 seconds...")

        # Load tokenizer and model from local path
        self.tokenizer = MBartTokenizer.from_pretrained(str(model_path))

        # Use memory-efficient loading
        self.model = MBartForConditionalGeneration.from_pretrained(
            str(model_path),
            low_cpu_mem_usage=True,
            device_map="auto",
            dtype=torch.float16 if device == "cuda" else torch.float32
        )

        self.model.eval()

        # Set source and target language codes for MBART
        # MBART uses language codes like "en_XX" for English, "ro_RO" for Romanian
        self.src_lang = "en_XX"
        self.tgt_lang = "ro_RO"
        self.tokenizer.src_lang = self.src_lang

        print("Model loaded successfully!")

    @property
    def target_language(self) -> str:
        """Return the target language name"""
        return self._target_language

    def translate(self, text: str, max_length: int = 256, num_beams: int = 5,
                  context: list = None, speaker: str = None) -> str:
        """
        Translate text using MBART

        Args:
            text: English text to translate
            max_length: Maximum number of new tokens to generate
            num_beams: Number of beams for beam search (default 5 for quality)
            context: Optional list of previous dialogue lines (for consistency)
            speaker: Optional character name/identifier

        Returns:
            Translated text
        """
        # Set source language before tokenization (important for MBART50)
        self.tokenizer.src_lang = self.src_lang

        # Tokenize input
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate translation
        with torch.no_grad():
            generated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[self.tgt_lang],
                max_new_tokens=max_length,
                num_beams=num_beams,
                early_stopping=True
            )

        # Decode translation
        translation = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

        # Clean up translation
        translation = translation.strip()

        return translation


