# 2024-2025 Model Options (Ranked by Quality)

The core requirements are: Gramatically correct, culturally and contextually aware translation EN to RO, uncensored, able to translate explicit adult content, able to use correct declensions, conjugations, syntax and topic in Romanian. They must run on a Windows PC with 16GB RAM, RTX3060 with 6GB VRAM + shared VRAM.

## Overview Table

| Model | Type | Params (B, billions) | BLEU Score | Tatoeba Score | Flores Score | VRAM GB required | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **[Aya-23-8B](https://huggingface.co/cohere/aya-23-8B)** | Multilingual LLM <br> GGUF | 8 | | | 34.8 | 5.8 |👍 Uncensored, GGUF, 23 languages <br>👎 Slower, larger VRAM |
| **[MBART-Ro-1B](https://huggingface.co/facebook/mbart-large-en-ro)** | __Ro-Translation__ <br> safetensors | 0.6 | __38.0__ (WMT16) | | | 2 |👍 Largest RO-specific, good context.<br>👎 Smaller than multilinguals |
| **[MADLAD-400-3B](https://huggingface.co/google/madlad-400-3b-mt)** | Translations <br> safetensors | 3 | ~35.11 | | 38.4 | 4 |👍 Uncensored, safetensors, 400+ languages <br>👎 Requires `trust_remote_code`, lower quality for some languages |
| **[Seamless-96-2B](https://huggingface.co/facebook/seamless-m4t-v2-large)** | Multimodal <br> safetensors | 2.3 | | | 38.8 | 5+ |👍 Most recent from Meta, better than NLLB.<br>👎 Includes unneeded speech features |
| **[Helsinki-Ro-0B](https://huggingface.co/Helsinki-NLP/opus-mt-en-ro)**| __Ro-Translation__ <br> safetensors | 0.075 | 34.0 (WMT16) | | | 0.3 |👍 Fast, lightweight Marian MT model.<br>👎 Smaller than MBART. Good for low VRAM. |
| **[NLLB-200](https://huggingface.co/facebook/nllb-200-3.3B)** | Translations <br> safetensors | 3.3 | ~31.17 | | 37.5 | 4.5 |👍 Proven, stable, large community.<br>👎 Older model (2022).  Good for reliability. |
| **[OPUS-MT-TC-Big](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-ro)**| Large OPUS <br> safetensors | 0.2 | 34.0 (Newstest2016) | 48.6 | 40.4 | 1 |👍 Good grammar for size, small footprint.<br>👎 Smaller than MBART, may be censored.  Good for low VRAM. |
| **[Helsinki-Tatoeba](https://huggingface.co/Helsinki-NLP/opus-tatoeba-en-ro)**| Transformer-align <br> safetensors | 0.078 | 31.7 (Newstest2016) | 46.9 | | 0.2 |👍 Better than standard OPUS, tiny footprint.<br>👎 Small model, not for complex grammar.  Requires `>>ron<<` token. |
| **[suzume-llama-3-8B](https://huggingface.co/lightblue/suzume-llama-3-8B-multilingual)**| Multilingual LLM <br> safetensors | 8 | | | | ~5-6 |👍 Based on powerful Llama 3, likely uncensored, very new (Oct 2024).<br>👎 Romanian is not a focus, EN-RO performance is unknown.  Experimental high-potential |
| **[Marcoroni-7B-v3](https://huggingface.co/TheBloke/Marcoroni-7B-v3-GGUF)**| Instruct LLM <br> GGUF | 7 | | | | ~4.8 |👍 Strong Mistral base, likely uncensored, was #1 on 7B leaderboard.<br>👎 Not for translations, for general tasks. EN-RO performance is unknown.  Experimental. |
| **[OLMo-7B](https://huggingface.co/allenai/OLMo-7B)** | Multilingual LLM <br> safetensors | 7 | | | | 5 |👍 Fully open source.<br>👎 Research-focused, may not match SOTA. For open-source enthusiasts. |
| **[BlackKakapo-MT](https://huggingface.co/BlackKakapo/opus-mt-en-ro)**| Community OPUS <br> safetensors | 0.075 | ~24.5 (Estimated) | 53.1 | | 0.5 |👍 Community fine-tuned.<br>👎 Single-person project, weakest grammar.  For extreme VRAM constraints. |
| **[Orion-14B](https://huggingface.co/OrionStarAI/Orion-14B)** | Multilingual LLM <br> safetensors | 14 | | | | 9 |👍 Large context window.<br>👎 Too heavy for 6GB VRAM. |
| **[OpenELM-3B](https://huggingface.co/apple/OpenELM-3B)** | Multilingual LLM <br> safetensors | 3 | | | | 2.5 |👍 Very fast and lightweight.<br>👎 Too small for complex Romanian.  NOT RECOMMENDED. |

---

## Removed/Unsupported Models

### LLMic-3B ❌ REMOVED
**Reason:** Translation functionality non-operational

While the [faur-ai/LLMic](https://huggingface.co/faur-ai/LLMic) model claims BLEU 41.01 on WMT16 EN-RO translation in its paper ([arXiv:2501.07721](https://arxiv.org/abs/2501.07721)), the publicly available Hugging Face model does not translate.

**Issues encountered:**
- Model generates random Romanian text unrelated to English input
- Multiple prompt formats tested (parallel corpus, few-shot, instruction-based) - all failed
- Model appears to be base pretrained version, not the translation-tuned variant
- No documentation on Hugging Face for translation usage or prompt format
- Suspected missing: translation adapter/LoRA or specific fine-tuned checkpoint

**Status:** The translation-capable version referenced in the paper is not publicly available or requires undocumented configuration. Removed from available models until proper translation checkpoint is released.

---

## Model Types Explained
- **Multilingual LLM:** General-purpose Large Language Models trained on many languages (e.g., Aya, Orion). They are good at understanding context but are not exclusively built for translation.
- **Instruct LLM:** A general-purpose LLM that has been fine-tuned to be good at following user commands or "instructions." Their translation ability varies.
- **Translations / Ro-Translations:** Models designed and trained specifically for translation tasks, either between many languages (Translations) or focused on Romanian (Ro-Translations).
- **Bilingual Ro-En:** Foundation models trained extensively on both Romanian and English, making them highly effective for translation between the two.
- **Multimodal:** Models that can process more than one type of data, such as both text and audio (e.g., SeamlessM4T).
- **OPUS / Transformer-align:** Architectures that are highly effective for translation. OPUS is a popular framework, and many models are built on it, sometimes with community fine-tuning.


  Current Status:

  | Model          | Status                  | Notes                         |
  |----------------|-------------------------|-------------------------------|
  | Aya-23-8B      | ✅ Production Ready     | Uses llama-cpp-python         |
  | MADLAD-400-3B  | ✅ Production Ready     | Works with float16 fallback   |
  | SeamlessM4T-v2 | ✅ Production Ready     | Works, slow to load (~90s)    |
  | MBART-En-Ro    | ✅ Production Ready     | Fixed source language setting |
  | Helsinki OPUS-MT | ✅ Production Ready   | Fast Marian MT, sacremoses warning suppressed |
  | LLMic-3B       | ❌ REMOVED              | Doesn't translate (see above) |

  What Changed:

  1. ✅ Removed torchao package (it was causing the conflict)
  2. ✅ Fixed Unicode arrows in translator print statements
  3. ✅ Fixed MADLAD test to use HuggingFace auto-download instead of looking for GGUF file

