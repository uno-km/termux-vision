# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-01

### Added
- **Official AMEVA Vulkan Runtime Bridge**: Direct dynamic integration with `dev/ameva-vulkan-runtime` for truthful hardware doctor probing and driver quirks mitigation.
- **Pure-C & C++ Dual Acceleration Engines**: Native `libfast_cv.so` and `libfast_cv_engine.so` with thread-local zero-allocation scratch buffers for sub-millisecond edge filters.
- **8-Directional BFS Hysteresis Queue**: Complete 2D connected-component tracking in Canny Edge Detection guaranteeing 100% boundary continuity.
- **COCO-80 Standard Class Alignment**: Full 80-class mapping for TinyYOLONano detector preventing channel shape mismatch.
- **Auto Delegation Hardware Contract**: Default `device="auto"` parameter passing `--device auto -ngl 99` directly to `llama-cli` for hardware execution.
- **All-in-One Core Dependencies**: Integrated `termux-llamacpp` and `ameva-vulkan-runtime` directly into core dependencies for clean one-line installation.

### Changed
- Removed legacy mock Vulkan C++ implementation (`vk_cv_engine.cpp`) in favor of honest C++ CPU acceleration (`fast_cv_engine.cpp`).
- Strict Vulkan metric reporting: `metrics.backend` now validates real log telemetry from the inference process instead of assuming request parameters.
- Network stream timeouts: Added explicit 30s timeout to all model download streams preventing infinite socket blocking.

### Fixed
- Fixed single-pass Canny truncation bug where upward/leftward weak edges were discarded.
- Fixed `install.sh` native compilation target synchronization.
- Fixed Node.js scaling fallback chain to attempt both `python3` and `python` binaries.

## [1.1.0] - 2026-08-15
- Dual Engine Python and Node.js SDK initial release.
- Heuristic Haar Cascade face candidate detector.
- Model Cache Manager and GGUF VLM loader.
