#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mutex>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

// Mutex for native thread-safety
static std::mutex g_cv_mutex;

// Thread-local scratch buffers with RAII automatic deallocation on thread exit
struct ThreadScratchBuffer {
    float* mag;
    unsigned char* dir;
    int* queue;
    size_t capacity;

    ThreadScratchBuffer() : mag(NULL), dir(NULL), queue(NULL), capacity(0) {}

    ~ThreadScratchBuffer() {
        cleanup();
    }

    void cleanup() {
        if (mag) { free(mag); mag = NULL; }
        if (dir) { free(dir); dir = NULL; }
        if (queue) { free(queue); queue = NULL; }
        capacity = 0;
    }

    int ensure_capacity(size_t required_px) {
        if (capacity >= required_px && mag && dir && queue) {
            return 1;
        }
        cleanup();
        mag = (float*)malloc(required_px * sizeof(float));
        dir = (unsigned char*)malloc(required_px * sizeof(unsigned char));
        queue = (int*)malloc(required_px * sizeof(int));
        if (!mag || !dir || !queue) {
            cleanup();
            return 0;
        }
        capacity = required_px;
        return 1;
    }
};

static thread_local ThreadScratchBuffer tl_scratch;

EXPORT void fast_cv_cleanup_context() {
    std::lock_guard<std::mutex> lock(g_cv_mutex);
    tl_scratch.cleanup();
}

// C++ Native CPU high-speed Canny Edge Detection (Zero-Trigonometric, Direct Ratio Quantization)
EXPORT int fast_canny_cpp(
    const unsigned char* src, 
    unsigned char* dst, 
    int width, 
    int height, 
    float low_thresh, 
    float high_thresh
) {
    if (!src || !dst || width <= 0 || height <= 0) return 0;

    size_t total_px = (size_t)width * (size_t)height;
    if (!tl_scratch.ensure_capacity(total_px)) {
        return 0;
    }
    float* mag = tl_scratch.mag;
    unsigned char* dir = tl_scratch.dir;
    int* queue = tl_scratch.queue;

    const float tan22_5 = 0.41421356f;
    const float tan67_5 = 2.41421356f;

    // Step 1. Sobel Gradient & Fast Direction Quantization (No atan2f, pure ratio comparisons)
    for (int y = 1; y < height - 1; y++) {
        int y_prev = (y - 1) * width;
        int y_curr = y * width;
        int y_next = (y + 1) * width;

        for (int x = 1; x < width - 1; x++) {
            int p00 = src[y_prev + (x - 1)];
            int p02 = src[y_prev + (x + 1)];
            int p10 = src[y_curr + (x - 1)];
            int p12 = src[y_curr + (x + 1)];
            int p20 = src[y_next + (x - 1)];
            int p22 = src[y_next + (x + 1)];

            float gx = (float)(-p00 + p02 - 2 * p10 + 2 * p12 - p20 + p22);
            float gy = (float)(-p00 - 2 * src[y_prev + x] - p02 + p20 + 2 * src[y_next + x] + p22);

            int idx = y_curr + x;
            mag[idx] = sqrtf(gx * gx + gy * gy);

            float abs_gx = fabsf(gx);
            float abs_gy = fabsf(gy);

            if (abs_gy <= abs_gx * tan22_5) {
                dir[idx] = 0; // Horizontal: 0 deg
            } else if (abs_gy >= abs_gx * tan67_5) {
                dir[idx] = 2; // Vertical: 90 deg
            } else if ((gx > 0.0f) == (gy > 0.0f)) {
                dir[idx] = 1; // Diagonal: 45 deg
            } else {
                dir[idx] = 3; // Anti-diagonal: 135 deg
            }
        }
    }

    // Step 2. NMS & Double Thresholding
    memset(dst, 0, total_px);
    int q_head = 0, q_tail = 0;

    for (int y = 1; y < height - 1; y++) {
        int y_prev = (y - 1) * width;
        int y_curr = y * width;
        int y_next = (y + 1) * width;

        for (int x = 1; x < width - 1; x++) {
            int idx = y_curr + x;
            float c = mag[idx];
            if (c < low_thresh) continue;

            unsigned char d = dir[idx];
            float p1, p2;

            switch (d) {
                case 0: // Horizontal
                    p1 = mag[y_curr + (x - 1)];
                    p2 = mag[y_curr + (x + 1)];
                    break;
                case 1: // 45 deg
                    p1 = mag[y_prev + (x + 1)];
                    p2 = mag[y_next + (x - 1)];
                    break;
                case 2: // Vertical (90 deg)
                    p1 = mag[y_prev + x];
                    p2 = mag[y_next + x];
                    break;
                default: // 135 deg
                    p1 = mag[y_prev + (x - 1)];
                    p2 = mag[y_next + (x + 1)];
                    break;
            }

            if (c >= p1 && c >= p2) {
                if (c >= high_thresh) {
                    dst[idx] = 255;
                    if (queue) {
                        queue[q_tail++] = idx;
                    }
                } else {
                    dst[idx] = 75; // Weak edge candidate
                }
            }
        }
    }

    // Step 3. 8-Connected BFS Hysteresis tracking
    if (queue) {
        int dx[8] = {-1,  0,  1, -1, 1, -1, 0, 1};
        int dy[8] = {-1, -1, -1,  0, 0,  1, 1, 1};

        while (q_head < q_tail) {
            int curr_idx = queue[q_head++];
            int cx = curr_idx % width;
            int cy = curr_idx / width;

            for (int k = 0; k < 8; k++) {
                int nx = cx + dx[k];
                int ny = cy + dy[k];

                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    int n_idx = ny * width + nx;
                    if (dst[n_idx] == 75) {
                        dst[n_idx] = 255;
                        queue[q_tail++] = n_idx;
                    }
                }
            }
        }
    }

    // Suppress remaining unconnected weak edges
    for (size_t i = 0; i < total_px; i++) {
        if (dst[i] == 75) {
            dst[i] = 0;
        }
    }

    return 1;
}

// Fast Bilinear Scaling
EXPORT int fast_scale_cpp(
    const unsigned char* src,
    unsigned char* dst,
    int src_w,
    int src_h,
    int dst_w,
    int dst_h,
    int channels
) {
    if (!src || !dst || src_w <= 0 || src_h <= 0 || dst_w <= 0 || dst_h <= 0) return 0;

    float x_ratio = (float)(src_w - 1) / (float)dst_w;
    float y_ratio = (float)(src_h - 1) / (float)dst_h;

    for (int y = 0; y < dst_h; y++) {
        int y_src = (int)(y_ratio * y);
        float y_diff = (y_ratio * y) - y_src;
        int y_next = (y_src + 1 < src_h) ? y_src + 1 : y_src;

        for (int x = 0; x < dst_w; x++) {
            int x_src = (int)(x_ratio * x);
            float x_diff = (x_ratio * x) - x_src;
            int x_next = (x_src + 1 < src_w) ? x_src + 1 : x_src;

            for (int c = 0; c < channels; c++) {
                float a = src[(y_src * src_w + x_src) * channels + c];
                float b = src[(y_src * src_w + x_next) * channels + c];
                float d = src[(y_next * src_w + x_src) * channels + c];
                float e = src[(y_next * src_w + x_next) * channels + c];

                float val = a * (1 - x_diff) * (1 - y_diff) +
                            b * (x_diff) * (1 - y_diff) +
                            d * (y_diff) * (1 - x_diff) +
                            e * (x_diff * y_diff);

                dst[(y * dst_w + x) * channels + c] = (unsigned char)val;
            }
        }
    }
    return 1;
}

}
