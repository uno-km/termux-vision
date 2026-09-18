# Release Notes - termux-vision v1.4.5

**Release Tag**: `v1.4.5`  
**Distribution Channels**: PyPI (`termux-vision`), NPM (`termux-vision`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. Multimodal Chat Template Collision Resolution
- **Resolved Prompt Tokenization Crash**: Stripped conflicting `--chat-template` arguments during multimodal inference, preventing `Failed to tokenize prompt` and marker-count mismatches with GGUF vision models (e.g. SmolVLM).
- **Vulkan Device Flag Sanitization**: Purged invalid `--device vulkan` argument from standalone execution paths, ensuring clean device selection and compatibility with modern llama.cpp runtime builds.

### 2. Enforced Single-Turn Non-Interactive Execution
- **Resolved REPL Deadlock**: Explicitly enforced `--single-turn` and `--no-conversation` CLI arguments across internal `llama-cli` execution pipelines to eliminate hung interactive chat loops.
- **Model-Native Chat Templates**: Directly passed clean user queries to let `llama-cli` parse Jinja chat templates natively, eradicating redundant token tag duplication and tokenizer parsing failures.
- **Eradicated Ambiguous Model Overloading**: Separated catalog preset names from custom GGUF file paths across CLI, Python SDK, and Node.js SDK.
- **Dedicated CLI Flags**:
  - `-m, --model`: Exclusively for official catalog identifiers (`smolvlm-500m-q4`, `qwen2-vl-2b-q4`).
  - `--model-path`: Dedicated flag for explicit custom `.gguf` language model paths.
  - **Strict Mutual Exclusivity**: Enforces clear fail-fast validation when conflicting arguments are provided.
- **Dual SDK Alignment**:
  - Python: `tv.vlm.load(model_id=...)` vs `tv.vlm.load(model_path=...)`.
  - Node.js: `vision.vlm.load({ modelId })` vs `vision.vlm.load({ modelPath })`.

### 2. Universal 2048 Context Window Baseline
- **Purged Legacy 1024 Limits**: Completely eradicated hardcoded 1024 context limits from custom manifest discovery, catalog entries (`qwen2-vl-2b-q4`), engine defaults, and Node.js cache managers.
- **Android Memory-Safe Architecture**: Aligned on 2048 tokens as the unified mobile baseline to prevent token overflows during 512x512 image patch tokenization while preserving RAM bounds against Low Memory Killer (LMK).

### 3. Native `termux-llamacpp` Primary SSOT Orchestration
- **Official Runtime Bridge**: Fully integrated `termux-llamacpp`'s execution environment (`prepare_env`) into `ZeroFlickerEngine` and `SubprocessVLMRuntime`.
- **Transparent Failure Guidance**: Upgraded `RuntimeNotFoundError` to explicitly guide users to install `pip install termux-llamacpp` and `npm install -g termux-llamacpp`.

---

## Detailed Changelog

### Added
- `--model-path` CLI option for explicit custom GGUF model files.
- `model_path` parameter to `tv.vlm.load` (Python) and `modelPath` to `vlm.load` (Node.js).
- Clear mutually exclusive argument verification preventing ambiguous invocation.

### Changed
- `termux_vision/vlm/cache.py`: Standardized all custom model manifests and catalog presets to `context_limit=2048`.
- `termux_vision/vlm/engine.py`: Updated default `context_limit` to 2048; wired `termux_llamacpp.prepare_env`.
- `termux_vision/vlm/manifest.py`: Updated `ModelManifest.from_dict` fallback `context_limit` to 2048.
- `termux_vision/errors.py` & `lib/errors.js`: Standardized runtime guidance to recommend `pip install termux-llamacpp` and `npm install -g termux-llamacpp`.
- `lib/cache.js`: Updated Node.js catalog and custom discovery context limits to 2048.
- Package versions synchronized to `1.4.3`.
