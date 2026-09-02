import os
import sys
import shutil
import platform
import subprocess
import json
import time
from typing import Dict, Any, Optional
from .. import __version__
from .. import csrc
from ..vlm.cache import ModelCacheManager

def run_doctor(probe_vulkan: bool = False, full_check: bool = False) -> Dict[str, Any]:
    """
    Runs truthful diagnostic inspection of the Android Termux runtime environment.
    - Default: Read-only environment inspection.
    - probe_vulkan: Checks driver presence and reports execution capability (Zero-Hype / Ground Truth).
    - full_check: Runs actual SHA-256 and byte-level integrity verification on installed models.
    """
    cache_mgr = ModelCacheManager()

    report = {
        "schema_version": 1,
        "client_version": __version__,
        "runtime_version": __version__,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "is_android": os.path.exists("/system/build.prop") or "ANDROID_ROOT" in os.environ
        },
        "hardware": {
            "cpu_cores": os.cpu_count() or 1,
            "total_ram_mb": None,
            "available_ram_mb": None
        },
        "vulkan": {
            "loader_detected": os.path.exists("/system/lib64/libvulkan.so") or os.path.exists("/system/lib/libvulkan.so"),
            "driver_file_detected": os.path.exists("/vendor/lib64/hw/vulkan.adreno.so") or os.path.exists("/vendor/lib64/hw/vulkan.mali.so"),
            "vulkan_loader_installed": shutil.which("vulkaninfo") is not None,
            "compute_probe_executed": probe_vulkan,
            "safe_for_vlm": None,
            "status": "unverified"
        },
        "vlm_runtime": {
            "llama_cli_available": shutil.which("llama-cli") is not None,
            "installed_models_count": 0,
            "cache_dir": cache_mgr.cache_root
        },
        "native_backends": {
            "has_c_backend": csrc.has_c_backend(),
            "c_backend_errors": csrc.get_c_backend_load_errors(),
            "cpp_backend_errors": csrc.get_cpp_backend_load_errors()
        },
        "recommended_preset": "Tier M (smolvlm-500m / 4-Threads CPU Reference)",
        "warnings": []
    }

    # RAM Inspection
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    report["hardware"]["total_ram_mb"] = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    report["hardware"]["available_ram_mb"] = int(line.split()[1]) // 1024
    except Exception:
        pass

    # Truthful Vulkan status via ameva-vulkan-runtime integration
    if probe_vulkan:
        try:
            import ameva_vulkan_runtime as avr
            if hasattr(avr, "doctor") and callable(avr.doctor):
                avr_diag = avr.doctor(full_probe=True)
            elif hasattr(avr, "doctor") and hasattr(avr.doctor, "run_doctor") and callable(avr.doctor.run_doctor):
                avr_diag = avr.doctor.run_doctor(probe_gpu=True)
            elif hasattr(avr, "run_doctor") and callable(avr.run_doctor):
                avr_diag = avr.run_doctor(probe_gpu=True)
            else:
                avr_diag = {}
            report["vulkan"]["ameva_runtime_detected"] = True
            is_avail = bool(avr.is_available()) if hasattr(avr, "is_available") and callable(avr.is_available) else False
            report["vulkan"]["status"] = "driver_detected_experimental" if is_avail else "disabled"
            dev_name = avr.get_device_name() if hasattr(avr, "get_device_name") and callable(avr.get_device_name) else "Vulkan GPU"
            report["vulkan"]["device_name"] = dev_name
            report["vulkan"]["note"] = "Hardware driver inspected via official ameva-vulkan-runtime bridge."
        except ImportError:
            report["vulkan"]["ameva_runtime_detected"] = False
            if report["vulkan"]["loader_detected"] and report["vulkan"]["driver_file_detected"]:
                report["vulkan"]["status"] = "driver_detected_experimental"
                report["vulkan"]["safe_for_vlm"] = None
                report["vulkan"]["note"] = "Hardware driver present. Install ameva-vulkan-runtime for optimized GPU compute shaders."
            else:
                report["vulkan"]["status"] = "disabled"
                report["vulkan"]["safe_for_vlm"] = False
                report["vulkan"]["note"] = "Vulkan hardware driver or loader missing. Operating on CPU reference pipeline."

    # Model count and Actual Full SHA-256 check
    installed = cache_mgr.list_installed()
    report["vlm_runtime"]["installed_models_count"] = len(installed)

    if full_check:
        report["vlm_runtime"]["models_integrity"] = {}
        for m in installed:
            mid = m["model_id"]
            report["vlm_runtime"]["models_integrity"][mid] = cache_mgr.verify_integrity(mid)

    return report
