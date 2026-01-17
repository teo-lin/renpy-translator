# poly_trans

Local neural translation engine with context awareness and glossary support.

## Description

Core translation package supporting 5 models (Aya23, MADLAD400, Helsinki, mBART, SeamlessM4T) with context extraction and prompt management.

## Setup

```bash
# Install dependencies
pip install -r ../../requirements.txt

# Or install as package
pip install -e .
```

## Configure

Edit `data/prompts/*.yaml` for translation prompts and `data/glossaries/*.yaml` for glossaries.

Model configuration: `../../models/models_config.yaml`

## Run

```python
from src.poly_trans.translate import ModularBatchTranslator

translator = ModularBatchTranslator(
    model_key="aya23",
    target_language="Romanian"
)

result = translator.translate(
    text="Hello world",
    glossary={"world": "lume"},
    context=["Previous line"]
)
```

## Test

```bash
# Run poly_trans tests
pytest ../../tests/test_unit_translate.py
pytest ../../tests/test_int_*.py
```

## Debug

Enable verbose logging in translator initialization or check CUDA setup with:
```python
import torch
print(torch.cuda.is_available())
```
