"""
Integration Test: Aya Expanse 8B Model Translation

Verifies that LlamaCppTranslator loads the ayaExpanse8b GGUF and produces
non-empty Romanian translations. Skipped automatically when the model file
is not present.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

PROJECT_ROOT = project_root

_MODEL_DIR = PROJECT_ROOT / "models" / "ayaExpanse8b"
_GGUF_FILES = list(_MODEL_DIR.glob("*.gguf")) if _MODEL_DIR.exists() else []
_MODEL_PATH = _GGUF_FILES[0] if _GGUF_FILES else None


@unittest.skipIf(_MODEL_PATH is None, "ayaExpanse8b model not downloaded — run 0-setup.ps1")
class TestAyaExpanse8bIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from translators.llama_cpp_translator import LlamaCppTranslator
        cls.translator = LlamaCppTranslator(
            model_path=str(_MODEL_PATH),
            target_language="Romanian",
            n_gpu_layers=-1,
            n_ctx=8192,
            n_batch=128,
        )

    @classmethod
    def tearDownClass(cls):
        del cls.translator

    def test_translate_returns_nonempty_string(self):
        result = self.translator.translate("Hello!")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0)

    def test_translate_with_context(self):
        result = self.translator.translate(
            "How are you?",
            context=["Alice: Hello!"],
            speaker="Alice",
        )
        self.assertIsInstance(result, str)

    def test_translate_does_not_echo_input(self):
        text = "The student walked into the academy."
        result = self.translator.translate(text)
        self.assertNotEqual(result.strip(), text)

    def test_target_language_property(self):
        self.assertEqual(self.translator.target_language, "Romanian")


if __name__ == "__main__":
    unittest.main()
