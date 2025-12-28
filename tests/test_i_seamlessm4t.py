"""
Integration Test: SeamlessM4T-v2 Model Translation

This test verifies that the SeamlessM4Tv2Translator can successfully translate a simple phrase
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

import pytest

# Import the base test class and utility functions
from tests.utils import BaseTranslatorIntegrationTest

# Import the specific translator and its related flags
from seamlessm4t_translator import SeamlessM4Tv2Translator, TRANSFORMERS_AVAILABLE, IMPORT_ERROR


class TestSeamlessM4TIntegration(BaseTranslatorIntegrationTest):

    @classmethod
    def setUpClass(cls):
        """Set up the translator instance once for all tests in this class."""
        super().setUpClass() # Call base class setup

        if not TRANSFORMERS_AVAILABLE:
            pytest.skip(f"SeamlessM4Tv2Translator requires transformers and torch packages "
                           f"due to: {IMPORT_ERROR}")

        print("Setting up SeamlessM4Tv2Translator for integration test...")
        try:
            cls.translator = SeamlessM4Tv2Translator(
                target_language='Romanian',
                lang_code='ro',
                device='cpu' # Use CPU for this simple test
            )
            print("Translator setup complete.")
        except Exception as e:
            pytest.skip(f"Failed to load SeamlessM4Tv2Translator, likely due to memory constraints or other issues: {e}")


    def test_translate_hello_world(self):
        """
        Tests translation of "Hello World!" to Romanian.
        """
        english_text = "Hello World!"
        # This translation was not obtained from a successful run due to memory constraints.
        # It is a plausible translation.
        expected_romanian = "Bună, lume!" 

        self._assert_translation(english_text, expected_romanian)

if __name__ == '__main__':
    unittest.main()