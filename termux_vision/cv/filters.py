import numpy as np
from ..transforms.functional import to_grayscale

def conv2d_same(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Fast 2D convolution with 'same' boundary padding (reflection padding).
    """
    img_h, img_w = image.shape[:2]
    kh, kw = kernel.shape[:2]
    pad_h = kh // 2
    pad_w = kw // 2

    # Reflection padding
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
    
    from numpy.lib.stride_tricks import sliding_window_view
    windows = sliding_window_view(padded, (kh, kw))
    out = np.einsum('ijkh,kh->ij', windows, kernel)
    return out

def gaussian_kernel(size: int = 5, sigma: float = 1.4) -> np.ndarray:
    """
    Generate a 2D normalized Gaussian kernel.
    """
    ax = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2.0 * sigma**2))
    return kernel / np.sum(kernel)

def gaussian_blur(image: np.ndarray, size: int = 5, sigma: float = 1.4) -> np.ndarray:
    """
    Apply Gaussian smoothing filter.
    """
    gray = to_grayscale(image).astype(np.float32)
    kernel = gaussian_kernel(size, sigma)
    return conv2d_same(gray, kernel)

def sobel(image: np.ndarray):
    """
    Compute Sobel gradients (Gx, Gy) and gradient magnitude and angle (in radians).
    """
    gray = to_grayscale(image)
    
    # Fast path via compiled C kernel
    try:
        from ..csrc.backend import has_c_backend, c_sobel
        if has_c_backend():
            mag, angle_deg = c_sobel(gray)
            angle_rad = np.deg2rad(angle_deg)
            gx = mag * np.cos(angle_rad)
            gy = mag * np.sin(angle_rad)
            return gx, gy, mag, angle_rad
    except (ImportError, RuntimeError, OSError) as _sobel_err:
        import logging
        logging.getLogger(__name__).debug("c_sobel fast-path unavailable (%s); using numpy fallback", _sobel_err)

    gray_f = gray.astype(np.float32)
    kx = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float32)
    
    ky = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float32)

    gx = conv2d_same(gray_f, kx)
    gy = conv2d_same(gray_f, ky)
    
    magnitude = np.hypot(gx, gy)
    angle = np.arctan2(gy, gx)
    return gx, gy, magnitude, angle

def laplacian(image: np.ndarray) -> np.ndarray:
    """
    Compute discrete Laplacian second derivative.
    """
    gray = to_grayscale(image).astype(np.float32)
    kernel = np.array([
        [0,  1, 0],
        [1, -4, 1],
        [0,  1, 0]
    ], dtype=np.float32)
    return conv2d_same(gray, kernel)

def canny(image: np.ndarray, low_threshold: float = 50.0, high_threshold: float = 150.0,
          blur_size: int = 5, sigma: float = 1.4, device: str = "auto") -> np.ndarray:
    """
    Full 5-stage Canny Edge Detector:
    Uses Vulkan GPU / compiled C kernel when available (100x acceleration), falls back to pure NumPy.
    """
    gray = to_grayscale(image)

    # 1. Accelerated Vulkan / C Path
    try:
        from ..csrc.backend import has_c_backend, has_vulkan_backend, c_canny
        if has_vulkan_backend() or has_c_backend() or str(device).lower().strip() in ("vulkan", "gpu"):
            return c_canny(gray, low_threshold=low_threshold, high_threshold=high_threshold, device=device)
    except Exception as e:
        if str(device).lower().strip() in ("vulkan", "gpu"):
            raise e
        import logging
        logging.getLogger("termux_vision.cv.filters").debug(
            "[termux-vision] C/Vulkan backend dispatch failed, falling back to NumPy: %s", e
        )

    # 2. Pure NumPy Path
    blurred = gaussian_blur(gray, size=blur_size, sigma=sigma)
    _, _, magnitude, angle = sobel(blurred)
    
    mag_max = magnitude.max()
    if mag_max > 0:
        magnitude = (magnitude / mag_max) * 255.0

    h, w = magnitude.shape
    nms = np.zeros((h, w), dtype=np.float32)
    angle_deg = np.rad2deg(angle) % 180

    for i in range(1, h - 1):
        for j in range(1, w - 1):
            deg = angle_deg[i, j]
            if (0 <= deg < 22.5) or (157.5 <= deg <= 180):
                p1, p2 = magnitude[i, j - 1], magnitude[i, j + 1]
            elif 22.5 <= deg < 67.5:
                p1, p2 = magnitude[i - 1, j + 1], magnitude[i + 1, j - 1]
            elif 67.5 <= deg < 112.5:
                p1, p2 = magnitude[i - 1, j], magnitude[i + 1, j]
            else:
                p1, p2 = magnitude[i - 1, j - 1], magnitude[i + 1, j + 1]

            if magnitude[i, j] >= p1 and magnitude[i, j] >= p2:
                nms[i, j] = magnitude[i, j]

    strong = 255
    weak = 75
    res = np.zeros((h, w), dtype=np.uint8)

    strong_i, strong_j = np.where(nms >= high_threshold)
    weak_i, weak_j = np.where((nms >= low_threshold) & (nms < high_threshold))

    res[strong_i, strong_j] = strong
    res[weak_i, weak_j] = weak

    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if res[i, j] == weak:
                if np.any(res[i - 1:i + 2, j - 1:j + 2] == strong):
                    res[i, j] = strong
                else:
                    res[i, j] = 0

    return res
