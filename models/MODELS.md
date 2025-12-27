# 2024-2025 Model Options (Ranked by Quality)

**Option 1: Aya-23-8B (Cohere, 2025) - NEWEST, BEST BENCHMARKS**  SELECTED
- **Type:** Multilingual LLM with excellent translation
- **Released:** January 2025
- **Performance:** Beats NLLB, Gemma, GPT-3.5 in multilingual benchmarks
- **Size:** 8B parameters
  - GGUF Q4_K_M: ~4.5GB storage, ~5GB VRAM (fits in 6GB)
  - GGUF Q5_K_M: ~5.5GB storage, ~6GB VRAM (tight fit)
- **Romanian:** One of 23 supported languages (high quality)
- **Pros:** State-of-art 2025, uncensored, handles context better
- **Cons:** General LLM (not pure translation model), needs prompting
- **Best for:** Highest quality with context understanding

**Option 2: Orion-14B (OrionStar, 2024) - LARGE CONTEXT**
- **Type:** Multilingual LLM
- **Released:** 2024
- **Performance:** Strong multilingual benchmarks, large context window
- **Size:** 14B parameters
  - GGUF Q4_K_M: ~8.5GB storage, ~9GB VRAM (heavy for 12GB)
- **Romanian:** Supported as part of multilingual training
- **Pros:** Larger size may improve context/grammar over 8B, very long context window
- **Cons:** Heavy for an RTX 3060 (slow), less tested than Aya-23
- **Best for:** Pushing hardware limits for maximum quality

**Option 3: MADLAD-400 (Google, 2024) - SPECIALIZED TRANSLATION**
- **Type:** Specialized translation model
- **Released:** 2024
- **Performance:** Outperforms NLLB-200 in recent tests
- **Size:** Multiple sizes available (3B, 7B, 10B)
  - MADLAD-400-3B: ~3GB storage, ~3.5GB VRAM
  - MADLAD-400-7B: ~7GB storage (too large for 6GB VRAM)
- **Romanian:** 400+ languages supported
- **Pros:** Newer than NLLB, specialized for translation, open license
- **Cons:** Less community adoption than NLLB
- **Best for:** Pure translation performance

**Option 4: NLLB-200 (Meta, 2022) - PROVEN, STABLE**
- **Type:** Specialized translation model
- **Released:** 2022
- **Performance:** Previous state-of-art, well-tested
- **Size:** Multiple sizes
  - 600M distilled: ~600MB storage, ~1.2GB VRAM
  - 1.3B: ~1.5GB storage, ~2.5GB VRAM
  - 3.3B: ~3.5GB storage, ~4.5GB VRAM
- **Romanian:** Tier 1 language (EU priority)
- **Pros:** Most proven, CTranslate2 optimized, large community
- **Cons:** 2022 model (older than alternatives)
- **Best for:** Reliability and community support

**Option 5: SeamlessM4T-v2 (Meta, 2024) - MOST RECENT FROM META**
- **Type:** Multimodal translation (text + speech)
- **Released:** 2024
- **Performance:** +1.3 BLEU over v1, state-of-art multimodal
- **Size:** v2-large: ~2.3GB fp16, ~5GB+ with speech
- **Romanian:** Nearly 100 languages
- **Pros:** Most recent Meta model, better than NLLB
- **Cons:** Larger, includes speech features you don't need
- **Best for:** If you want Meta's latest

**Option 6: OLMo-7B (AI2, 2024) - FULLY OPEN**
- **Type:** Multilingual LLM
- **Released:** 2024
- **Performance:** Solid benchmarks, fully open training data and code
- **Size:** 7B parameters
  - GGUF Q4_K_M: ~4.1GB storage, ~5GB VRAM (fits in 6GB)
- **Romanian:** Supported as part of multilingual training
- **Pros:** Truly open source (data, code, weights), strong for research
- **Cons:** Research-focused, may not match SOTA commercial model performance
- **Best for:** Open-source enthusiasts and reproducibility

**Option 7: OpenELM-3B (Apple, 2024) - EFFICIENT / ON-DEVICE**
- **Type:** Multilingual LLM
- **Released:** April 2024
- **Performance:** Optimized for on-device (mobile) efficiency
- **Size:** 3B parameters
  - GGUF Q4_K_M: ~1.8GB storage, ~2.5GB VRAM
- **Romanian:** Supported as part of multilingual training
- **Pros:** Very fast and lightweight, SOTA for its small size
- **Cons:** Unsuitable for this task. Too small for complex Romanian grammar/context.
- **Best for:** Low-resource applications. (NOT RECOMMENDED for this project)

### RECOMMENDED: Aya-23-8B Q4_K_M

**Why Aya-23-8B (Q4_K_M):**
- Released January 2025 (newest available)
- Beats all competitors in benchmarks
- 8B parameters: Better context than small models
- Fits in 6GB VRAM with Q4 quantization
- Can fine-tune with LoRA using your 331 training pairs
- Uncensored by default (Cohere policy)

**Why MADLAD-400-3B (backup option):**
- Specialized translation (faster than general LLM)
- Outperforms NLLB-200 (2024 vs 2022)
- 3GB model: More VRAM headroom than Aya-23
- CTranslate2 conversion possible

---

## Romanian-Specific Models (En→Ro)

