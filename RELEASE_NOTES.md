# Release Notes - termux-vision v1.4.2

**Release Tag**: `v1.4.2`  
**Distribution Channels**: PyPI (`termux-vision`), NPM (`termux-vision`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. 100% Zero-Hardcoding Dynamic Provisioning Architecture
- **Eradicated Static Version Fallbacks**: Permanently eliminated static version strings (`1.4.0`) from `termux_vision/installer.py` and `install.sh`.
- **Unified 3-Tier Resolution Protocol**:
  1. **Tier 1 (Explicit Environment Overrides)**: Prioritizes `TERMUX_VISION_RELEASE_BASE` and `TERMUX_VISION_RELEASE_TAG`.
  2. **Tier 2 (GitHub Releases Latest Canonical SSOT)**: Directly fetches release wheels and native engine tarballs (`termux-vision-vulkan-android-arm64.tar.gz`) from `https://github.com/uno-km/termux-vision/releases/latest/download/`.
  3. **Tier 3 (Runtime Dynamic Version Resolution)**: Leverages `_resolve_package_version()` using `importlib.metadata` to bind to currently installed package version tags dynamically.
- **Dynamic HTTP User-Agent**: Replaced static user-agent headers with dynamic package version introspection (`termux-vision-installer/{ver}`).

### 2. Dual Engine Python & Node.js SSOT Synchronization
- **One-Line Bootstrap Hardening**: Upgraded `install.sh` to query the GitHub Releases API dynamically and use `pip install --upgrade termux-vision`.
- **Full Packaging Parity**: Fully aligned `pyproject.toml`, `package.json`, and `termux_vision/__init__.py` to `1.4.2`.

---

## Detailed Changelog

### Changed
- `install.sh`: Dynamic version resolution via GitHub Releases API and `--upgrade` pip provisioning.
- `termux_vision/installer.py`: Replaced static release URLs with prioritized 3-Tier candidate URL generator.
- `CHANGELOG.md`: Added release documentation for `v1.4.2`.
- Package manifests bumped to `1.4.2`.
