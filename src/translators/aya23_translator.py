"""
Aya-23-8B Translator Implementation

Uses llama.cpp for fast, local translation with 23 language support.
Optimized for quality on major European and Asian languages.
"""

import sys
import os
from pathlib import Path

# Fix Windows PATH for CUDA DLLs (required for llama-cpp-python)
# This must happen BEFORE importing llama_cpp
if sys.platform == "win32":
    project_root = Path(__file__).parent.parent.parent
    torch_lib = project_root / "venv" / "Lib" / "site-packages" / "torch" / "lib"
    if torch_lib.exists() and str(torch_lib) not in os.environ["PATH"]:
        os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ["PATH"]

from llama_cpp import Llama


class Aya23Translator:
    """
    Aya-23-8B translator using llama.cpp

    Supports 23 languages with high quality translations.
    Uses GGUF quantized models for efficient GPU inference.
    """

    def __init__(self, model_path: str, target_language: str = "Romanian",
                 n_gpu_layers: int = -1, n_ctx: int = 8192,
                 prompt_template: str = None, glossary: dict = None):
        """
        Initialize Aya-23-8B translator

        Args:
            model_path: Path to Aya-23 GGUF model file
            target_language: Target language name (e.g., "Romanian", "Spanish", "French")
            n_gpu_layers: Number of layers to offload to GPU (-1 = all layers, optimal for RTX 3060 6GB)
            n_ctx: Context window size (default 8192, matches model training)
            prompt_template: Optional custom prompt template string
            glossary: Optional dict of EN→target language term mappings
        """
        self._target_language = target_language
        self.glossary = glossary or {}
        self.prompt_template = prompt_template

        print(f"Loading Aya-23-8B from {model_path}...")
        print("This may take 30-60 seconds...")

        self.llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=n_gpu_layers,  # Use GPU
            n_ctx=n_ctx,
            n_batch=256,
            verbose=False
        )

        print("Model loaded successfully!")
        print(f"  Context window: {n_ctx} tokens")
        print(f"  GPU layers: {n_gpu_layers if n_gpu_layers != -1 else 'All'}")

    @property
    def target_language(self) -> str:
        """Return the target language name"""
        return self._target_language

    def _build_translation_prompt(self, text: str, context: list = None, speaker: str = None) -> str:
        """
        Build prompt for translation with context awareness

        Args:
            text: Clean English text to translate
            context: Optional list of previous dialogue lines
            speaker: Optional character name/identifier

        Returns:
            Complete translation prompt
        """
        # Build glossary instructions if provided
        glossary_instructions = ""
        if self.glossary:
            key_terms = []
            # Only include terms that actually appear in the text
            for en_term, target_term in self.glossary.items():
                # Skip comment entries
                if en_term.startswith("_comment"):
                    continue
                if en_term.lower() in text.lower():
                    key_terms.append(f'"{en_term}" = "{target_term}"')

            if key_terms:
                glossary_instructions = "\nMandatory term translations: " + ", ".join(key_terms[:10]) + "."

        # Build context if provided
        context_section = ""
        if context and len(context) > 0:
            context_lines = "\n".join([f"  {line}" for line in context[-4:]])  # Last 4 lines
            context_section = f"\n\nPrevious dialogue:\n{context_lines}"

        # Build speaker hint if provided
        speaker_hint = ""
        if speaker:
            speaker_hint = f"\nSpeaker: {speaker}"

        # Use custom prompt template or load from prompts module
        if self.prompt_template:
            return self.prompt_template.format(
                target_language=self._target_language,
                glossary_instructions=glossary_instructions,
                context_section=context_section,
                speaker_hint=speaker_hint,
                text=text
            )
        else:
            # Fallback: import from prompts module
            try:
                from prompts import create_translation_prompt
                return create_translation_prompt(
                    text, self._target_language,
                    glossary_instructions, context_section, speaker_hint
                )
            except ImportError:
                # Ultimate fallback: simple inline template
                return f"Translate this English text to {self._target_language}.\n\nEnglish: {text}\n{self._target_language}:"

    def translate(self, text: str, context: list = None, speaker: str = None,
                  temperature: float = 0.2, max_tokens: int = 512) -> str:
        """
        Translate single text with optional context

        Args:
            text: English text to translate
            context: Optional list of previous dialogue lines for context
            speaker: Optional character name/identifier
            temperature: Lower = more deterministic (0.1-0.3 for translation)
            max_tokens: Maximum length of translation

        Returns:
            Translated text
        """
        prompt = self._build_translation_prompt(text, context, speaker)

        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["English:", "\nEnglish:", "\nTranslation:", "Translation:", "\n\n\n"],
            echo=False
        )

        raw_translation = output['choices'][0]['text'].strip()

        # Post-process: Clean up any remaining artifacts
        translation = self._clean_translation(raw_translation)

        return translation

    def _clean_translation(self, text: str) -> str:
        """
        Clean up translation output by removing common artifacts

        Args:
            text: Raw translation output

        Returns:
            Cleaned translation
        """
        # Remove "Translation:" prefix if present
        if text.startswith("Translation:"):
            text = text[12:].strip()

        # Take only the first line (in case model generated multiple)
        lines = text.split('\n')
        if lines:
            text = lines[0].strip()

        # Remove any trailing quotes that might be artifacts
        text = text.strip('"').strip("'")

        # Remove language prefix if present (e.g., "Romanian:", "Spanish:")
        for lang_name in ["Romanian", "Spanish", "French", "German", "Italian", "Portuguese",
                          "Russian", "Arabic", "Chinese", "Japanese", "Korean"]:
            prefix = f"{lang_name}:"
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        return text


if __name__ == "__main__":
    """
    CLI entry point for standalone translation script usage.

    Usage:
        python aya23_translator.py <input_file> --language <language>

    Example:
        python aya23_translator.py script.rpy --language ro
    """
    import sys
    from pathlib import Path
    from translator_utils import (
        get_project_root, load_glossary, parse_cli_language_arg,
        load_prompt_template, setup_sys_path
    )

    # Add parent directory to path for imports
    setup_sys_path()
    from translation_pipeline import RenpyTranslationPipeline

    if len(sys.argv) < 3:
        print("Usage: python aya23_translator.py <input_file> --language <lang_code>")
        print("Example: python aya23_translator.py script.rpy --language ro")
        sys.exit(1)

    # Parse arguments
    input_file = Path(sys.argv[1])
    target_language, target_language_code = parse_cli_language_arg()

    if not target_language:
        print("Error: --language parameter is required")
        sys.exit(1)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Default paths
    project_root = get_project_root()
    model_path = project_root / "models" / "aya-23-8B-GGUF" / "aya-23-8B-Q4_K_M.gguf"

    if not model_path.exists():
        print(f"Error: Model file not found: {model_path}")
        sys.exit(1)

    # Load glossary using shared utility
    glossary = load_glossary(target_language_code, project_root)

    # Load prompt template using shared utility
    prompt_template = load_prompt_template(target_language_code, project_root)

    # Initialize translator
    translator = Aya23Translator(
        model_path=str(model_path),
        target_language=target_language,
        prompt_template=prompt_template,
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
