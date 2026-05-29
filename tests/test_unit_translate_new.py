"""
Unit tests for scripts/translate_new.py.
llama_cpp and renpy_utils are mocked — no real model or Ren'Py install needed.
"""

import sys
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── module-level mocks (must precede any translate_new import) ────────────────
sys.modules.setdefault("llama_cpp", MagicMock())
sys.modules.setdefault("renpy_utils", MagicMock())

_mock_show_progress = MagicMock()
sys.modules["renpy_utils"].show_progress = _mock_show_progress

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from translate_new import ModularBatchTranslator, load_config, load_resources


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_translator():
    m = MagicMock()
    m.translate.side_effect = lambda text, **kw: f"[TR] {text}"
    return m


def _write_yaml(path: Path, data):
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


# ── load_config ───────────────────────────────────────────────────────────────

class TestLoadConfig:
    def _make_config(self, tmp_path, games=None, current_game=None):
        config = {
            "current_game": current_game or "TestGame",
            "games": games or {
                "TestGame": {
                    "name": "TestGame",
                    "path": str(tmp_path / "game"),
                    "target_language": {"code": "ro", "name": "Romanian"},
                    "model": "euroLLM9b",
                    "context_before": 3,
                    "context_after": 1,
                }
            },
        }
        config_dir = tmp_path / "models"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "current_config.yaml"
        _write_yaml(config_file, config)
        return tmp_path

    def test_loads_current_game(self, tmp_path):
        project_root = self._make_config(tmp_path)
        cfg = load_config(project_root)
        assert cfg["name"] == "TestGame"

    def test_loads_named_game(self, tmp_path):
        project_root = self._make_config(tmp_path, games={
            "Alpha": {"name": "Alpha", "path": "/alpha", "target_language": {"code": "ro", "name": "Romanian"}, "model": "aya23"},
            "Beta":  {"name": "Beta",  "path": "/beta",  "target_language": {"code": "fr", "name": "French"},   "model": "euroLLM9b"},
        }, current_game="Alpha")
        cfg = load_config(project_root, game_name="Beta")
        assert cfg["name"] == "Beta"

    def test_missing_config_file_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            load_config(tmp_path)

    def test_unknown_game_name_exits(self, tmp_path):
        project_root = self._make_config(tmp_path)
        with pytest.raises(SystemExit):
            load_config(project_root, game_name="NoSuchGame")

    def test_no_current_game_set_exits(self, tmp_path):
        config_dir = tmp_path / "models"
        config_dir.mkdir()
        _write_yaml(config_dir / "current_config.yaml", {"games": {"TestGame": {}}})
        with pytest.raises(SystemExit):
            load_config(tmp_path)


# ── load_resources ────────────────────────────────────────────────────────────

