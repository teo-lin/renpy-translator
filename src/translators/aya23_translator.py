"""
Aya-23-8B translator — thin subclass of LlamaCppTranslator with Aya-23 defaults.
"""

from pathlib import Path
from translators.llama_cpp_translator import LlamaCppTranslator

_DEFAULT_MODEL_PATH = (
    Path(__file__).parent.parent.parent
    / "models" / "aya23" / "aya-23-8B-Q4_K_M.gguf"
)


class Aya23Translator(LlamaCppTranslator):
    """LlamaCppTranslator pre-configured for Aya-23-8B with its original defaults."""

    def __init__(
        self,
        model_path: str = None,
        target_language: str = "Romanian",
        n_gpu_layers: int = -1,
        n_ctx: int = 8192,
        n_batch: int = 256,
        prompt_template: str = None,
        glossary: dict = None,
    ):
        super().__init__(
            model_path=str(model_path or _DEFAULT_MODEL_PATH),
            target_language=target_language,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            n_batch=n_batch,
            prompt_template=prompt_template,
            glossary=glossary,
        )
