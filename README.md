# Termux-Vision

[![PyPI](https://img.shields.io/pypi/v/termux-vision.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-vision/)
[![Python](https://img.shields.io/pypi/pyversions/termux-vision.svg?style=flat-square)](https://pypi.org/project/termux-vision/)
[![npm](https://img.shields.io/npm/v/termux-vision.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-vision)
[![npm downloads](https://img.shields.io/npm/dm/termux-vision.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-vision)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-vision)

> **디바이스 리소스를 활용한 안드로이드 Termux 제로 디펜던시 온디바이스 컴퓨터 비전 & VLM 멀티모달 추론 엔진**  
> *Zero-Dependency On-Device Computer Vision & Multimodal VLM Inference Engine Utilizing Device Resources for Android Termux*

---

## 📌 Architecture & Overview

순수 ARM64 NEON 커널과 4단계 화질 프리셋(fast, optimal, high, original), 디바이스 리소스 최적화 연산을 결합하여 메모리 격리 환경에서 엣지 검출과 VLM 멀티모달 시각 추론을 실현합니다.

Eliminates heavy C++ dependencies by integrating SIMD NEON spatial image transforms with on-device VLM (Qwen2-VL, SmolVLM) multi-tier resolution presets (fast, optimal, high, original) utilizing device resources under strict memory isolation.

---

## 🚀 Installation & Quickstart

### Python (PyPI)
```bash
pip install termux-vision
```
```python
import termux_vision as tv

# 1. Zero-Dependency Spatial Filtering (0.01s ultra-fast)
img = tv.io.load_image("photo.jpg")
edges = tv.cv.canny(tv.transforms.to_grayscale(img), 40, 120)

# 2. On-Device VLM Multimodal Inference with 4-Tier Quality Presets
with tv.vlm.load("qwen2-vl-2b-q4", quality="optimal") as engine:
    res = engine.describe("photo.jpg", prompt="Describe this scene in detail.", quality="optimal")
    print(f"Generated ({res.metrics.tokens_per_second:.1f} t/s): {res.text}")

```

### Node.js / TypeScript (npm)
```bash
npm install termux-vision
```
```typescript
import tv from 'termux-vision';

// 1. Diagnostics & Hardware Probe
const doc = tv.doctor(true);
console.log(`Vulkan GPU: ${doc.vulkan.status} | RAM: ${doc.hardware.availableRamMb} MB`);

// 2. Multimodal VLM Inference with Quality Preset
const engine = await tv.load({ modelId: 'qwen2-vl-2b-q4', contextLimit: 4096 });
const result = await engine.describe('photo.jpg', { quality: 'optimal', maxTokens: 300 });
console.log(`[${result.metrics.backend.toUpperCase()}] ${result.text}`);
engine.close();

```

---

## 📖 Official Documentation & Benchmarks
- [Official Architecture & API Reference](https://uno-km.vercel.app/lib/vision/)
- [Ecosystem Metrics & Registry Stats](https://uno-km.vercel.app/foundation/metrics)
- [AMEVA Open-Source Foundation Portal](https://uno-km.vercel.app/foundation/index.html)

---

## 📄 License
Licensed under the Apache-2.0 License. Copyright (c) 2026 Eunho Kim ([@uno-km](https://github.com/uno-km)).