class TestLoadResources:
    def test_finds_uncensored_glossary_first(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        _write_yaml(data_dir / "ro_uncensored_glossary.yaml", {"hello": "salut"})
        _write_yaml(data_dir / "ro_glossary.yaml", {"bye": "pa"})

        glossary, _, _ = load_resources(tmp_path, {}, "ro")

        assert glossary == {"hello": "salut"}

    def test_falls_back_to_regular_glossary(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        _write_yaml(data_dir / "ro_glossary.yaml", {"bye": "pa"})

        glossary, _, _ = load_resources(tmp_path, {}, "ro")

        assert glossary == {"bye": "pa"}

    def test_no_glossary_returns_none(self, tmp_path):
        (tmp_path / "data").mkdir()
        glossary, _, _ = load_resources(tmp_path, {}, "ro")
        assert glossary is None

    def test_finds_uncensored_corrections_first(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        _write_yaml(data_dir / "ro_uncensored_corrections.yaml", {"a": "b"})
        _write_yaml(data_dir / "ro_corrections.yaml", {"c": "d"})

        _, corrections, _ = load_resources(tmp_path, {}, "ro")

        assert corrections == {"a": "b"}

    def test_falls_back_to_regular_corrections(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        _write_yaml(data_dir / "ro_corrections.yaml", {"c": "d"})

        _, corrections, _ = load_resources(tmp_path, {}, "ro")

        assert corrections == {"c": "d"}

    def test_no_corrections_returns_none(self, tmp_path):
        (tmp_path / "data").mkdir()
        _, corrections, _ = load_resources(tmp_path, {}, "ro")
        assert corrections is None

    def test_finds_uncensored_prompt_first(self, tmp_path):
        prompts_dir = tmp_path / "data" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "translate_uncensored.txt").write_text("uncensored", encoding="utf-8")
        (prompts_dir / "translate.txt").write_text("regular", encoding="utf-8")
        (tmp_path / "data").mkdir(exist_ok=True)

        _, _, prompt = load_resources(tmp_path, {}, "ro")

        assert prompt == "uncensored"

    def test_falls_back_to_regular_prompt(self, tmp_path):
        prompts_dir = tmp_path / "data" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "translate.txt").write_text("regular", encoding="utf-8")
        (tmp_path / "data").mkdir(exist_ok=True)

        _, _, prompt = load_resources(tmp_path, {}, "ro")

        assert prompt == "regular"

    def test_no_prompt_returns_none(self, tmp_path):
        (tmp_path / "data").mkdir()
        _, _, prompt = load_resources(tmp_path, {}, "ro")
        assert prompt is None


# ── ModularBatchTranslator ────────────────────────────────────────────────────

_PARSED_BLOCKS = {
    "1-Amelia":        {"en": "Hello!",     "ro": "Salut!"},
    "2-MainCharacter": {"en": "Hi Amelia!", "ro": ""},       # untranslated
    "separator-1":     {"type": "separator"},
    "3-Choice":        {"en": "Help her",   "ro": ""},       # untranslated choice
}

_BLOCK_ORDER = ["1-Amelia", "2-MainCharacter", "separator-1", "3-Choice"]


def _make_batch_translator(tmp_path):
    translator = _make_translator()
    return ModularBatchTranslator(
        translator=translator,
        characters={"am": {"name": "Amelia"}},
        target_lang_code="ro",
        context_before=3,
        context_after=1,
    ), translator


def _write_parsed_and_tags(tmp_path, parsed_blocks=None, block_order=None):
    parsed = parsed_blocks or _PARSED_BLOCKS
    order = block_order or _BLOCK_ORDER

    parsed_f = tmp_path / "test.parsed.yaml"
    tags_f = tmp_path / "test.tags.yaml"

    parsed_f.write_text(yaml.dump(parsed, allow_unicode=True), encoding="utf-8")

    tags_data = {
        "metadata": {"extracted_at": "2026-01-01"},
        "structure": {"block_order": order},
    }
    tags_f.write_text(yaml.dump(tags_data, allow_unicode=True), encoding="utf-8")

    return parsed_f, tags_f


class TestIdentifyUntranslated:
    def test_identifies_empty_translations(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        result = bt._identify_untranslated(_PARSED_BLOCKS, "ro")
        assert "2-MainCharacter" in result
        assert "3-Choice" in result

    def test_skips_already_translated_blocks(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        result = bt._identify_untranslated(_PARSED_BLOCKS, "ro")
        assert "1-Amelia" not in result

    def test_skips_separator_blocks(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        result = bt._identify_untranslated(_PARSED_BLOCKS, "ro")
        assert "separator-1" not in result

    def test_empty_string_is_untranslated(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        blocks = {"1-Narrator": {"en": "Hi", "ro": "   "}}
        result = bt._identify_untranslated(blocks, "ro")
        assert "1-Narrator" in result


class TestExtractContexts:
    def test_dialogue_block_has_context(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        contexts = bt._extract_contexts(
            ["2-MainCharacter"], _PARSED_BLOCKS, _BLOCK_ORDER
        )
        assert len(contexts) == 1
        assert contexts[0]["block_id"] == "2-MainCharacter"
        assert contexts[0]["is_choice"] is False

    def test_choice_block_has_no_context(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        contexts = bt._extract_contexts(
            ["3-Choice"], _PARSED_BLOCKS, _BLOCK_ORDER
        )
        assert len(contexts) == 1
        assert contexts[0]["is_choice"] is True
        assert contexts[0]["context"] == []

    def test_block_not_in_order_is_skipped(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        contexts = bt._extract_contexts(
            ["99-Ghost"], _PARSED_BLOCKS, _BLOCK_ORDER
        )
        assert contexts == []

    def test_character_name_extracted(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        contexts = bt._extract_contexts(
            ["2-MainCharacter"], _PARSED_BLOCKS, _BLOCK_ORDER
        )
        assert contexts[0]["character_name"] == "MainCharacter"


class TestTranslateFile:
    def test_all_translated_returns_zero_translated(self, tmp_path):
        blocks = {
            "1-Amelia": {"en": "Hello!", "ro": "Salut!"},
        }
        order = ["1-Amelia"]
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path, blocks, order)
        bt, _ = _make_batch_translator(tmp_path)

        stats = bt.translate_file(parsed_f, tags_f, tmp_path / "out.yaml")

        assert stats["translated"] == 0
        assert stats["skipped"] == 1

    def test_untranslated_blocks_are_translated(self, tmp_path):
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path)
        bt, mock_tr = _make_batch_translator(tmp_path)

        stats = bt.translate_file(parsed_f, tags_f, tmp_path / "out.yaml")

        assert stats["translated"] == 2  # 2-MainCharacter and 3-Choice
        assert mock_tr.translate.call_count == 2

    def test_output_yaml_written(self, tmp_path):
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path)
        out_f = tmp_path / "out.yaml"
        bt, _ = _make_batch_translator(tmp_path)

        bt.translate_file(parsed_f, tags_f, out_f)

        assert out_f.exists()

    def test_output_defaults_to_input_path(self, tmp_path):
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path)
        bt, _ = _make_batch_translator(tmp_path)

        bt.translate_file(parsed_f, tags_f)

        assert parsed_f.exists()

    def test_translation_error_counts_as_failed(self, tmp_path):
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path)
        bt, mock_tr = _make_batch_translator(tmp_path)
        mock_tr.translate.side_effect = RuntimeError("model error")

        stats = bt.translate_file(parsed_f, tags_f, tmp_path / "out.yaml")

        assert stats["failed"] == 2

    def test_narrator_speaker_passed_as_none(self, tmp_path):
        blocks = {"1-Narrator": {"en": "Once upon a time.", "ro": ""}}
        order = ["1-Narrator"]
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path, blocks, order)
        bt, mock_tr = _make_batch_translator(tmp_path)

        bt.translate_file(parsed_f, tags_f, tmp_path / "out.yaml")

        call_kwargs = mock_tr.translate.call_args[1]
        assert call_kwargs.get("speaker") is None

    def test_named_character_speaker_passed(self, tmp_path):
        blocks = {"1-Amelia": {"en": "Hello!", "ro": ""}}
        order = ["1-Amelia"]
        parsed_f, tags_f = _write_parsed_and_tags(tmp_path, blocks, order)
        bt, mock_tr = _make_batch_translator(tmp_path)

        bt.translate_file(parsed_f, tags_f, tmp_path / "out.yaml")

        call_kwargs = mock_tr.translate.call_args[1]
        assert call_kwargs.get("speaker") == "Amelia"


class TestSaveYaml:
    def test_creates_output_file(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        blocks = {"1-Narrator": {"en": "Hi", "ro": "Buna"}}
        out = tmp_path / "out.yaml"
        metadata = {"extracted_at": "2026-01-01"}

        bt._save_yaml(blocks, out, metadata)

        assert out.exists()
        assert out.stat().st_size > 0

    def test_yaml_contains_translated_text(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        blocks = {"1-Narrator": {"en": "Hi", "ro": "Buna"}}
        out = tmp_path / "out.yaml"
        bt._save_yaml(blocks, out, {"extracted_at": "2026-01-01"})

        content = out.read_text(encoding="utf-8")
        assert "Buna" in content

    def test_creates_parent_directory(self, tmp_path):
        bt, _ = _make_batch_translator(tmp_path)
        blocks = {"1-Narrator": {"en": "Hi", "ro": "Buna"}}
        out = tmp_path / "subdir" / "out.yaml"

        bt._save_yaml(blocks, out, {"extracted_at": "2026-01-01"})

        assert out.exists()


# ── main() error paths ────────────────────────────────────────────────────────

_GOOD_PROFILE = {
    "tier": "medium",
    "gpu": "RTX 5070",
    "vram_gb": 8,
    "models": {
        "euroLLM9b": {
            "file": "models/euroLLM9b/EuroLLM.Q5_K_M.gguf",
            "n_ctx": 16384,
            "n_batch": 512,
            "n_gpu_layers": -1,
            "quant": "Q5_K_M",
        }
    },
}

_GOOD_GAME_CONFIG = {
    "name": "TestGame",
    "path": "/fake/game",
    "target_language": {"code": "ro", "name": "Romanian"},
    "model": "euroLLM9b",
    "context_before": 3,
    "context_after": 1,
}


class TestMain:
    def test_exits_when_no_compute_profile(self):
        import translate_new
        with (
            patch("translate_new.load_profile", side_effect=FileNotFoundError("no profile")),
            patch.object(sys, "argv", ["translate_new.py"]),
            pytest.raises(SystemExit),
        ):
            translate_new.main()

    def test_exits_when_model_not_in_profile(self):
        profile_without_model = {**_GOOD_PROFILE, "models": {}}  # euroLLM9b absent
        import translate_new
        with (
            patch("translate_new.load_profile", return_value=profile_without_model),
            patch("translate_new.load_config", return_value=_GOOD_GAME_CONFIG),
            patch.object(sys, "argv", ["translate_new.py"]),
            pytest.raises(SystemExit),
        ):
            translate_new.main()

    def test_exits_when_model_file_missing(self, tmp_path):
        # Profile points at a file that doesn't exist on disk
        import translate_new
        with (
            patch("translate_new.load_profile", return_value=_GOOD_PROFILE),
            patch("translate_new.load_config", return_value=_GOOD_GAME_CONFIG),
            patch("translate_new.load_resources", return_value=(None, None, None)),
            patch.object(sys, "argv", ["translate_new.py"]),
            pytest.raises(SystemExit),
        ):
            translate_new.main()
