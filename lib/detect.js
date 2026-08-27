/**
 * BoundingBox Geometry & Non-Maximum Suppression (NMS) for Node.js.
 * Open-Source under Apache License 2.0.
 */

'use strict';

function computeIoU(boxA, boxB) {
  const x1 = Math.max(boxA.x, boxB.x);
  const y1 = Math.max(boxA.y, boxB.y);
  const x2 = Math.min(boxA.x + boxA.width, boxB.x + boxB.width);
  const y2 = Math.min(boxA.y + boxA.height, boxB.y + boxB.height);

  const interArea = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const areaA = boxA.width * boxA.height;
  const areaB = boxB.width * boxB.height;
  const unionArea = areaA + areaB - interArea;

  return unionArea <= 0 ? 0 : interArea / unionArea;
}

function nms(boxes, iouThreshold = 0.45) {
  if (!boxes || boxes.length === 0) return [];
  const sorted = [...boxes].sort((a, b) => (b.score || 0) - (a.score || 0));
  const keep = [];

  for (let i = 0; i < sorted.length; i++) {
    const current = sorted[i];
    let suppressed = false;
    for (let j = 0; j < keep.length; j++) {
      if (computeIoU(current, keep[j]) > iouThreshold) {
        suppressed = true;
        break;
      }
    }
    if (!suppressed) {
      keep.push(current);
    }
  }

  return keep;
}

module.exports = {
  computeIoU,
  nms
};
