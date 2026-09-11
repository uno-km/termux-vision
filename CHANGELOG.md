# Changelog

All notable changes to termux-vision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.1] - 2026-09-07

### Added
- Official GitHub Release v1.3.1 asset distribution with verified SHA-256 checksums.
- Dynamic shields badge integration for PyPI and npm.

### Changed
- Bumped version to 1.3.1 across pyproject.toml, package.json, installer.py, install.sh, and documentation portals.

## [1.3.0] - 2026-09-07

### Added
- **Universal Parameter Suite & Sibling Alignment**: Full parameterization (`-d/--device`, `-b/--backend`, `-i`, `-p`, `-m`, `--mmproj`, `-n`, `-c`, `-t`, `-W`, `-H`, `--image-size`, `-q`, `--tune-mali`, `--json`) matching official ecosystem CLI standards.
- **ARM Mali GPU Acceleration (Production Verified)**: Full 99-layer Vulkan SPIR-V offloading on ARM Mali-G78 (Galaxy S21) and Mali-G68 (Galaxy A35), achieving pure GPU execution with 0.00 MiB CPU Mapped VRAM.
- **Mali MMVQ Optimization Kernel**: `--tune-mali` flag enabling `GGML_VK_FORCE_MMVQ=1` for Mali TBDR tile-cache alignment.
- **Real-Device Benchmarks**: Galaxy S21 (12.65 tok/s, +58.9% over CPU baseline) and Galaxy A35 (5.47 tok/s, +55.8% over CPU baseline).
- **Dynamic Installer & Asset Provisioner**: `install.sh` and `termux_vision/installer.py` resolving dynamic GitHub Releases candidate endpoints with SHA-256 integrity verification.
- **Architecture Roadmap**: Qualcomm Adreno and Samsung Xclipse acceleration targets defined as Under Active Development.

---

## [1.2.0] - 2026-09-07

### Added
- Direct integration with `VisionAdapter` from `ameva_runtime.adapters` SSOT.
- Enforced strict E001 Fail-Fast on explicit Vulkan/GPU acceleration requests.
- Full English localization of diagnostic logs, Canny edge detection bridge, and VLM loaders.

---

## [1.1.4] - 2026-09-05

### Changed
- Resolved Node.js doctor `@ameva/runtime` module require preventing runtime lookup errors.
- Aligned backend docstrings, install script dependencies, and subprocess environment bindings.

---

## [1.1.3] - 2026-09-05

### Changed
- Migrated hardware acceleration dependency to unified `ameva-runtime>=2.0.0` and `@ameva/runtime>=2.0.0`.
- Fixed Doctor Vulkan driver discovery keys (`loader_detected`, `driver_file_detected`).
- Standardized VLM and OpenCV Canny acceleration bridge.

---

## [1.1.1] - 2026-09-02

### Added
- **ConvBlock Hardening**: Added explicit warnings.warn for uncalibrated random weights and is_trained property.
- **Multimodal Pipeline**: Depthwise separable convolution layers for memory-constrained edge devices.

### Cleaned
- Purged legacy 1.0.0.tgz tarball, .egg-info, and orphan .pyc files from source tree.

### Verification
- **Unit Tests**: 70 / 70 passed with 100% assertion coverage.
