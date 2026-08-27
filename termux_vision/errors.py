"""
termux-vision Structured Exceptions & Dynamic User Error Guidance.
Zero-Hype & Truthful Diagnostics under Apache License 2.0.
"""

from typing import Tuple, Optional, Sequence

class TermuxVisionError(Exception):
    """Base exception for all termux-vision errors."""
    pass

class ImageDecodeError(TermuxVisionError):
    """Raised when an image file cannot be parsed or decoded."""
    def __init__(self, image_path: str, reason: str = ""):
        self.image_path = str(image_path)
        self.reason = reason
        detail = f" ({reason})" if reason else ""
        msg = (
            f"Failed to decode image from '{self.image_path}'{detail}.\n"
            f"Supported formats: JPEG, PNG, BMP, PPM, WebP."
        )
        super().__init__(msg)

class ImageEncodeError(TermuxVisionError):
    """Raised when an image cannot be encoded to disk or memory."""
    pass

class DecompressionBombError(TermuxVisionError):
    """Raised when an image exceeds safe dimensions or pixel allocation limits."""
    pass

class IncompatibleEmbeddingError(TermuxVisionError):
    """Raised when computing similarity between embeddings from different models or spaces."""
    pass

class InsufficientMemoryError(TermuxVisionError):
    """Raised when physical RAM or user budget is insufficient for model execution."""
    def __init__(self, required_mb: int, available_mb: int, message: str = ""):
        self.required_mb = required_mb
        self.available_mb = available_mb
        msg = message or f"Insufficient memory: required {required_mb}MB, available {available_mb}MB"
        super().__init__(msg)

class ModelNotFoundError(TermuxVisionError):
    """Raised when a specified model artifact is absent from on-device cache."""
    def __init__(
        self,
        message: str = "",
        model_id: Optional[str] = None,
        available_local_models: Sequence[str] = (),
        catalog_models: Sequence[str] = ()
    ):
        self.model_id = model_id
        self.available_local_models = tuple(available_local_models)
        self.catalog_models = tuple(catalog_models)

        if not message:
            parts = []
            if model_id:
                parts.append(f"Model '{model_id}' was not found locally or on remote registry.")
            else:
                parts.append("Requested model was not found.")

            if self.available_local_models:
                parts.append(
                    f"\nCurrently installed local models ({len(self.available_local_models)}):\n"
                    + "\n".join(f"  - {m}" for m in self.available_local_models)
                )
                parts.append(
                    f"\nTo run with an installed model:\n"
                    f"  termux-vision vlm <IMAGE> --model {self.available_local_models[0]}"
                )
            elif self.catalog_models:
                parts.append(
                    f"\nNo models installed locally. Available catalog presets:\n"
                    + "\n".join(f"  - {m}" for m in self.catalog_models)
                )
                parts.append(
                    f"\nInstall an official model:\n"
                    f"  termux-vision model install {self.catalog_models[0]}"
                )
            message = "\n".join(parts)

        super().__init__(message)

class NoInstalledModelsError(ModelNotFoundError):
    """Raised when no usable VLM model is installed locally."""
    def __init__(self, catalog_models: Sequence[str] = ()):
        self.catalog_models = tuple(catalog_models)
        cat_text = "\n".join(f"  - {m}" for m in sorted(self.catalog_models)) if self.catalog_models else "  (none)"
        msg = (
            "No installed VLM models were found in local cache (~/.cache/termux-vision/models).\n\n"
            "How to use VLM models:\n"
            "1. Install an official catalog model:\n"
            f"{cat_text}\n"
            f"   Example: termux-vision model install smolvlm-500m-q4\n\n"
            "2. Use custom/external ('싸제') models:\n"
            "   - Place your text model GGUF and vision projector mmproj GGUF in:\n"
            "     ~/.cache/termux-vision/models/<custom_model_name>/\n"
            "   - Or pass direct file paths:\n"
            "     termux-vision vlm <IMAGE> --model /path/to/model.gguf --mmproj /path/to/mmproj.gguf\n"
            "   (Note: VLM inference requires both a language model .gguf and a vision projector mmproj-*.gguf)"
        )
        super().__init__(message=msg, catalog_models=self.catalog_models)

