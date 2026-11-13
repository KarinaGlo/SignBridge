/**
 * tests/js/handcrop.test.mjs
 * Kontrak 4 & 5 (PDF Hal. 11 & 23): Uji paritas signbridge/image/crop.py <-> web/js/handcrop.js
 * Menjalankan: node --test tests/js/handcrop.test.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  computeHandCropBox,
  cropAndResizeHand,
  normalizeImagenet
} from "../../web/js/handcrop.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturePath = path.join(__dirname, "fixtures", "parity_fixture.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf-8"));

test("Kontrak 4: computeHandCropBox (+25% margin) identik dengan Python", () => {
  const { img_h, img_w, hand_lm, expected_box } = fixture.handcrop;
  const jsBox = computeHandCropBox(hand_lm, img_w, img_h, 0.25);
  assert.deepEqual(jsBox, expected_box);
});

test("Kontrak 4 & 5: cropAndResizeHand dan normalizeImagenet identik dengan Python (< 1e-5)", () => {
  const {
    img_h,
    img_w,
    img_rgb,
    hand_lm,
    out_size,
    expected_resized,
    expected_imagenet_chw
  } = fixture.handcrop;

  const jsResized = cropAndResizeHand(img_rgb, img_h, img_w, hand_lm, out_size, 0.25);
  assert.equal(jsResized.length, expected_resized.length);

  let maxDiffResize = 0.0;
  for (let i = 0; i < jsResized.length; i++) {
    const d = Math.abs(jsResized[i] - expected_resized[i]);
    if (d > maxDiffResize) maxDiffResize = d;
  }
  assert.ok(maxDiffResize < 1e-4, `Max diff cropAndResizeHand: ${maxDiffResize}`);

  const jsCHW = normalizeImagenet(jsResized, out_size);
  assert.equal(jsCHW.length, expected_imagenet_chw.length);

  let maxDiffNorm = 0.0;
  for (let i = 0; i < jsCHW.length; i++) {
    const d = Math.abs(jsCHW[i] - expected_imagenet_chw[i]);
    if (d > maxDiffNorm) maxDiffNorm = d;
  }
  assert.ok(maxDiffNorm < 1e-4, `Max diff normalizeImagenet: ${maxDiffNorm}`);
});

