import os
import sys
import ctypes
import threading
import numpy as np

# Thread-safe synchronization lock
_backend_lock = threading.Lock()

_lib = None
_lib_path = None
_c_backend_load_errors = {}

def _load_c_backend():
    global _lib, _lib_path
    if _lib is not None:
        return _lib

    with _backend_lock:
        if _lib is not None:
            return _lib

        dir_path = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(dir_path, "libfast_cv.so"),
            os.path.join(dir_path, "fast_cv.so"),
            os.path.join(dir_path, "fast_cv.dll"),
            os.path.join(dir_path, "..", "libfast_cv.so"),
            os.path.expanduser("~/.local/lib/libfast_cv.so"),
            "/data/data/com.termux/files/usr/lib/libfast_cv.so"
        ]

        for p in candidates:
            if not os.path.exists(p):
                _c_backend_load_errors[p] = "File not found"
                continue

            try:
                lib_handle = ctypes.CDLL(p)
                _setup_signatures(lib_handle)
                _lib = lib_handle
                _lib_path = p
                return _lib
            except Exception as e:
                _c_backend_load_errors[p] = f"{type(e).__name__}: {e}"
                import logging
                logging.getLogger("termux_vision.csrc.backend").debug(
                    "[termux-vision] C backend dlopen failed at '%s': %s", p, e
                )

        return None

def _setup_signatures(lib):
    # compute_integral_c
    lib.compute_integral_c.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_int
    ]
    lib.compute_integral_c.restype = None

    # sobel_c
    lib.sobel_c.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int
    ]
    lib.sobel_c.restype = None

    # canny_nms_threshold_c
    lib.canny_nms_threshold_c.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float
    ]
    lib.canny_nms_threshold_c.restype = None

    # morphology_c
    lib.morphology_c.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int
    ]
    lib.morphology_c.restype = None

    # haar_detect_multiscale_c
    lib.haar_detect_multiscale_c.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int
    ]
    lib.haar_detect_multiscale_c.restype = ctypes.c_int

def has_c_backend() -> bool:
    return _load_c_backend() is not None

def c_compute_integral(src_uint8: np.ndarray) -> np.ndarray:
    lib = _load_c_backend()
    if lib is None:
        err_msg = "\n".join(f"  - {path}: {err}" for path, err in _c_backend_load_errors.items())
        raise RuntimeError(
            f"Native C backend is not available.\nSearched candidate paths:\n{err_msg}\n"
            f"[Action Recommendation] Please compile libfast_cv.so via clang: clang -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv.so termux_vision/csrc/fast_cv.c -lm"
        )
    
    h, w = src_uint8.shape
    dst = np.zeros((h + 1, w + 1), dtype=np.float64)
    src_cont = np.ascontiguousarray(src_uint8, dtype=np.uint8)

    src_ptr = src_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    dst_ptr = dst.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    lib.compute_integral_c(src_ptr, dst_ptr, w, h)
    return dst

def c_sobel(src_uint8: np.ndarray):
    lib = _load_c_backend()
    if lib is None:
        err_msg = "\n".join(f"  - {path}: {err}" for path, err in _c_backend_load_errors.items())
        raise RuntimeError(
            f"Native C backend is not available.\nSearched candidate paths:\n{err_msg}\n"
            f"[Action Recommendation] Please compile libfast_cv.so via clang: clang -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv.so termux_vision/csrc/fast_cv.c -lm"
        )

    h, w = src_uint8.shape
    mag = np.zeros((h, w), dtype=np.float32)
    angle = np.zeros((h, w), dtype=np.float32)
    src_cont = np.ascontiguousarray(src_uint8, dtype=np.uint8)

    src_ptr = src_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    mag_ptr = mag.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    angle_ptr = angle.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    lib.sobel_c(src_ptr, mag_ptr, angle_ptr, w, h)
    return mag, angle

_vk_lib = None
_vk_lib_path = None
_vk_backend_load_errors = {}

def _load_vulkan_backend():
    global _vk_lib, _vk_lib_path
    if _vk_lib is not None:
        return _vk_lib

    with _backend_lock:
        if _vk_lib is not None:
            return _vk_lib

        dir_path = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(dir_path, "libfast_cv_vk.so"),
            os.path.join(dir_path, "fast_cv_vk.so"),
            os.path.join(dir_path, "..", "libfast_cv_vk.so"),
            os.path.expanduser("~/.local/lib/libfast_cv_vk.so"),
            "/data/data/com.termux/files/usr/lib/libfast_cv_vk.so"
        ]

        for p in candidates:
            if not os.path.exists(p):
                _vk_backend_load_errors[p] = "File not found"
                continue

            try:
                vk = ctypes.CDLL(p)
                # setup signatures
                vk.vk_is_available.argtypes = []
                vk.vk_is_available.restype = ctypes.c_int
                
                vk.vk_get_device_name.argtypes = []
                vk.vk_get_device_name.restype = ctypes.c_char_p

                vk.vk_canny_c.argtypes = [
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_float,
                    ctypes.c_float
                ]
                vk.vk_canny_c.restype = ctypes.c_int

                vk.vk_scale_c.argtypes = [
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_int
                ]
                vk.vk_scale_c.restype = ctypes.c_int

                _vk_lib = vk
                _vk_lib_path = p
                return _vk_lib
            except Exception as e:
                _vk_backend_load_errors[p] = f"{type(e).__name__}: {e}"
                import logging
                logging.getLogger("termux_vision.csrc.backend").warning(
                    "[termux-vision] Vulkan backend dlopen failed at '%s': %s", p, e
                )

        return None

