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

try:
    from . import __version__
except Exception:
    __version__ = "1.4.0"

GITHUB_REPO = "uno-km/termux-vision"
AMEVA_RUNTIME_RELEASE_LATEST = "https://github.com/uno-km/ameva-runtime/releases/latest/download"
TERMUX_VISION_RELEASE_LATEST = f"https://github.com/{GITHUB_REPO}/releases/latest/download"


def get_prebuilt_base_url() -> str:
    """Resolve dynamic base URL for release assets."""
    if custom := os.environ.get("TERMUX_VISION_RELEASE_BASE") or os.environ.get("AMEVA_RELEASE_BASE"):
        return custom.rstrip("/")
    if custom_tag := os.environ.get("TERMUX_VISION_RELEASE_TAG") or os.environ.get("AMEVA_RELEASE_TAG"):
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        return f"https://github.com/{GITHUB_REPO}/releases/download/{tag}"
    return f"https://github.com/{GITHUB_REPO}/releases/download/v{__version__}"


def get_candidate_wheel_urls(version: Optional[str] = None) -> List[str]:
    """Resolve prioritized candidate URLs for downloading release wheel packages."""
    ver = version or __version__
    wheel_name = f"termux_vision-{ver}-py3-none-any.whl"
    urls: List[str] = []

    if custom_base := os.environ.get("TERMUX_VISION_RELEASE_BASE") or os.environ.get("AMEVA_RELEASE_BASE"):
        urls.append(f"{custom_base.rstrip('/')}/{wheel_name}")
    if custom_tag := os.environ.get("TERMUX_VISION_RELEASE_TAG") or os.environ.get("AMEVA_RELEASE_TAG"):
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/{wheel_name}")

    urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/{wheel_name}")
    urls.append(f"{TERMUX_VISION_RELEASE_LATEST}/{wheel_name}")
    urls.append(f"{AMEVA_RUNTIME_RELEASE_LATEST}/{wheel_name}")
    return urls


def download_with_progress(url: str, dest_path: Path, label: str) -> bool:
    """Download a file atomically with percentage progress reporting."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_name(f".{dest_path.name}.tmp")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"termux-vision-installer/{__version__} (Android; ARM64)"}
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