// Paritas fitur & MLP abjad jari: Python (signbridge/fingerspell_landmarks.py) vs JS (web/js/fingerspell_mlp.js).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { FingerspellMLP, handFeatures } from "../../web/js/fingerspell_mlp.js";

const cases = JSON.parse(readFileSync(new URL("./fixtures/fingerspell_mlp_fixture.json", import.meta.url)));
const model = new FingerspellMLP(JSON.parse(readFileSync(new URL("../../web/model/fingerspell_mlp.json", import.meta.url))));

test("handFeatures identik dengan Python (< 1e-4)", () => {
  for (const c of cases) {
    const f = handFeatures(c.hands);
    c.feat.forEach((v, i) => assert.ok(Math.abs(f[i] - v) < 1e-4, `fitur ${i}: ${f[i]} vs ${v}`));
  }
});

test("probabilitas MLP identik dengan Python (< 1e-4) dan berjumlah 1", () => {
  for (const c of cases) {
    const p = model.predictProba(handFeatures(c.hands));
    c.proba.forEach((v, i) => assert.ok(Math.abs(p[i] - v) < 1e-4, `kelas ${i}: ${p[i]} vs ${v}`));
    assert.ok(Math.abs(p.reduce((a, b) => a + b, 0) - 1) < 1e-9);
  }
});

test("menerima format landmark MediaPipe {x,y,z}", () => {
  const h = cases[1].hands[0].map(([x, y]) => ({ x, y, z: 0 }));
  assert.deepEqual(Array.from(handFeatures([h])), Array.from(handFeatures([cases[1].hands[0]])));
});
