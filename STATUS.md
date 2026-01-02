# Enro - Ren'Py Translation System Status

**Last Updated:** 2026-01-03

---

## Current State Summary

**Status:** ✅ Production Ready with 5/6 models working

**Working Models:**
- ✅ Aya-23-8B (llama.cpp) - Production ready, 5.8GB VRAM
- ✅ MADLAD-400-3B (T5) - Working, 4GB VRAM
- ✅ SeamlessM4T-v2 (Multimodal) - Working but slow, 5GB+ VRAM
- ✅ MBART-En-Ro (BART) - Working, 2GB VRAM
- ✅ Helsinki-RO (OPUS-MT) - Working, 1GB VRAM
- ❌ QuickMT-En-Ro - Not implemented

**Test Results:** All core tests passing

---

## Architecture Overview

### Current Pipeline Flow

```
1-config.ps1          →  Discover games & characters
2-extract.ps1         →  .rpy → .parsed.yaml + .tags.json
3-translate.ps1       →  Translate .parsed.yaml files
4-correct.ps1         →  Grammar/pattern corrections
5-merge.ps1           →  .parsed.yaml + .tags.json → .translated.rpy
7-all-in-one.ps1      →  Direct .rpy translation (legacy)
```

### Directory Structure

```
enro/
├── src/                      # Core modules
│   ├── extract.py           # RenpyExtractor
│   ├── merger.py            # RenpyMerger
│   ├── renpy_utils.py       # Tag handling utilities
│   ├── models.py            # Data type definitions
│   ├── translation_pipeline.py  # Legacy pipeline
│   └── translators/         # Translation backends
│       ├── aya23_translator.py
│       ├── madlad400_translator.py
│       ├── mbartRo_translator.py
│       ├── helsinkyRo_translator.py
│       └── seamless96_translator.py
├── scripts/                 # Entry point scripts
│   ├── translate.py        # Main translation orchestrator
│   └── correct.py          # Grammar correction
├── tests/                   # Test suite
├── data/                    # Prompts, glossaries, corrections
└── models/                  # Model configs & downloads
```

---

## Architecture Issues: Coupling Analysis

### Current Coupling Problems

#### 1. **Tight Coupling via Shared Utilities**
- `renpy_utils.py` contains both Ren'Py-specific logic AND translation utilities
- `RenpyTagExtractor` is used by extract, merge, AND translation
- Hard to reuse translation logic for other game engines

#### 2. **Config Monolith**
- `current_config.json` mixes:
  - Game-specific settings (paths, character names)
  - Translation settings (language, model)
  - Ren'Py-specific settings (SDK paths)
- Changing one aspect requires understanding all aspects

#### 3. **Data Model Coupling**
- `models.py` defines Ren'Py-specific types (`RenpyBlock`, `TaggedBlock`)
- Translation code depends on these Ren'Py-specific structures
- Can't easily adapt to other formats (Unity TextMeshPro, etc.)

#### 4. **Orchestration Coupling**
- PowerShell launchers call Python scripts directly
- No abstraction layer between UI and business logic
- Hard to create alternative frontends (GUI, web service)

#### 5. **Translation Backend Coupling**
- Each translator imports Ren'Py-specific utilities
- Character context handling is Ren'Py-aware
- Can't reuse translators in non-Ren'Py projects

---

## Decoupling Plan

### Phase 1: Define Core Abstractions 🎯

**Goal:** Establish clear interfaces between concerns

#### 1.1 Create Abstract Game Engine Interface

**New File:** `src/interfaces/game_engine.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class GameContent:
    """Language-agnostic game content block"""
    id: str
    type: str  # dialogue, narrator, choice, string
    text: str
    metadata: Dict[str, Any]
    speaker: Optional[str]

class GameEngine(ABC):
    """Abstract game engine adapter"""

    @abstractmethod
    def extract(self, file_path: str) -> List[GameContent]:
        """Extract translatable content from game file"""
        pass

    @abstractmethod
    def merge(self, file_path: str, content: List[GameContent]) -> str:
        """Merge translated content back to game format"""
        pass

    @abstractmethod
    def validate(self, original: GameContent, translated: GameContent) -> List[str]:
        """Validate translation integrity"""
        pass
```

#### 1.2 Create Abstract Translation Interface

**New File:** `src/interfaces/translator.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class TranslationContext:
    """Generic translation context"""
    text: str
    preceding: List[str]
    following: List[str]
    speaker: Optional[str]
    metadata: Dict[str, Any]

class Translator(ABC):
    """Abstract translator backend"""

    @abstractmethod
    def translate(self, context: TranslationContext, target_lang: str) -> str:
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
```

