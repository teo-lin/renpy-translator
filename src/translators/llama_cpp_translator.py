"""
Generic GGUF translator via llama.cpp.
Works with any instruction-tuned GGUF model (Aya-23, Aya Expanse, EuroLLM, etc.).
Accepts hardware-tier-resolved params from models/compute_profile.yaml.
"""

import sys
import os
from pathlib import Path

# Fix Windows PATH for CUDA DLLs — must happen before importing llama_cpp
if sys.platform == "win32":
    project_root = Path(__file__).parent.parent.parent
    torch_lib = project_root / "venv" / "Lib" / "site-packages" / "torch" / "lib"
    if torch_lib.exists() and str(torch_lib) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(torch_lib) + os.pathsep + os.environ["PATH"]

from llama_cpp import Llama

from translators.translator_utils import glossary_prompt_entries, apply_ro_subjunctive, apply_source_conditioned, back_map_for


class LlamaCppTranslator:
    """
    Generic GGUF translator. All inference parameters come from the caller
    (resolved from compute_profile.yaml) — nothing is hardcoded here.
    """

    def __init__(
        self,
        model_path: str,
        target_language: str = "Romanian",
        n_gpu_layers: int = -1,
        n_ctx: int = 8192,
        n_batch: int = 256,
        prompt_template: str = None,
        glossary: dict = None,
    ):
        self._target_language = target_language
        self.glossary = glossary or {}
        self.prompt_template = prompt_template

        model_name = Path(model_path).stem
        print(f"Loading {model_name}...")
        print("This may take 30-60 seconds...")

        self.llm = Llama(
            model_path=str(model_path),
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            n_batch=n_batch,
            verbose=False,
        )

        print("Model loaded successfully!")
        print(f"  Context window : {n_ctx} tokens")
        print(f"  GPU layers     : {'All' if n_gpu_layers == -1 else n_gpu_layers}")

    @property
    def target_language(self) -> str:
        return self._target_language

    def _build_translation_prompt(
        self, text: str, context: list = None, speaker: str = None
    ) -> str:
        glossary_instructions = ""
        if self.glossary:
            key_terms = glossary_prompt_entries(self.glossary, text)
            if key_terms:
                glossary_instructions = "\nMandatory term translations: " + ", ".join(key_terms) + "."

        context_section = ""
        if context:
            lines = "\n".join(f"  {line}" for line in context[-4:])
            context_section = f"\n\nPrevious dialogue:\n{lines}"

        speaker_hint = f"\nSpeaker: {speaker}" if speaker else ""

        if self.prompt_template:
            return self.prompt_template.format(
                target_language=self._target_language,
                glossary_instructions=glossary_instructions,
                context_section=context_section,
                speaker_hint=speaker_hint,
                text=text,
            )

        try:
            from prompts import create_translation_prompt
            return create_translation_prompt(
                text, self._target_language,
                glossary_instructions, context_section, speaker_hint,
            )
        except ImportError:
            return (
                f"Translate this English text to {self._target_language}.\n\n"
                f"English: {text}\n{self._target_language}:"
            )

    def translate(
        self,
        text: str,
        context: list = None,
        speaker: str = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        prompt = self._build_translation_prompt(text, context, speaker)

        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["English:", "\nEnglish:", "\nTranslation:", "Translation:", "\n\n\n"],
            echo=False,
        )

        raw = output["choices"][0]["text"].strip()
        translation = self._clean_translation(raw)
        translation = apply_ro_subjunctive(translation)
        translation = apply_source_conditioned(text, translation, back_map_for(self._target_language))
        return translation

    def _clean_translation(self, text: str) -> str:
        if text.startswith("Translation:"):
            text = text[12:].strip()

        lines = text.split("\n")
        if lines:
            text = lines[0].strip()

        # Strip surrounding **bold** markdown (EuroLLM wraps output in **)
        if text.startswith("**") and text.endswith("**") and len(text) > 4:
            text = text[2:-2].strip()

        text = text.strip('"').strip("'")

        for lang in [
            "Romanian", "Spanish", "French", "German", "Italian", "Portuguese",
            "Russian", "Arabic", "Chinese", "Japanese", "Korean",
        ]:
            if text.startswith(f"{lang}:"):
                text = text[len(lang) + 1:].strip()
                break

        return text
