/**
 * tests/js/parity.test.mjs
 * Kontrak 3 (PDF Hal. 11 & 15): Uji paritas numerik signbridge/features.py <-> web/js/features.js
 * Menjalankan: node --test tests/js/parity.test.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  NUM_NODES,
  NUM_COORDS,
  SEQ_LEN,
  selectFromHolistic,
  trimInactive,
  normalizePose,
  resampleFrames,
  preprocessKeypoints,
  flattenKeypoints
} from "../../web/js/features.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturePath = path.join(__dirname, "fixtures", "parity_fixture.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf-8"));

function maxAbsDiffNested(a, b) {
  let maxDiff = 0.0;
  const stack = [[a, b]];
  while (stack.length > 0) {
    const [x, y] = stack.pop();
    if (Array.isArray(x) && Array.isArray(y)) {
      assert.equal(x.length, y.length, "Panjang array tidak sama");
      for (let i = 0; i < x.length; i++) {
        stack.push([x[i], y[i]]);
      }
    } else {
      const d = Math.abs(Number(x) - Number(y));
      if (d > maxDiff) maxDiff = d;
    }
  }
  return maxDiff;
}

test("Kontrak 1 & 3: selectFromHolistic identik dengan Python (< 1e-6)", () => {
  const { pose33, left21, right21, face468, expected_selected86 } = fixture.holistic;
  const jsSelected = selectFromHolistic(pose33, left21, right21, face468);
  assert.equal(jsSelected.length, NUM_NODES);
  assert.equal(jsSelected[0].length, NUM_COORDS);
  const diff = maxAbsDiffNested(jsSelected, expected_selected86);
  assert.ok(diff < 1e-5, `Max diff selectFromHolistic terlalu besar: ${diff}`);
});

test("Kontrak 3: trimInactive memangkas frame diam identik dengan Python", () => {
  const { kp_raw, expected_trimmed } = fixture.sequence;
  const jsTrimmed = trimInactive(kp_raw);
  assert.equal(jsTrimmed.length, expected_trimmed.length);
  const diff = maxAbsDiffNested(jsTrimmed, expected_trimmed);
  assert.ok(diff < 1e-5, `Max diff trimInactive terlalu besar: ${diff}`);
});

test("Kontrak 3: normalizePose (pusat bahu & lebar bahu) identik dengan Python (< 1e-5)", () => {
  const { expected_trimmed, expected_normed } = fixture.sequence;
  const jsNormed = normalizePose(expected_trimmed);
  const diff = maxAbsDiffNested(jsNormed, expected_normed);
  assert.ok(diff < 1e-5, `Max diff normalizePose terlalu besar: ${diff}`);
});

test("Kontrak 3: resampleFrames(64) identik dengan Python (< 1e-5)", () => {
  const { expected_normed, expected_resampled } = fixture.sequence;
  const jsResampled = resampleFrames(expected_normed, SEQ_LEN);
  assert.equal(jsResampled.length, SEQ_LEN);
  const diff = maxAbsDiffNested(jsResampled, expected_resampled);
  assert.ok(diff < 1e-5, `Max diff resampleFrames terlalu besar: ${diff}`);
});

test("Kontrak 3: preprocessKeypoints end-to-end identik dengan Python (< 1e-5)", () => {
  const { kp_raw, expected_preprocessed } = fixture.sequence;
  const jsPre = preprocessKeypoints(kp_raw, SEQ_LEN, true);
  const diff = maxAbsDiffNested(jsPre, expected_preprocessed);
  assert.ok(diff < 1e-5, `Max diff preprocessKeypoints terlalu besar: ${diff}`);

  const flat = flattenKeypoints(jsPre);
  assert.equal(flat.length, SEQ_LEN * NUM_NODES * NUM_COORDS);
});