**Compared for:** Adult visual novel translation (uncensored, context-aware, proper grammar/declension/conjugation)

### Option 5: MBART-Large-En-Ro (Facebook, 2023) - LARGEST RO-SPECIFIC
- **Type:** Romanian-specialized MBART variant
- **Size:** 600M parameters (~1.2GB storage, ~2GB VRAM)
- **Released:** September 2023
- **Downloads:** 11.3k (popular)
- **Model:** `facebook/mbart-large-en-ro`
- **Pros:**
  - Largest Romanian-specific model available
  - MBART architecture = strong context awareness
  - Better grammar/conjugation than small models
  - Facebook backing = quality training data
- **Cons:**
  - Smaller than Aya-23-8B (600M vs 8B)
  - May still struggle with complex grammar
  - Not specifically uncensored
- **Best for:** If you want Romanian-specific over general multilingual

### Option 6: OPUS-MT-TC-Big-En-Ro (Helsinki, 2023) - TRANSFORMER-BIG VARIANT
- **Type:** Large OPUS Transformer variant
- **Size:** 200M parameters (~400MB storage, ~1GB VRAM)
- **Released:** October 2023
- **Downloads:** 110 (niche)
- **Model:** `Helsinki-NLP/opus-mt-tc-big-en-ro`
- **Pros:**
  - "tc-big" = larger than standard OPUS (77M)
  - Transformer architecture good for grammar
  - Small VRAM footprint
  - Helsinki NLP has good reputation
- **Cons:**
  - Still smaller than MBART and Aya
  - Less community testing
  - Academic model (may be more censored)
- **Best for:** Low VRAM constraint with decent quality

### Option 7: QuickMT-En-Ro (QuickMT, 2024) - NEWEST RO-SPECIFIC
- **Type:** Latest Romanian translation model
- **Size:** Unknown parameters (~500MB estimated)
- **Released:** October 2024
- **Downloads:** 21 (very new)
- **Model:** `quickmt/quickmt-en-ro`
- **Pros:**
  - Most recent Romanian model (Oct 2024)
  - May include latest improvements
  - Active development
- **Cons:**
  - Unknown architecture/training
  - Minimal community testing
  - No performance benchmarks available
  - Size unknown
- **Best for:** Experimental - testing newest approaches
- **Risk:** Unproven quality, may underperform established models

### Option 8: BlackKakapo OPUS-MT-En-Ro (Community, 2023) - COMMUNITY FINE-TUNED
- **Type:** Community-tuned OPUS variant
- **Size:** 74.7M parameters (~150MB storage, ~500MB VRAM)
- **Released:** July 2023
- **Downloads:** 44 (niche)
- **Model:** `BlackKakapo/opus-mt-en-ro`
- **Pros:**
  - Fine-tuned by community member
  - Potentially optimized for specific use cases
  - Smallest VRAM footprint
  - Based on proven OPUS architecture
- **Cons:**
  - Single-person project (less reliable)
  - Smallest model = weakest grammar/context
  - No documentation on fine-tuning data
  - May not handle complex sentences
- **Best for:** Extreme VRAM constraints (<1GB)

---

## Recommendation for Adult Visual Novels (Uncensored, Context-Aware)

**STICK WITH Aya-23-8B** - Here's why:

### Context & Grammar Requirements:
Adult visual novels need:
- **Long context** (dialogue flow, character relationships) → 8B > 600M
- **Cultural nuance** (Romanian idioms, not literal) → LLM > translation model
- **Complex grammar** (declension, conjugation, gender agreement) → Larger = better
- **Uncensored** (explicit content) → General LLM > academic translation model

### Model Comparison:
| Model | Size | Context | Grammar | Uncensored | VRAM |
|-------|------|---------|---------|------------|------|
| **Aya-23-8B** ⭐ | 8B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Yes | 5GB |
| MBART-Large-En-Ro | 600M | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❓ Unknown | 2GB |
| OPUS-TC-Big | 200M | ⭐⭐ | ⭐⭐⭐ | ❌ Academic | 1GB |
| QuickMT | Unknown | ❓ | ❓ | ❓ Unknown | Unknown |
| BlackKakapo | 75M | ⭐ | ⭐⭐ | ❓ Unknown | 500MB |

### The Problem with Small Models:
Romanian grammar is **complex**:
- 3 genders (masculine, feminine, neuter)
- 5 cases (nominative, accusative, genitive, dative, vocative)
- Multiple conjugation patterns
- Context-dependent word order

Small models (< 1B params) consistently fail at:
- Proper gender agreement across sentences
- Choosing correct case based on sentence role
- Maintaining consistent formality (tu vs dumneavoastră)
- Cultural idioms (translate meaning, not words)

**Example failure** (75M OPUS model):
```
EN: "She gave him the book"
BAD: "Ea a dat lui cartea" (wrong case, wrong word order)
GOOD: "I-a dat cartea" (correct dative case, natural Romanian)
```

### Verdict:
**Aya-23-8B remains the best choice.** Romanian-specific models are too small for:
1. Complex grammar handling
2. Long-context dialogue
3. Cultural/idiomatic translation
4. Uncensored content

**Alternative if VRAM is limited (<4GB):**
Use **MADLAD-400-3B** instead of Romanian-specific models - it's specialized for translation but large enough for decent grammar.