#### 1.3 Create Configuration Abstraction

**New Files:**
- `src/config/game_config.py` - Game-specific settings
- `src/config/translation_config.py` - Translation settings
- `src/config/engine_config.py` - Engine-specific settings

---

### Phase 2: Refactor Ren'Py Logic 🔧

**Goal:** Isolate all Ren'Py-specific code

#### 2.1 Create Ren'Py Engine Adapter

**New File:** `src/engines/renpy/renpy_engine.py`

**Responsibilities:**
- Implements `GameEngine` interface
- Contains all Ren'Py parsing logic
- Manages tag extraction/restoration
- Validates Ren'Py-specific constraints

**Consolidates:**
- `src/extract.py` → `RenpyEngine.extract()`
- `src/merger.py` → `RenpyEngine.merge()`
- `src/renpy_utils.py` → Internal utilities

#### 2.2 Reorganize Ren'Py Module

**New Structure:**
```
src/engines/renpy/
├── __init__.py
├── renpy_engine.py          # Main adapter implementing GameEngine
├── parser.py                # .rpy parsing logic
├── tag_handler.py           # Tag extraction/restoration
├── validator.py             # Ren'Py-specific validation
└── models.py                # Ren'Py-specific data types
```

#### 2.3 Move Ren'Py Tools

**Relocate:**
- `renpy/` SDK → `src/engines/renpy/sdk/`
- `renpy/tools_config.json` → `src/engines/renpy/config.json`

---

### Phase 3: Refactor Translation Logic 🌍

**Goal:** Make translation engine-agnostic

#### 3.1 Create Generic Translation Service

**New File:** `src/services/translation_service.py`

```python
class TranslationService:
    """Engine-agnostic translation orchestrator"""

    def __init__(self,
                 translator: Translator,
                 engine: GameEngine,
                 config: TranslationConfig):
        self.translator = translator
        self.engine = engine
        self.config = config

    def translate_file(self, input_path: str, output_path: str):
        # 1. Extract using engine
        content = self.engine.extract(input_path)

        # 2. Translate using translator
        for block in content:
            context = self._build_context(block)
            block.text = self.translator.translate(context)

        # 3. Validate using engine
        errors = self.engine.validate(original, content)

        # 4. Merge using engine
        result = self.engine.merge(input_path, content)

        # 5. Save
        self._save(output_path, result)
```

#### 3.2 Refactor Translator Backends

**For each translator in `src/translators/`:**

