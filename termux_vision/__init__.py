"""
termux-vision: Lightweight On-Device Computer Vision & VLM Framework for Android Termux.
Open-Source under Apache License 2.0.
"""

__version__ = "1.1.4"
__author__ = "termux-vision contributors"
__license__ = "Apache-2.0"

from . import errors
from . import io
from . import transforms
from . import cv
from . import detect
from . import models
from . import bridge
from . import csrc
from . import vlm
from . import cli

from .detect.types import BoundingBox, Detection
from .detect.haar import detect_faces
from .models.embedding import Embedding, compute_similarity
from .vlm.api import load

__all__ = [
    "io",
    "transforms",
    "cv",
    "detect",
    "models",
    "bridge",
    "csrc",
    "vlm",
    "errors",
    "cli",
    "BoundingBox",
    "Detection",
    "detect_faces",
    "Embedding",
    "compute_similarity",
    "load",
    "__version__"
]
