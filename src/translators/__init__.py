"""
Translation Backends

This package contains translator implementations for different models.
All translators implement the BaseTranslator interface from translation_pipeline.
"""

from .aya23_translator import Aya23Translator
from .madlad400_translator import MADLAD400Translator

__all__ = ['Aya23Translator', 'MADLAD400Translator']
