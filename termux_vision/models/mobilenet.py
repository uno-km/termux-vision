import numpy as np
from .conv_block import DepthwiseSeparableConv2D

class MobileNetV3FeatureExtractor:
    """
    Lightweight Depthwise-Separable Convolutional Feature Extractor Prototype.
    Constructs a stacked depthwise separable convolution architecture.
    (Note: Prototype uses initialized structural weights; downstream production models load trained weights).
    """
    def __init__(self, in_channels: int = 3, feature_dim: int = 512):
        self.in_channels = in_channels
        self.feature_dim = feature_dim
        
        self.block1 = DepthwiseSeparableConv2D(in_channels=in_channels, out_channels=32, kernel_size=3, stride=2)
        self.block2 = DepthwiseSeparableConv2D(in_channels=32, out_channels=64, kernel_size=3, stride=2)
        self.block3 = DepthwiseSeparableConv2D(in_channels=64, out_channels=128, kernel_size=3, stride=2)
        self.block4 = DepthwiseSeparableConv2D(in_channels=128, out_channels=feature_dim, kernel_size=3, stride=2)

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)

    def forward(self, x: np.ndarray) -> np.ndarray:
        if x.ndim == 3:
            x = x[np.newaxis, ...]

        out = self.block1(x)
        out = self.block2(out)
        out = self.block3(out)
        out = self.block4(out)

        # Global Average Pooling
        pooled = np.mean(out, axis=(2, 3))
        # L2 Normalization
        norm = np.linalg.norm(pooled, axis=1, keepdims=True)
        norm = np.maximum(norm, 1e-8)
        embedding = pooled / norm

        return embedding[0] if embedding.shape[0] == 1 else embedding

def compute_similarity(feat1: np.ndarray, feat2: np.ndarray) -> float:
    """
    Computes cosine similarity between two feature vectors.
    """
    v1 = np.ascontiguousarray(feat1.flatten(), dtype=np.float32)
    v2 = np.ascontiguousarray(feat2.flatten(), dtype=np.float32)
    
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 > 0:
        v1 = v1 / n1
    if n2 > 0:
        v2 = v2 / n2
    return float(np.dot(v1, v2))
