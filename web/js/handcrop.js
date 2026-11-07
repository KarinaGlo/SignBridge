/**
 * web/js/handcrop.js
 * Kontrak 4 & 5 (PDF Hal. 11 & 23): Paritas Hand Crop & ImageNet Normalization Python <-> JS
 * Identik dengan signbridge/image/crop.py:
 *   - computeHandCropBox(handLandmarks, imgW, imgH, margin = 0.25) -> {x0, y0, x1, y1, size}
 *   - resizeBilinearRGB(cropHWC, cropH, cropW, outSize = 224) -> Float32Array [outSize * outSize * 3]
 *   - normalizeImagenet(rgbHWC, size = 224) -> Float32Array [3 * size * size] (CHW)
 *   - cropAndResizeHand(rgbHWC, imgH, imgW, handLandmarks, outSize = 224, margin = 0.25)
 */

export const IMAGENET_MEAN = [0.485, 0.456, 0.406];
export const IMAGENET_STD = [0.229, 0.224, 0.225];
export const CROP_SIZE = 224;
export const PAD_RATIO = 0.25;

/**
 * Hitung kotak potong persegi berpusat pada 21 titik tangan + margin 25%.
 * Mengembalikan objek {x0, y0, x1, y1, size} identik dengan signbridge.image.crop.compute_hand_crop_box.
 */
export function computeHandCropBox(handLandmarks, imgW, imgH, margin = PAD_RATIO) {
  if (!handLandmarks || handLandmarks.length === 0) {
    const side = Math.min(imgW, imgH);
    const x0 = Math.floor((imgW - side) / 2);
    const y0 = Math.floor((imgH - side) / 2);
    return { x0, y0, x1: x0 + side, y1: y0 + side, size: side };
  }

  let maxAbs = 0.0;
  const pts = [];
  for (let i = 0; i < handLandmarks.length; i++) {
    const p = handLandmarks[i];
    if (!p) continue;
    const x = Array.isArray(p) ? Number(p[0]) : Number(p.x);
    const y = Array.isArray(p) ? Number(p[1]) : Number(p.y);
    if (Number.isFinite(x) && Number.isFinite(y)) {
      pts.push([x, y]);
      if (Math.abs(x) > maxAbs) maxAbs = Math.abs(x);
      if (Math.abs(y) > maxAbs) maxAbs = Math.abs(y);
    }
  }

  if (pts.length === 0) {
    const side = Math.min(imgW, imgH);
    const x0 = Math.floor((imgW - side) / 2);
    const y0 = Math.floor((imgH - side) / 2);
    return { x0, y0, x1: x0 + side, y1: y0 + side, size: side };
  }

  const normalized = maxAbs <= 1.5;
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;

  for (let i = 0; i < pts.length; i++) {
    const px = normalized ? pts[i][0] * imgW : pts[i][0];
    const py = normalized ? pts[i][1] * imgH : pts[i][1];
    if (px < minX) minX = px;
    if (px > maxX) maxX = px;
    if (py < minY) minY = py;
    if (py > maxY) maxY = py;
  }

  const cx = 0.5 * (minX + maxX);
  const cy = 0.5 * (minY + maxY);
  const span = Math.max(maxX - minX, maxY - minY, 16.0);
  let halfSide = 0.5 * span * (1.0 + 2.0 * Number(margin));

  const maxHalf = 0.5 * Math.min(imgW, imgH);
  if (halfSide > maxHalf) halfSide = maxHalf;

  let x0f = cx - halfSide;
  let y0f = cy - halfSide;
  if (x0f < 0.0) x0f = 0.0;
  if (y0f < 0.0) y0f = 0.0;
  if (x0f + 2.0 * halfSide > imgW) x0f = imgW - 2.0 * halfSide;
  if (y0f + 2.0 * halfSide > imgH) y0f = imgH - 2.0 * halfSide;

  const x0 = Math.round(Math.max(0.0, x0f));
  const y0 = Math.round(Math.max(0.0, y0f));
  let size = Math.round(2.0 * halfSide);
  size = Math.max(1, Math.min(size, imgW - x0, imgH - y0));

  return {
    x0,
    y0,
    x1: x0 + size,
    y1: y0 + size,
    size
  };
}

/**
 * Resize bilinear deterministik identik dengan signbridge.image.crop._bilinear_resize_rgb.
 * Input cropHWC adalah nested array [H][W][3] atau flat array H*W*3.
 * Mengembalikan Float32Array [outSize * outSize * 3] dalam urutan HWC.
 */
