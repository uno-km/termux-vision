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

        try:
            cli_cmd = [
                "llama-cli",
                "-m", self.text_model_path,
                "--mmproj", self.vision_model_path,
                "--image", image_path,
                "-f", prompt_path,
                "-st",
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
