# Termux-Vision Release Notes

**License:** Apache-2.0

---

## Key Highlights in v1.1.3 (2026-09-05)

### 1. Unified AMEVA Runtime Integration
- Migrated acceleration dependency to unified `ameva-runtime>=2.0.0` and `@ameva/runtime>=2.0.0`.
- Synchronized Doctor hardware probe keys (`loader_detected`, `driver_file_detected`) with zero silent fallback.
- Enforced Fail-Fast error propagation on explicit Vulkan requests (`--device vulkan`).

---

## Key Highlights in v1.1.0 (2026-09-01)

### 1. Official AMEVA Runtime Integration
- Direct dynamic integration with `ameva-runtime` for truthful hardware doctor probing, Bionic system loader inspection, and Snapdragon/Mali quirks mitigation.
- Replaced all legacy mock C++ Vulkan implementations with honest C++ CPU acceleration kernels and clean auto delegation.

### 2. Native C/C++ BFS Canny Edge Detection Engine
- Implemented complete 8-directional connected-component BFS queue for Canny Hysteresis, eliminating edge truncation bugs.
- Thread-local zero-allocation scratch buffers ensuring sub-millisecond execution times without heap fragmentation.

### 3. All-in-One One-Line Installation
- Integrated `termux-llamacpp` and `ameva-runtime` directly into core dependencies.
- Single command installation: `pip install termux-vision && termux-llama install`.

### 4. COCO-80 Standard Alignment & Dual Engine Parity
- Full 80-class mapping for TinyYOLONano detector preventing channel shape mismatch.
- Standalone pure-JS Canny/Sobel/NMS filters for full Node.js operational autonomy.

---

## Upgrade Guide

```bash
# Python
pip install --upgrade termux-vision

# Node.js
npm install -g termux-vision@latest
```
