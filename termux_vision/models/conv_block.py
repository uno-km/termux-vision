import numpy as np

class DepthwiseSeparableConv2D:
    """
    Lightweight MobileNet-style Depthwise Separable 2D Convolution Layer.
    Splits standard conv into:
    1. Depthwise Conv (Spatial filtering per channel)
    2. Pointwise Conv (1x1 Linear combination across channels)
    """
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, stride: int = 1):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride

        # Initialize lightweight weights
        scale_dw = np.sqrt(2.0 / (kernel_size * kernel_size))
        self.dw_weights = np.random.randn(in_channels, kernel_size, kernel_size).astype(np.float32) * scale_dw
        
        scale_pw = np.sqrt(2.0 / in_channels)
        self.pw_weights = np.random.randn(out_channels, in_channels).astype(np.float32) * scale_pw
        self.bias = np.zeros(out_channels, dtype=np.float32)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Input shape: (C_in, H, W) or (B, C_in, H, W)
        Output shape: (C_out, H_out, W_out) or (B, C_out, H_out, W_out)
        """
        has_batch = (x.ndim == 4)
        if not has_batch:
            x_batched = x[np.newaxis, ...]
        else:
            x_batched = x

        b, c_in, h, w = x_batched.shape
        k = self.kernel_size
        pad = k // 2

        # 1. Depthwise Convolution (Same padding)
        padded = np.pad(x_batched, ((0, 0), (0, 0), (pad, pad), (pad, pad)), mode='constant')
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(padded, (k, k), axis=(2, 3))
        # windows shape: (B, C_in, H, W, k, k)
        
        # Strided slicing if stride > 1
        if self.stride > 1:
            windows = windows[:, :, ::self.stride, ::self.stride, :, :]

        # Depthwise output: (B, C_in, H_out, W_out)
        dw_out = np.einsum('bchwkl,ckl->bchw', windows, self.dw_weights)
        
        # ReLU6 activation
        dw_out = np.clip(dw_out, 0.0, 6.0)

        # 2. Pointwise Convolution (1x1): (B, C_out, H_out, W_out)
        pw_out = np.einsum('bchw,oc->bohw', dw_out, self.pw_weights) + self.bias[None, :, None, None]

        if not has_batch:
            return pw_out[0]
        return pw_out

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)
