# Termux-Vision Release Notes

**Version:** v1.3.1  
**Release Date:** 2026-09-07  
**License:** Apache-2.0  

---

## Key Highlights in v1.3.1 (2026-09-07)

### 1. Release Asset Verification & Distribution
- Prebuilt release wheel assets published to GitHub Releases (`v1.3.1`) with cryptographic SHA-256 validation.
- Live deployment confirmed across official registries:
  - **PyPI**: `pip install termux-vision==1.3.1`
  - **NPM**: `npm install -g termux-vision@1.3.1`
  - **GitHub Releases Wheel**: `termux_vision-1.3.1-py3-none-any.whl`

### 2. ARM Mali GPU Acceleration (Production Verified)
- 99-layer Vulkan GPU offloading on Samsung Galaxy S21 5G (Mali-G78 MP14) and Galaxy A35 5G (Mali-G68 MP5).
- Pure GPU VRAM execution: **0.00 MiB CPU Mapped VRAM**, completely eliminating CPU host-mapping bottlenecks.
- Generation throughput speedup:
  - **Galaxy S21 5G**: 14.28 prompt tok/s, **12.65 generation tok/s** (+58.9% faster than CPU).
  - **Galaxy A35 5G**: 5.67 prompt tok/s, **5.47 generation tok/s** (+55.8% faster than CPU).

### 3. Dynamic Installer & Universal CLI Sibling Parity
- Universal dynamic bootstrap installer (`install.sh`) with candidate endpoint resolution.
- Standardized CLI flags: `-d, --device`, `-b, --backend` matching sibling runtimes (`termux-diffusion`, `termux-tts`).
- Full bidirectional orchestrator component adapter parity (`VisionControl.analyze()`).

### 4. Silicon Microarchitecture Roadmap
- **ARM Mali GPU**: Production Verified & Fully Supported.
- **Qualcomm Adreno GPU**: Under Active Development (개발 진행 중).
- **Samsung Xclipse GPU**: Under Active Development (개발 진행 중).

---

## Upgrade & Installation Guide

```bash
# Python (PyPI)
pip install --upgrade termux-vision

# Direct GitHub Releases Wheel Asset
pip install https://github.com/uno-km/termux-vision/releases/download/v1.3.1/termux_vision-1.3.1-py3-none-any.whl

# Node.js (npm)
npm install -g termux-vision@1.3.1
```
