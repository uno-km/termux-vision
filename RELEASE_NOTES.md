# Termux-Vision Release Notes

**Version:** v1.4.0  
**Release Date:** 2026-09-07  
**License:** Apache-2.0  

---

## Key Highlights in v1.4.0 (2026-09-07)

### 1. Qualcomm Snapdragon 8 Elite (Adreno 830) Full-GPU VLM Acceleration
- **Pure GPU Offloading**: Dispatches all 25 layers of Moondream2 1.8B f16 directly to Qualcomm Adreno 830 GPU VRAM (**2,706.00 MiB**, with **0.00 MiB CPU mapped VRAM**).
- **Qualcomm SPIR-V Compiler Patch**: Resolved Qualcomm JIT shader abort (`VK_ERROR_UNKNOWN -13`) during unrolled vector compilation by adjusting `mul_mat_vec_max_cols = 2` (preventing vector register spilling).
- **KGSL Watchdog & `ErrorDeviceLost` Defense**: Prefilling large multimodal token sets (729 vision tokens) triggers Android kernel GPU timeouts unless micro-batched. Automated injection of `GGML_VULKAN_SKIP_CHECKS="999999999"` and `-b 64 -ub 64` guarantees stable prefill execution under 1.8s per slice.
- **Generation Throughput**:
  - **Prompt Processing**: **19.84 tokens/sec** (747 tokens in 37.6s)
  - **Token Generation**: **15.00 tokens/sec** (24 tokens in 1.6s)

### 2. Dual Silicon Architecture Production Verification
| Target Device | SoC & GPU Architecture | Model Architecture | Precision | Prompt Processing | Token Generation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Samsung Galaxy S25** | Snapdragon 8 Elite (Adreno 830) | **Moondream2 1.8B** | Text f16 + ViT f16 | **19.84 tok/s** | **15.00 tok/s** | **Production Verified** |
| **Samsung Galaxy S21 5G** | Exynos 2100 (Mali-G78 MP14) | SmolVLM-500M-Instruct | Q4_K_M + Q8_0 mmproj | **14.28 tok/s** | **12.65 tok/s** | **Production Verified** |
| **Samsung Galaxy A35 5G** | Exynos 1380 (Mali-G68 MP5) | SmolVLM-500M-Instruct | Q4_K_M + Q8_0 mmproj | **5.67 tok/s** | **5.47 tok/s** | **Production Verified** |

### 3. Empirical Visual QA Verification
- **Geometric Reasoning (`test_shapes_224x224.png`)**:
  - Prompt: *"Describe the colors and geometric shapes visible in this image."*
  - Output: *"The image features a white background with three distinct geometric shapes: two triangles and one rectangle..."* (14.97 tok/s, 0 errors).
- **Complex Photorealistic Scene (`test_elephant_gpu_step2.png`)**:
  - Prompt: *"What animal is this and what is it doing?"*
  - Output: *"The image shows a large elephant riding on top of a surfboard in the ocean."* (15.00 tok/s, Exit code 0).

### 4. Dynamic Parameter Un-Clamping & Installer Hardening
- **ZeroFlickerEngine**: Removed artificial thread and batch clamping, providing direct parameter forwarding to `VisionAdapter`.
- **Installer (`install.sh`)**: Unified wheel installation into a single `pip install "${WHEEL_FILE}"` step, preventing legacy package overwrites.

---

## Upgrade & Installation Guide

```bash
# Python (PyPI)
pip install --upgrade termux-vision

# Direct GitHub Releases Wheel Asset (v1.4.0)
pip install https://github.com/uno-km/termux-vision/releases/download/v1.4.0/termux_vision-1.4.0-py3-none-any.whl

# Node.js (npm)
npm install -g termux-vision@1.4.0
```
