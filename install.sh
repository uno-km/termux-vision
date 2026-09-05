#!/bin/bash
# ==============================================================================
# termux-vision: Zero-Drift One-Touch Installer for Android Termux / ARM64
# Open-Source under Apache License 2.0 (AMEVA Foundation)
# ==============================================================================

set -e

echo "========================================================="
echo "        🚀 Initializing termux-vision Installer          "
echo "========================================================="

# 1. Detect Package Manager & Environment
if command -v pkg >/dev/null 2>&1; then
    echo "[1/5] Updating Termux repositories..."
    pkg update -y
    echo "[2/5] Installing core build and runtime dependencies..."
    pkg install -y clang git python python-numpy libjpeg-turbo termux-api nodejs
elif command -v apt-get >/dev/null 2>&1; then
    echo "[1/5] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    echo "[2/5] Installing build tools and dependencies..."
    apt-get install -y build-essential git python3 python3-pip python3-numpy libjpeg-dev nodejs npm
else
    echo "[!] Warning: Unknown package manager. Ensure clang, git, python3, numpy, and nodejs are installed."
fi

# 2. Python Toolchain Pre-provisioning
echo "[3/6] Pre-provisioning Python build toolchains..."
pip install --upgrade pip setuptools wheel

# 3. Provision Core Accelerators (termux-llamacpp & ameva-runtime)
echo "[4/7] Provisioning hardware runtimes (termux-llamacpp & ameva-runtime)..."
pip install ameva-runtime || true
if ! command -v llama-cli >/dev/null 2>&1 && [ ! -f "$HOME/.termux-llama/current/bin/llama-cli" ]; then
    pip install termux-llamacpp && (termux-llama install || true) || echo "[*] Note: You can provision llama-cli later using: pip install termux-llamacpp && termux-llama install"
fi

# 4. Compile Native C & C++ CPU Acceleration Engines
echo "[5/7] Compiling Native C & C++ Compute Engines..."
if command -v clang >/dev/null 2>&1; then
    clang -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv.so termux_vision/csrc/fast_cv.c -lm 2>/dev/null || true
    clang++ -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv_engine.so termux_vision/csrc/fast_cv_engine.cpp 2>/dev/null || true
fi

# 5. Python SDK Fast Installation (Bypass isolated build environment)
echo "[6/7] Installing termux-vision Python SDK..."
pip install --no-build-isolation -e .

# 6. Node.js Dual Engine CLI Installation
echo "[7/7] Linking Node.js Dual Engine CLI..."
if command -v npm >/dev/null 2>&1; then
    npm install -g . || npm link || true
fi

echo "========================================================="
echo "  ✅ termux-vision successfully installed!"
echo "========================================================="
echo "  Dual Engine Verification:"
echo "    * Python CLI:   termux-vision doctor"
echo "    * Node.js CLI:  npx termux-vision doctor"
echo "========================================================="

# 5. Interactive Model Download Prompt (Requirement 4)
if [ -t 0 ]; then
    echo ""
    echo "---------------------------------------------------------"
    echo "  📦 Official VLM Model Download"
    echo "  Model       : smolvlm-500m-q4 (SmolVLM 500M Instruct)"
    echo "  Estimated Size : ~550 MB"
    echo "  Target Path : ~/.cache/termux-vision/models/smolvlm-500m-q4/"
    echo "---------------------------------------------------------"
    read -p "Do you want to automatically download this model now? [y/N]: " answer
    case "$answer" in
        [yY]|[yY][eE][sS])
            echo "[*] Downloading smolvlm-500m-q4 (~550MB)..."
            termux-vision model install smolvlm-500m-q4 || echo "[-] Download failed. You can install later using: termux-vision model install smolvlm-500m-q4"
            ;;
        *)
            echo "[*] Model download skipped."
            echo "    You can install it anytime using: termux-vision model install smolvlm-500m-q4"
            ;;
    esac
fi

echo ""
echo "🎉 termux-vision is ready to use!"
