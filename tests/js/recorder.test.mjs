/**
 * tests/js/recorder.test.mjs
 * Kontrak 7: Perekam Dataset Multimodal (WAV 16 kHz, resampling, manifest 4 modalitas, ZIP).
 * Menjalankan: node --test tests/js/recorder.test.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  MANIFEST_HEADER,
  MultimodalRecorder,
  buildStoreZip,
  csvEscape,
  encodeWavPCM16,
  resampleLinear
} from "../../web/js/recorder.js";

test("resampleLinear 48 kHz -> 16 kHz menjaga panjang & nilai ujung", () => {
  const n = 48000;
  const x = new Float32Array(n);
  for (let i = 0; i < n; i++) x[i] = i / (n - 1);
  const y = resampleLinear(x, 48000, 16000);
  assert.equal(y.length, 16000);
  assert.ok(Math.abs(y[0] - 0) < 1e-6);
  assert.ok(Math.abs(y[y.length - 1] - 1) < 1e-6);
  assert.ok(Math.abs(y[8000] - 8000 / 15999) < 1e-4); // ramp linear tetap linear
});

test("encodeWavPCM16 menghasilkan header RIFF/WAVE mono 16 kHz 16-bit yang benar", () => {
  const pcm = new Float32Array([0, 0.5, -0.5, 1, -1]);
  const wav = encodeWavPCM16(pcm, 16000);
  const v = new DataView(wav.buffer);
  const str = (o, n) => String.fromCharCode(...wav.slice(o, o + n));
  assert.equal(str(0, 4), "RIFF");
  assert.equal(str(8, 4), "WAVE");
  assert.equal(v.getUint16(22, true), 1);
  assert.equal(v.getUint32(24, true), 16000);
  assert.equal(v.getUint16(34, true), 16);
  assert.equal(v.getUint32(40, true), pcm.length * 2);
  assert.equal(v.getInt16(44 + 2, true), Math.round(0.5 * 32767));
  assert.equal(v.getInt16(44 + 8, true), -32767);
});

test("csvEscape mengamankan koma & kutip pada kalimat", () => {
  assert.equal(csvEscape("Saya makan."), "Saya makan.");
  assert.equal(csvEscape('Halo, "guru"'), '"Halo, ""guru"""');
});

test("MultimodalRecorder menulis 4 modalitas + manifest lengkap", () => {
  const rec = new MultimodalRecorder();
  const kp = Array.from({ length: 10 }, () => Array.from({ length: 86 }, () => [0.5, 0.5, 0]));
  rec.addClip({
    signer: "S01", category: "gloss", target: "MAKAN", label: 7, keypoints: kp,
    sentence: "Saya mau makan, guru.",
    wav: encodeWavPCM16(new Float32Array(160), 16000),
    handJpg: new Uint8Array([0xff, 0xd8, 0xff]),
    portraitJpg: new Uint8Array([0xff, 0xd8, 0xff])
  });
  rec.addClip({ signer: "S01", category: "gloss", target: "AIR", label: 0, keypoints: kp, sentence: "" });
  const s = rec.summary();
  assert.deepEqual(s, { clips: 2, video: 2, image: 1, audio: 1, text: 1, complete: 1 });

  const files = rec.buildFiles();
  const names = files.map((f) => f.name);
  assert.ok(names.includes("S01/gloss/MAKAN/take_01_kp.json"));
  assert.ok(names.includes("S01/gloss/MAKAN/take_01_hand.jpg"));
  assert.ok(names.includes("S01/gloss/MAKAN/take_01.wav"));
  assert.ok(!names.includes("S01/gloss/AIR/take_02.wav")); // audio tidak ada -> tidak ditulis
  const manifest = files.find((f) => f.name === "manifest_selfrec.csv").data.split("\n");
  assert.equal(manifest[0], MANIFEST_HEADER);
  assert.ok(manifest[1].endsWith('"Saya mau makan, guru."'));
  assert.ok(manifest[2].includes(",S01/gloss/AIR/take_02_kp.json,,,,")); // citra/audio kosong

  const zip = buildStoreZip(files);
  assert.equal(new DataView(zip.buffer).getUint32(0, true), 0x04034b50);
});
