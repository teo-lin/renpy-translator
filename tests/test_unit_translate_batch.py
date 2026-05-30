"""
Unit tests for translate_batch() on all 5 HF translators.

Mocks `transformers` in sys.modules so no model files are needed.
Bypasses __init__ via __new__ to set up the minimal attribute surface each
translate_batch() implementation reads from `self`.

Shared behavior (empty input, list-of-strings, single-matches-batch, glossary,
strip) is covered once in _BatchTranslatorTestBase; translator-specific
behavior (subjunctive, src_lang, cedilla, lang tags, non-Latin fallback) is
added per subclass.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock transformers BEFORE any translator import so loading never runs.
_mock_transformers = MagicMock()
sys.modules.setdefault("transformers", _mock_transformers)
_mock_transformers.logging.set_verbosity_error = MagicMock()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from translators.nllb200_translator import NLLB200Translator
from translators.helsinkyRo_translator import QuickMTTranslator
from translators.mbartRo_translator import MBARTTranslator
from translators.madlad400_translator import MADLAD400Translator
from translators.seamless96_translator import SeamlessM4Tv2Translator


def _make_tokenizer_inputs():
    """A dict whose values have a working `.to(device)` method."""
    return {"input_ids": MagicMock(), "attention_mask": MagicMock()}


def _make_tokenizer(decoded):
    """
    A tokenizer mock whose `__call__` returns a dict-with-.to() values, and
    whose `batch_decode` returns the given list. Also exposes
    `convert_tokens_to_ids` and `lang_code_to_id` for the NLLB/MBART paths.
    """
    tok = MagicMock()
    tok.return_value = _make_tokenizer_inputs()
    tok.batch_decode = MagicMock(return_value=decoded)
    tok.convert_tokens_to_ids = MagicMock(return_value=0)
    tok.lang_code_to_id = {"ro_RO": 0}
    return tok


# ─── Shared base ──────────────────────────────────────────────────────────────

class _BatchTranslatorTestBase:
    """
    Common behavioral tests for translate_batch on any of the 5 HF translators.

    Subclasses must define:
      - SAFE_GENERATE_MODULE: dotted path of the translator module that imports
        safe_generate (used by the default _patch_safe_generate).
      - _build(decoded=None, glossary=None): construct a translator instance
        wired with mocked tokenizer/model and ready for translate_batch().

    Translators with structured `safe_generate` outputs (Seamless) override
    `_patch_safe_generate` to return the right shape.
    """

    SAFE_GENERATE_MODULE: str = None

    def _build(self, decoded=None, glossary=None):
        raise NotImplementedError

    def _patch_safe_generate(self, monkeypatch):
        monkeypatch.setattr(
            f"{self.SAFE_GENERATE_MODULE}.safe_generate",
            lambda model, inputs, device, gen_fn: (MagicMock(), model, device),
        )

    def test_empty_input_returns_empty_list(self):
        t = self._build()
        assert t.translate_batch([]) == []

    def test_returns_list_of_strings_matching_input_size(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["Salut!", "Pa!"])
        result = t.translate_batch(["Hello!", "Bye!"])
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, str) for r in result)

    def test_translate_returns_translated_string(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["Salut!"])
        assert t.translate("Hello!") == "Salut!"

    def test_strips_each_item(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["  Salut!  ", "\nPa!\n"])
        assert t.translate_batch(["a", "b"]) == ["Salut!", "Pa!"]

    def test_glossary_applied_per_item(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(
            decoded=["protagonist", "alt cuvant"],
            glossary={"protagonist": "PROTAGONIST"},
        )
        result = t.translate_batch(["the protagonist walks", "nothing here"])
        assert result[0] == "PROTAGONIST"
        assert result[1] == "alt cuvant"


# ─── NLLB200Translator ────────────────────────────────────────────────────────

class TestNLLB200TranslateBatch(_BatchTranslatorTestBase):
    SAFE_GENERATE_MODULE = "translators.nllb200_translator"

    def _build(self, decoded=None, glossary=None):
        t = NLLB200Translator.__new__(NLLB200Translator)
        t._target_language = "Romanian"
        t.lang_code = "ro"
        t.glossary = glossary or {}
        t.device = "cpu"
        t.nllb_src = "eng_Latn"
        t.nllb_tgt = "ron_Latn"
        t.tokenizer = _make_tokenizer(decoded if decoded is not None else ["Salut!"])
        t.model = MagicMock()
        return t

    def test_subjunctive_applied_per_item(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["să fute", "nimic special"])
        result = t.translate_batch(["text1", "text2"])
        assert result[0] == "să fută"
        assert result[1] == "nimic special"


# ─── QuickMTTranslator (helsinkiRo) ───────────────────────────────────────────

class TestQuickMTTranslateBatch(_BatchTranslatorTestBase):
    SAFE_GENERATE_MODULE = "translators.helsinkyRo_translator"

    def _build(self, decoded=None, glossary=None):
        t = QuickMTTranslator.__new__(QuickMTTranslator)
        t._target_language = "Romanian"
        t.lang_code = "ro"
        t.glossary = glossary or {}
        t.device = "cpu"
        t.tokenizer = _make_tokenizer(decoded if decoded is not None else ["Salut!"])
        t.model = MagicMock()
        return t


# ─── MBARTTranslator ──────────────────────────────────────────────────────────

class TestMBARTTranslateBatch(_BatchTranslatorTestBase):
    SAFE_GENERATE_MODULE = "translators.mbartRo_translator"

    def _build(self, decoded=None, glossary=None):
        t = MBARTTranslator.__new__(MBARTTranslator)
        t._target_language = "Romanian"
        t.lang_code = "ro"
        t.glossary = glossary or {}
        t.device = "cpu"
        t.src_lang = "en_XX"
        t.tgt_lang = "ro_RO"
        t.tokenizer = _make_tokenizer(decoded if decoded is not None else ["Salut!"])
        t.model = MagicMock()
        return t

    def test_src_lang_set_on_tokenizer(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["x"])
        t.translate_batch(["test"])
        assert t.tokenizer.src_lang == "en_XX"


# ─── MADLAD400Translator ──────────────────────────────────────────────────────

class TestMADLAD400TranslateBatch(_BatchTranslatorTestBase):
    SAFE_GENERATE_MODULE = "translators.madlad400_translator"

    def _build(self, decoded=None, glossary=None):
        t = MADLAD400Translator.__new__(MADLAD400Translator)
        t._target_language = "Romanian"
        t.lang_code = "ro"
        t.glossary = glossary or {}
        t.device = "cpu"
        t.tokenizer = _make_tokenizer(decoded if decoded is not None else ["Salut"])
        t.model = MagicMock()
        return t

    def test_lang_tag_prepended_per_item(self, monkeypatch):
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["x", "y"])
        t.translate_batch(["hello", "world"])
        passed_texts = t.tokenizer.call_args[0][0]
        assert passed_texts == ["<2ro> hello", "<2ro> world"]

    def test_non_latin_item_falls_back_to_single_translate(self, monkeypatch):
        # 1st batch decode → ['Salut', 'გამარჯობა']  (second is Georgian)
        # 2nd (per-item retry, beam): still non-Latin
        # 3rd (per-item retry, greedy): now Latin
        self._patch_safe_generate(monkeypatch)
        t = self._build()
        t.tokenizer.batch_decode = MagicMock(side_effect=[
            ["Salut", "გამარჯობა"],
            ["გამარჯობა"],
            ["fallback latin"],
        ])
        result = t.translate_batch(["hello", "hi"])
        assert result[0] == "Salut"
        assert result[1] == "fallback latin"


# ─── SeamlessM4Tv2Translator ──────────────────────────────────────────────────

class TestSeamlessM4Tv2TranslateBatch(_BatchTranslatorTestBase):
    SAFE_GENERATE_MODULE = "translators.seamless96_translator"

    def _build(self, decoded=None, glossary=None):
        t = SeamlessM4Tv2Translator.__new__(SeamlessM4Tv2Translator)
        t._target_language = "Romanian"
        t.lang_code = "ro"
        t.lang_code_3letter = "ron"
        t.glossary = glossary or {}
        t.device = "cpu"

        # Seamless uses self.processor(...) rather than self.tokenizer(...).
        proc = MagicMock()
        proc.return_value = _make_tokenizer_inputs()
        # processor.tokenizer.decode is called per item; side_effect yields one
        # string per call. The base tests call _build with a 1 or 2 item list.
        decoded = decoded if decoded is not None else ["Salut!"]
        proc.tokenizer.decode = MagicMock(side_effect=decoded)
        t.processor = proc
        t.model = MagicMock()
        return t

    def _patch_safe_generate(self, monkeypatch):
        """Seamless's safe_generate returns a ModelOutput with `.sequences`."""
        import torch
        sequences = MagicMock()
        sequences.dtype = torch.long
        sequences.__getitem__ = MagicMock(side_effect=lambda i: MagicMock())
        output = MagicMock()
        output.sequences = sequences
        monkeypatch.setattr(
            f"{self.SAFE_GENERATE_MODULE}.safe_generate",
            lambda model, inputs, device, gen_fn: (output, model, device),
        )

    def test_cedilla_normalized_per_item(self, monkeypatch):
        # Seamless can emit cedilla-form ş / ţ — translate_batch should map them
        # to ș / ț before glossary/correction passes.
        self._patch_safe_generate(monkeypatch)
        t = self._build(decoded=["aşa ţipi", "fără diacritice"])
        result = t.translate_batch(["a", "b"])
        assert result[0] == "așa țipi"
        assert result[1] == "fără diacritice"
