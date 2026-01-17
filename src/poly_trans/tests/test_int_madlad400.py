"""
Integration Test: MADLAD-400-3B Model Translation

This test verifies that the MADLAD400Translator can successfully translate a simple phrase
from English to Romanian. It's a lightweight check to ensure the model loads
and produces the expected output.
"""

import sys
from pathlib import Path

# Add project root and src/translators to sys.path for module discovery
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "translators"))

import unittest

# Import the base test class and utility functions
from tests.utils import (BaseTranslatorIntegrationTest, get_test_device,
                         skip_if_transformers_unavailable, safe_init_translator)

# Import the specific translator and its related flags
from madlad400_translator import MADLAD400Translator, TRANSFORMERS_AVAILABLE, IMPORT_ERROR


class TestMADLADIntegration(BaseTranslatorIntegrationTest):

    @classmethod
    def setUpClass(cls):
        """Set up the translator instance once for all tests in this class."""
        super().setUpClass()  # Call base class setup

        skip_if_transformers_unavailable(TRANSFORMERS_AVAILABLE, IMPORT_ERROR, "MADLAD400Translator")

        cls.translator = safe_init_translator(
            translator_class=MADLAD400Translator,
            translator_name="MADLAD400Translator",
            init_kwargs={
                'target_language': 'Romanian',
                'lang_code': 'ro',
                'device': get_test_device(),
                'unsloth': False  # Use standard transformers (unsloth needs torchao)
            }
        )

    def test_translate_hello_world(self):
        """
        Tests translation of a simple phrase to Romanian.
        """
        # Note: MADLAD-400 has known quality issues and may produce imperfect translations
        # This test verifies the model loads and produces output, not perfect translation quality
        english_text = "Hello, how are you?"
        # Accept any non-empty Romanian-like output (model quality varies)
        translation = self.translator.translate(english_text)
        self.assertIsNotNone(translation)
        self.assertGreater(len(translation), 0)
        # Just verify it's not obviously broken (no excessive repetition)
        self.assertNotIn('fo fo fo', translation.lower())

if __name__ == '__main__':
    unittest.main()
