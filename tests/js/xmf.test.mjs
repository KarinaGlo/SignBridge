// Paritas fungsi preprocessing XMF: web/js/xmf.js == signbridge/xmf (fixture dari Python)
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

globalThis.window = globalThis.window || {};
const { encodeText, personBoxFromShoulders, uniformIndices, normalizeHandsStatic, fitAudio, medianBox, unionBox } =
  await import("../../web/js/xmf.js");
const fx = JSON.parse(fs.readFileSync(new URL("./fixtures/xmf_fixture.json", import.meta.url)));
const close = (a, b, tol) => assert.ok(Math.abs(a - b) <= tol, `${a} vs ${b}`);

test("encodeText identik dengan Python", () => {
  for (const c of fx.text) assert.deepEqual(encodeText(c.text), c.ids);
});

test("kotak crop badan-atas identik", () => {
  for (const c of fx.person_box) personBoxFromShoulders(c.l, c.r, c.w, c.h).forEach((v, i) => close(v, c.box[i], 1e-6));
});

test("indeks frame merata identik", () => {
  for (const c of fx.uniform) assert.deepEqual(uniformIndices(c.n, c.k), c.idx);
});

test("normalisasi tangan statis identik", () => {
  const kp = fx.hands.kp.map((p) => p.map((v) => (v === null ? NaN : v)));
  normalizeHandsStatic(kp).forEach((p, i) => p.forEach((v, j) => close(v, fx.hands.out[i][j], 2e-5)));
});

test("fitAudio identik (pemotongan hening + penempatan di tengah)", () => {
  const y = fitAudio(Float32Array.from(fx.audio.pcm), fx.audio.n);
  close(y.reduce((s, v) => s + Math.abs(v), 0), fx.audio.out_sum, 1e-2);
  assert.equal(y.findIndex((v) => Math.abs(v) > 1e-6), fx.audio.first_nz);
});

test("medianBox & unionBox", () => {
  assert.deepEqual(medianBox([null], 200, 100), [100, 50, 100]);
  assert.deepEqual(medianBox([[1, 2, 3], [3, 4, 5], null, [2, 3, 4]], 9, 9), [2, 3, 4]);
  assert.deepEqual(unionBox([[10, 10, 4], [20, 10, 4]]), [15, 10, 14]);
});
