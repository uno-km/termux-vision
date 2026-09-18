"""
Automated Dynamic Installer and Asset Provisioner for termux-vision.
Resolves dynamic GitHub Releases endpoints and provisions on-device models and runtimes.
"""
import os
import sys
import shutil
import urllib.request
from pathlib import Path
from typing import List, Optional

def _resolve_package_version() -> Optional[str]:
    """Dynamically resolve current installed package version without static fallback."""
    try:
        from . import __version__
        if __version__:
            return __version__
    except Exception:
        pass
    try:
        import importlib.metadata
        return importlib.metadata.version("termux-vision")
    except Exception:
        return None


GITHUB_REPO = "uno-km/termux-vision"
TERMUX_VISION_RELEASE_LATEST = f"https://github.com/{GITHUB_REPO}/releases/latest/download"


def get_prebuilt_base_url() -> str:
    """Resolve dynamic base URL for release assets."""
    if custom := os.environ.get("TERMUX_VISION_RELEASE_BASE") or os.environ.get("AMEVA_RELEASE_BASE"):
        return custom.rstrip("/")
    if custom_tag := os.environ.get("TERMUX_VISION_RELEASE_TAG") or os.environ.get("AMEVA_RELEASE_TAG"):
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        return f"https://github.com/{GITHUB_REPO}/releases/download/{tag}"
    ver = _resolve_package_version()
    if ver:
        return f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}"
    return TERMUX_VISION_RELEASE_LATEST


def get_candidate_wheel_urls(version: Optional[str] = None) -> List[str]:
    """Resolve prioritized candidate URLs for downloading release wheel packages."""
    ver = version or _resolve_package_version()
    wheel_name = f"termux_vision-{ver}-py3-none-any.whl" if ver else "termux_vision-py3-none-any.whl"
    urls: List[str] = []

    # Tier 1: Explicit environment overrides
    if custom_base := os.environ.get("TERMUX_VISION_RELEASE_BASE") or os.environ.get("AMEVA_RELEASE_BASE"):
        urls.append(f"{custom_base.rstrip('/')}/{wheel_name}")
    if custom_tag := os.environ.get("TERMUX_VISION_RELEASE_TAG") or os.environ.get("AMEVA_RELEASE_TAG"):
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/{wheel_name}")

    # Tier 2: GitHub Releases latest canonical endpoint (Zero-Hardcoding SSOT)
    urls.append(f"{TERMUX_VISION_RELEASE_LATEST}/{wheel_name}")
    urls.append(f"{TERMUX_VISION_RELEASE_LATEST}/termux-vision-vulkan-android-arm64.tar.gz")

    # Tier 3: Installed package dynamic version matching
    if ver:
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/{wheel_name}")
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/termux-vision-vulkan-android-arm64.tar.gz")

    return urls


def download_with_progress(url: str, dest_path: Path, label: str) -> bool:
    """Download a file atomically with percentage progress reporting."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_name(f".{dest_path.name}.tmp")
    ver = _resolve_package_version() or "latest"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"termux-vision-installer/{ver} (Android; ARM64)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as out_f:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                if total > 0 and sys.stdout.isatty():
                    pct = (downloaded / total) * 100
                    sys.stdout.write(f"\r  [{label}] {pct:.1f}% ({downloaded / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB)")
                    sys.stdout.flush()

        if sys.stdout.isatty() and total > 0:
            sys.stdout.write("\n")
            sys.stdout.flush()

        if temp_path.exists() and temp_path.stat().st_size > 0:
            if dest_path.exists():
                dest_path.unlink()
            temp_path.rename(dest_path)
            return True
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        sys.stderr.write(f"[-] Download failed from {url}: {exc}\n")
        return False

    return False


def ensure_llamacpp_runtime(auto_yes: bool = False, interactive: bool = True) -> bool:
    """
    Verify termux-llamacpp installation, prompt user for approval or update if version differs,
    and enforce installing the latest version. Supports non-interactive flags (-y, --all).
    """
    import subprocess
    import json

    current_ver = None
    try:
        import importlib.metadata
        current_ver = importlib.metadata.version("termux-llamacpp")
    except Exception:
        pass

    latest_ver = None
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/termux-llamacpp/json",
            headers={"User-Agent": "termux-vision-installer"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest_ver = data.get("info", {}).get("version")
    except Exception:
        pass

    target_ver_str = f"v{latest_ver}" if latest_ver else "최신 버전"

    if not current_ver:
        sys.stderr.write("  [Notice] 'termux-llamacpp'가 현재 설치되어 있지 않습니다.\n")
        if auto_yes:
            sys.stderr.write(f"  -> 자동 승인(-y/--all) 감지: {target_ver_str}을 설치합니다...\n")
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "termux-llamacpp"]
            return subprocess.call(cmd) == 0
        elif interactive and sys.stdin.isatty():
            try:
                ans = input("지금 termux-llamacpp 설치가 필요합니다. 설치하시겠습니까? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = "n"
            if ans in ("y", "yes"):
                sys.stderr.write(f"  -> {target_ver_str} 설치 중...\n")
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "termux-llamacpp"]
                return subprocess.call(cmd) == 0
            else:
                sys.stderr.write("  [경고] 사용자가 설치를 건너뛰었습니다. VLM 멀티모달 기능을 사용할 수 없습니다.\n")
                return False
        else:
            return False

    # Already installed, check version discrepancy
    if latest_ver and current_ver != latest_ver:
        if auto_yes:
            sys.stderr.write(f"  -> 자동 승인(-y/--all) 감지: termux-llamacpp (v{current_ver}) -> v{latest_ver} 업데이트 중...\n")
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "termux-llamacpp"]
            return subprocess.call(cmd) == 0
        elif interactive and sys.stdin.isatty():
            try:
                ans = input(f"현재 termux-llamacpp 버전(v{current_ver})이 최신 버전(v{latest_ver})과 다릅니다. 업데이트하시겠습니까? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = "n"
            if ans in ("y", "yes"):
                sys.stderr.write(f"  -> termux-llamacpp 최신 버전(v{latest_ver})으로 업데이트 중...\n")
                cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "termux-llamacpp"]
                return subprocess.call(cmd) == 0
            else:
                sys.stderr.write(f"  -> 현재 설치된 v{current_ver} 버전을 유지합니다.\n")
                return True

    return True