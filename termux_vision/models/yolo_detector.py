from typing import List, Dict, Tuple
import numpy as np
from .conv_block import DepthwiseSeparableConv2D
from .yolo_post import YOLODecoder

class TinyYOLONanoDetector:
    """
    Ultra-lightweight On-Device Object Detector (YOLO-Nano architecture) with Depthwise Separable Convolutions.
    """
    def __init__(self, num_classes: int = 80, class_names: List[str] = None):
        self.num_classes = num_classes
        self.class_names = class_names or ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light"]
        # Lightweight Mobile Backbone
        self.conv1 = DepthwiseSeparableConv2D(3, 16, kernel_size=3, stride=2)
        self.conv2 = DepthwiseSeparableConv2D(16, 32, kernel_size=3, stride=2)
        self.conv3 = DepthwiseSeparableConv2D(32, 64, kernel_size=3, stride=2)
        
        # Detection Head: (cx, cy, w, h) + num_classes
        self.head = DepthwiseSeparableConv2D(64, 4 + len(self.class_names), kernel_size=1, stride=1)
        self.decoder = YOLODecoder(class_names=self.class_names, conf_threshold=0.25, iou_threshold=0.45)

    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Input image: (H, W, 3) uint8 or float.
        Returns: list of detections [{"box": (x,y,w,h), "score": float, "class_name": str}]
        """
        orig_h, orig_w = image.shape[:2]
        
        # Resize to standard 256x256 input
        from ..transforms.functional import resize
        img_res = resize(image, (256, 256))
        
        # Channel-first float32
        x = np.transpose(img_res.astype(np.float32) / 255.0, (2, 0, 1))

        # Forward pass
        h1 = self.conv1(x)
        h2 = self.conv2(h1)
        h3 = self.conv3(h2)
        out = self.head(h3) # (4 + num_classes, 32, 32)

        # Reshape to (1024, 4 + num_classes)
        c, grid_h, grid_w = out.shape
        out_trans = np.transpose(out, (1, 2, 0)).reshape(grid_h * grid_w, c)

        # Softmax on class scores
        class_logits = out_trans[:, 4:]
        exp_logits = np.exp(class_logits - np.max(class_logits, axis=-1, keepdims=True))
        out_trans[:, 4:] = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

        # Decode bounding boxes
        detections = self.decoder.decode(out_trans, (orig_w, orig_h))
        return detections
