# Termux-Vision

[![PyPI](https://img.shields.io/pypi/v/termux-vision.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-vision/)
[![Python](https://img.shields.io/pypi/pyversions/termux-vision.svg?style=flat-square)](https://pypi.org/project/termux-vision/)
[![npm](https://img.shields.io/npm/v/termux-vision.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-vision)
[![npm downloads](https://img.shields.io/npm/dm/termux-vision.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-vision)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-vision)

> **안드로이드 Termux를 위한 제로 디펜던시 온디바이스 컴퓨터 비전 & VLM 멀티모달 추론 엔진**  
> *Zero-Dependency On-Device Computer Vision & Multimodal VLM Inference Engine for Android Termux*

---

## Architecture & Overview

- **초고속 C/C++ CPU 비전 커널**: 8-방향 2차원 BFS Hysteresis Canny 에지 검출, Sobel 3x3, 적분 영상 필터링을 스레드 로컬 0-Allocation 스크래치 버퍼로 1ms 내에 완료.
- **AMEVA Vulkan Runtime 완전 통합**: 기기 드라이버 및 칩셋 버그(Quirks)를 자동 패치하고 `--device auto -ngl 99`로 모바일 GPU 가속 완전 위임.
- **스마트 4단계 해상도 프리셋**: `fast` (384px), `optimal` (768px), `high` (1280px), `original`로 모바일 메모리 한계 내에서 VLM 추론 최적화.
- **듀얼 엔진 지원**: Python (`pip`) 및 Node.js (`npm`) 양대 언어에서 100% 동일한 비전 파이프라인 제공.

---

## Installation & Quickstart

### One-Touch Installer (Recommended)
```bash
curl -sL https://raw.githubusercontent.com/uno-km/termux-vision/main/install.sh | bash
```

### Python (PyPI)
```bash
pip install termux-vision && termux-llama install
```
```python
import termux_vision as tv

# 1. Classical CV Filters (Sub-millisecond C/C++ Engine)
img = tv.io.load_image("photo.jpg")
edges = tv.cv.canny(tv.transforms.to_grayscale(img), 40, 120)

# 2. On-Device VLM Multimodal Inference
with tv.vlm.load("smolvlm-500m-q4", quality="optimal") as engine:
    res = engine.describe("photo.jpg", prompt="Describe this scene in detail.")
    print(f"[{res.metrics.backend.upper()}] {res.text}")
```

### Node.js / TypeScript (npm)
```bash
npm install -g termux-vision && pkg install termux-llamacpp
```
```typescript
import tv from 'termux-vision';

// 1. Diagnostics & Hardware Probe
const doc = tv.doctor(true);
console.log(`Vulkan GPU: ${doc.vulkan.status} | Cores: ${doc.hardware.cpuCores}`);

// 2. Multimodal VLM Inference
const engine = await tv.load({ modelId: 'smolvlm-500m-q4' });
const result = await engine.describe('photo.jpg', { prompt: 'What is inside this image?' });
console.log(`[${result.metrics.backend.toUpperCase()}] ${result.text}`);
engine.close();
```

---

## Official Documentation & Benchmarks
- [Official Architecture & API Reference](https://uno-km.vercel.app/lib/vision/)
- [Ecosystem Metrics & Registry Stats](https://uno-km.vercel.app/foundation/metrics)
- [AMEVA Open-Source Foundation Portal](https://uno-km.vercel.app/foundation/index.html)

---

## License
Licensed under the Apache-2.0 License. Copyright (c) 2026 Eunho Kim ([@uno-km](https://github.com/uno-km)).
