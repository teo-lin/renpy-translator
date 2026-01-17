"""
Translation Backends

This package contains translator implementations for different models.

IMPORTANT: Imports are lazy to avoid triggering dependency conflicts.
Import translators directly when needed:
    from .aya23_translator import Aya23Translator
    from .madlad400_translator import MADLAD400Translator
    from .helsinkyRo_translator import HelsinkiRoTranslator
    from .mbartRo_translator import MBARTRoTranslator
    from .seamless96_translator import SeamlessM4Tv2Translator
"""

# Lazy loading to avoid import errors from incompatible dependencies
# Do NOT import translators here - import them directly where needed
__all__ = [
    'Aya23Translator',
    'MADLAD400Translator',
    'HelsinkiRoTranslator',
    'MBARTRoTranslator',
    'SeamlessM4Tv2Translator',
]
