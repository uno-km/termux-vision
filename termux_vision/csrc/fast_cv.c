#include <stdlib.h>
#include <math.h>
#include <string.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

// Fast 2D Integral Image Computation: O(W * H) single-pass
EXPORT void compute_integral_c(const unsigned char* src, double* dst, int width, int height) {
    int dst_w = width + 1;
    memset(dst, 0, dst_w * sizeof(double));

    for (int y = 0; y < height; y++) {
        double row_sum = 0.0;
        int dst_row = (y + 1) * dst_w;
        int src_row = y * width;
        dst[dst_row] = 0.0;

        for (int x = 0; x < width; x++) {
            row_sum += (double)src[src_row + x];
            dst[dst_row + x + 1] = dst[dst_row - dst_w + x + 1] + row_sum;
        }
    }
}

// Inline helper for O(1) box sum
static inline double box_sum_inline(const double* integral, int stride, int x1, int y1, int x2, int y2) {
    return integral[y2 * stride + x2]
         - integral[y1 * stride + x2]
         - integral[y2 * stride + x1]
         + integral[y1 * stride + x1];
}

// Fast Sobel Gradient Magnitude and Angle
EXPORT void sobel_c(const unsigned char* src, float* mag, float* angle_deg, int width, int height) {
    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            int p00 = src[(y - 1) * width + (x - 1)];
            int p01 = src[(y - 1) * width + x];
            int p02 = src[(y - 1) * width + (x + 1)];
            int p10 = src[y * width + (x - 1)];
            int p12 = src[y * width + (x + 1)];
            int p20 = src[(y + 1) * width + (x - 1)];
            int p21 = src[(y + 1) * width + x];
            int p22 = src[(y + 1) * width + (x + 1)];

            float gx = (float)(-p00 + p02 - 2 * p10 + 2 * p12 - p20 + p22);
            float gy = (float)(-p00 - 2 * p01 - p02 + p20 + 2 * p21 + p22);

            float m = sqrtf(gx * gx + gy * gy);
            mag[y * width + x] = m;

            float rad = atan2f(gy, gx);
            float deg = rad * (180.0f / 3.1415926535f);
            if (deg < 0.0f) deg += 180.0f;
            angle_deg[y * width + x] = deg;
        }
    }
}

// Fast Canny NMS and Double Thresholding with Full 8-Connected Queue-based Hysteresis
EXPORT void canny_nms_threshold_c(
    const float* mag, 
    const float* angle_deg, 
    unsigned char* dst, 
    int width, 
    int height, 
    float low_thresh, 
    float high_thresh
) {
    memset(dst, 0, (size_t)width * (size_t)height);

    int total_pixels = width * height;
    int* queue = (int*)malloc((size_t)total_pixels * sizeof(int));
    int q_head = 0, q_tail = 0;

    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            int idx = y * width + x;
            float c = mag[idx];
            if (c < low_thresh) continue;

            float deg = angle_deg[idx];
            float p1 = 0.0f, p2 = 0.0f;

            if ((deg >= 0.0f && deg < 22.5f) || (deg >= 157.5f && deg <= 180.0f)) {
                p1 = mag[y * width + (x - 1)];
                p2 = mag[y * width + (x + 1)];
            } else if (deg >= 22.5f && deg < 67.5f) {
                p1 = mag[(y - 1) * width + (x + 1)];
                p2 = mag[(y + 1) * width + (x - 1)];
            } else if (deg >= 67.5f && deg < 112.5f) {
                p1 = mag[(y - 1) * width + x];
                p2 = mag[(y + 1) * width + x];
            } else {
                p1 = mag[(y - 1) * width + (x - 1)];
                p2 = mag[(y + 1) * width + (x + 1)];
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

    // 8-Connected BFS Hysteresis tracking
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
                        dst[n_idx] = 255; // Promote connected weak edge
                        queue[q_tail++] = n_idx;
                    }
                }
            }
        }
        free(queue);
    }

    // Suppress remaining unconnected weak edges
    for (int i = 0; i < total_pixels; i++) {
        if (dst[i] == 75) {
            dst[i] = 0;
        }
    }
}

// Fast Morphology Dilation and Erosion (3x3 Rectangular Element) with Zero-Init Border
EXPORT void morphology_c(const unsigned char* src, unsigned char* dst, int width, int height, int is_dilate) {
    memset(dst, 0, (size_t)width * (size_t)height);

    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            if (is_dilate) {
                unsigned char max_val = 0;
                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        unsigned char val = src[(y + dy) * width + (x + dx)];
                        if (val > max_val) max_val = val;
                    }
                }
                dst[y * width + x] = max_val;
            } else {
                unsigned char min_val = 255;
                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        unsigned char val = src[(y + dy) * width + (x + dx)];
                        if (val < min_val) min_val = val;
                    }
                }
                dst[y * width + x] = min_val;
            }
        }
    }
}

