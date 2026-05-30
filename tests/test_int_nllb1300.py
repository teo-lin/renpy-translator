"""
Integration tests for NLLB200Translator with the nllb-200-distilled-1.3B model.
Skipped automatically when models/nllb1300 is not present.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tests.utils import TranslateBatchTestMixin

_MODEL_PATH = PROJECT_ROOT / "models" / "nllb1300"
_SKIP_REASON = "nllb1300 model not downloaded (run 0-setup.ps1)"


@unittest.skipIf(not _MODEL_PATH.exists() or not any(_MODEL_PATH.iterdir()), _SKIP_REASON)
class TestNLLB1300Integration(TranslateBatchTestMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from translators.nllb200_translator import NLLB200Translator
        print(f"\nIntegration test: loading nllb1300 from {_MODEL_PATH}")
        cls.translator = NLLB200Translator(
            model_path=str(_MODEL_PATH),
            target_language="Romanian",
            lang_code="ro",
        )

    @classmethod
    def tearDownClass(cls):
        del cls.translator
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except (ImportError, RuntimeError):
            pass

    def test_translate_returns_string(self):
        result = self.translator.translate("Hello!")
        self.assertIsInstance(result, str)

    def test_translate_returns_nonempty_string(self):
        result = self.translator.translate("Hello!")
        self.assertGreater(len(result.strip()), 0)

    def test_translate_does_not_echo_input(self):
        text = "Good morning."
        result = self.translator.translate(text)
        self.assertNotEqual(result.strip(), text)

    def test_translate_short_phrase(self):
        result = self.translator.translate("Thank you.")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result.strip()), 0)

    def test_target_language_property(self):
        self.assertEqual(self.translator.target_language, "Romanian")

    def test_translate_with_context_does_not_crash(self):
        result = self.translator.translate(
            "How are you?",
            context=["Alice: Hello!", "Bob: Hi there!"],
        )
        self.assertIsInstance(result, str)

    def test_translate_with_glossary(self):
        from translators.nllb200_translator import NLLB200Translator
        t = NLLB200Translator(
            model_path=str(_MODEL_PATH),
            target_language="Romanian",
            lang_code="ro",
            glossary={"protagonist": "protagonist"},
        )
        result = t.translate("The protagonist walks forward.")
        self.assertIsInstance(result, str)
        del t


if __name__ == "__main__":
    unittest.main()
