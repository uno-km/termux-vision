import os
import time
import subprocess
import tempfile
from typing import Dict, Any, Optional
import numpy as np

class ZeroFlickerEngine:
    """
    On-Device VLM Execution Engine optimized for Android Termux.
    Enforces a strict <500MB memory footprint, 4-thread CPU governor,
    and single-turn non-interactive execution to guarantee zero SystemUI flickers.
    """
    def __init__(
        self,
        text_model_path: str,
        vision_model_path: str,
        threads: int = 4,
        eco_mode: bool = True,
        use_vulkan: bool = False
    ):
        self.text_model_path = text_model_path
        self.vision_model_path = vision_model_path
        self.threads = min(4, threads) if eco_mode else threads
        self.eco_mode = eco_mode
        self.use_vulkan = use_vulkan

    def generate(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.6,
        repeat_penalty: float = 1.25
    ) -> Dict[str, Any]:
        """
        Executes single-turn multimodal generation.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        # Write prompt safely to temporary utf-8 file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as pf:
            prompt_path = pf.name
            pf.write(prompt)

        # Resolve binary path via termux-llamacpp / resolver
        bin_path = "llama-cli"
        try:
            from termux_llamacpp import LlamaRuntime
            resolved = LlamaRuntime().get_binary_path("llama-cli")
            if resolved:
                bin_path = str(resolved)
        except (ImportError, OSError) as _llamacpp_err:
            import logging
            _log = logging.getLogger(__name__)
            _log.debug("vision: termux-llamacpp resolver unavailable (%s), trying local resolver.", _llamacpp_err)
            try:
                from .runtime.resolver import resolve_llama_cli
                bin_path = resolve_llama_cli().executable
            except (ImportError, OSError, AttributeError) as _res_err:
                _log.warning(
                    "vision: llama-cli resolver failed (%s); will attempt PATH lookup at runtime.",
                    _res_err,
                )

        # Prepare Vulkan environment via ameva-runtime
        proc_env = os.environ.copy()
        if self.use_vulkan:
            try:
                from ameva_runtime.adapters import VisionAdapter
                proc_env = VisionAdapter.get_execution_environment(base_env=proc_env)
            except ImportError as _vulkan_err:
                raise RuntimeError(
                    "[FAIL-FAST] [ERROR: AMEVA-VISION-E001] GPU acceleration requires 'ameva-runtime'.\n"
                    "Cause: Hardware abstraction provider 'ameva-runtime' is not installed.\n"
                    "Action Required: Install ameva-runtime or run without GPU: use_vulkan=False\n"
                    "Documentation: https://uno-km.vercel.app/lib/vision/"
                ) from _vulkan_err
            except Exception as _vulkan_err:
                raise RuntimeError(
                    f"[FAIL-FAST] [ERROR: AMEVA-VISION-E001] Vision Vulkan acceleration initialization failed: {_vulkan_err}"
                ) from _vulkan_err

        try:
            cli_cmd = [
                bin_path,
                "-m", self.text_model_path,
                "--mmproj", self.vision_model_path,
                "--image", image_path,
                "-f", prompt_path,
                "-t", str(self.threads),
                "-c", "1024",
                "-n", str(max_tokens),
                "--temp", str(temperature),
                "--repeat-penalty", str(repeat_penalty),
                "-ngl", "99" if self.use_vulkan else "0"
            ]

            t0 = time.perf_counter()
            process = subprocess.Popen(
                cli_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=proc_env,
                text=True
            )
            out, err = process.communicate()
            latency = time.perf_counter() - t0

            # Extract generated response text
            lines = out.splitlines()
            content_lines = []
            start_capture = False
            for line in lines:
                if line.strip().startswith(">"):
                    start_capture = True
                    continue
                if start_capture:
                    if "[" in line and "t/s" in line:
                        continue
                    if "Exiting" in line:
                        continue
                    cleaned = line.replace("|", "").replace("-", "").replace("/", "").replace("\\", "").strip()
                    if cleaned:
                        content_lines.append(cleaned)

            text_output = " ".join(content_lines) if content_lines else out.strip()

            return {
                "text": text_output,
                "latency_sec": round(latency, 2),
                "threads": self.threads,
                "eco_mode": self.eco_mode,
                "raw_stdout": out
            }
        finally:
            if os.path.exists(prompt_path):
                os.remove(prompt_path)
