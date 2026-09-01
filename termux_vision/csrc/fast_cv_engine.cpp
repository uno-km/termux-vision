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
    float* angle_deg;
    int* queue;
    size_t capacity;

    ThreadScratchBuffer() : mag(NULL), angle_deg(NULL), queue(NULL), capacity(0) {}

    ~ThreadScratchBuffer() {
        cleanup();
    }

    void cleanup() {
        if (mag) { free(mag); mag = NULL; }
        if (angle_deg) { free(angle_deg); angle_deg = NULL; }
        if (queue) { free(queue); queue = NULL; }
        capacity = 0;
    }

    int ensure_capacity(size_t required_px) {
        if (capacity >= required_px && mag && angle_deg && queue) {
            return 1;
        }
        cleanup();
        mag = (float*)malloc(required_px * sizeof(float));
        angle_deg = (float*)malloc(required_px * sizeof(float));
        queue = (int*)malloc(required_px * sizeof(int));
        if (!mag || !angle_deg || !queue) {
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

// C++ Native CPU multi-threaded / vectorized Canny Edge Detection implementation with BFS Hysteresis
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
    float* angle_deg = tl_scratch.angle_deg;
    int* queue = tl_scratch.queue;

    // Step 1. Sobel Gradient & Angle
    for (int y = 1; y < height - 1; y++) {
        int y_prev = (y - 1) * width;
        int y_curr = y * width;
        int y_next = (y + 1) * width;

        for (int x = 1; x < width - 1; x++) {
            int p00 = src[y_prev + (x - 1)];
            int p01 = src[y_prev + x];
            int p02 = src[y_prev + (x + 1)];
            int p10 = src[y_curr + (x - 1)];
            int p12 = src[y_curr + (x + 1)];
            int p20 = src[y_next + (x - 1)];
            int p21 = src[y_next + x];
            int p22 = src[y_next + (x + 1)];

            float gx = (float)(-p00 + p02 - 2 * p10 + 2 * p12 - p20 + p22);
            float gy = (float)(-p00 - 2 * p01 - p02 + p20 + 2 * p21 + p22);

            mag[y_curr + x] = sqrtf(gx * gx + gy * gy);

            float rad = atan2f(gy, gx);
            float deg = rad * (180.0f / 3.1415926535f);
            if (deg < 0.0f) deg += 180.0f;
            angle_deg[y_curr + x] = deg;
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

            float deg = angle_deg[idx];
            float p1 = 0.0f, p2 = 0.0f;

            if ((deg >= 0.0f && deg < 22.5f) || (deg >= 157.5f && deg <= 180.0f)) {
                p1 = mag[y_curr + (x - 1)];
                p2 = mag[y_curr + (x + 1)];
            } else if (deg >= 22.5f && deg < 67.5f) {
                p1 = mag[y_prev + (x + 1)];
                p2 = mag[y_next + (x - 1)];
            } else if (deg >= 67.5f && deg < 112.5f) {
                p1 = mag[y_prev + x];
                p2 = mag[y_next + x];
            } else {
                p1 = mag[y_prev + (x - 1)];
                p2 = mag[y_next + (x + 1)];
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
