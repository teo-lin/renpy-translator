# poly_bench

Translation model comparison and benchmarking tools.

## Description

Compare translation model performance (speed) and quality (BLEU scores) across different translation models.

## Setup

```bash
# Install dependencies (includes nltk for BLEU)
pip install -r ../../requirements.txt
pip install nltk

# Or install as package
pip install -e .
```

## Configure

Benchmark data: Create YAML files in `../../data/` with format:
```yaml
- source: "English text"
  target: "Reference translation"
  context: "Optional previous line"
```

## Run

### Speed Comparison
```bash
# Python CLI
python cli.py compare <input_yaml>

# Or programmatically
from src.poly_bench.compare import BenchmarkTranslator
benchmark = BenchmarkTranslator()
benchmark.compare_all_models("test_data.yaml")
```

### Quality Benchmark (BLEU)
```bash
# Python CLI
python cli.py benchmark <benchmark_yaml> --model aya23 --glossary <glossary_yaml>

# Or programmatically
from src.poly_bench.benchmark import run_benchmark
stats = run_benchmark("ro_benchmark.yaml", "ro_glossary.yaml", "aya23")
```

## Test

```bash
# Run poly_bench tests
pytest ../../tests/test_unit_compare.py
pytest ../../tests/test_e2e_compare.py
pytest ../../tests/test_e2e_benchmark.py
```

## Debug

Check model loading, CUDA availability, or enable verbose output in compare/benchmark scripts.
