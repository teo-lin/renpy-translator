"""
Unit tests for NLLB200Translator.
transformers and torch are mocked so no real model is required.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── mock transformers + torch before import ───────────────────────────────────
_mock_torch = MagicMock()
_mock_torch.cuda.is_available.return_value = False
_mock_torch.float16 = "float16"
_mock_torch.float32 = "float32"
_mock_torch.no_grad.return_value.__enter__ = lambda s, *a: s
_mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

_mock_tokenizer_instance = MagicMock()
_mock_tokenizer_instance.lang_code_to_id = {"ron_Latn": 256204, "spa_Latn": 256022}
_mock_tokenizer_instance.batch_decode.return_value = ["Salut lume"]

_mock_model_instance = MagicMock()
_mock_model_instance.generate.return_value = MagicMock()

_mock_transformers = MagicMock()
_mock_transformers.AutoTokenizer.from_pretrained.return_value = _mock_tokenizer_instance
_mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.return_value = _mock_model_instance

sys.modules["torch"] = _mock_torch
sys.modules["transformers"] = _mock_transformers

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from translators.nllb200_translator import NLLB200Translator, _NLLB_CODES


@pytest.fixture(autouse=True)
def reset_mocks():
    _mock_transformers.AutoTokenizer.from_pretrained.reset_mock()
    _mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.reset_mock()
    _mock_tokenizer_instance.reset_mock()
    _mock_tokenizer_instance.lang_code_to_id = {"ron_Latn": 256204, "spa_Latn": 256022}
    _mock_tokenizer_instance.batch_decode.return_value = ["Salut lume"]
    _mock_model_instance.reset_mock()
    _mock_model_instance.generate.return_value = MagicMock()


@pytest.fixture
def translator():
    return NLLB200Translator(
        model_path="/fake/nllb200",
        target_language="Romanian",
        lang_code="ro",
    )


# ── _NLLB_CODES ───────────────────────────────────────────────────────────────

class TestNllbCodes:
    def test_romanian_code(self):
        assert _NLLB_CODES["ro"] == "ron_Latn"

    def test_english_not_in_codes(self):
        assert "en" not in _NLLB_CODES

    def test_all_iso_codes_map_to_nllb_format(self):
        for iso, nllb in _NLLB_CODES.items():
            assert "_" in nllb, f"{iso} maps to invalid NLLB code '{nllb}'"

    def test_cyrillic_languages_use_cyrl_script(self):
        assert _NLLB_CODES["ru"].endswith("Cyrl")
        assert _NLLB_CODES["uk"].endswith("Cyrl")
        assert _NLLB_CODES["bg"].endswith("Cyrl")

    def test_latin_languages_use_latn_script(self):
        for code in ["ro", "es", "fr", "de", "it", "pt", "nl"]:
            assert _NLLB_CODES[code].endswith("Latn"), f"{code} should be Latn"

    def test_30_languages_covered(self):
        assert len(_NLLB_CODES) == 30


# ── __init__ ──────────────────────────────────────────────────────────────────

class TestInit:
    def test_target_language_property(self, translator):
        assert translator.target_language == "Romanian"

    def test_nllb_src_is_english(self, translator):
        assert translator.nllb_src == "eng_Latn"

    def test_nllb_tgt_for_romanian(self, translator):
        assert translator.nllb_tgt == "ron_Latn"

    def test_default_model_path_points_to_nllb200(self):
        t = NLLB200Translator(target_language="Romanian", lang_code="ro")
        assert "nllb200" in t.model_path

    def test_custom_model_path_stored(self, translator):
        assert translator.model_path == "/fake/nllb200"

    def test_tokenizer_loaded_with_src_lang(self):
        NLLB200Translator(model_path="/fake", target_language="Romanian", lang_code="ro")
        _mock_transformers.AutoTokenizer.from_pretrained.assert_called_once_with(
            "/fake", src_lang="eng_Latn"
        )

    def test_model_loaded_from_path(self):
        NLLB200Translator(model_path="/fake", target_language="Romanian", lang_code="ro")
        _mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.assert_called_once()
        call_args = _mock_transformers.AutoModelForSeq2SeqLM.from_pretrained.call_args
        assert call_args[0][0] == "/fake"

    def test_model_set_to_eval(self, translator):
        _mock_model_instance.eval.assert_called()

    def test_invalid_lang_code_raises(self):
        with pytest.raises(ValueError, match="no NLLB mapping"):
            NLLB200Translator(model_path="/fake", lang_code="xx")

    def test_cpu_device_used_when_no_cuda(self, translator):
        assert translator.device == "cpu"

    def test_cuda_device_when_available(self):
        _mock_torch.cuda.is_available.return_value = True
        t = NLLB200Translator(model_path="/fake", lang_code="ro")
        assert t.device == "cuda"
        _mock_torch.cuda.is_available.return_value = False

    def test_glossary_defaults_to_empty(self, translator):
        assert translator.glossary == {}

    def test_custom_glossary_stored(self):
        t = NLLB200Translator(model_path="/fake", lang_code="ro", glossary={"hi": "salut"})
        assert t.glossary == {"hi": "salut"}

    def test_spanish_lang_code(self):
        t = NLLB200Translator(model_path="/fake", lang_code="es", target_language="Spanish")
        assert t.nllb_tgt == "spa_Latn"
        assert t.target_language == "Spanish"

    def test_raises_when_transformers_unavailable(self):
        import translators.nllb200_translator as mod
        original = mod.TRANSFORMERS_AVAILABLE
        mod.TRANSFORMERS_AVAILABLE = False
        try:
            with pytest.raises(ImportError, match="transformers"):
                NLLB200Translator(model_path="/fake", lang_code="ro")
        finally:
            mod.TRANSFORMERS_AVAILABLE = original


# ── translate ─────────────────────────────────────────────────────────────────

class TestTranslate:
    def test_returns_decoded_string(self, translator):
        result = translator.translate("Hello world")
        assert result == "Salut lume"

    def test_tokenizer_src_lang_set_before_call(self, translator):
        translator.translate("Hi")
        assert _mock_tokenizer_instance.src_lang == "eng_Latn"

    def test_generate_called_with_forced_bos(self, translator):
        translator.translate("Hi")
        kwargs = _mock_model_instance.generate.call_args[1]
        assert kwargs["forced_bos_token_id"] == 256204  # ron_Latn

    def test_generate_called_with_max_new_tokens(self, translator):
        translator.translate("Hi", max_new_tokens=128)
        kwargs = _mock_model_instance.generate.call_args[1]
        assert kwargs["max_new_tokens"] == 128

    def test_generate_called_with_num_beams(self, translator):
        translator.translate("Hi", num_beams=2)
        kwargs = _mock_model_instance.generate.call_args[1]
        assert kwargs["num_beams"] == 2

    def test_context_and_speaker_accepted_without_crash(self, translator):
        result = translator.translate("Hi", context=["A: Hello"], speaker="Alice")
        assert isinstance(result, str)

    def test_output_stripped(self, translator):
        _mock_tokenizer_instance.batch_decode.return_value = ["  Salut  "]
        result = translator.translate("Hi")
        assert result == "Salut"

    def test_batch_decode_skip_special_tokens(self, translator):
        translator.translate("Hi")
        _mock_tokenizer_instance.batch_decode.assert_called_once()
        _, kwargs = _mock_tokenizer_instance.batch_decode.call_args
        assert kwargs.get("skip_special_tokens") is True

    def test_inputs_moved_to_device(self, translator):
        fake_tensor = MagicMock()
        _mock_tokenizer_instance.return_value = {"input_ids": fake_tensor, "attention_mask": fake_tensor}
        translator.translate("Hi")
        fake_tensor.to.assert_called_with("cpu")
