"""
Integration Test: Aya-23-8B Model Translation

This test verifies that the Aya23Translator can successfully translate a simple phrase
from English to Romanian. It's a lightweight check to ensure the model loads
and produces the expected output.
"""

import sys
from pathlib import Path
import unittest

# Import from installed poly_trans package
from poly_trans.translators.aya23_translator import Aya23Translator

# Import the base test class from repo root
# Current location: packages/poly_trans/tests/test_int_aya23.py
# Project root: 3 levels up
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from tests.utils import BaseTranslatorIntegrationTest


# Test configuration
MODEL_SUBDIR = "aya23"
MODEL_FILENAME = "aya-23-8B-Q4_K_M.gguf"


class TestAya23Integration(BaseTranslatorIntegrationTest):
    # Use the helper method from the base class to construct the model path
    model_path = BaseTranslatorIntegrationTest.project_root / "models" / MODEL_SUBDIR / MODEL_FILENAME

    @classmethod
    def setUpClass(cls):
        """Set up the translator instance once for all tests in this class."""
        super().setUpClass()  # Call base class setup

        if not cls.model_path.exists():
            raise unittest.SkipTest(f"Aya-23 model not found at {cls.model_path}")

        print("Setting up Aya23Translator for integration test...")
        cls.translator = Aya23Translator(
            model_path=str(cls.model_path),
            target_language='Romanian',
            n_gpu_layers=0  # Use CPU for this simple test to avoid GPU memory issues
        )
        print("Translator setup complete.")

    def test_translate_hello_world(self):
        """
        Tests translation of a simple phrase to Romanian.
        """
        english_text = "The quick brown fox jumps over the lazy dog."
        expected_romanian = "Foxul brun rapid sare peste câinele leneș."

        self._assert_translation(english_text, expected_romanian)

if __name__ == '__main__':
    unittest.main()