// High-speed Multiscale Haar Face Detector in C
EXPORT int haar_detect_multiscale_c(
    const double* integral,
    int width,
    int height,
    float scale_factor,
    int min_size,
    int max_size,
    int* out_boxes,     // Array of size max_boxes * 4 (x, y, w, h)
    float* out_scores,  // Array of size max_boxes
    int max_boxes
) {
    int count = 0;
    int stride = width + 1;
    float scale = (float)min_size / 24.0f;

    while (count < max_boxes) {
        int win_w = (int)(24.0f * scale);
        int win_h = (int)(24.0f * scale);

        if (win_w > width || win_h > height || win_w > max_size || win_h > max_size) {
            break;
        }

        int step = (int)(4.0f * scale);
        if (step < 2) step = 2;

        float s2 = scale * scale;

        for (int y = 0; y <= height - win_h; y += step) {
            for (int x = 0; x <= width - win_w; x += step) {
                // Stage 1: Horizontal Eye Darkness vs Cheek Brightness
                int e_x1 = x + (int)(2 * scale);
                int e_y1 = y + (int)(6 * scale);
                int e_w  = (int)(20 * scale);
                int e_h  = (int)(6 * scale);
                double eyes = box_sum_inline(integral, stride, e_x1, e_y1, e_x1 + e_w, e_y1 + e_h);

                int c_x1 = x + (int)(2 * scale);
                int c_y1 = y + (int)(12 * scale);
                int c_w  = (int)(20 * scale);
                int c_h  = (int)(6 * scale);
                double cheeks = box_sum_inline(integral, stride, c_x1, c_y1, c_x1 + c_w, c_y1 + c_h);

                double val1 = -1.0 * eyes + 1.0 * cheeks;
                float s1 = (val1 < -10.0 * s2) ? -1.0f : 1.2f;
                if (s1 < 0.2f) continue; // Fast reject

                // Stage 2: Vertical Nose Bridge (3-rect)
                int n1_x = x + (int)(6 * scale);
                int n1_y = y + (int)(6 * scale);
                int n1_w = (int)(4 * scale);
                int n1_h = (int)(12 * scale);
                double l_cheek = box_sum_inline(integral, stride, n1_x, n1_y, n1_x + n1_w, n1_y + n1_h);

                int n2_x = x + (int)(10 * scale);
                int n2_w = (int)(4 * scale);
                double nose = box_sum_inline(integral, stride, n2_x, n1_y, n2_x + n2_w, n1_y + n1_h);

                int n3_x = x + (int)(14 * scale);
                int n3_w = (int)(4 * scale);
                double r_cheek = box_sum_inline(integral, stride, n3_x, n1_y, n3_x + n3_w, n1_y + n1_h);

                double val2 = -1.0 * l_cheek + 2.0 * nose - 1.0 * r_cheek;
                float s2_score = (val2 < -5.0 * s2) ? -0.8f : 1.5f;
                if (s2_score < 0.3f) continue; // Fast reject

                // Stage 3: Mouth region
                int m1_x = x + (int)(4 * scale);
                int m1_y = y + (int)(16 * scale);
                int m1_w = (int)(16 * scale);
                int m1_h = (int)(4 * scale);
                double mouth = box_sum_inline(integral, stride, m1_x, m1_y, m1_x + m1_w, m1_y + m1_h);

                int m2_y = y + (int)(12 * scale);
                double upper = box_sum_inline(integral, stride, m1_x, m2_y, m1_x + m1_w, m2_y + m1_h);

                double val3 = -1.0 * mouth + 1.0 * upper;
                float s3 = (val3 < -2.0 * s2) ? -0.5f : 1.1f;
                if (s3 < 0.2f) continue;

                // Passed all stages
                out_boxes[count * 4 + 0] = x;
                out_boxes[count * 4 + 1] = y;
                out_boxes[count * 4 + 2] = win_w;
                out_boxes[count * 4 + 3] = win_h;
                
                double area = (double)(win_w * win_h);
                double mean_v = box_sum_inline(integral, stride, x, y, x + win_w, y + win_h) / (area > 0 ? area : 1.0);
                out_scores[count] = (float)mean_v;
                count++;

                if (count >= max_boxes) break;
            }
        }

        scale *= scale_factor;
    }

    return count;
}
