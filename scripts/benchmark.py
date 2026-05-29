"""
Translation Quality Benchmark using BLEU Scores

Benchmarks translation quality by comparing model outputs to reference translations
using BLEU (Bilingual Evaluation Understudy) scores.

Benchmark data format (YAML):
- source: English text to translate
  target: Reference translation
  context: Optional previous dialogue for context
- source: Another text...
  target: Another translation...

Usage:
    python benchmark.py data/ro_benchmark.yaml [--glossary data/ro_glossary.yaml]
    python benchmark.py data/de_benchmark.yaml --glossary data/de_glossary.yaml
"""

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
import re

# Try to import BLEU from nltk
try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("WARNING: nltk not installed. Install with: pip install nltk")
    print("Falling back to simple word-match accuracy")

# Fix Windows PATH for CUDA DLLs
if sys.platform == "win32":
    import os
    torch_lib = str(Path(__file__).parent.parent / "venv" / "Lib" / "site-packages" / "torch" / "lib")
    if os.path.exists(torch_lib) and torch_lib not in os.environ["PATH"]:
        os.environ["PATH"] = torch_lib + os.pathsep + os.environ["PATH"]

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from translators.aya23_translator import Aya23Translator
from translators.helsinkyRo_translator import QuickMTTranslator
from translators.llama_cpp_translator import LlamaCppTranslator
from translators.madlad400_translator import MADLAD400Translator
from translators.mbartRo_translator import MBARTTranslator
from translators.nllb200_translator import NLLB200Translator
from translators.seamless96_translator import SeamlessM4Tv2Translator


def tokenize(text: str) -> List[str]:
    """Simple tokenization: split on whitespace and punctuation"""
    # Remove Ren'Py tags and variables for fair comparison
    text = re.sub(r'\{[^}]+\}', '', text)  # Remove {color=...}, etc.
    text = re.sub(r'\[[^\]]+\]', '', text)  # Remove [name], etc.

    # Tokenize
    return text.lower().split()


def calculate_bleu(reference: str, hypothesis: str) -> float:
    """
    Calculate BLEU score between reference and hypothesis

    Returns score between 0.0 (worst) and 1.0 (perfect match)
    """
    if not NLTK_AVAILABLE:
        # Fallback: simple word overlap accuracy
        ref_words = set(tokenize(reference))
        hyp_words = set(tokenize(hypothesis))
        if not ref_words:
            return 0.0
        overlap = len(ref_words & hyp_words)
        return overlap / len(ref_words)

    # NLTK BLEU with smoothing (for short sentences)
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)

    smoothing = SmoothingFunction().method1
    return sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothing)


