# Changelog

All notable changes to 	ermux-vision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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