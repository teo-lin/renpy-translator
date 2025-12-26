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

**Option 2: MADLAD-400 (Google, 2024) - SPECIALIZED TRANSLATION**
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

**Option 3: NLLB-200 (Meta, 2022) - PROVEN, STABLE**
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

**Option 4: SeamlessM4T-v2 (Meta, 2024) - MOST RECENT FROM META**
- **Type:** Multimodal translation (text + speech)
- **Released:** 2024
- **Performance:** +1.3 BLEU over v1, state-of-art multimodal
- **Size:** v2-large: ~2.3GB fp16, ~5GB+ with speech
- **Romanian:** Nearly 100 languages
- **Pros:** Most recent Meta model, better than NLLB
- **Cons:** Larger, includes speech features you don't need
- **Best for:** If you want Meta's latest

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
