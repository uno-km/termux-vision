# termux-vision v1.4.1: Pure CPU Lightweight Architecture & Real-Device Multimodal VLM Stabilization

We are pleased to announce the release of **`termux-vision` v1.4.1**, an enterprise-grade on-device computer vision and multimodal vision-language model (VLM) framework designed for Android Termux and edge computing devices.

This release establishes a **pure CPU lightweight architecture**, decouples heavy GPU runtime dependencies into a modular structure, and delivers verified physical device multimodal inference capabilities across ARM64 silicon.

---

## Key Highlights & Architecture Upgrades

### 1. Pure CPU Lightweight Architecture Decoupling
* **Zero Heavy Dependencies**: Removed hard build-time dependency on `ameva-runtime` from the core distribution wheel and npm package.
* **Ultra-Compact Footprint**: Reduced package size to **~102 KB**, enabling instant installation over standard `pip install termux-vision` and `npm install termux-vision` without complex native build toolchains.
* **Modular GPU Path**: Vulkan GPU hardware acceleration remains available as an optional extension via `termux-vision-vulkan-android-arm64.tar.gz`.

### 2. Autonomous VLM Context Scaling (`-c 2048`)
* **Elimination of Context Overflow**: Resolved the context boundary issue where SmolVLM-500M ViT patch tokenization (1,139 image tokens) exceeded the legacy 1024 token limit.
* **Default Window Expansion**: Default context window is now calibrated to **2048 tokens**, enabling end-to-end multimodal image reasoning out-of-the-box.
* **CLI Parameter Accessibility**: Added explicit `-c, --ctx-size, --ctx` CLI argument to `termux-vision vlm` for full runtime flexibility.

### 3. Real-Device Physical Validation Scorecard (Ground Truth)
All metrics measured on physical, unrooted Android hardware under standard Termux user space with pure CPU execution (ARMv8.2-A NEON SIMD, 4 execution threads):

| Device | SoC Architecture | Model Architecture | Prompt Processing | Token Generation | Peak RAM | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Samsung Galaxy S25** | Snapdragon 8 Elite (Oryon CPU) | SmolVLM-500M-Instruct (Q4_K_M) | **19.3 tok/s** | **22.6 ~ 37.7 tok/s** | 421 MiB | **PASS (E2E Scene Reasoning)** |
| **Samsung Galaxy S21 5G** | Exynos 2100 (Cortex-X1/A78) | SmolVLM-500M-Instruct (Q4_K_M) | **22.3 tok/s** | **46.1 tok/s** | 421 MiB | **PASS (E2E Dolphin Identification)** |
| **Samsung Galaxy A35 5G** | Exynos 1380 (Cortex-A78/A55) | SmolVLM-500M-Instruct (Q4_K_M) | **3.1 tok/s** | **4.5 tok/s** | 421 MiB | **PASS (E2E Bear Illustration Reasoning)** |
| **Samsung Galaxy S20** | Snapdragon 865 (Kryo 585) | Classical Canny Edge Detection | *674.51 ms* | — | Low (<50MB) | **PASS (High-Hysteresis Edge Map)** |

---

## Distribution Packages & Verified Checksums

* **PyPI / Wheel**: `termux_vision-1.4.1-py3-none-any.whl`
* **Source Distribution**: `termux_vision-1.4.1.tar.gz`
* **NPM Tarball**: `termux-vision-1.4.1.tgz`
* **Optional Vulkan Binary**: `termux-vision-vulkan-android-arm64.tar.gz`

All distribution files are published with cryptographic SHA-256 validation signatures in the GitHub Release and local `releases/` repository directory.

---

## Quick Installation

### Python (PyPI)
```bash
pip install --upgrade pip
pip install termux-vision
```

### Direct Release Wheel
```bash
pip install https://github.com/uno-km/termux-vision/releases/download/v1.4.1/termux_vision-1.4.1-py3-none-any.whl
```

### Node.js (npm)
```bash
npm install -g termux-vision
```

---

**License**: Apache License 2.0  
**Copyright**: (c) 2026 Eunho Kim (@uno-km) & AMEVA Open-Source Foundation (AOSF)
