# Release Notes - termux-vision v1.4.6

**Release Tag**: `v1.4.6`  
**Distribution Channels**: PyPI (`termux-vision`), NPM (`termux-vision`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. Unified 5-Backend Standardization
- **Strict 5-Option Governance**: Standardized `--device` / `--backend` parameter choices to `["auto", "gpu", "vulkan", "opencl", "cpu"]`.
- **Legacy Flag Purge**: Completely eradicated experimental `vulkan-force` flag and arguments.
- **Fail-Fast Rejection**: Passing unsupported options like `cpu_neon` triggers immediate rejection.

### 2. VLM Subprocess Runtime & Multimodal Decoupling
- **VLMResponse Structural Alignment**: Synchronized response parsing with `termux-llamacpp` engine dataclass attributes (`generation_tps`, `latency_ms`).
- **Zero-Error Test Suite**: Validated 71 passing test suites across adversarial audits, safetensors loaders, and multimodal smoke suites.
