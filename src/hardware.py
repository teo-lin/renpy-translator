"""
Hardware detection and compute profile resolution.
Called once during 0-setup.ps1 to write models/compute_profile.yaml.
At translation time, only load_profile() is used — no re-detection.
"""

from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).parent.parent
SYSTEM_FILE = ROOT_DIR / "models" / "current_system.yaml"
PROFILES_FILE = ROOT_DIR / "models" / "compute_profiles.yaml"
MODELS_CONFIG_FILE = ROOT_DIR / "models" / "models_config.yaml"
PROFILE_OUT = ROOT_DIR / "models" / "compute_profile.yaml"

# (min_vram_gb, tier_name) — checked top-down, first match wins
_TIER_THRESHOLDS = [
    (10.0, "high"),
    (6.0,  "medium"),
    (0.1,  "low"),
]


def _detect_tier(system: dict) -> str:
    gpu = system.get("gpu_primary", {})
    vram = float(gpu.get("vram_gb", 0) or 0)
    for min_vram, tier_name in _TIER_THRESHOLDS:
        if vram >= min_vram:
            return tier_name
    return "cpu_only"


def _resolve_model_path(model_key: str, quant: str, models_config: dict) -> str | None:
    """Return the relative file path for a model+quant combo, or None if unresolvable."""
    model = models_config.get("available_models", {}).get(model_key)
    if not model:
        return None

    destination = model.get("destination", "")

    # Multi-quant model: files dict keyed by quant name
    files = model.get("files", {})
    if files:
        filename = files.get(quant)
        if not filename:
            return None
        return str(Path(destination) / filename)

    # Single-file model (legacy aya23 style): destination is the full path
    if destination.endswith(".gguf"):
        return destination

    # Single-file model with separate file field
    filename = model.get("file")
    if filename:
        return str(Path(destination).parent / filename) if "/" in destination else str(Path(destination) / filename)

    return None


def detect_and_write_profile() -> dict:
    """
    Read current_system.yaml, derive tier, resolve per-model params,
    write models/compute_profile.yaml. Returns the written profile dict.
    """
    with open(SYSTEM_FILE, "r", encoding="utf-8") as f:
        system = yaml.safe_load(f)

    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_cfg = yaml.safe_load(f)

    with open(MODELS_CONFIG_FILE, "r", encoding="utf-8") as f:
        models_config = yaml.safe_load(f)

    tier = _detect_tier(system)
    tier_params = profiles_cfg.get("profiles", {}).get(tier, {})

    resolved_models = {}
    for model_key, params in tier_params.items():
        if not isinstance(params, dict):
            continue
        quant = params.get("quant", "Q4_K_M")
        file_path = _resolve_model_path(model_key, quant, models_config)
        if file_path:
            resolved_models[model_key] = {
                "file": file_path,
                "n_gpu_layers": params.get("n_gpu_layers", -1),
                "n_ctx": params.get("n_ctx", 8192),
                "n_batch": params.get("n_batch", 256),
                "quant": quant,
            }

    # Add HF models (no hardware params — just destination for display/reference)
    for model_key, model_cfg in models_config.get("available_models", {}).items():
        if model_key in resolved_models:
            continue
        if model_cfg.get("huggingface_download"):
            resolved_models[model_key] = {
                "destination": model_cfg.get("destination", ""),
                "type": "hf",
            }

    gpu = system.get("gpu_primary", {})
    profile = {
        "tier": tier,
        "gpu": gpu.get("model", "unknown"),
        "vram_gb": gpu.get("vram_gb", 0),
        "models": resolved_models,
    }

    with open(PROFILE_OUT, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False)

    return profile


def load_profile() -> dict:
    """Load the resolved compute profile written by detect_and_write_profile()."""
    if not PROFILE_OUT.exists():
        raise FileNotFoundError(
            f"Compute profile not found at {PROFILE_OUT}. "
            "Please run 0-setup.ps1 first."
        )
    with open(PROFILE_OUT, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    profile = detect_and_write_profile()
    print(f"Tier  : {profile['tier']}")
    print(f"GPU   : {profile['gpu']} ({profile['vram_gb']}GB)")
    print("Models available in this tier:")
    for name, params in profile["models"].items():
        if params.get("type") == "hf":
            print(f"  {name:20s} HF safetensors  dest={params['destination']}")
        else:
            print(f"  {name:20s} n_ctx={params['n_ctx']:6d}  quant={params['quant']}  file={params['file']}")
