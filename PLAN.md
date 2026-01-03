# Hybrid Glossary Integration Plan
## Smart Post-Processing + LoRA Fine-Tuning for Encoder-Decoder Translation Models

**Goal:** Enable Helsinki, MBART, SeamlessM4T, and MADLAD400 models to use the uncensored glossary effectively.

**Strategy:** Hybrid approach combining rule-based post-processing (quick win) with neural fine-tuning (quality boost).

---

## Overview

### Current State
- ✅ Aya23 (LLM) uses glossary via prompt injection
- ❌ Encoder-decoder models load glossary but don't apply it (stub `_apply_glossary` methods)
- ✅ Comprehensive `ro_uncensored_glossary.yaml` with complete declensions/conjugations
- ✅ Uncensored prompt templates with fallbacks

### Target State
- ✅ All models use glossary effectively
- ✅ 70-80% accuracy with post-processing (Phase 1)
- ✅ 90-95% accuracy with hybrid approach (Phase 3)
- ✅ Maintainable, debuggable, and extensible system

---

## Phase 1: Smart Post-Processing Implementation
**Timeline:** 2-4 hours
**Dependencies:** None
**Risk:** Low

### 1.1 Create Glossary Matcher Module

**File:** `src/glossary_matcher.py`

**Features:**
- Load YAML/JSON glossary with all inflected forms
- Build reverse mapping (detect what model might have written)
- Context-aware replacement (avoid breaking grammar)
- Word boundary detection (avoid partial matches)
- Case preservation (lowercase/title case handling)

**Key Functions:**
```python
class GlossaryMatcher:
    def __init__(self, glossary: dict, source_lang: str = "en", target_lang: str = "ro")

    def build_replacement_map(self, source_text: str) -> dict[str, str]
        """Find all glossary terms in source and prepare replacements"""

    def apply_replacements(self, translation: str, replacement_map: dict) -> str
        """Apply replacements with word boundary awareness"""

    def get_inflected_forms(self, en_term: str) -> list[str]
        """Extract all inflected forms for a term from glossary"""
```

**Implementation Notes:**
- Use regex with word boundaries: `\b{term}\b`
- Sort by length (longest first) to avoid partial replacements
- Skip `_comment` entries
- Handle case sensitivity intelligently
- Log all replacements for debugging

### 1.2 Integrate Into Existing Translators

**Files to modify:**
- `src/translators/helsinkyRo_translator.py`
- `src/translators/mbartRo_translator.py`
- `src/translators/seamless96_translator.py`
- `src/translators/madlad400_translator.py`

**Changes:**
```python
from glossary_matcher import GlossaryMatcher

class TranslatorClass:
    def __init__(self, ..., glossary: dict = None):
        # ... existing code ...
        self.glossary_matcher = GlossaryMatcher(glossary) if glossary else None

    def _apply_glossary(self, text: str, translation: str) -> str:
        """Smart glossary application with inflection handling"""
        if not self.glossary_matcher:
            return translation

        # Build replacement map from source text
        replacement_map = self.glossary_matcher.build_replacement_map(text)

        # Apply replacements
        result = self.glossary_matcher.apply_replacements(translation, replacement_map)

        return result
```

### 1.3 Add YAML Glossary Loading Support

**File:** `src/translators/*.py` (all translators)

**Current state:** Only loads JSON glossaries
**Target state:** Load YAML with fallback to JSON

**Changes to `__main__` section:**
```python
# Try to load glossary (YAML preferred, JSON fallback)
glossary = None
for glossary_variant in [
    f"{lang_code}_uncensored_glossary.yaml",  # NEW: Try YAML first
    f"{lang_code}_uncensored_glossary.json",
    f"{lang_code}_glossary.yaml",             # NEW: Try YAML fallback
    f"{lang_code}_glossary.json"
]:
    glossary_path = project_root / "data" / glossary_variant
    if glossary_path.exists():
        if glossary_variant.endswith('.yaml'):
            import yaml
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary = yaml.safe_load(f)
        else:
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
        print(f"[OK] Using glossary: {glossary_variant}")
        break
```

### 1.4 Testing

**Create:** `tests/test_glossary_matcher.py`

**Test cases:**
- Direct term replacement: "dick" → "pulă"
- Inflected form replacement: "my dick" → "pula mea"
- Multi-word phrases: "suck my dick" → "suge-mi pula"
- Context preservation: Don't replace "Dick" (name) with "pulă"
- Word boundaries: "fucking" in "unfuckingbelievable" → don't replace
- Multiple replacements in one sentence
- Case preservation: "Fucking" → "Futând" (capital preserved)

