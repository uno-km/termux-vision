"""
AMEVA Unified Model Downloader for termux-vision.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from .hardware import get_unified_model_search_dirs
from .vlm.model_hub import VLMModelHub

AVAILABLE_MODELS = {
    "smolvlm-500m": {"name": "smolvlm-500m-q8_0.gguf", "size_mb": 510, "desc": "SmolVLM 500M Compact Vision Model"},
    "moondream2": {"name": "moondream2-text-model-f16.gguf", "size_mb": 1800, "desc": "Moondream2 1.8B High Quality Vision Model"},
}

def resolve_model_path(model_name: str = "smolvlm-500m") -> Path:
    search_dirs = get_unified_model_search_dirs("vision")
    for d in search_dirs:
        cand = d / model_name
        if cand.exists():
            return cand.resolve()
    hub = VLMModelHub()
    return Path(hub.resolve_model_path(model_name))

def download_model(model_name: str = "smolvlm-500m", output_dir: Optional[Path] = None, force: bool = False) -> Path:
    hub = VLMModelHub(cache_dir=output_dir)
    return Path(hub.download_model(model_name, force=force))

def list_models() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in AVAILABLE_MODELS.items()]
