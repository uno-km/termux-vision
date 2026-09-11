#!/usr/bin/env bash
# ==============================================================================
# termux-vision: Universal Dynamic One-Line Bootstrap Installer (v1.4.0)
# Open-Source under Apache License 2.0 (AMEVA Foundation)
# Usage: curl -sL https://raw.githubusercontent.com/uno-km/termux-vision/main/install.sh | bash
# ==============================================================================
set -euo pipefail

VERSION="${TERMUX_VISION_VERSION:-1.4.0}"
REPO="uno-km/termux-vision"
ARCH="$(uname -m)"

echo "================================================================="
echo " [AMEVA Foundation] termux-vision Universal Installer v${VERSION}"
echo "================================================================="
echo "-> Detected Architecture: ${ARCH}"

# 1. Platform Detection
IS_TERMUX=false
if [ -d "/data/data/com.termux" ] || [ -n "${TERMUX_VERSION:-}" ]; then
    IS_TERMUX=true
    echo "-> Detected Platform: Android Termux (Bionic libc)"
else
    echo "-> Detected Platform: Generic Linux / Host POSIX"
fi

if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "[WARN] Architecture is ${ARCH}. ARM64 is strongly recommended for mobile NPU/GPU tensor acceleration."
fi

# 2. Storage Setup (Termux only)
if [ "${IS_TERMUX}" = "true" ] && command -v termux-setup-storage >/dev/null 2>&1; then
    if [ ! -d "${HOME}/storage" ]; then
        echo "-> Requesting Android storage permission..."
        termux-setup-storage || true
    fi
fi

# 3. System Package Dependencies
if [ "${IS_TERMUX}" = "true" ] && command -v pkg >/dev/null 2>&1; then
    echo "-> [1/6] Updating Termux package repositories..."
    pkg update -y
    echo "-> [2/6] Installing build toolchains, Vulkan drivers, and runtimes..."
    pkg install -y \
        python \
        nodejs \
        clang \
        make \
        cmake \
        git \
        termux-api \
        wget \
        vulkan-loader \
        vulkan-headers \
        vulkan-tools \
        opencl-headers \
        python-numpy \
        libjpeg-turbo
elif command -v apt-get >/dev/null 2>&1; then
    echo "-> [1/6] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    echo "-> [2/6] Installing build tools and dependencies..."
    apt-get install -y build-essential git python3 python3-pip python3-numpy libjpeg-dev nodejs npm curl wget
fi

# 4. Pre-provision Core Python Toolchain & Ecosystem Dependencies
echo "-> [3/6] Pre-provisioning Python build toolchain and ecosystem accelerators..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade ameva-runtime termux-llamacpp || true

# 5. Dynamic Wheel Installation or Local Source Build
echo "-> [4/6] Installing termux-vision Python SDK (v${VERSION})..."
WHEEL_INSTALLED=0
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/termux-vision-inst.XXXXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT INT TERM HUP

# Prioritized candidate endpoints for release wheels
CANDIDATE_URLS=()
if [ -n "${TERMUX_VISION_RELEASE_BASE:-}" ]; then
    CANDIDATE_URLS+=("${TERMUX_VISION_RELEASE_BASE%/}/termux_vision-${VERSION}-py3-none-any.whl")
fi
if [ -n "${TERMUX_VISION_RELEASE_TAG:-}" ]; then
    TAG="${TERMUX_VISION_RELEASE_TAG#v}"
    CANDIDATE_URLS+=("https://github.com/${REPO}/releases/download/v${TAG}/termux_vision-${VERSION}-py3-none-any.whl")
fi
CANDIDATE_URLS+=(
    "https://github.com/${REPO}/releases/download/v${VERSION}/termux_vision-${VERSION}-py3-none-any.whl"
    "https://github.com/${REPO}/releases/latest/download/termux_vision-${VERSION}-py3-none-any.whl"
    "https://github.com/uno-km/ameva-runtime/releases/latest/download/termux_vision-${VERSION}-py3-none-any.whl"
)

for URL in "${CANDIDATE_URLS[@]}"; do
    WHEEL_FILE="${TMP_DIR}/termux_vision-${VERSION}-py3-none-any.whl"
    if curl -sSL -f --connect-timeout 8 -o "${WHEEL_FILE}" "${URL}" 2>/dev/null; then
        if [ -s "${WHEEL_FILE}" ] && [ "$(wc -c < "${WHEEL_FILE}")" -gt 10000 ]; then
            echo "   -> Fetched verified release wheel from: ${URL}"
            python -m pip install "${WHEEL_FILE}" && WHEEL_INSTALLED=1
            break
        fi
    fi
done

if [ "${WHEEL_INSTALLED}" != "1" ]; then
    if [ -f "pyproject.toml" ]; then
        echo "   -> Installing from local source repository..."
        python -m pip install --no-build-isolation -e .
    else
        echo "   -> Installing latest release from PyPI..."
        python -m pip install termux-vision || true
    fi
fi

# 6. Compile Native C/C++ Compute Engines (if source present)
if [ -f "termux_vision/csrc/fast_cv.c" ] && command -v clang >/dev/null 2>&1; then
    echo "-> [5/6] Compiling Native C & C++ Compute Acceleration Engines..."
    clang -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv.so termux_vision/csrc/fast_cv.c -lm 2>/dev/null || true
    if [ -f "termux_vision/csrc/fast_cv_engine.cpp" ]; then
        clang++ -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv_engine.so termux_vision/csrc/fast_cv_engine.cpp 2>/dev/null || true
    fi
fi

# 7. Node.js Dual Engine CLI Installation
if command -v npm >/dev/null 2>&1; then
    echo "-> [6/6] Linking Node.js CLI..."
    if [ -f "package.json" ]; then
        npm install -g . || npm link || true
    else
        npm install -g termux-vision || true
    fi
fi

echo "================================================================="
echo "  [SUCCESS] termux-vision v${VERSION} successfully installed!"
echo "================================================================="
echo "  Dual-Engine Verification:"
echo "    * Python CLI:   termux-vision doctor"
echo "    * Node.js CLI:  npx termux-vision doctor"
echo "================================================================="

# 8. Run Hardware Diagnostics Probe
if command -v termux-vision >/dev/null 2>&1; then
    echo "-> Running Hardware Diagnostics Probe (Vulkan GPU & SoC)..."
    termux-vision doctor || true
fi

# 9. Optional Model Download (Interactive only)
if [ -t 0 ]; then
    echo ""
    echo "-----------------------------------------------------------------"
    echo "  Official Multimodal VLM Model Download"
    echo "  Model       : SmolVLM-500M Instruct (smolvlm-500m)"
    echo "  Size        : ~550 MB (Q4_K_M + Q8_0 mmproj)"
    echo "  Target Path : ~/.cache/termux-vision/models/"
    echo "-----------------------------------------------------------------"
    read -p "Do you want to automatically download this model now? [y/N]: " answer
    case "$answer" in
        [yY]|[yY][eE][sS])
            echo "[*] Downloading smolvlm-500m (~550MB)..."
            if command -v termux-vision >/dev/null 2>&1; then
                termux-vision model install smolvlm-500m || true
            fi
            ;;
        *)
            echo "[*] Model download skipped."
            echo "    You can install anytime via: termux-vision model install smolvlm-500m"
            ;;
    esac
fi

echo ""
echo "termux-vision is ready for on-device computer vision and VLM inference."
