/**
 * Fast Pure-JS Spatial Filters & Classical Computer Vision for Node.js.
 * Open-Source under Apache License 2.0.
 */

'use strict';

function sobel(grayPixels, width, height) {
  const gradX = new Float32Array(width * height);
  const gradY = new Float32Array(width * height);
  const magnitude = new Float32Array(width * height);

  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const gx =
        -grayPixels[(y - 1) * width + (x - 1)] + grayPixels[(y - 1) * width + (x + 1)] +
        -2 * grayPixels[y * width + (x - 1)] + 2 * grayPixels[y * width + (x + 1)] +
        -grayPixels[(y + 1) * width + (x - 1)] + grayPixels[(y + 1) * width + (x + 1)];

      const gy =
        -grayPixels[(y - 1) * width + (x - 1)] - 2 * grayPixels[(y - 1) * width + x] - grayPixels[(y - 1) * width + (x + 1)] +
        grayPixels[(y + 1) * width + (x - 1)] + 2 * grayPixels[(y + 1) * width + x] + grayPixels[(y + 1) * width + (x + 1)];

      gradX[idx] = gx;
      gradY[idx] = gy;
      magnitude[idx] = Math.sqrt(gx * gx + gy * gy);
    }
  }

  return { gradX, gradY, magnitude };
}

function canny(grayPixels, width, height, lowThreshold = 40.0, highThreshold = 120.0) {
  const { magnitude } = sobel(grayPixels, width, height);
  const edges = new Uint8Array(width * height);

  for (let i = 0; i < magnitude.length; i++) {
    if (magnitude[i] >= highThreshold) {
      edges[i] = 255;
    } else if (magnitude[i] >= lowThreshold) {
      edges[i] = 128;
    } else {
      edges[i] = 0;
    }
  }

  return edges;
}

module.exports = {
  sobel,
  canny
};
