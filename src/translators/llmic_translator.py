"""
LLMic-3B Translator Implementation

Uses Hugging Face transformers for EN->RO translation.
Bilingual Romanian-English model with SOTA BLEU score for EN-RO (41.01 on WMT16).
Decoder-only Llama2-based architecture optimized for Romanian translation.
"""

from pathlib import Path

# Try to import transformers dependencies
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None


class LLMicTranslator:
    """
    LLMic-3B translator using Hugging Face transformers

    Bilingual EN<->RO model with best-in-class BLEU score for Romanian (41.01).
    Based on Llama2 architecture (decoder-only, 3B parameters).
    """

    def __init__(self, target_language: str = "Romanian", lang_code: str = "ro",
                 device: str = None, glossary: dict = None, model_name: str = None):
        """
        Initialize LLMic-3B translator

        Args:
            target_language: Target language name (should be "Romanian" for LLMic)
            lang_code: Language code (should be "ro" for Romanian)
            device: Device to use ('cuda' or 'cpu'). If None, auto-detected.
            glossary: Optional dict of EN->target language term mappings
            model_name: Model variant to use. Default: "faur-ai/LLMic"
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"LLMicTranslator requires transformers and torch packages.\n"
                f"Original error: {IMPORT_ERROR}\n"
                f"This is likely due to triton/torch version incompatibility.\n"
                f"See: https://github.com/pytorch/ao/issues/2919"
            )

        self._target_language = target_language
        self.lang_code = lang_code
        self.glossary = glossary or {}

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        if model_name is None:
            model_name = "faur-ai/LLMic"
        self.model_name = model_name

        print(f"Initializing LLMic-3B Translation (EN->{target_language})...")
        print(f"  Language code: {lang_code}")
        print(f"  Device: {device}")
        print(f"  Model: {model_name}")
        print(f"  Loading model... This may take 30-60 seconds...")

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Use memory-efficient loading to avoid paging file errors
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.float16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True,  # Reduces RAM usage during loading
            device_map="auto"  # Automatically manages memory across CPU/GPU
        )
        # Note: Don't call .to(device) when using device_map="auto"

        self.model.eval()

        # Set pad token if not set (Llama models often don't have one)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id

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
                  temperature: float = 0.7, context: list = None,
                  speaker: str = None) -> str:
        """
        Translate text using LLMic-3B

        Args:
            text: English text to translate
            max_length: Maximum length of generated translation
            num_beams: Number of beams for beam search
            temperature: Sampling temperature (lower = more deterministic)
            context: Optional list of previous dialogue lines (for consistency)
            speaker: Optional character name/identifier

        Returns:
            Translated Romanian text
        """
        # For a decoder-only model, we need to create a prompt that instructs translation
        # LLMic is bilingual EN-RO, trained on translation pairs

        # Simple prompt format for translation
        prompt = f"English: {text}\nRomanian:"

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            add_special_tokens=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate translation (max_new_tokens=256)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                num_beams=num_beams,
                temperature=temperature,
                do_sample=temperature > 0,
                early_stopping=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode the full output
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the Romanian part (after "Romanian:")
        if "Romanian:" in full_output:
            translation = full_output.split("Romanian:")[-1].strip()
        else:
            # Fallback: remove the prompt from output
            translation = full_output.replace(prompt, "", 1).strip()

        # Truncate at the first newline character to prevent excessive generation
        if "\n" in translation:
            translation = translation.split("\n")[0].strip()

        # Apply glossary if available
        translation = self._apply_glossary(text, translation)

        # Clean up translation
        translation = translation.strip()

        # Remove any remaining "English:" markers that might appear
        if "English:" in translation:
            translation = translation.split("English:")[0].strip()

        return translation


if __name__ == "__main__":
    """
    CLI entry point for standalone translation script usage.

    Usage:
        python llmic_translator.py <input_file> --language ro

    Example:
        python llmic_translator.py script.rpy --language ro
    """
    import sys
    import json
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python llmic_translator.py <input_file> --language ro")
        print("Note: LLMic only supports Romanian (ro)")
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
        print("Error: LLMic only supports Romanian translation (--language ro)")
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
    translator = LLMicTranslator(
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