**Success Criteria:**
- 95% accuracy on known glossary terms
- No false positives (replacing things that shouldn't be replaced)
- All existing tests still pass

---

## Phase 2: LoRA Fine-Tuning Setup
**Timeline:** 1-2 days initial setup + 2-4 hours per model training
**Dependencies:** Phase 1 complete (to generate training data)
**Risk:** Medium (requires GPU, ML expertise)

### 2.1 Prepare Training Infrastructure

**Install dependencies:**
```bash
pip install peft transformers datasets accelerate bitsandbytes
```

**Create:** `src/finetuning/` directory structure
```
src/finetuning/
├── prepare_training_data.py    # Convert glossary + existing translations to training data
├── train_lora.py                # Main training script
├── evaluate_lora.py             # Evaluate adapter quality
└── configs/
    ├── helsinki_lora_config.yaml
    ├── mbart_lora_config.yaml
    ├── seamless_lora_config.yaml
    └── madlad400_lora_config.yaml
```

### 2.2 Generate Training Data

**Source 1:** Convert glossary to training examples
```python
# From: ro_uncensored_glossary.yaml
# To: training pairs

# Example:
"suck my dick!" → "suge-mi pula!"
"keeps sucking my dick" → "continuă să-mi sugă pula"
"while sucking my dick" → "sugându-mi pula"
```

**Estimate:** ~500-800 examples from glossary alone

**Source 2:** Use Phase 1 translations as training data
```python
# After translating a few game files with Phase 1:
# 1. Manual review/correction of translations
# 2. Extract (English, corrected Romanian) pairs
# 3. Add to training set
```

**Estimate:** ~200-500 more examples after translating 2-3 game files

**Total target:** 700-1300 training examples

**File:** `data/training/ro_adult_dialogue_train.jsonl`
```json
{"en": "Suck my dick!", "ro": "Suge-mi pula!"}
{"en": "She keeps fucking her mouth", "ro": "Continuă s-o fută în gură"}
...
```

### 2.3 Create Training Script

**File:** `src/finetuning/train_lora.py`

**Features:**
- Load base model (Helsinki/MBART/SeamlessM4T/MADLAD400)
- Add LoRA adapters to attention layers
- Train on adult dialogue dataset
- Save adapter weights separately (don't modify base model)
- Track metrics: BLEU, exact term match rate, grammar correctness

**LoRA Configuration:**
```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,                          # Rank (8-16 typical, higher = more capacity)
    lora_alpha=32,                # Scaling factor (usually 2-4x rank)
    target_modules=[              # Which layers to adapt
        "q_proj", "v_proj",       # Attention layers (always)
        "k_proj", "o_proj"        # Optional: more coverage
    ],
    lora_dropout=0.1,             # Regularization
    bias="none",                  # Don't train bias terms
    task_type="SEQ_2_SEQ_LM"      # Translation task
)

model = get_peft_model(base_model, lora_config)
trainable_params = model.print_trainable_parameters()
# Expect: ~0.5-1% of total parameters (10-50MB)
```

**Training hyperparameters:**
```python
training_args = TrainingArguments(
    output_dir="./models/lora_adapters/helsinkyRo_adult",
    num_train_epochs=3-5,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    warmup_steps=100,
    logging_steps=50,
    save_steps=500,
    evaluation_strategy="steps",
    eval_steps=500,
    fp16=True,                    # Use half precision (faster on RTX 3060)
)
```

**Estimated training time:**
- Helsinki (smallest): 1-2 hours
- MBART (medium): 2-3 hours
- SeamlessM4T (large): 3-4 hours
- MADLAD400 (large): 3-4 hours

### 2.4 Evaluation Strategy

**File:** `src/finetuning/evaluate_lora.py`

**Metrics:**
1. **Term accuracy:** % of glossary terms used correctly
2. **BLEU score:** Overall translation quality vs reference
3. **Grammar check:** Manual review of 50 random translations
4. **Comparison:** Base model vs LoRA vs Post-processing vs Hybrid

**Test set:** Hold out 100 examples (not used in training)

**Success criteria:**
- Term accuracy: >85%
- BLEU score: ≥ base model (shouldn't degrade general quality)
- Grammar: Natural Romanian, proper pronoun clusters

### 2.5 Integrate LoRA Adapters into Translators

**Modify:** `src/translators/*.py`

**Add parameter:**
```python
def __init__(self, ..., lora_adapter_path: str = None):
    # Load base model
    self.model = ModelClass.from_pretrained(model_path, ...)

    # Load LoRA adapter if provided
    if lora_adapter_path and Path(lora_adapter_path).exists():
        from peft import PeftModel
        self.model = PeftModel.from_pretrained(self.model, lora_adapter_path)
        print(f"[OK] Loaded LoRA adapter from {lora_adapter_path}")
```

**Auto-detection:**
```python
# Check for adapter in models directory
adapter_path = project_root / "models" / "lora_adapters" / f"{model_name}_adult"
if adapter_path.exists():
    lora_adapter_path = str(adapter_path)
```

---

## Phase 3: Hybrid Integration
**Timeline:** 2-4 hours
**Dependencies:** Phase 1 + Phase 2 complete
**Risk:** Low

### 3.1 Combined Pipeline

**Flow:**
```
English Input
    ↓
LoRA-Adapted Model Translation (learns patterns)
    ↓
Smart Post-Processing (enforces exact terms)
    ↓
Final Output
```

**Implementation:**
```python
def translate(self, text: str, ...) -> str:
    # Step 1: Translate with LoRA-adapted model
    translation = self._generate_translation(text)  # Uses LoRA if loaded

    # Step 2: Apply glossary post-processing
    if self.glossary_matcher:
        translation = self._apply_glossary(text, translation)

    # Step 3: Additional cleanup (diacritics, spacing, etc.)
    translation = self._post_process(translation)

    return translation
```

### 3.2 Configuration Options

**Add to translator initialization:**
```python
def __init__(
    self,
    ...,
    glossary: dict = None,
    lora_adapter_path: str = None,
    use_post_processing: bool = True,  # NEW: Toggle post-processing
    post_processing_mode: str = "smart"  # "smart" or "aggressive"
):
    ...
```

**Modes:**
- `smart`: Only replace high-confidence matches
- `aggressive`: Replace all glossary terms found in source
- `lora_only`: Use LoRA without post-processing
- `post_only`: Use post-processing without LoRA

### 3.3 Logging and Debugging

**Add translation logging:**
```python
def translate(self, text: str, ..., debug: bool = False) -> str:
    if debug:
        print(f"[DEBUG] Input: {text}")

    base_translation = self._generate_translation(text)
    if debug:
        print(f"[DEBUG] Base translation: {base_translation}")

    if self.glossary_matcher:
        replacement_map = self.glossary_matcher.build_replacement_map(text)
        if debug and replacement_map:
            print(f"[DEBUG] Applying replacements: {replacement_map}")

        translation = self.glossary_matcher.apply_replacements(
            base_translation, replacement_map
        )

        if debug and translation != base_translation:
            print(f"[DEBUG] After post-processing: {translation}")

    return translation
```

### 3.4 Performance Benchmarking

**Create:** `scripts/benchmark_glossary.py`

**Compare:**
1. Base model (no glossary)
2. Post-processing only
3. LoRA only
4. Hybrid (LoRA + post-processing)

**Metrics:**
- Translation speed (tokens/sec)
- Memory usage (GB)
- Term accuracy (%)
- BLEU score
- Grammar quality (manual review)

**Test set:** 100 adult dialogue sentences from game

---

## Phase 4: Documentation and Maintenance
**Timeline:** 4-6 hours
**Dependencies:** Phase 1-3 complete
**Risk:** Low

### 4.1 Update Documentation

**Files to update:**
- `README.md`: Add glossary integration section
- `docs/TRANSLATORS.md`: Document new features
- `docs/GLOSSARY.md`: Explain glossary format and usage
- `docs/FINETUNING.md`: Guide for training custom adapters

### 4.2 Create User Guide

**File:** `docs/GLOSSARY_GUIDE.md`

**Sections:**
- How to add new terms to glossary
- Understanding inflections and declensions
- When to use YAML vs JSON format
- How to enable/disable post-processing
- How to train custom LoRA adapters
- Troubleshooting common issues

### 4.3 Add Configuration Examples

**File:** `config/translation_config.yaml.example`

```yaml
translation:
  model: "helsinkyRo"  # or "mbart", "seamless96", "madlad400", "aya23"

  glossary:
    enabled: true
    path: "data/ro_uncensored_glossary.yaml"
    post_processing: true
    mode: "smart"  # "smart" or "aggressive"

  lora:
    enabled: true
    adapter_path: "models/lora_adapters/helsinkyRo_adult"

  output:
    debug: false
    log_replacements: true
```

### 4.4 Testing Suite

**Files:**
- `tests/test_glossary_matcher.py` (Phase 1)
- `tests/test_lora_integration.py` (Phase 2)
- `tests/test_hybrid_pipeline.py` (Phase 3)
- `tests/test_e2e_glossary.py` (Full end-to-end with real game files)

**Coverage target:** >80% for new code

---

## Timeline Summary

| Phase | Task | Time Estimate | Dependencies |
|-------|------|---------------|--------------|
| **1.1** | Create GlossaryMatcher module | 2 hours | None |
| **1.2** | Integrate into translators | 1 hour | 1.1 |
| **1.3** | Add YAML loading | 30 min | None |
| **1.4** | Testing Phase 1 | 1 hour | 1.1-1.3 |
| **2.1** | Setup training infrastructure | 2 hours | Phase 1 done |
| **2.2** | Generate training data | 3 hours | 2.1 |
| **2.3** | Create training script | 3 hours | 2.1, 2.2 |
| **2.4** | Train first model | 2-4 hours | 2.3 |
| **2.5** | Integrate LoRA adapters | 2 hours | 2.4 |
| **3.1** | Hybrid pipeline | 2 hours | Phase 1+2 |
| **3.2** | Configuration options | 1 hour | 3.1 |
| **3.3** | Logging/debugging | 1 hour | 3.1 |
| **3.4** | Benchmarking | 2 hours | 3.1-3.3 |
| **4.1-4.4** | Documentation & testing | 4 hours | All phases |
| **TOTAL** | | **26-28 hours** + training time per model | |

**Realistic timeline:** 1-2 weeks (working part-time)

---

## Success Metrics

### Phase 1 Success (Post-Processing)
- ✅ All models apply glossary post-processing
- ✅ 70-80% term accuracy on test set
- ✅ No regression on non-glossary terms
- ✅ All tests pass

### Phase 2 Success (LoRA)
- ✅ Successfully train adapter for at least one model
- ✅ 85%+ term accuracy on test set
- ✅ BLEU score ≥ base model
- ✅ Natural Romanian output (manual review)

### Phase 3 Success (Hybrid)
- ✅ 90-95% term accuracy on test set
- ✅ BLEU score ≥ base model
- ✅ Faster than Aya23 (LLM)
- ✅ Configurable and debuggable

### Overall Success
- ✅ All 5 translation models use glossary effectively
- ✅ Measurable quality improvement over base models
- ✅ Maintainable codebase with good documentation
- ✅ Users can easily add new glossary terms

---

## Risk Mitigation

### Risk: Post-processing breaks grammar
**Mitigation:**
- Use word boundary detection
- Test extensively with real game dialogue
- Add grammar validation step
- Allow disabling per-term via `_no_replace_` prefix

### Risk: Insufficient training data for LoRA
**Mitigation:**
- Start with glossary-derived examples (500-800)
- Augment with existing translations
- Use data augmentation (paraphrasing)
- Start with smallest model (Helsinki) first

### Risk: LoRA degrades general translation quality
**Mitigation:**
- Monitor BLEU score on non-adult test set
- Use regularization (dropout, early stopping)
- Keep LoRA rank small (r=8)
- Validate on diverse test cases

### Risk: Compatibility issues with existing pipeline
**Mitigation:**
- Make all features opt-in (backwards compatible)
- Extensive testing on existing test suite
- Feature flags for gradual rollout
- Keep base models unchanged (adapters separate)

---

## Future Enhancements

### Post-Phase 3 Improvements
1. **Multi-language support:** Extend to Spanish, French, etc.
2. **Active learning:** Suggest glossary additions based on translation patterns
3. **Grammar correction:** Add language-specific grammar rules
4. **Confidence scoring:** Report confidence for each translation
5. **A/B testing:** Compare model outputs side-by-side
6. **Web UI:** Visual glossary editor and translation reviewer

### Advanced LoRA Techniques
1. **QLoRA:** 4-bit quantization for larger models with less memory
2. **Multi-adapter fusion:** Combine multiple specialized adapters
3. **Dynamic adapter selection:** Choose adapter based on content type
4. **Continuous learning:** Incrementally update adapters with new data

---

## Notes

- All file paths are relative to project root: `C:\_____\_CODE\enro\`
- GPU training tested on RTX 3060 6GB (should work fine)
- YAML format preferred for glossary (human-readable, supports comments)
- JSON maintained for backwards compatibility
- Keep base models untouched (adapters stored separately)
- Phase 1 is fully independent - can deploy without Phase 2
- Phase 2 training can be done per-model (don't need to train all at once)

---

## Questions to Address During Implementation

1. Should we train separate adapters for dialogue vs narration vs UI strings?
2. Do we need separate glossaries for different formality levels (tu vs dumneavoastră)?
3. Should post-processing be applied before or after diacritic correction?
4. How to handle character name translations (never replace)?
5. Should we include SFW glossary fallback for non-adult content?

---

**Status:** Planning Phase
**Next Step:** Begin Phase 1.1 - Create GlossaryMatcher module
**Estimated Completion:** 1-2 weeks from start
**Owner:** [Your name]
**Last Updated:** 2026-01-03
