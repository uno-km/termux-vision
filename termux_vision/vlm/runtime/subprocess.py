import os
import sys
import time
import subprocess
import tempfile
import signal
from typing import Dict, Any, Optional, Sequence
from dataclasses import replace

from ..manifest import ModelManifest
from ..adapters import get_adapter
from ..result import VLMResult, InferenceMetrics
from ...errors import (
    SubprocessRuntimeError,
    VulkanNotAvailableError,
    GpuExecutionError
)

def _is_vulkan_failure(exc: Exception) -> bool:
    """Checks if an exception indicates a Vulkan driver/GPU failure."""
    text = str(exc).lower()
    markers = (
        "vulkan",
        "vk_error",
        "device lost",
        "failed to initialize gpu",
        "no vulkan device",
        "gpu backend",
        "vkcreateinstance",
        "vkcreatedevice",
        "ggml_vulkan",
        "vulkan loader"
    )
    return any(marker in text for marker in markers)

class SubprocessVLMRuntime:
    """
    Supervised native inference runner using real llama-cli executable.
    Provides process-group isolation on POSIX, strict hardware mode enforcement,
    and truthful metrics reporting.
    """
    def __init__(
        self,
        manifest: ModelManifest,
        model_dir: str,
        executable: str,
        threads: int = 4,
        backend: str = "cpu",
        timeout_sec: int = 120,
        fallback: bool = True,
        custom_text_model: Optional[str] = None,
        custom_vision_model: Optional[str] = None,
        context_limit: Optional[int] = None,
        ngl: Optional[int] = None
    ):
        self.manifest = manifest
        self.model_dir = model_dir
        self.executable = executable
        self.threads = threads
        self.backend = backend.lower().strip()
        self.timeout_sec = timeout_sec
        self.fallback = fallback
        self.adapter = get_adapter(manifest.adapter)
        self.context_limit = context_limit or manifest.context_limit
        self.custom_ngl = ngl

        # Artifact resolution
        if custom_text_model and os.path.isfile(custom_text_model):
            self.text_model_path = custom_text_model
        else:
            self.text_model_path = None

        if custom_vision_model and os.path.isfile(custom_vision_model):
            self.vision_model_path = custom_vision_model
        else:
            self.vision_model_path = None

        for a in manifest.artifacts:
            p = os.path.join(model_dir, a.filename)
            if os.path.exists(p):
                if a.role == "language_model" and not self.text_model_path:
                    self.text_model_path = p
                elif a.role == "vision_projector" and not self.vision_model_path:
                    self.vision_model_path = p

        # Fallback to search directory for any .gguf if custom
        if not self.text_model_path or not self.vision_model_path:
            if os.path.isdir(model_dir):
                files = os.listdir(model_dir)
                if not self.text_model_path:
                    texts = [os.path.join(model_dir, f) for f in files if f.endswith(".gguf") and not ("mmproj" in f.lower() or "vision" in f.lower())]
                    if texts:
                        self.text_model_path = texts[0]
                if not self.vision_model_path:
                    visions = [os.path.join(model_dir, f) for f in files if f.endswith(".gguf") and ("mmproj" in f.lower() or "vision" in f.lower())]
                    if visions:
                        self.vision_model_path = visions[0]

        if not self.text_model_path or not self.vision_model_path:
            raise FileNotFoundError(
                f"Missing required VLM artifacts in '{model_dir}' for '{manifest.model_id}'. "
                f"Found: text={self.text_model_path}, vision={self.vision_model_path}. "
                f"VLM models require both a text .gguf and a vision projector mmproj-*.gguf."
            )

    def _execute_once(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.2,
        target_backend: str = "cpu",
        **kwargs
    ) -> VLMResult:
        system_prompt = kwargs.get("system_prompt")
        top_p = kwargs.get("top_p")
        top_k = kwargs.get("top_k")
        repeat_penalty = kwargs.get("repeat_penalty", 1.2)
        presence_penalty = kwargs.get("presence_penalty")
        frequency_penalty = kwargs.get("frequency_penalty")
        seed = kwargs.get("seed")
        stop_tokens = kwargs.get("stop_tokens")

        if hasattr(self.adapter, "format_prompt"):
            try:
                formatted_prompt = self.adapter.format_prompt(prompt, system_prompt=system_prompt)
            except TypeError:
                formatted_prompt = self.adapter.format_prompt(prompt)
        else:
            formatted_prompt = f"<image>\nUser: {prompt}\nAssistant:"

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as pf:
            prompt_file = pf.name
            pf.write(formatted_prompt)

        if self.custom_ngl is not None:
            ngl_val = str(self.custom_ngl)
        else:
            ngl_val = "99" if target_backend == "vulkan" else "0"

        cli_cmd = [
            self.executable,
            "-m", str(self.text_model_path),
            "--mmproj", str(self.vision_model_path),
            "--image", str(image_path),
            "-f", str(prompt_file),
            "-st",
            "-t", str(self.threads),
            "-c", str(self.context_limit),
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "-ngl", ngl_val
        ]

        if repeat_penalty is not None:
            cli_cmd.extend(["--repeat-penalty", str(repeat_penalty)])
        if top_p is not None:
            cli_cmd.extend(["--top-p", str(top_p)])
        if top_k is not None:
            cli_cmd.extend(["--top-k", str(top_k)])
        if presence_penalty is not None:
            cli_cmd.extend(["--presence-penalty", str(presence_penalty)])
        if frequency_penalty is not None:
            cli_cmd.extend(["--frequency-penalty", str(frequency_penalty)])
        if seed is not None:
            cli_cmd.extend(["-s", str(seed)])
        if stop_tokens:
            for st in stop_tokens:
                cli_cmd.extend(["-r", str(st)])

        popen_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace"
        }
        if os.name == "posix":
            popen_kwargs["start_new_session"] = True

        try:
            t0 = time.perf_counter()
            process = subprocess.Popen(cli_cmd, **popen_kwargs)

            try:
                out, err = process.communicate(timeout=self.timeout_sec)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                        process.wait(timeout=2)
                    except (subprocess.TimeoutExpired, ProcessLookupError):
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                else:
                    process.kill()
                raise SubprocessRuntimeError(f"VLM inference timed out after {self.timeout_sec}s")

            if process.returncode != 0:
                err_detail = err.strip() or out.strip()
                if process.returncode in (-9, 137, 247):
                    raise SubprocessRuntimeError(
                        f"VLM inference process was terminated by system (OOM / LowMemoryKiller / SIGKILL, exit code {process.returncode}).\n"
                        f"[Action Recommendation] Use a smaller model (e.g. smolvlm-500m-q4), reduce thread count (-t 2), lower max tokens, or close background apps."
                    )
                raise SubprocessRuntimeError(
                    f"llama-cli exited with returncode {process.returncode}: {err_detail}"
                )

            total_ms = (time.perf_counter() - t0) * 1000.0

            lines = out.splitlines()
            content_lines = []
            start_capture = False
            actual_tps = None

            for line in lines:
                if line.strip().startswith(">"):
                    start_capture = True
                    continue
                if start_capture:
                    if "[" in line and "t/s" in line:
                        try:
                            parts = line.split("Generation:")
                            if len(parts) > 1:
                                actual_tps = float(parts[1].replace("t/s", "").replace("]", "").strip())
                        except Exception:
                            pass
                        continue
                    if "Exiting" in line or "main: image" in line:
                        continue
                    cleaned = line.replace("|", "").replace("-", "").replace("/", "").replace("\\", "").strip()
                    if cleaned:
                        content_lines.append(cleaned)

            text_output = " ".join(content_lines) if content_lines else out.strip()
            word_count = len(text_output.split())

            metrics = InferenceMetrics(
                backend=target_backend,
                model_id=self.manifest.model_id,
                load_ms=None,
                vision_ms=0.0,
                decode_ms=round(total_ms, 2),
                tokens_per_second=actual_tps,
                peak_rss_mb=None
            )

            return VLMResult(
                text=text_output,
                finish_reason="stop",
                input_tokens=None,
                output_tokens=None,
                word_count=word_count,
                metrics=metrics,
                warnings=()
            )
        finally:
            if os.path.exists(prompt_file):
                os.remove(prompt_file)

    def execute(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.2,
        **kwargs
    ) -> VLMResult:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        try:
            try:
                return self._execute_once(
                    image_path,
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    target_backend=self.backend,
                    **kwargs
                )
            except TypeError:
                return self._execute_once(
                    image_path,
                    prompt,
                    max_tokens,
                    temperature,
                    self.backend
                )
        except Exception as exc:
            if self.backend == "vulkan":
                if self.fallback:
                    try:
                        try:
                            fallback_res = self._execute_once(
                                image_path,
                                prompt,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                target_backend="cpu",
                                **kwargs
                            )
                        except TypeError:
                            fallback_res = self._execute_once(
                                image_path,
                                prompt,
                                max_tokens,
                                temperature,
                                "cpu"
                            )
                        return replace(
                            fallback_res,
                            warnings=fallback_res.warnings + (f"Vulkan execution failed; retried on CPU: {exc}",)
                        )
                    except Exception as cpu_exc:
                        raise SubprocessRuntimeError(f"Both Vulkan and CPU fallback execution failed: {cpu_exc}") from exc
                else:
                    raise VulkanNotAvailableError(reason=str(exc)) from exc
            raise

    def close(self):
        pass