def load_benchmark_data(data_path: Path) -> List[Dict]:
    """Load benchmark data from JSON file"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        raise ValueError("Benchmark data must be a JSON array")

    # Validate format
    for i, item in enumerate(data):
        if 'source' not in item or 'target' not in item:
            raise ValueError(f"Item {i} missing 'source' or 'target' field")

    return data


def load_glossary(glossary_path: Path) -> Dict:
    """Load glossary from JSON file"""
    if not glossary_path.exists():
        return {}

    with open(glossary_path, 'r', encoding='utf-8') as f:
        glossary = yaml.safe_load(f)

    # Filter out comment entries (starting with _)
    return {k: v for k, v in glossary.items() if not k.startswith('_')}


def detect_language_from_filename(filename: str) -> str:
    """
    Detect language from filename (e.g., 'ro_benchmark.yaml' → 'Romanian')
    """
    lang_map = {
        'ro': 'Romanian',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'tr': 'Turkish',
        'cs': 'Czech',
        'pl': 'Polish',
        'uk': 'Ukrainian',
        'bg': 'Bulgarian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'vi': 'Vietnamese',
        'th': 'Thai',
        'id': 'Indonesian',
        'ar': 'Arabic',
        'he': 'Hebrew',
        'fa': 'Persian',
        'hi': 'Hindi',
        'bn': 'Bengali',
    }

    # Extract language code from filename
    for code, lang in lang_map.items():
        if filename.startswith(f'{code}_') or f'_{code}_' in filename:
            return lang

    # Default to Romanian
    return 'Romanian'


def _resolve_model_file(project_root: Path, model_key: str, model_info: dict) -> Path:
    dest_path = project_root / model_info['destination']
    if 'files' not in model_info:
        return dest_path
    profile_path = project_root / 'models' / 'compute_profile.yaml'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        file_rel = profile.get('models', {}).get(model_key, {}).get('file')
        if file_rel:
            return project_root / file_rel
    files = model_info['files']
    filename = files.get('Q4_K_M') or files.get('Q3_K_M') or next(iter(files.values()))
    return dest_path / filename


def _load_profile_params(project_root: Path, model_key: str) -> dict:
    profile_path = project_root / 'models' / 'compute_profile.yaml'
    if profile_path.exists():
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        params = profile.get('models', {}).get(model_key, {})
        if params:
            return {
                'n_gpu_layers': params.get('n_gpu_layers', -1),
                'n_ctx': params.get('n_ctx', 8192),
                'n_batch': params.get('n_batch', 256),
            }
    return {'n_gpu_layers': -1, 'n_ctx': 8192, 'n_batch': 256}


def detect_lang_code_from_filename(filename: str) -> str:
    for code in ['ro', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'tr', 'cs', 'pl',
                 'uk', 'bg', 'zh', 'ja', 'ko', 'vi', 'th', 'id', 'ar', 'he',
                 'fa', 'hi', 'bn', 'nl', 'sv', 'da', 'fi', 'el', 'hu']:
        if filename.startswith(f'{code}_') or f'_{code}_' in filename:
            return code
    return 'ro'


def run_benchmark(data_path: Path, glossary_path: Path = None, model_key: str = "aya23") -> Dict:
    """
    Run translation quality benchmark

    Returns:
        Statistics dict with scores and examples
    """
    print("=" * 70)
    print("Translation Quality Benchmark")
    print("=" * 70)

    # Detect target language
    target_language = detect_language_from_filename(data_path.name)
    print(f"\nTarget language: {target_language}")
    print(f"Benchmark data: {data_path}")

    # Load data
    print("\nLoading benchmark data...")
    benchmark_data = load_benchmark_data(data_path)
    print(f"  Loaded {len(benchmark_data)} test cases")

    # Load glossary
    glossary = {}
    if glossary_path and glossary_path.exists():
        print(f"\nLoading glossary: {glossary_path}")
        glossary = load_glossary(glossary_path)
        print(f"  Loaded {len(glossary)} terms")

    # Load model configuration
    project_root = Path(__file__).parent.parent
    models_config_path = project_root / "models" / "models_config.yaml"

    with open(models_config_path, 'r', encoding='utf-8') as f:
        models_config = yaml.safe_load(f)

    model_info = models_config['available_models'].get(model_key)
    if not model_info:
        print(f"ERROR: Model '{model_key}' not found in models_config.yaml")
        sys.exit(1)

    print(f"\nModel: {model_info['name']}")
    print(f"Initializing translator...")

    lang_code = detect_lang_code_from_filename(data_path.name)

    # Create translator based on model type
    if model_key == "aya23":
        model_path = project_root / model_info['destination']
        translator = Aya23Translator(str(model_path), target_language=target_language)
    elif model_key in ("helsinkyRo", "helsinkiRo"):
        model_path = project_root / model_info['destination']
        translator = QuickMTTranslator(model_path=str(model_path), target_language=target_language)
    elif model_key == "madlad400":
        translator = MADLAD400Translator(target_language=target_language)
    elif model_key == "mbartRo":
        model_path = project_root / model_info['destination']
        translator = MBARTTranslator(model_path=str(model_path), target_language=target_language)
    elif model_key == "nllb200":
        model_path = project_root / model_info['destination']
        translator = NLLB200Translator(model_path=str(model_path), target_language=target_language, lang_code=lang_code)
    elif model_key in ("seamlessm96", "seamless96"):
        model_path = project_root / model_info['destination']
        translator = SeamlessM4Tv2Translator(model_name=str(model_path), target_language=target_language)
    elif model_key in ("ayaExpanse8b", "euroLLM9b"):
        model_path = _resolve_model_file(project_root, model_key, model_info)
        profile_params = _load_profile_params(project_root, model_key)
        translator = LlamaCppTranslator(model_path=str(model_path), target_language=target_language, **profile_params)
    else:
        print(f"ERROR: Model '{model_key}' not supported for benchmarking")
        sys.exit(1)

    # Run translations and calculate scores
    print("\n" + "=" * 70)
    print("Running translations...")
    print("=" * 70)

    scores = []
    results = []

    for i, item in enumerate(benchmark_data, 1):
        source = item['source']
        reference = item['target']
        context = item.get('context', None)

        print(f"\n[{i}/{len(benchmark_data)}]")
        print(f"  Source: {source}")

        # Parse context (can be string or list)
        context_list = None
        if context:
            if isinstance(context, str):
                context_list = [context]
            elif isinstance(context, list):
                context_list = context

        # Translate
        hypothesis = translator.translate(
            source,
            glossary=glossary,
            context=context_list
        )

        # Calculate BLEU
        score = calculate_bleu(reference, hypothesis)
        scores.append(score)

        print(f"  Reference:  {reference}")
        print(f"  Hypothesis: {hypothesis}")
        print(f"  BLEU Score: {score:.4f}")

        results.append({
            'source': source,
            'reference': reference,
            'hypothesis': hypothesis,
            'score': score
        })

    # Calculate statistics
    avg_score = sum(scores) / len(scores) if scores else 0.0
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nTotal test cases: {len(benchmark_data)}")
    print(f"Average BLEU:     {avg_score:.4f}")
    print(f"Min BLEU:         {min_score:.4f}")
    print(f"Max BLEU:         {max_score:.4f}")

    # Show best and worst examples
    sorted_results = sorted(results, key=lambda x: x['score'])

    print("\n" + "-" * 70)
    print("WORST TRANSLATION:")
    worst = sorted_results[0]
    print(f"  Source:     {worst['source']}")
    print(f"  Reference:  {worst['reference']}")
    print(f"  Hypothesis: {worst['hypothesis']}")
    print(f"  Score:      {worst['score']:.4f}")

    print("\n" + "-" * 70)
    print("BEST TRANSLATION:")
    best = sorted_results[-1]
    print(f"  Source:     {best['source']}")
    print(f"  Reference:  {best['reference']}")
    print(f"  Hypothesis: {best['hypothesis']}")
    print(f"  Score:      {best['score']:.4f}")

    print("\n" + "=" * 70)

    return {
        'total': len(benchmark_data),
        'average_bleu': avg_score,
        'min_bleu': min_score,
        'max_bleu': max_score,
        'results': results
    }


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print("  python benchmark.py data/ro_benchmark.yaml")
        print("  python benchmark.py data/ro_benchmark.yaml --model aya23")
        print("  python benchmark.py data/ro_benchmark.yaml --model madlad400 --glossary data/ro_glossary.yaml")
        sys.exit(1)

    # Parse arguments
    data_path = Path(sys.argv[1])
    glossary_path = None
    model_key = "aya23"  # Default model

    # Check for --glossary and --model parameters
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--glossary' and i + 1 < len(sys.argv):
            glossary_path = Path(sys.argv[i + 1])
            i += 2
        elif arg == '--model' and i + 1 < len(sys.argv):
            model_key = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not data_path.exists():
        print(f"ERROR: Benchmark data not found: {data_path}")
        sys.exit(1)

    # Auto-detect glossary if not specified
    if glossary_path is None:
        # Try to find matching glossary (e.g., ro_benchmark.yaml → ro_glossary.yaml)
        lang_code = data_path.stem.split('_')[0]  # Extract 'ro' from 'ro_benchmark'

        # Try uncensored first, then regular
        uncensored_glossary = data_path.parent / f"{lang_code}_uncensored_glossary.yaml"
        regular_glossary = data_path.parent / f"{lang_code}_glossary.yaml"

        if uncensored_glossary.exists():
            glossary_path = uncensored_glossary
            print(f"Auto-detected glossary: {glossary_path}")
        elif regular_glossary.exists():
            glossary_path = regular_glossary
            print(f"Auto-detected glossary: {glossary_path}")

    # Run benchmark
    run_benchmark(data_path, glossary_path, model_key)


if __name__ == "__main__":
    main()
