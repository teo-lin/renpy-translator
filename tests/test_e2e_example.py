"""
E2E Test: Single-block translation with the currently selected model

Reads the active model from current_config.yaml (games[current_game].model),
translates one hardcoded block, and verifies a non-empty translation is produced.
Uses games/Example Temp as a scratch directory; removes it after the test.
Does NOT touch games/Example.
"""

import os
import re
import shutil
import subprocess
import time
import yaml
from pathlib import Path

project_root = Path(__file__).parent.parent
TMP_GAME_DIR = project_root / "games" / "Example Temp"
TMP_TL_DIR   = TMP_GAME_DIR / "game" / "tl" / "romanian"

TEST_BLOCK_ID = "1-U"
TEST_BLOCK_EN = "Would you mind helping me with my princess?"

PARSED_YAML_CONTENT = {
    TEST_BLOCK_ID: {"en": TEST_BLOCK_EN}
}

TAGS_YAML_CONTENT = {
    "metadata": {
        "source_file": "test",
        "target_language": "romanian",
        "source_language": "english",
        "extracted_at": "2026-01-01T00:00:00",
        "file_structure_type": "dialogue_and_strings",
        "has_separator_lines": False,
        "total_blocks": 1,
        "untranslated_blocks": 1,
    },
    "structure": {
        "block_order": [TEST_BLOCK_ID],
        "string_section_start": None,
        "string_section_header": None,
    },
    "blocks": {},
    "character_map": {},
}

_KEY_OVERRIDES = {
    "ayaExpanse8b":  "ae",
    "euroLLM9b":     "eu",
    "euroLLM9b2512": "e3",
    "euroLLM22b":    "e2",
    "seamlessm96":   "se",
    "nllb1300":      "n3",
}


def test_translate_current_model():
    python_exe     = project_root / "venv" / "Scripts" / "python.exe"
    compare_script = project_root / "scripts" / "compare.py"

    with open(project_root / "models" / "models_config.yaml", "r", encoding="utf-8") as f:
        models_config = yaml.safe_load(f)
    with open(project_root / "models" / "current_config.yaml", "r", encoding="utf-8") as f:
        current_config = yaml.safe_load(f)

    current_game = current_config.get("current_game")
    assert current_game, "No current_game in current_config.yaml — run 1-config.ps1 first"
    model_key = current_config["games"][current_game]["model"]
    model_name = models_config["available_models"][model_key]["name"]
    save_key = _KEY_OVERRIDES.get(model_key, model_key[:2].lower())

    print(f"\n  Current game:  {current_game}")
    print(f"  Current model: {model_name} ({model_key}) -> key: {save_key}")

    if TMP_GAME_DIR.exists():
        shutil.rmtree(TMP_GAME_DIR)
    TMP_TL_DIR.mkdir(parents=True)

    parsed_file = TMP_TL_DIR / "test.parsed.yaml"
    tags_file   = TMP_TL_DIR / "test.tags.yaml"

    try:
        with open(parsed_file, "w", encoding="utf-8") as f:
            yaml.dump(PARSED_YAML_CONTENT, f, allow_unicode=True, default_flow_style=False)
        with open(tags_file, "w", encoding="utf-8") as f:
            yaml.dump(TAGS_YAML_CONTENT, f, allow_unicode=True, default_flow_style=False)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        torch_lib = project_root / "venv" / "Lib" / "site-packages" / "torch" / "lib"
        if torch_lib.exists():
            env["PATH"] = f"{torch_lib};{env.get('PATH', '')}"

        wall_start = time.time()
        result = subprocess.run(
            [str(python_exe), str(compare_script),
             "--model", model_key, "--key", save_key,
             "--tl-dir", str(TMP_TL_DIR)],
            env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300
        )
        wall_elapsed = time.time() - wall_start

        if result.stdout:
            print(result.stdout)
        assert result.returncode == 0, (
            f"Model {model_key} failed (exit {result.returncode}):\n{result.stderr}"
        )

        match = re.search(r"BENCHMARK_DURATION:(\d+\.?\d*)", result.stdout)
        duration = float(match.group(1)) if match else wall_elapsed

        with open(parsed_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        block = content[TEST_BLOCK_ID]
        assert save_key in block, f"Missing key '{save_key}' in output"
        translation = block[save_key]
        assert translation.strip(), f"Empty translation for key '{save_key}'"

        print(f"\n  [{save_key}] {model_name}: \"{translation.encode('ascii', 'replace').decode('ascii')}\"  ({duration:.2f}s)")

    finally:
        shutil.rmtree(TMP_GAME_DIR, ignore_errors=True)
