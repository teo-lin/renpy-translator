"""
Translation Backends

This package contains translator implementations for different models.
All translators implement the BaseTranslator interface from translation_pipeline.

IMPORTANT: Imports are lazy to avoid triggering dependency conflicts.
Import translators directly when needed:
    from translators.aya23_translator import Aya23Translator
    from translators.madlad400_translator import MADLAD400Translator
    from translators.seamlessm4t_translator import SeamlessM4TTranslator
"""

# Lazy loading to avoid import errors from incompatible dependencies
# Do NOT import translators here - import them directly where needed
__all__ = [
    'Aya23Translator',
    'MADLAD400Translator',
    'SeamlessM4TTranslator'
]
