# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-27

### Added
- **Native Computer Vision Core**:
  - Pure Python/NumPy spatial filters: Canny edge detector, Sobel $3\times3$, Gaussian blur, Laplacian.
  - High-performance 2D Integral Images and box filter kernels.
  - Morphological operations: dilation, erosion, opening, closing.
  - 8-connectivity contour tracer and multi-channel color histogram analysis.
- **Object & Face Detection Engine**:
  - Haar-like Feature Cascade classifier with integral image evaluation.
  - Non-Maximum Suppression (NMS) with configurable IoU thresholds and bounding box geometry utils.
- **On-Device Neural Vision Models**:
  - Patch-based Vision Transformer (ViT) patch embedding extraction for linear sequence projection.
  - Depthwise Separable Convolution blocks for lightweight mobile inference.
  - Tiny-YOLO / YOLOv8-nano anchor-free/anchor-based prediction decoding and NMS pipeline.
- **IO & Mobile Hardware Integration**:
  - `ImageLoader` supporting JPEG, PNG, BMP, PPM, WebP with automatic EXIF orientation normalization.
  - `CameraCapture` supporting Android `termux-camera-photo` CLI and Linux V4L2 device nodes.
- **termux-train Bridge (`termux_vision.bridge`)**:
  - Zero-copy tensor converter between NumPy images and `termux_train.Tensor`.
  - `VisionPatchDataset` and `LoRAVisionHead` for direct on-device fine-tuning and classification.
- **CLI & Granular Audit Protocol**:
  - `termux-vision` command-line interface with `capture`, `detect`, and `bench` subcommands.
  - Rigorous 0-Point Baseline Granular Scoring test suite with 100.0/100.0 Grade A+ audit target.