class ModelSelectionRequiredError(ModelNotFoundError):
    """Raised when multiple models are installed and --model is omitted."""
    def __init__(self, installed_models: Sequence[str] = ()):
        self.installed_models = tuple(installed_models)
        models_text = "\n".join(f"  - {m}" for m in self.installed_models)
        example_model = self.installed_models[0] if self.installed_models else "MODEL_ID"
        msg = (
            f"Multiple models are installed. Please specify one with --model:\n"
            f"{models_text}\n\n"
            f"Example:\n"
            f"  termux-vision vlm <IMAGE> --model {example_model} -p \"Describe this image\""
        )
        super().__init__(message=msg, available_local_models=self.installed_models)

class ModelArtifactsMissingError(ModelNotFoundError):
    """Raised when a model entry exists but required artifacts are missing."""
    def __init__(self, model_id: str, missing_artifacts: Sequence[str] = ()):
        self.model_id = model_id
        self.missing_artifacts = tuple(missing_artifacts)
        missing_text = ", ".join(missing_artifacts)
        msg = (
            f"Model '{model_id}' is incomplete. Missing artifacts: {missing_text}\n"
            f"VLM models require both a language model (.gguf) and a vision encoder (mmproj-*.gguf).\n\n"
            f"To repair/re-download:\n"
            f"  termux-vision model remove {model_id}\n"
            f"  termux-vision model install {model_id}"
        )
        super().__init__(message=msg, model_id=model_id)

class ModelCorruptedError(TermuxVisionError):
    """Raised when downloaded or cached model fails integrity validation."""
    pass

class ModelDownloadError(TermuxVisionError):
    """Raised when downloading a model from Hugging Face or remote registry fails."""
    def __init__(self, model_source: str, reason: str = "", available_local: Sequence[str] = ()):
        self.model_source = model_source
        self.reason = reason
        self.available_local = tuple(available_local)
        
        parts = [f"Failed to download model from '{model_source}': {reason}"]
        if self.available_local:
            parts.append(
                f"\nInstalled local models available:\n"
                + "\n".join(f"  - {m}" for m in self.available_local)
                + f"\nRun with local model: termux-vision vlm <IMAGE> --model {self.available_local[0]}"
            )
        else:
            parts.append(
                "\nNo models found in local cache. You can place GGUF files in ~/.cache/termux-vision/models/ "
                "or specify explicit file paths with --model <model.gguf> --mmproj <mmproj.gguf>."
            )
        super().__init__("\n".join(parts))

class SubprocessRuntimeError(TermuxVisionError):
    """Raised when an isolated native inference subprocess fails or crashes."""
    pass

class RuntimeNotFoundError(TermuxVisionError):
    """Raised when the real llama-cli executable cannot be located."""
    def __init__(self, executable: str = "llama-cli", searched_paths: Sequence[str] = ()):
        self.executable = executable
        self.searched_paths = tuple(searched_paths)
        searched = ""
        if searched_paths:
            searched = "\n\nSearched paths:\n" + "\n".join(f"  - {path}" for path in searched_paths)
        message = (
            f"Required runtime '{executable}' was not found.{searched}\n\n"
            f"Please ensure llama.cpp is installed on Termux:\n"
            f"  pkg install termux-llamacpp  (or place llama-cli in PATH / $PREFIX/bin)"
        )
        super().__init__(message)

class VulkanNotAvailableError(SubprocessRuntimeError):
    """Raised when explicit GPU/Vulkan mode is requested but Vulkan hardware/driver is unavailable or failed."""
    def __init__(self, reason: str = ""):
        self.reason = reason
        detail = f"\nFailure detail: {reason}" if reason else ""
        msg = (
            f"Vulkan GPU acceleration is unavailable or failed on this device.{detail}\n\n"
            f"[Action Required] Explicit GPU mode cannot proceed. "
            f"Please switch to CPU mode:\n"
            f"  CLI: --device cpu\n"
            f"  Python API: device='cpu'\n"
            f"Or use automatic detection: --device auto (device='auto')"
        )
        super().__init__(msg)

class GpuExecutionError(VulkanNotAvailableError):
    """Raised when GPU inference terminates abnormally."""
    pass

class CameraPermissionError(TermuxVisionError):
    """Raised when camera access permission is denied on Android."""
    pass

class TermuxAPIUnavailableError(TermuxVisionError):
    """Raised when termux-camera-photo or Termux:API is missing or unavailable."""
    pass
