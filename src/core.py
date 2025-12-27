from pathlib import Path
import sys
import io
import json
import os

# Fix Windows PATH for CUDA DLLs (required for llama-cpp-python)
# This must happen BEFORE importing llama_cpp
if sys.platform == "win32":
    # Try to find torch lib directory
    project_root = Path(__file__).parent.parent.parent
    torch_lib = project_root / "venv" / "Lib" / "site-packages" / "torch" / "lib"
    if torch_lib.exists() and str(torch_lib) not in os.environ["PATH"]:
        os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ["PATH"]

# Now import llama_cpp after PATH is set
from llama_cpp import Llama

# Import prompts (try relative import first, fall back to direct import)
try:
    from .prompts import create_translation_prompt, create_correction_prompt
except ImportError:
    from prompts import create_translation_prompt, create_correction_prompt

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class Aya23Translator:
    """Aya-23-8B translator using llama.cpp - supports 23 languages"""

    def __init__(self, model_path, target_language="Romanian", n_gpu_layers=-1, n_ctx=8192):
        """
        Args:
            model_path: Path to Aya-23 GGUF model
            target_language: Target language name (e.g., "Romanian", "Spanish", "French")
            n_gpu_layers: Number of layers to offload to GPU (-1 = all layers, optimal for RTX 3060 6GB)
            n_ctx: Context window size (default 8192, matches model training)
        """
        self.target_language = target_language
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

    def build_translation_prompt(self, text, glossary=None, context=None, speaker=None):
        """Build prompt for translation with context awareness"""

        # Build glossary instructions if provided
        glossary_instructions = ""
        if glossary:
            key_terms = []
            # Only include terms that actually appear in the text
            for en_term, target_term in glossary.items():
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

        # Use prompt template from prompts module
        return create_translation_prompt(text, self.target_language, glossary_instructions, context_section, speaker_hint)

    def translate(self, text, glossary=None, context=None, speaker=None, temperature=0.2, max_tokens=512):
        """
        Translate single text with optional context

        Args:
            text: English text to translate
            glossary: Optional dict of EN→target language term mappings
            context: Optional list of previous dialogue lines for context
            speaker: Optional character name/identifier
            temperature: Lower = more deterministic (0.1-0.3 for translation)
            max_tokens: Maximum length of translation

        Returns:
            Translated text
        """
        prompt = self.build_translation_prompt(text, glossary, context, speaker)

        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["English:", "\n\n", "\nTranslation:", "Translation:"],
            echo=False
        )

        translation = output['choices'][0]['text'].strip()

        # Post-process: Clean up any remaining artifacts
        translation = self._clean_translation(translation)

        return translation

    def _clean_translation(self, text):
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

    def translate_batch(self, texts, glossary=None, temperature=0.3):
        """
        Translate batch of texts (sequential, no true batching in llama.cpp)

        Args:
            texts: List of English strings
            glossary: Optional dict of EN→target language term mappings
            temperature: Translation temperature

        Returns:
            List of translations
        """
        translations = []
        for i, text in enumerate(texts):
            print(f"Translating {i+1}/{len(texts)}...", end='\r')
            trans = self.translate(text, glossary, temperature)
            translations.append(trans)
        print()  # New line after progress
        return translations
