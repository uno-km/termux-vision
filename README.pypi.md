# Termux-Vision (Python)

[![PyPI](https://img.shields.io/pypi/v/termux-vision.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-vision/)
[![Python](https://img.shields.io/pypi/pyversions/termux-vision.svg?style=flat-square)](https://pypi.org/project/termux-vision/)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-vision)

> **안드로이드 Termux를 위한 제로 디펜던시 온디바이스 컴퓨터 비전 & VLM 멀티모달 추론 엔진**  
> *Zero-Dependency On-Device Computer Vision & Multimodal VLM Inference Engine for Android Termux*

## Installation

```bash
pip install termux-vision
```

## Quickstart

```python
import termux_vision as tv
img = tv.io.load_image("photo.jpg")
edges = tv.cv.canny(tv.transforms.to_grayscale(img), 40, 120)
with tv.vlm.load("qwen2-vl-2b-q4", quality="optimal") as engine:
    res = engine.describe("photo.jpg", prompt="Describe this scene in detail.", quality="optimal")
    print(f"Generated ({res.metrics.tokens_per_second:.1f} t/s): {res.text}")
```

## Description
Eliminates heavy C++ dependencies by integrating SIMD NEON spatial image transforms with on-device VLM (Qwen2-VL, SmolVLM) multi-tier resolution presets (fast, optimal, high, original) and Vulkan GPU acceleration under strict memory isolation.

## Documentation
- [Official Documentation & API Reference](https://uno-km.vercel.app/lib/vision/)
- [GitHub Repository](https://github.com/uno-km/termux-vision)

## License
Apache-2.0 License. Copyright (c) 2026 Eunho Kim (@uno-km).
