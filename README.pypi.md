# termux-vision

> **On-Device Vision Language Model & Depthwise Separable Conv2D Engine for Android Termux**  
> *Non-Root Native Execution · VLM Multimodal Pipeline · Mobile Resilient Architecture · Zero Heavy PyTorch Lock-in*

---

## ⚡ 5-Minute Quickstart

### Python Installation

`ash
# In Android Termux:
pkg update && pkg install -y python python-numpy git
pip install termux-vision
`

### Python SDK Usage

`python
import numpy as np
from termux_vision.models import DepthwiseSeparableConv2D

layer = DepthwiseSeparableConv2D(in_channels=3, out_channels=16, kernel_size=3)
x = np.random.randn(1, 3, 224, 224).astype(np.float32)
out = layer.forward(x)
print("Output Shape:", out.shape)
`

---

## 📚 Official Documentation

- **Official Web Documentation**: [https://uno-km.vercel.app/lib/vision/](https://uno-km.vercel.app/lib/vision/)
- **GitHub Repository**: [https://github.com/uno-km/termux-vision](https://github.com/uno-km/termux-vision)
- **License**: MIT