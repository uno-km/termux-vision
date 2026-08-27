# Release Notes: termux-vision v0.2.0-alpha.1

## Overview
termux-vision (AMEVA-Vision) v0.2.0-alpha.1 introduces native Visual Language Model (VLM) execution, dynamic model management, Hugging Face automated resolution, Vulkan GPU vs CPU strict hardware isolation, and zero-dependency autograd bridges for Android Termux.

## Highlights
- **VLM Inference Engine**: Native support for SmolVLM and Qwen2-VL multimodal vision-language architectures.
- **Dynamic Model Selection**: Support for catalog models, Hugging Face hub repositories, and external custom GGUF and mmproj models.
- **Hardware Isolation**:
  - `auto` mode: Automatic Vulkan GPU detection with transparent, resilient CPU fallback.
  - `gpu`/`vulkan` mode: Strict Vulkan GPU enforcement with immediate diagnostics on failure.
  - `cpu` mode: Pure CPU execution.
- **Boundary & Supply Chain Hardening**: Path traversal elimination (`require_path_within_root`), strict SHA-256 validation, and argument vector process execution (`shell=False`).
- **Comprehensive Diagnostics**: Dynamic error reporting with local cache scanning, custom model installation guidance, and OOM recovery recommendations.