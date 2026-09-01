# Termux-Vision v1.1.0 Release Notes

**Release Date:** 2026-09-01  
**Architecture:** Dual-Engine (Python & Node.js/TypeScript) for Android Termux & ARM64  
**License:** Apache-2.0

---

## Key Highlights in v1.1.0

### 1. Official AMEVA Vulkan Runtime Integration
- Direct dynamic integration with `dev/ameva-vulkan-runtime` for truthful hardware doctor probing, Bionic system loader inspection, and Snapdragon/Mali quirks mitigation.
- Replaced all legacy mock C++ Vulkan implementations with honest C++ CPU acceleration kernels and clean auto delegation.

### 2. Native C/C++ BFS Canny Edge Detection Engine
- Implemented complete 8-directional connected-component BFS queue for Canny Hysteresis, eliminating edge truncation bugs.
- Thread-local zero-allocation scratch buffers ensuring sub-millisecond execution times without heap fragmentation.

### 3. All-in-One One-Line Installation
- Integrated `termux-llamacpp` and `ameva-vulkan-runtime` directly into core dependencies.
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