def has_vulkan_backend() -> bool:
    lib = _load_vulkan_backend()
    if lib is None:
        return False
    try:
        return bool(lib.vk_is_available())
    except Exception as e:
        import logging
        logging.getLogger("termux_vision.csrc.backend").warning(
            "[termux-vision] vk_is_available check failed: %s", e
        )
        return False

def get_vulkan_device_name() -> str:
    lib = _load_vulkan_backend()
    if lib is None:
        return "None"
    try:
        name = lib.vk_get_device_name()
        return name.decode('utf-8') if isinstance(name, bytes) else str(name)
    except Exception as e:
        import logging
        logging.getLogger("termux_vision.csrc.backend").warning(
            "[termux-vision] vk_get_device_name failed: %s", e
        )
        return "None"

def c_canny(
    src_uint8: np.ndarray, 
    low_threshold: float = 40.0, 
    high_threshold: float = 120.0,
    device: str = "auto"
) -> np.ndarray:
    dev = (device or "auto").lower().strip()
    h, w = src_uint8.shape

    # 1. Try Vulkan acceleration if requested
    if dev in ("auto", "vulkan", "gpu"):
        vk_lib = _load_vulkan_backend()
        if vk_lib is not None and has_vulkan_backend():
            dst = np.zeros((h, w), dtype=np.uint8)
            src_cont = np.ascontiguousarray(src_uint8, dtype=np.uint8)
            src_ptr = src_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
            dst_ptr = dst.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

            ok = vk_lib.vk_canny_c(src_ptr, dst_ptr, w, h, float(low_threshold), float(high_threshold))
            if ok:
                return dst
            elif dev in ("vulkan", "gpu"):
                from ..errors import VulkanNotAvailableError
                raise VulkanNotAvailableError(
                    reason="Vulkan Canny execution kernel returned error code.\n"
                           "[Action Required] Explicit GPU mode cannot proceed. Please switch to CPU mode:\n"
                           "  Python API: device='cpu'\n"
                           "  CLI: --device cpu\n"
                           "Or use automatic detection: device='auto'"
                )
        elif dev in ("vulkan", "gpu"):
            from ..errors import VulkanNotAvailableError
            err_details = "\n".join(f"  - {path}: {err}" for path, err in _vk_backend_load_errors.items())
            raise VulkanNotAvailableError(
                reason=f"Vulkan GPU acceleration is unavailable or libfast_cv_vk.so is not loaded.\n"
                       f"Candidate search details:\n{err_details}\n"
                       f"[Action Required] Explicit GPU mode cannot proceed. Please switch to CPU mode:\n"
                       f"  Python API: device='cpu'\n"
                       f"  CLI: --device cpu\n"
                       f"Or use automatic detection: device='auto'"
            )

    # 2. Fallback to high-speed C Backend (Graceful Fallback)
    lib = _load_c_backend()
    if lib is None:
        err_msg = "\n".join(f"  - {path}: {err}" for path, err in _c_backend_load_errors.items())
        raise RuntimeError(
            f"Native C backend is not available.\nSearched candidate paths:\n{err_msg}\n"
            f"[Action Recommendation] Please compile libfast_cv.so via clang: clang -O3 -shared -fPIC -o termux_vision/csrc/libfast_cv.so termux_vision/csrc/fast_cv.c -lm"
        )

    mag, angle = c_sobel(src_uint8)
    dst = np.zeros((h, w), dtype=np.uint8)
    mag_ptr = mag.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    angle_ptr = angle.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    dst_ptr = dst.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

    lib.canny_nms_threshold_c(mag_ptr, angle_ptr, dst_ptr, w, h, low_threshold, high_threshold)
    return dst

def c_morphology(src_uint8: np.ndarray, is_dilate: bool = True) -> np.ndarray:
    lib = _load_c_backend()
    if lib is None:
        err_msg = "\n".join(f"  - {path}: {err}" for path, err in _c_backend_load_errors.items())
        raise RuntimeError(
            f"Native C backend is not available.\nSearched candidate paths:\n{err_msg}"
        )

    h, w = src_uint8.shape
    dst = np.zeros((h, w), dtype=np.uint8)
    src_cont = np.ascontiguousarray(src_uint8, dtype=np.uint8)

    src_ptr = src_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    dst_ptr = dst.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

    lib.morphology_c(src_ptr, dst_ptr, w, h, 1 if is_dilate else 0)
    return dst

def c_haar_detect(integral: np.ndarray, width: int, height: int, scale_factor: float = 1.2, min_size: int = 24, max_size: int = 512, max_boxes: int = 1000):
    lib = _load_c_backend()
    if lib is None:
        err_msg = "\n".join(f"  - {path}: {err}" for path, err in _c_backend_load_errors.items())
        raise RuntimeError(
            f"Native C backend is not available.\nSearched candidate paths:\n{err_msg}"
        )

    out_boxes = np.zeros((max_boxes, 4), dtype=np.int32)
    out_scores = np.zeros(max_boxes, dtype=np.float32)

    int_cont = np.ascontiguousarray(integral, dtype=np.float64)
    int_ptr = int_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    boxes_ptr = out_boxes.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    scores_ptr = out_scores.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    num_found = lib.haar_detect_multiscale_c(
        int_ptr,
        width,
        height,
        scale_factor,
        min_size,
        max_size,
        boxes_ptr,
        scores_ptr,
        max_boxes
    )

    boxes = [tuple(out_boxes[i].tolist()) for i in range(num_found)]
    scores = [float(out_scores[i]) for i in range(num_found)]
    return boxes, scores
