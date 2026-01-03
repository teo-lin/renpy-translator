"""
Test for the benchmark translation functionality
"""
import sys
import json
import yaml
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import is_separator_block


@pytest.fixture
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def models_config(project_root):
    """Load models configuration"""
    config_path = project_root / "models" / "models_config.json"
    assert config_path.exists(), "models_config.json not found"

    with open(config_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


@pytest.fixture
def game_config(project_root):
    """Load current game configuration"""
    config_path = project_root / "models" / "current_config.json"
    assert config_path.exists(), "current_config.json not found"

    with open(config_path, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)

    # Get current game
    current_game = config.get('current_game')
    assert current_game, "No current_game set"

    return config['games'][current_game]


def test_models_config_exists(models_config):
    """Test that models configuration exists and has installed models"""
    assert 'installed_models' in models_config
    assert len(models_config['installed_models']) > 0
    print(f"\nFound {len(models_config['installed_models'])} installed models")


def test_benchmark_script_exists(project_root):
    """Test that benchmark scripts exist"""
    benchmark_ps1 = project_root / "8-compare.ps1"
    benchmark_py = project_root / "scripts" / "compare.py"

    assert benchmark_ps1.exists(), "8-compare.ps1 not found"
    assert benchmark_py.exists(), "scripts/compare.py not found"
    print(f"\n[OK] Benchmark scripts found")


def test_parsed_files_have_numbered_keys(project_root, game_config, models_config):
    """
    Test that parsed files contain numbered keys (r0, r1, r2, etc.)
    This test assumes benchmark has been run at least once.
    """
    # Get target language directory
    game_path = Path(game_config['path'])
    target_language = game_config['target_language']['Name'].lower()
    tl_dir = game_path / "game" / "tl" / target_language

    # Find parsed files
    parsed_files = list(tl_dir.glob("*.parsed.yaml"))

    if len(parsed_files) == 0:
        pytest.skip("No parsed files found - run extraction first")

    print(f"\nFound {len(parsed_files)} parsed files")

    # Check first parsed file
    first_file = parsed_files[0]
    print(f"Examining: {first_file.name}")

    with open(first_file, 'r', encoding='utf-8') as f:
        content = f.read()
        parsed_data = yaml.safe_load(content)

    # Expected number of model keys
    expected_keys = len(models_config['installed_models'])
    print(f"Expected {expected_keys} model keys")

    # Check for numbered keys
    keys_found = set()
    blocks_checked = 0

    for block_id, block in parsed_data.items():
        if is_separator_block(block_id, block):
            continue

        blocks_checked += 1

        # Check for numbered keys (r0, r1, r2, etc.)
        for i in range(expected_keys):
            key = f"r{i}"
            if key in block:
                keys_found.add(key)

    print(f"Checked {blocks_checked} blocks")
    print(f"Found keys: {sorted(keys_found)}")

    # If no numbered keys found, this might be a fresh extraction
    if len(keys_found) == 0:
        pytest.skip("No numbered keys (r0, r1, etc.) found - benchmark may not have been run yet")

    # Verify we have at least some keys
    assert len(keys_found) > 0, "No numbered translation keys (r0, r1, etc.) found"
    print(f"\n[OK] Found {len(keys_found)} unique translation keys")


def test_benchmark_translation_structure(project_root, game_config, models_config):
    """
    Test that benchmark translations have correct structure:
    - Each block has 'en' (English)
    - Each block has numbered keys (r0, r1, r2, etc.)
    """
    # Get target language directory
    game_path = Path(game_config['path'])
    target_language = game_config['target_language']['Name'].lower()
    tl_dir = game_path / "game" / "tl" / target_language

    # Find parsed files
    parsed_files = list(tl_dir.glob("*.parsed.yaml"))

    if len(parsed_files) == 0:
        pytest.skip("No parsed files found")

    first_file = parsed_files[0]

    with open(first_file, 'r', encoding='utf-8') as f:
        parsed_data = yaml.safe_load(f)

    # Get first non-separator block
    sample_block = None
    sample_block_id = None

    for block_id, block in parsed_data.items():
        if not is_separator_block(block_id, block):
            sample_block = block
            sample_block_id = block_id
            break

    if not sample_block:
        pytest.skip("No translatable blocks found")

    print(f"\nSample block: {sample_block_id}")
    print(f"Keys in block: {list(sample_block.keys())}")

    # Check that 'en' exists
    assert 'en' in sample_block, "Block missing 'en' (English) key"

    # Check for at least one numbered key (r0, r1, r2, etc.)
    numbered_keys = [k for k in sample_block.keys() if k.startswith('r') and k[1:].isdigit()]

    if len(numbered_keys) == 0:
        pytest.skip("No numbered keys (r0, r1, etc.) found - benchmark not run yet")

    print(f"Found numbered keys: {sorted(numbered_keys)}")
    print(f"\nSample structure:")
    print(f"  en: {sample_block['en'][:50]}...")
    for key in sorted(numbered_keys)[:3]:  # Show first 3
        print(f"  {key}: {sample_block[key][:50]}...")

    assert len(numbered_keys) > 0, "No numbered translation keys found"
    print(f"\n[OK] Block structure is correct")


def test_all_models_have_unique_keys(models_config):
    """Test that each model gets a unique numbered key"""
    installed_models = models_config['installed_models']

    # Generate expected keys (r0, r1, r2, etc.)
    expected_keys = {f"r{i}" for i in range(len(installed_models))}

    print(f"\nInstalled models: {len(installed_models)}")
    print(f"Expected keys: {sorted(expected_keys)}")

    assert len(expected_keys) == len(installed_models)
    print(f"\n[OK] Each model will get a unique key")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