1. Remove Ren'Py imports
2. Implement new `Translator` interface
3. Accept `TranslationContext` instead of raw strings
4. Remove character-specific logic (move to Ren'Py adapter)

**Example Migration:**

**Before:** `aya23_translator.py`
```python
from src.renpy_utils import show_progress  # ❌ Coupled

class Aya23Translator:
    def translate(self, text: str, speaker: str) -> str:  # ❌ Ren'Py-aware
        ...
```

**After:** `aya23_translator.py`
```python
from src.interfaces.translator import Translator, TranslationContext

class Aya23Translator(Translator):
    def translate(self, context: TranslationContext, target_lang: str) -> str:
        # Generic translation logic
        ...

    @property
    def supported_languages(self) -> List[str]:
        return ["ro", "es", "fr", ...]
```

#### 3.3 Reorganize Translation Module

**New Structure:**
```
src/translators/
├── __init__.py
├── base.py                  # Re-export Translator interface
├── aya23.py                # Aya-23-8B implementation
├── madlad400.py            # MADLAD-400 implementation
├── mbart.py                # MBART implementation
├── helsinki.py             # Helsinki OPUS-MT implementation
└── seamless.py             # SeamlessM4T implementation
```

---

### Phase 4: Decouple Configuration 📋

**Goal:** Separate concerns in configuration

#### 4.1 Split Configuration Files

**Current:** `models/current_config.json` (monolith)

**New:**
- `config/game.json` - Game paths, character mappings
- `config/translation.json` - Target language, glossary paths
- `config/engines/renpy.json` - Ren'Py SDK paths, extraction settings
- `config/models.json` - Model metadata (keep as-is)

#### 4.2 Create Config Loader

**New File:** `src/config/loader.py`

```python
class ConfigLoader:
    @staticmethod
    def load_game_config(game_name: str) -> GameConfig:
        ...

    @staticmethod
    def load_translation_config() -> TranslationConfig:
        ...

    @staticmethod
    def load_engine_config(engine_name: str) -> EngineConfig:
        ...
```

---

### Phase 5: Decouple Orchestration 🎭

**Goal:** Separate business logic from UI

#### 5.1 Create Workflow Orchestrator

**New File:** `src/workflows/translation_workflow.py`

```python
class TranslationWorkflow:
    """High-level workflow orchestrator"""

    def __init__(self, engine_type: str, translator_type: str):
        self.engine = self._create_engine(engine_type)
        self.translator = self._create_translator(translator_type)

    def extract(self, game_path: str):
        """Extract translatable content"""
        ...

    def translate(self, language: str):
        """Translate extracted content"""
        ...

    def correct(self, rules_path: str):
        """Apply corrections"""
        ...

    def merge(self, output_path: str):
        """Merge back to game format"""
        ...

    def full_pipeline(self, game_path: str, language: str):
        """Run complete workflow"""
        self.extract(game_path)
        self.translate(language)
        self.correct()
        self.merge(output_path)
```

#### 5.2 Refactor PowerShell Launchers

**Update all `.ps1` scripts to use orchestrator:**

**Before:** `2-extract.ps1`
```powershell
python src/extract.py --game $gamePath  # ❌ Direct call
```

**After:** `2-extract.ps1`
```powershell
python scripts/run_workflow.py extract --engine renpy --game $gamePath
```

#### 5.3 Create Unified CLI

**New File:** `scripts/run_workflow.py`

```python
import click
from src.workflows.translation_workflow import TranslationWorkflow

@click.group()
def cli():
    pass

@cli.command()
@click.option('--engine', default='renpy')
@click.option('--game', required=True)
def extract(engine, game):
    workflow = TranslationWorkflow(engine_type=engine)
    workflow.extract(game)

@cli.command()
@click.option('--translator', default='aya23')
@click.option('--language', required=True)
def translate(translator, language):
    workflow = TranslationWorkflow(translator_type=translator)
    workflow.translate(language)

# ... more commands
```

---

### Phase 6: Update Tests 🧪

**Goal:** Test decoupled components independently

#### 6.1 Add Interface Tests

**New Files:**
- `tests/test_interface_game_engine.py` - Test GameEngine contract
- `tests/test_interface_translator.py` - Test Translator contract

#### 6.2 Add Adapter Tests

**New Files:**
- `tests/test_renpy_engine.py` - Test Ren'Py adapter
- `tests/test_translator_aya23.py` - Test Aya23 with generic context

#### 6.3 Update Integration Tests

**Modify existing tests to use new interfaces:**
- `tests/test_e2e_aya23.py` → Use `TranslationWorkflow`
- `tests/test_e2e_example_game.py` → Use `RenpyEngine` directly

---

## Migration Strategy

### Step-by-Step Implementation

#### Week 1: Foundation
- [ ] Create `src/interfaces/` with abstract base classes
- [ ] Create `src/config/` with split configuration
- [ ] Write interface tests
- [ ] Update documentation

#### Week 2: Ren'Py Isolation
- [ ] Create `src/engines/renpy/` module structure
- [ ] Move `extract.py` → `renpy_engine.py::extract()`
- [ ] Move `merger.py` → `renpy_engine.py::merge()`
- [ ] Move `renpy_utils.py` → `renpy/tag_handler.py`
- [ ] Update tests for Ren'Py adapter

#### Week 3: Translation Refactor
- [ ] Refactor all translators to implement `Translator` interface
- [ ] Create `TranslationService`
- [ ] Remove Ren'Py dependencies from translators
- [ ] Update translator tests

#### Week 4: Orchestration
- [ ] Create `TranslationWorkflow`
- [ ] Create unified CLI (`run_workflow.py`)
- [ ] Update PowerShell launchers
- [ ] Run full regression tests

#### Week 5: Polish
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Add examples for extending with new engines
- [ ] Performance testing

---

## Benefits of Decoupling

### 1. **Reusability**
- Translation backends can work with Unity, Godot, etc.
- Ren'Py engine can be used in other translation tools
- Easy to create standalone CLI tools

### 2. **Maintainability**
- Changes to Ren'Py parsing don't affect translators
- Changes to translation logic don't affect extraction/merge
- Clear separation of concerns

### 3. **Testability**
- Mock engines for testing translators
- Mock translators for testing engines
- Integration tests more focused

### 4. **Extensibility**
- Add new game engines by implementing `GameEngine`
- Add new translators by implementing `Translator`
- Add new workflows without modifying core code

### 5. **Clarity**
- New contributors understand boundaries
- Config files have clear purposes
- Code organization matches mental model

---

## Post-Decoupling Architecture

### Final Structure

```
enro/
├── src/
│   ├── interfaces/              # Abstract contracts
│   │   ├── game_engine.py
│   │   └── translator.py
│   ├── engines/                 # Game engine adapters
│   │   ├── renpy/
│   │   │   ├── renpy_engine.py
│   │   │   ├── parser.py
│   │   │   ├── tag_handler.py
│   │   │   └── validator.py
│   │   └── unity/               # Future: Unity adapter
│   ├── translators/             # Translation backends
│   │   ├── base.py
│   │   ├── aya23.py
│   │   ├── madlad400.py
│   │   └── ...
│   ├── services/                # Business logic
│   │   └── translation_service.py
│   ├── workflows/               # Orchestration
│   │   └── translation_workflow.py
│   └── config/                  # Configuration management
│       ├── loader.py
│       ├── game_config.py
│       ├── translation_config.py
│       └── engine_config.py
├── config/                      # Configuration files
│   ├── game.json
│   ├── translation.json
│   └── engines/
│       └── renpy.json
├── scripts/                     # CLI entry points
│   └── run_workflow.py
├── tests/
│   ├── test_interface_*.py
│   ├── test_engine_*.py
│   ├── test_translator_*.py
│   └── test_e2e_*.py
└── *.ps1                        # PowerShell UI (now thin wrappers)
```

---

## Risk Mitigation

### Backward Compatibility
- Keep old scripts as deprecated wrappers during transition
- Provide migration path for existing projects
- Document breaking changes clearly

### Testing Strategy
- All existing tests must pass after each phase
- Add new tests before refactoring
- Regression testing after each week

### Rollback Plan
- Git branch for each phase
- Tagged releases for stable points
- Keep `main` branch stable

---

## Success Metrics

### Technical Metrics
- [ ] Zero circular dependencies between modules
- [ ] 100% test coverage on interfaces
- [ ] All existing functionality preserved
- [ ] Performance within 10% of current

### Code Quality Metrics
- [ ] Ren'Py code only in `engines/renpy/`
- [ ] Translation code has zero Ren'Py imports
- [ ] Config files < 50 lines each
- [ ] Clear documentation for all interfaces

### Usability Metrics
- [ ] PowerShell scripts still work (as thin wrappers)
- [ ] New CLI provides same functionality
- [ ] Migration guide tested by 3rd party
- [ ] Example Unity adapter can be created in < 1 day

---

## Conclusion

This decoupling plan transforms **enro** from a Ren'Py-specific tool into a **modular translation framework** where:

- **Ren'Py is just one engine adapter** among many
- **Translators are engine-agnostic** and reusable
- **Configuration is split by concern** and easy to understand
- **Workflows are composable** and testable
- **Extensions are straightforward** via clear interfaces

**Estimated effort:** 5 weeks for one developer
**Priority:** Medium (current system works, but extensibility needed)
**Recommended start:** After implementing QuickMT translator

---

## Model Implementation Status

### Working Models (5/6)

| Model | Status | Implementation | Memory | Notes |
|-------|--------|---------------|--------|-------|
| **Aya-23-8B** | ✅ Production | `aya23_translator.py` | 5.8GB VRAM | llama-cpp (GGUF), no transformers |
| **MADLAD-400-3B** | ✅ Working | `madlad400_translator.py` | 4GB VRAM | T5-based, 400+ languages |
| **SeamlessM4T-v2** | ✅ Working | `seamlessm4t_translator.py` | 5GB+ VRAM | Slow to load (~90s) |
| **MBART-En-Ro** | ✅ Working | `mbartRo_translator.py` | 2GB VRAM | BART-based, bilingual |
| **Helsinki-RO** | ✅ Working | `helsinkyRo_translator.py` | 1GB VRAM | OPUS-MT, lightweight |
| **QuickMT-En-Ro** | ❌ Not Implemented | - | 0.5GB VRAM | Needs implementation |

### Recent Fixes
- ✅ Removed torchao (was causing triton/torch incompatibility)
- ✅ All transformers-based models now compatible
- ✅ Memory optimizations: `device_map="auto"`, `low_cpu_mem_usage=True`, fp16

### Test Results: All Passing ✅

```
✅ test_e2e_aya23.py
✅ test_e2e_example_game.py
✅ test_e2e_translate_aio.py
✅ test_u_extract.py
✅ test_u_merge.py
✅ test_u_renpy_tags.py
✅ test_u_translate_modular.py
```
