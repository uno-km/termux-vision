# Termux-Vision Release Notes

**Version:** v1.3.0  
**Release Date:** 2026-09-07  
**License:** Apache-2.0  

---

## Key Highlights in v1.3.0 (2026-09-07)

### 1. Universal Parameter Suite & Sibling Ecosystem Parity
- Standardized CLI flags: `-d, --device, -b, --backend` (`auto`, `gpu`, `vulkan`, `cpu`, `vulkan-force`).
- Input and model controls: `-i/--image`, `-p/--prompt`, `-m/--model`, `--mmproj`, `-n/--max-tokens`, `-c/--ctx-size`, `-t/--threads`.
- Dynamic vision scaling: `-W/--width`, `-H/--height`, `--image-size` (e.g. 224x224, 384x384), and 4-tier presets (`fast`, `optimal`, `high`, `original`).

### 2. ARM Mali GPU Acceleration (Production Verified)
- 99-layer Vulkan GPU offloading on Samsung Galaxy S21 5G (Mali-G78 MP14) and Galaxy A35 5G (Mali-G68 MP5).
- Pure GPU VRAM execution: **0.00 MiB CPU Mapped VRAM**, completely eliminating CPU host-mapping bottlenecks.
- Generation throughput speedup:
  - **Galaxy S21 5G**: 14.28 prompt tok/s, **12.65 generation tok/s** (+58.9% faster than CPU).
  - **Galaxy A35 5G**: 5.67 prompt tok/s, **5.47 generation tok/s** (+55.8% faster than CPU).

### 3. Dynamic Installer & Release Asset Distribution
- Universal dynamic bootstrap installer (`install.sh`) removing all hardcoded versions and URLs.
- Automated release candidate endpoint resolution via `termux_vision/installer.py`.
- Prebuilt release wheel assets published with SHA-256 cryptographic verification.

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
pip install https://github.com/uno-km/termux-vision/releases/download/v1.3.0/termux_vision-1.3.0-py3-none-any.whl

# Node.js (npm)
npm install -g termux-vision@1.3.0
```
