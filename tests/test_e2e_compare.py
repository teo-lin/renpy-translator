"""
E2E Test: Model Comparison — fast variant

Translates a single hardcoded block through every installed model.
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


def test_compare_all_models():
    python_exe     = project_root / "venv" / "Scripts" / "python.exe"
    compare_script = project_root / "scripts" / "compare.py"

    with open(project_root / "models" / "models_config.yaml", "r", encoding="utf-8") as f:
        models_config = yaml.safe_load(f)
    with open(project_root / "models" / "current_config.yaml", "r", encoding="utf-8") as f:
        current_config = yaml.safe_load(f)
    installed_models = current_config.get("installed_models", [])
    assert installed_models, "No models installed — run 0-setup.ps1 first"

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

        durations = {}

        for model_key in installed_models:
            key = _KEY_OVERRIDES.get(model_key, model_key[:2].lower())
            model_name = models_config["available_models"][model_key]["name"]
            print(f"\n  [{installed_models.index(model_key)+1}/{len(installed_models)}] {model_name} -> key: {key}")
            wall_start = time.time()
            result = subprocess.run(
                [str(python_exe), str(compare_script),
                 "--model", model_key, "--key", key,
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
            durations[model_key] = float(match.group(1)) if match else wall_elapsed

        with open(parsed_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        block = content[TEST_BLOCK_ID]

        for model_key in installed_models:
            key = _KEY_OVERRIDES.get(model_key, model_key[:2].lower())
            assert key in block, f"Missing key '{key}' for model {model_key}"
            assert block[key].strip(), f"Empty translation for key '{key}' (model {model_key})"

        print("\n" + "=" * 60)
        print("  MODEL RANKING (fastest first)")
        print("=" * 60)
        ranked = sorted(durations.items(), key=lambda x: x[1])
        for rank, (model_key, dur) in enumerate(ranked, 1):
            key = _KEY_OVERRIDES.get(model_key, model_key[:2].lower())
            model_name = models_config["available_models"][model_key]["name"]
            translation = block.get(key, "")[:50].encode("ascii", "replace").decode("ascii")
            print(f"  {rank}. [{key}] {model_name:<22} {dur:6.2f}s  \"{translation}\"")
        print("=" * 60)
        print(f"\n  All {len(installed_models)} models produced translations.")

    finally:
        shutil.rmtree(TMP_GAME_DIR, ignore_errors=True)
