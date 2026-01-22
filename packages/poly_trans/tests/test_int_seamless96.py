"""
Integration Test: SeamlessM4T-v2 Model Translation

This test verifies that the SeamlessM4Tv2Translator can successfully translate a simple phrase
from English to Romanian. It's a lightweight check to ensure the model loads
and produces the expected output.
"""

import sys
from pathlib import Path
import unittest

# Import from installed poly_trans package
from poly_trans.translators.seamless96_translator import SeamlessM4Tv2Translator, TRANSFORMERS_AVAILABLE, IMPORT_ERROR

# Import the base test class from repo root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from tests.utils import (BaseTranslatorIntegrationTest, get_test_device,
                         skip_if_transformers_unavailable, safe_init_translator)


class TestSeamlessM4TIntegration(BaseTranslatorIntegrationTest):

    @classmethod
    def setUpClass(cls):
        """Set up the translator instance once for all tests in this class."""
        super().setUpClass()  # Call base class setup

        skip_if_transformers_unavailable(TRANSFORMERS_AVAILABLE, IMPORT_ERROR, "SeamlessM4Tv2Translator")

        cls.translator = safe_init_translator(
            translator_class=SeamlessM4Tv2Translator,
            translator_name="SeamlessM4Tv2Translator",
            init_kwargs={
                'target_language': 'Romanian',
                'lang_code': 'ro',
                'device': get_test_device()
            }
        )

    def test_translate_hello_world(self):
        """
        Tests translation of a simple phrase to Romanian.
        """
        english_text = "The quick brown fox jumps over the lazy dog."
        # SeamlessM4T-v2 expected translation (update after first successful run)
        expected_romanian = "Vulpea maro rapidă sare peste câinele leneș."

        self._assert_translation(english_text, expected_romanian)

if __name__ == '__main__':
    unittest.main()
