# Termux-Vision: On-Device Computer Vision & Multimodal VLM Framework

[![PyPI](https://img.shields.io/pypi/v/termux-vision.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-vision/)
[![Python](https://img.shields.io/pypi/pyversions/termux-vision.svg?style=flat-square)](https://pypi.org/project/termux-vision/)
[![npm](https://img.shields.io/npm/v/termux-vision.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-vision)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-vision)

> **Native On-Device Computer Vision & Multimodal Vision-Language Model (VLM) Runtime for Android Termux via Direct Bionic libc & Vulkan Compute Acceleration.**  
> *Zero PRoot. Zero Virtualization. 100% Native ARMv8.2-A NEON SIMD & Hardware GPU Offloading.*

---

## 1. Overview & Key Capabilities

`termux-vision` is an enterprise-grade, on-device multimodal vision inference and spatial computing framework engineered specifically for mobile Android devices. Operating directly against Android's native Bionic libc ABI and host Vulkan compute drivers, `termux-vision` eliminates heavyweight desktop dependencies (OpenCV, TorchVision) and enables high-throughput visual question answering, OCR image captioning, and classical feature extraction directly on edge hardware.

* **Native Bionic libc ABI Direct Binding**: Runs directly inside Termux user space with zero virtualization indirection.
* **Dual Compute Acceleration**: Integrates ARMv8.2-A DotProd/FP16 SIMD vector instructions with mobile Vulkan compute shader pipelines.
* **Full-Layer GPU Offloading (-ngl 99)**: Dispatches all 99 transformer layers and cross-attention vision projections directly to device GPU VRAM (**0.00 MiB CPU mapped VRAM**).
* **Zero-Dependency Classical Vision Suite**: Native 5-stage Canny edge detector (8-directional BFS hysteresis), Sobel 3x3 filtering, 2D Integral Images, and Haar-like face candidate localization.

---

## 2. Installation Guide

### 2.1 Python Package Installation (PyPI)
```bash
pip install --upgrade pip setuptools wheel
pip install termux-vision
```

### 2.2 Direct GitHub Releases Wheel Asset
```bash
pip install https://github.com/uno-km/termux-vision/releases/download/v1.3.1/termux_vision-1.3.1-py3-none-any.whl
```

### 2.3 One-Line Bootstrap Installer
```bash
curl -sL https://raw.githubusercontent.com/uno-km/termux-vision/main/install.sh | bash
```

---

## 3. GPU Hardware Acceleration (`ameva-runtime`)

```bash
pip install termux-vision ameva-runtime termux-llamacpp
```

### Silicon Architecture Support Status
* **ARM Mali GPU (Mali-G78, Mali-G68, etc.)**: Production Verified & Supported (Pure GPU offloading, 0.00 MiB CPU Mapped VRAM, MMVQ tuning via `--tune-mali`).
* **Qualcomm Adreno GPU (Adreno 730 / 740 / 750 / 830)**: Under Active Development (In Progress / 개발 진행 중).
* **Samsung Xclipse GPU (Xclipse 920 / 940 - AMD RDNA)**: Under Active Development (In Progress / 개발 진행 중).

Run hardware diagnostics:
```bash
termux-vision doctor
```

---

## 4. Standardized CLI & Parameter Matrix

| Parameter | Alias | Default | Description |
| :--- | :--- | :--- | :--- |
| `-d, --device` | `-b, --backend` | `auto` | Compute acceleration backend: `auto`, `gpu`, `vulkan`, `cpu`, `vulkan-force` |
| `-i, --image` | `--image-path` | *Required* | Path to input image (`.png`, `.jpg`, `.webp`) |
| `-p, --prompt` | *N/A* | `"Describe this image"` | Multimodal text instruction query |
| `-m, --model` | *N/A* | `smolvlm-500m` | GGUF language model path or catalog identifier |
| `--mmproj` | *N/A* | *Auto-paired* | Vision projector GGUF model path (`mmproj-*.gguf`) |
| `-n, --max-tokens` | `--n-predict` | `150` | Maximum number of generated tokens |
| `-c, --ctx-size` | `--ctx` | `2048` | Context window size |
| `-t, --threads` | *N/A* | `auto` | Number of CPU execution threads |
| `-q, --quality` | *N/A* | `optimal` | 4-tier resolution preset: `fast` (384px), `optimal` (768px), `high` (1280px), `original` (1:1) |
| `--tune-mali` | *N/A* | `False` | Enable ARM Mali GPU MMVQ tuning (`GGML_VK_FORCE_MMVQ=1`) |
| `--json` | *N/A* | `False` | Emit machine-readable JSON benchmark telemetry |

### CLI Example
```bash
# GPU-Accelerated Multimodal VLM Inference
termux-vision vlm photo.jpg -d gpu --tune-mali -p "What objects are visible?"

# Classical 5-stage Canny Edge Detection
termux-vision canny photo.jpg -o edges.png --low 40 --high 120
```

---

## 5. Python SDK Quickstart

```python
import termux_vision as tv

# 1. Zero-Dependency Classical CV Filtering
image = tv.io.load_image("document.jpg")
grayscale = tv.transforms.to_grayscale(image)
edges = tv.cv.canny(grayscale, low_threshold=40, high_threshold=120)
tv.io.save_image(edges, "edges.png")

# 2. On-Device Multimodal VLM Inference
with tv.vlm.load("smolvlm-500m", device="gpu") as engine:
    result = engine.describe("document.jpg", prompt="Summarize this document.", quality="optimal")
    print(f"TPS: {result.metrics.tokens_per_second:.2f} tok/s | Output: {result.text}")
```

---

## 6. Real-World Benchmarks (SmolVLM-500M)

| Target Device | SoC / GPU | Mode | Prompt Eval | Token Generation | CPU Mapped VRAM | GPU VRAM | Speedup |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Samsung Galaxy S21 5G** | Exynos 2100 / Mali-G78 | **GPU (Vulkan)** | **14.28 tok/s** | **12.65 tok/s** | **0.00 MiB** | **1059.02 MiB** | **+58.9%** |
| Samsung Galaxy S21 5G | Exynos 2100 / 8-Core CPU | CPU (NEON) | 8.84 tok/s | 7.96 tok/s | 1059.02 MiB | 0.00 MiB | Baseline |
| **Samsung Galaxy A35 5G** | Exynos 1380 / Mali-G68 | **GPU (Vulkan)** | **5.67 tok/s** | **5.47 tok/s** | **0.00 MiB** | **1059.02 MiB** | **+55.8%** |
| Samsung Galaxy A35 5G | Exynos 1380 / 8-Core CPU | CPU (NEON) | 4.88 tok/s | 3.51 tok/s | 1059.02 MiB | 0.00 MiB | Baseline |

---

## 7. License
Licensed under the Apache-2.0 License. Copyright (c) 2026 Eunho Kim ([@uno-km](https://github.com/uno-km)) & AOSF.
