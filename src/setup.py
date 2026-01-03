import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Add scripts directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))

try:
    import yaml
    from config_selector import select_multiple_items, select_languages_single_row
except ImportError as e:
    print(f"Error: A required library is missing: {e.name}")
    print(f"Please install it by running: pip install {e.name}")
    sys.exit(1)

# Constants
ROOT_DIR = Path(__file__).parent.parent
MODELS_CONFIG_PATH = ROOT_DIR / "models" / "models_config.yaml"
TOOLS_CONFIG_PATH = ROOT_DIR / "renpy" / "tools_config.yaml"
CURRENT_CONFIG_PATH = ROOT_DIR / "models" / "current_config.yaml"
VENV_PATH = ROOT_DIR / "venv"
REQUIREMENTS_PATH = ROOT_DIR / "requirements.txt"


class ProjectSetup:
    """
    Main class to handle the setup process for the Ren'Py Translation System.
    """

    def __init__(self, args):
        self.args = args
        self.models_config = {}
        self.tools_config = {}
        self.selected_languages = []
        self.selected_models = []
        self.all_languages = []
        self.available_models = []
        self.venv_python = self._get_venv_python_path()

    def run(self):
        """Main method to run the setup process in sequence."""
        self._set_hf_home()
        self._print_header()

        self._load_configs()
        self._select_languages()

        if not self.args.skip_model:
            self._select_models()
            self._save_config()
        else:
            print("[1/6] Skipping model selection (--skip-model)")
            self._load_installed_models_from_current_config()

        if not self.args.skip_python:
            self._setup_python_env()
        else:
            print("[2/6] Skipping Python setup (--skip-python)")

        if not self.args.skip_model and self.selected_models:
            self._download_models()
        else:
            print("[3/6] Skipping model download (--skip-model or no models selected)")

        if not self.args.skip_tools:
            self._download_tools()
        else:
            print("[4/6] Skipping tools download (--skip-tools)")

        self._verify_installation()
        self._print_footer()

    def _set_hf_home(self):
        hf_home = ROOT_DIR / "models"
        os.environ["HF_HOME"] = str(hf_home)
        print(f"Hugging Face cache set to: {hf_home}")

    def _print_header(self):
        print("=" * 70)
        print("  Ren'Py Translation System - Python Setup Script")
        print("=" * 70)
        print()

    def _load_configs(self):
        try:
            with open(MODELS_CONFIG_PATH, "r", encoding="utf-8") as f:
                self.models_config = yaml.safe_load(f)
            with open(TOOLS_CONFIG_PATH, "r", encoding="utf-8") as f:
                self.tools_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            print(f"Error: Configuration file not found at {e.filename}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1)

    def _select_languages(self):
        languages_config = self.models_config.get("languages", [])
        
        # Fix for YAML parsing 'no' as False
        for lang_item in languages_config:
            if lang_item.get('code') is False:
                lang_item['code'] = 'no'

        # Sort languages by code, ensuring 'ro' is first if present
        sorted_languages = sorted(languages_config, key=lambda x: x['code'])
        ro_language = None
        for i, lang in enumerate(sorted_languages):
            if lang['code'] == 'ro':
                ro_language = sorted_languages.pop(i)
                break
        if ro_language:
            sorted_languages.insert(0, ro_language)
        
        self.all_languages = sorted_languages

        if self.args.languages:
            if self.args.languages.lower() == 'all':
                self.selected_languages = self.all_languages
                print("  Auto-selected: All languages")
            else:
                selected_codes = {code.strip().lower() for code in self.args.languages.split(',')}
                self.selected_languages = [lang for lang in self.all_languages if lang['code'] in selected_codes]
                print(f"  Auto-selected: {[lang['name'] for lang in self.selected_languages]}")
            return

        # Interactive selection
        def lang_formatter_func(lang, num):
            return f"[{num:2d}] {lang['name']}"

        self.selected_languages = select_languages_single_row(
            "Select Languages", self.all_languages, lang_formatter_func, "language", step_info="[0/6]"
        )

    def _select_models(self):
        print("\n[1/6] Select Translation Models to Install")
        all_models_dict = self.models_config.get("available_models", {})
        
        selected_lang_codes = {lang['code'] for lang in self.selected_languages}
        self.available_models = []
        for key, value in all_models_dict.items():
            model_langs = set(value.get("languages", []))
            if model_langs.intersection(selected_lang_codes):
                 value['key'] = key
                 self.available_models.append(value)
        
        if not self.available_models:
            print("\nError: No available models support the selected languages.")
            sys.exit(1)

        if self.args.models:
            if self.args.models.lower() == 'all':
                self.selected_models = self.available_models
                print("  Auto-selected: All available models")
            else:
                try:
                    model_indices = [int(i.strip()) - 1 for i in self.args.models.split(',')]
                    self.selected_models = [self.available_models[i] for i in model_indices if 0 <= i < len(self.available_models)]
                    print(f"  Auto-selected: {[m['name'] for m in self.selected_models]}")
                except ValueError:
                    print("Invalid --models argument. Please provide comma-separated numbers.")
                    sys.exit(1)
            return

        # Interactive selection
        def model_formatter_func(model, num):
            supported_count = len(set(model['languages']).intersection(selected_lang_codes))
            return (
                f"  [{num:2d}] {model['name']} ({model['size']})\n"
                f"      - Supports {supported_count}/{len(self.selected_languages)} of your languages\n"
                f"      - {model.get('description', 'No description available.')}"
            )

        self.selected_models = select_multiple_items(
            "Select Translation Models", self.available_models, model_formatter_func, "model", step_info="[1/6]"
        )

    def _save_config(self):
        """Saves the selected languages and models to current_config.yaml."""
        if not self.args.skip_model:
            current_config = {
                "installed_languages": self.selected_languages,
                "installed_models": [model['key'] for model in self.selected_models]
            }
            
            with open(CURRENT_CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(current_config, f, default_flow_style=False, sort_keys=False)
            
            print(f"\n  Configuration saved to: {CURRENT_CONFIG_PATH}")

    def _load_installed_models_from_current_config(self):
        if not CURRENT_CONFIG_PATH.exists():
            print(f"Warning: {CURRENT_CONFIG_PATH} not found. Cannot determine installed models.")
            return
        
        with open(CURRENT_CONFIG_PATH, 'r') as f:
            current_config = yaml.safe_load(f)
        
        installed_keys = current_config.get("installed_models", [])
        all_models_dict = self.models_config.get("available_models", {})
        self.selected_models = []
        for key in installed_keys:
            if key in all_models_dict:
                model_data = all_models_dict[key]
                model_data['key'] = key
                self.selected_models.append(model_data)

    def _setup_python_env(self):
        print("\n[2/6] Setting up Python environment...")
        if not VENV_PATH.exists():
            print("  Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(VENV_PATH)], check=True, capture_output=True)
        self._run_venv_pip(["install", "--upgrade", "pip"], quiet=True)
        self._run_venv_pip(["install", "-r", str(REQUIREMENTS_PATH)], quiet=True)
        print("  Python environment setup complete!")

    def _get_venv_python_path(self):
        return VENV_PATH / ("Scripts" if platform.system() == "Windows" else "bin") / "python.exe"

    def _run_venv_pip(self, command, quiet=False):
        cmd = [str(self.venv_python), "-m", "pip"] + command
        subprocess.run(cmd, check=True, capture_output=quiet, text=True)

    def _download_models(self):
        from huggingface_hub import hf_hub_download
        print("\n[3/6] Downloading selected translation models...")
        for model in self.selected_models:
            model_config = model
            dest_path = ROOT_DIR / model_config['destination']

            if dest_path.exists() and (not dest_path.is_dir() or any(dest_path.iterdir())):
                 print(f"    Model '{model['name']}' already downloaded.")
                 continue
            
            print(f"    Downloading {model['name']}...")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            repo_id = model_config['repo']
            if model_config.get('huggingface_download'):
                 py_code = f"from transformers import AutoModel; model = AutoModel.from_pretrained('{repo_id}'); model.save_pretrained('{dest_path.as_posix()}')"
                 subprocess.run([str(self.venv_python), "-c", py_code], check=True, capture_output=True)
            else: 
                hf_hub_download(repo_id=repo_id, filename=model_config['file'], local_dir=str(dest_path.parent), local_dir_use_symlinks=False)
                downloaded_file = dest_path.parent / model_config['file']
                if downloaded_file.exists() and downloaded_file != dest_path:
                    downloaded_file.rename(dest_path)

    def _download_tools(self):
        print("\n[4/6] Downloading external tools...")
        renpy_config = self.tools_config['tools']['renpy']
        renpy_path = ROOT_DIR / renpy_config['destination']
        
        if renpy_path.exists():
            print("  Ren'Py SDK already exists.")
        else:
            print(f"  Downloading Ren'Py SDK {renpy_config['version']}...")
            temp_zip = ROOT_DIR / "renpy.zip"
            try:
                import urllib.request
                with urllib.request.urlopen(renpy_config['url']) as response, open(temp_zip, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                with zipfile.ZipFile(temp_zip, 'r') as zf: zf.extractall(ROOT_DIR)
                extracted = next(ROOT_DIR.glob('renpy-*/'), None)
                if extracted: extracted.rename(renpy_path)
            except Exception as e:
                print(f"  WARNING: Could not download Ren'Py SDK: {e}")
            finally:
                if temp_zip.exists(): temp_zip.unlink()

    def _verify_installation(self):
        print("\n[5/6] Verifying installation...")
        print("  Verification checks passed (placeholder).")

    def _print_footer(self):
        print("\n" + "=" * 70)
        print("  SETUP COMPLETE!")
        print("\n  You're all set! Next steps:")
        print("  1. Copy your Ren'Py game to the games/ folder")
        print("  2. Run the translation script: ./3-translate.ps1")
        print("\n" + "=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Ren'Py Translation System - Setup Script")
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-tools", action="store_true")
    parser.add_argument("--skip-model", action="store_true")
    parser.add_argument("--languages", type=str, default="")
    parser.add_argument("--models", type=str, default="")
    
    args = parser.parse_args()

    try:
        ProjectSetup(args).run()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
