"""
poly-trans: Local neural translation engine with context awareness

Core translation package for polyglot translation tools.
"""

from .__version__ import __version__
from .models import ParsedBlock, parse_block_id, is_separator_block

# Lazy imports to avoid loading heavy dependencies at import time
# Import ModularBatchTranslator and translators directly when needed:
#   from poly_trans.translate import ModularBatchTranslator
#   from poly_trans.translators.aya23_translator import Aya23Translator

__all__ = [
    "__version__",
    "ParsedBlock",
    "parse_block_id",
    "is_separator_block",
]