export function resizeBilinearRGB(cropHWC, cropH, cropW, outSize = CROP_SIZE) {
  const out = new Float32Array(outSize * outSize * 3);
  if (cropH <= 0 || cropW <= 0) return out;

  const isNested = Array.isArray(cropHWC) && Array.isArray(cropHWC[0]);
  const getPixel = (y, x, c) => {
    if (isNested) return Number(cropHWC[y][x][c]);
    return Number(cropHWC[(y * cropW + x) * 3 + c]);
  };

  for (let i = 0; i < outSize; i++) {
    const gy = Math.fround((Math.fround(i + 0.5) * cropH) / outSize - 0.5);
    const yClamped = Math.max(0.0, Math.min(gy, Math.max(0.0, cropH - 1.0)));
    const y0 = Math.floor(yClamped);
    const y1 = Math.min(y0 + 1, cropH - 1);
    const dr = Math.fround(yClamped - y0);

    for (let j = 0; j < outSize; j++) {
      const gx = Math.fround((Math.fround(j + 0.5) * cropW) / outSize - 0.5);
      const xClamped = Math.max(0.0, Math.min(gx, Math.max(0.0, cropW - 1.0)));
      const x0 = Math.floor(xClamped);
      const x1 = Math.min(x0 + 1, cropW - 1);
      const dc = Math.fround(xClamped - x0);

      const dstIdx = (i * outSize + j) * 3;
      for (let c = 0; c < 3; c++) {
        const top = (1.0 - dc) * getPixel(y0, x0, c) + dc * getPixel(y0, x1, c);
        const bot = (1.0 - dc) * getPixel(y1, x0, c) + dc * getPixel(y1, x1, c);
        out[dstIdx + c] = Math.fround((1.0 - dr) * top + dr * bot);
      }
    }
  }
  return out;
}

/**
 * Normalisasi ImageNet ke layout CHW Float32Array [3 * size * size] untuk input ONNX [1, 3, 224, 224].
 */
export function normalizeImagenet(rgbHWC, size = CROP_SIZE) {
  const numPixels = size * size;
  const chw = new Float32Array(3 * numPixels);

  let maxVal = 0.0;
  for (let i = 0; i < rgbHWC.length; i++) {
    if (rgbHWC[i] > maxVal) maxVal = rgbHWC[i];
  }
  const scale = maxVal > 1.5 ? 1.0 / 255.0 : 1.0;

  for (let p = 0; p < numPixels; p++) {
    const r = Math.fround(rgbHWC[p * 3 + 0] * scale);
    const g = Math.fround(rgbHWC[p * 3 + 1] * scale);
    const b = Math.fround(rgbHWC[p * 3 + 2] * scale);

    chw[0 * numPixels + p] = Math.fround((r - Math.fround(IMAGENET_MEAN[0])) / Math.fround(IMAGENET_STD[0]));
    chw[1 * numPixels + p] = Math.fround((g - Math.fround(IMAGENET_MEAN[1])) / Math.fround(IMAGENET_STD[1]));
    chw[2 * numPixels + p] = Math.fround((b - Math.fround(IMAGENET_MEAN[2])) / Math.fround(IMAGENET_STD[2]));
  }
  return chw;
}

/**
 * Potong citra HWC pada kotak tangan (+25%) dan ubah ukuran ke outSize x outSize x 3.
 */
export function cropAndResizeHand(
  imageRGB,
  imgH,
  imgW,
  handLandmarks,
  outSize = CROP_SIZE,
  margin = PAD_RATIO
) {
  const box = computeHandCropBox(handLandmarks, imgW, imgH, margin);
  const cropH = box.y1 - box.y0;
  const cropW = box.x1 - box.x0;
  const isNested = Array.isArray(imageRGB) && Array.isArray(imageRGB[0]);

  const cropFlat = new Float32Array(cropH * cropW * 3);
  for (let r = 0; r < cropH; r++) {
    for (let c = 0; c < cropW; c++) {
      const dst = (r * cropW + c) * 3;
      if (isNested) {
        const px = imageRGB[box.y0 + r][box.x0 + c];
        cropFlat[dst + 0] = px[0];
        cropFlat[dst + 1] = px[1];
        cropFlat[dst + 2] = px[2];
      } else {
        const src = ((box.y0 + r) * imgW + (box.x0 + c)) * 3;
        cropFlat[dst + 0] = imageRGB[src + 0];
        cropFlat[dst + 1] = imageRGB[src + 1];
        cropFlat[dst + 2] = imageRGB[src + 2];
      }
    }
  }
  return resizeBilinearRGB(cropFlat, cropH, cropW, outSize);
}
