import os
import sys
import ctypes
import numpy as np

_lib = None
_lib_path = None

def _load_c_backend():
    global _lib, _lib_path
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
        if os.path.exists(p):
            try:
                _lib = ctypes.CDLL(p)
                _lib_path = p
                _setup_signatures(_lib)
                return _lib
            except Exception:
                continue

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
        raise RuntimeError("C backend not available.")
    
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
        raise RuntimeError("C backend not available.")

    h, w = src_uint8.shape
    mag = np.zeros((h, w), dtype=np.float32)
    angle = np.zeros((h, w), dtype=np.float32)
    src_cont = np.ascontiguousarray(src_uint8, dtype=np.uint8)

    src_ptr = src_cont.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
    mag_ptr = mag.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    angle_ptr = angle.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    lib.sobel_c(src_ptr, mag_ptr, angle_ptr, w, h)
    return mag, angle

def c_canny(src_uint8: np.ndarray, low_threshold: float = 40.0, high_threshold: float = 120.0) -> np.ndarray:
    lib = _load_c_backend()
    if lib is None:
        raise RuntimeError("C backend not available.")

    h, w = src_uint8.shape
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
        raise RuntimeError("C backend not available.")

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
        raise RuntimeError("C backend not available.")

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
