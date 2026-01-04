import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config_selector import select_item, select_languages_single_row

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def load_models_config() -> Dict[str, Any]:
    """Load models_config.yaml."""
    models_config_path = get_project_root() / "models" / "models_config.yaml"
    if not models_config_path.exists():
        print(f"ERROR: models_config.yaml not found at {models_config_path}")
        sys.exit(1)
    with open(models_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_available_correction_modes() -> List[Dict[str, Any]]:
    """Define available correction modes."""
    return [
        {
            "Name": "Both (Patterns + LLM)",
            "Description": "Apply pattern corrections, then LLM corrections (recommended)",
            "Flag": None,
            "Details": "Speed: Slow (~2-3s/sentence) | Quality: Best | Uses: Aya-23-8B + YAML rules"
        },
        {
            "Name": "Patterns Only",
            "Description": "Fast pattern-based corrections using YAML rules",
            "Flag": "--patterns-only",
            "Details": "Speed: Very fast (<1s/file) | Quality: Good | Uses: YAML correction rules"
        },
        {
            "Name": "LLM Only",
            "Description": "AI-powered corrections using Aya-23-8B model",
            "Flag": "--llm-only",
            "Details": "Speed: Slow (~2-3s/sentence) | Quality: Best | Uses: Aya-23-8B only"
        }
    ]

def get_available_languages(models_config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Load available languages from models_config."""
    languages_section = models_config.get('installed_languages', [])
    # Ensure 'code' is a string, as YAML can parse 'no' as False
    for lang in languages_section:
        if isinstance(lang.get('code'), bool):
            lang['code'] = 'no'
    return languages_section

def scan_games_folder(selected_language: Dict[str, str]) -> List[Dict[str, Any]]:
    """Scan games folder for translations in the selected language."""
    games_folder = get_project_root() / "games"
    found_games = []

    if not games_folder.exists():
        return []

    for game_folder in games_folder.iterdir():
        if game_folder.is_dir():
            # Use lowercased language name for folder, as per Ren'Py convention
            lang_dir_name = selected_language["Name"].lower()
            tl_path = game_folder / "game" / "tl" / lang_dir_name

            # Test if the path exists before globbing
            if tl_path.is_dir():
                rpy_files = list(tl_path.glob("*.rpy"))
                if rpy_files:
                    found_games.append({
                        "Name": game_folder.name,
                        "Path": str(tl_path) # Store as string to avoid PowerShell path issues
                    })
    return found_games

def display_banner():
    """Display the script banner."""
    print("\n" + "=" * 70)
    print("       Ren'Py Grammar Correction - Interactive Setup            ")
    print("=" * 70)

def display_summary(selected_mode: Dict[str, Any], selected_language: Dict[str, str], selected_game: Dict[str, Any]):
    """Display the selected configuration summary."""
    print("\n" + "=" * 70)
    print("       Correction Summary                                        ")
    print("=" * 70)
    print(f"  Mode:     {selected_mode['Name']}")
    print(f"  Language: {selected_language['Name']} ({selected_language['Code']})")
    print(f"  Game:     {selected_game['Name']}")
    print(f"  Path:     {selected_game['Path']}")
    print("=" * 70)

def get_correction_arguments(args_from_ps: Dict[str, Any]) -> None:
    """
    Main function to get arguments for correct.py, handling interactive selection or parameter-based auto-selection.
    Prints the arguments, one per line, to stdout for PowerShell to parse.
    """
    print("DEBUG: args_from_ps:", args_from_ps)
    display_banner()

    models_config = load_models_config()

    # Step 1: Select Mode
    modes = get_available_correction_modes()
    selected_mode = None
    if args_from_ps.get('ModeName'):
        found_mode = next((m for m in modes if m['Name'] == args_from_ps['ModeName']), None)
        if found_mode:
            selected_mode = found_mode
            print(f"\nAuto-selecting mode by name '{args_from_ps['ModeName']}': {selected_mode['Name']}")
        else:
            print(f"ERROR: Invalid mode name: {args_from_ps['ModeName']}. Available modes: {[m['Name'] for m in modes]}")
            sys.exit(1)
    elif args_from_ps.get('Mode'): # Mode number (1-based index)
        mode_idx = args_from_ps['Mode'] - 1
        if 0 <= mode_idx < len(modes):
            selected_mode = modes[mode_idx]
            print(f"\nAuto-selecting mode {args_from_ps['Mode']}: {selected_mode['Name']}")
        else:
            print(f"ERROR: Invalid mode number: {args_from_ps['Mode']}. Available modes: 1-{len(modes)}")
            sys.exit(1)
    else:
        selected_mode = select_item(
            title="Step 1: Select Correction Mode",
            items=modes,
            item_formatter_func=lambda m, num: (
                f"  [{num}] {m['Name']} - {m['Description']}\n"
                f"      {m['Details']}"
            ),
            item_type_name="mode"
        )
    
    # Step 2: Select Language
    languages = get_available_languages(models_config)
    if not languages:
        print("ERROR: No languages found in models_config.yaml installed_languages section. Please run 0-setup.ps1.")
        sys.exit(1)
    
    selected_language = None
    if args_from_ps.get('LanguageName'):
        found_lang = next((l for l in languages if l['Code'] == args_from_ps['LanguageName']), None)
        if found_lang:
            selected_language = found_lang
            print(f"\nAuto-selecting language by name '{args_from_ps['LanguageName']}': {selected_language['Name']} ({selected_language['Code']})")
        else:
            print(f"ERROR: Invalid language name: {args_from_ps['LanguageName']}. Available languages: {[l['Name'] for l in languages]}")
            sys.exit(1)
    elif args_from_ps.get('Language'): # Language number (1-based index)
        lang_idx = args_from_ps['Language'] - 1
        if 0 <= lang_idx < len(languages):
            selected_language = languages[lang_idx]
            print(f"\nAuto-selecting language {args_from_ps['Language']}: {selected_language['Name']} ({selected_language['Code']})")
        else:
            print(f"ERROR: Invalid language number: {args_from_ps['Language']}. Available languages: 1-{len(languages)}")
            sys.exit(1)
    else:
        selected_language = select_item(
            title="Step 2: Select Target Language",
            items=languages,
            item_formatter_func=lambda l, num: f"  [{num}] {l['Name']} ({l['Code']})",
            item_type_name="language"
        )

    # Step 3: Scan games and select game
    print(f"\nScanning games folder for {selected_language['Name']} translations...")
    games = scan_games_folder(selected_language)
    if not games:
        print(f"\nERROR: No games found with {selected_language['Name']} translations!")
        print(f"Please generate translation files first using Ren'Py:")
        print(f"  renpy.exe \"path\\to\\game\" generate-translations {selected_language['Name'].lower()}")
        sys.exit(1)
    
    selected_game = None
    if args_from_ps.get('GameName'):
        found_game = next((g for g in games if g['Name'] == args_from_ps['GameName']), None)
        if found_game:
            selected_game = found_game
            print(f"\nAuto-selecting game by name '{args_from_ps['GameName']}': {selected_game['Name']}")
        else:
            print(f"ERROR: Invalid game name: {args_from_ps['GameName']}. Available games: {[g['Name'] for g in games]}")
            sys.exit(1)
    elif args_from_ps.get('Game'): # Game number (1-based index)
        game_idx = args_from_ps['Game'] - 1
        if 0 <= game_idx < len(games):
            selected_game = games[game_idx]
            print(f"\nAuto-selecting game {args_from_ps['Game']}: {selected_game['Name']}")
        else:
            print(f"ERROR: Invalid game number: {args_from_ps['Game']}. Available games: 1-{len(games)}")
            sys.exit(1)
    else:
        selected_game = select_item(
            title="Step 3: Select Game to Correct",
            items=games,
            item_formatter_func=lambda g, num: f"  [{num}] {g['Name']} (Path: {g['Path']})",
            item_type_name="game"
        )
    
    display_summary(selected_mode, selected_language, selected_game)

    # Build arguments for scripts/correct.py
    script_args = [selected_game['Path'], "--language", selected_language['Code']]
    if selected_mode['Flag']:
        script_args.append(selected_mode['Flag'])
    
    # Any additional arguments provided in the initial PowerShell call are also passed through
    if args_from_ps.get('Arguments'):
        script_args.extend(args_from_ps['Arguments'])

    for arg in script_args:
        print(arg)

if __name__ == "__main__":
    # This block is for testing correct_utils.py directly, not for normal execution via 4-correct.ps1
    # For actual execution, 4-correct.ps1 will call get_correction_arguments()
    
    # Simple parsing of command-line args for direct testing
    parsed_args_from_ps = {}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--'):
            key = arg[2:].replace('-', '_') # e.g., --mode-name -> mode_name
            if i + 1 < len(sys.argv) and not sys.argv[i+1].startswith('--'):
                value = sys.argv[i+1]
                # Convert to int if possible
                try:
                    parsed_args_from_ps[key] = int(value)
                except ValueError:
                    parsed_args_from_ps[key] = value
                i += 2
            else:
                # Handle boolean flags without explicit values, e.g., --yes
                # For this script, we don't expect such flags from PowerShell input,
                # but it's good practice. For now, just skip.
                i += 1
        else: # Positional arguments
            if 'Arguments' not in parsed_args_from_ps:
                parsed_args_from_ps['Arguments'] = []
            parsed_args_from_ps['Arguments'].append(arg)
            i += 1
            
    # Call the main function with parsed arguments
    try:
        get_correction_arguments(parsed_args_from_ps)
    except SystemExit:
        pass # Handle sys.exit from select_item/sys.exit(0)
