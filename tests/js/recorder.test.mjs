/**
 * tests/js/recorder.test.mjs
 * Kontrak 7: Perekam Dataset Multimodal (WAV 16 kHz, resampling, manifest 4 modalitas, ZIP).
 * Menjalankan: node --test tests/js/recorder.test.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  MANIFEST_HEADER,
  MultimodalCapture,
  MultimodalRecorder,
  buildStoreZip,
  classifyMicrophoneError,
  csvEscape,
  encodeWavPCM16,
  resampleLinear
} from "../../web/js/recorder.js";
import { CLASSROOM_CONTEXT_PROMPTS, BISINDO_GLOSSES } from "../../web/js/config.js";
import { drawSkeleton86 } from "../../web/js/vision.js";
import { speakText } from "../../web/js/speech.js";

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
  const clip1 = rec.addClip({
    signer: "S01", category: "gloss", target: "MAKAN", label: 7, keypoints: kp,
    sentence: "Saya mau makan, guru.",
    wav: encodeWavPCM16(new Float32Array(160), 16000),
    handJpg: new Uint8Array([0xff, 0xd8, 0xff]),
    portraitJpg: new Uint8Array([0xff, 0xd8, 0xff])
  });
  const clip2 = rec.addClip({ signer: "S01", category: "gloss", target: "AIR", label: 0, keypoints: kp, sentence: "" });
  
  // Verifikasi standarisasi sample identity SB_<SIGNER>_<TARGET>_T<TAKE>
  assert.equal(clip1.clipId, "SB_S01_MAKAN_T01");
  assert.equal(clip1.sampleId, "SB_S01_MAKAN_T01");
  assert.equal(clip2.clipId, "SB_S01_AIR_T02");
  assert.equal(clip2.sampleId, "SB_S01_AIR_T02");

  const s = rec.summary();
  assert.deepEqual(s, { clips: 2, video: 2, image: 1, audio: 1, text: 1, complete: 1 });

  const files = rec.buildFiles();
  const names = files.map((f) => f.name);
  assert.ok(names.includes("S01/gloss/MAKAN/take_01_kp.json"));
  assert.ok(names.includes("S01/gloss/MAKAN/take_01_hand.jpg"));
  assert.ok(names.includes("S01/gloss/MAKAN/take_01.wav"));
  assert.ok(!names.includes("S01/gloss/AIR/take_02.wav")); // audio tidak ada -> tidak ditulis

  // Periksa metadata json dan keypoint json mengandung sample_id dan clip_id
  const kpJson = JSON.parse(files.find((f) => f.name === "S01/gloss/MAKAN/take_01_kp.json").data);
  assert.equal(kpJson.clip_id, "SB_S01_MAKAN_T01");
  assert.equal(kpJson.sample_id, "SB_S01_MAKAN_T01");

  const metaJson = JSON.parse(files.find((f) => f.name === "S01/gloss/MAKAN/take_01_meta.json").data);
  assert.equal(metaJson.clip_id, "SB_S01_MAKAN_T01");
  assert.equal(metaJson.sample_id, "SB_S01_MAKAN_T01");
  assert.deepEqual(metaJson.modalities, { video: true, image: true, audio: true, text: true });

  const manifest = files.find((f) => f.name === "manifest_selfrec.csv").data.split("\n");
  assert.equal(manifest[0], MANIFEST_HEADER);
  assert.ok(manifest[1].startsWith("SB_S01_MAKAN_T01,S01,gloss,MAKAN,7,1,"));
  assert.ok(manifest[1].endsWith('"Saya mau makan, guru."'));
  assert.ok(manifest[2].includes(",S01/gloss/AIR/take_02_kp.json,,,,")); // citra/audio kosong

  const zip = buildStoreZip(files);
  assert.equal(new DataView(zip.buffer).getUint32(0, true), 0x04034b50);
});

test("CLASSROOM_CONTEXT_PROMPTS mencakup 32 konsep BISINDO secara lengkap", () => {
  for (const gloss of BISINDO_GLOSSES) {
    const prompt = CLASSROOM_CONTEXT_PROMPTS[gloss];
    assert.ok(prompt, `Prompt konteks untuk gloss ${gloss} harus tersedia`);
    assert.ok(prompt.length >= 10, `Prompt konteks untuk ${gloss} harus memiliki panjang memadai`);
  }
});

test("MultimodalRecorder mendukung penutur S05 (Expert BISINDO) dengan sample_id baku", () => {
  const rec = new MultimodalRecorder();
  const kp = Array.from({ length: 15 }, () => Array.from({ length: 86 }, () => [0.5, 0.5, 0]));
  const clip = rec.addClip({
    signer: "S05",
    category: "gloss",
    target: "BELAJAR",
    label: 1,
    keypoints: kp,
    sentence: "Mari kita buka buku modul bersama.",
    wav: encodeWavPCM16(new Float32Array(320), 16000),
    handJpg: new Uint8Array([0xff, 0xd8, 0xff]),
    portraitJpg: new Uint8Array([0xff, 0xd8, 0xff])
  });

  assert.equal(clip.clipId, "SB_S05_BELAJAR_T01");
  assert.equal(clip.sampleId, "SB_S05_BELAJAR_T01");
  assert.equal(clip.signer, "S05");

  const files = rec.buildFiles();
  const fileNames = files.map((f) => f.name);
  assert.ok(fileNames.includes("S05/gloss/BELAJAR/take_01_kp.json"));
  assert.ok(fileNames.includes("S05/gloss/BELAJAR/take_01_hand.jpg"));
  assert.ok(fileNames.includes("S05/gloss/BELAJAR/take_01.wav"));
  assert.ok(fileNames.includes("S05/gloss/BELAJAR/take_01_meta.json"));

  const meta = JSON.parse(files.find((f) => f.name === "S05/gloss/BELAJAR/take_01_meta.json").data);
  assert.equal(meta.clip_id, "SB_S05_BELAJAR_T01");
  assert.equal(meta.sample_id, "SB_S05_BELAJAR_T01");

  const manifest = files.find((f) => f.name === "manifest_selfrec.csv").data;
  assert.ok(manifest.includes("SB_S05_BELAJAR_T01,S05,gloss,BELAJAR,1,1,"));
});

test("drawSkeleton86 menghormati parameter clear: true vs clear: false", () => {
  const createMockCtx = () => {
    const calls = [];
    return {
      calls,
      clearRect(x, y, w, h) { calls.push({ method: "clearRect", args: [x, y, w, h] }); },
      save() { calls.push({ method: "save" }); },
      restore() { calls.push({ method: "restore" }); },
      beginPath() { calls.push({ method: "beginPath" }); },
      moveTo(x, y) { calls.push({ method: "moveTo", args: [x, y] }); },
      lineTo(x, y) { calls.push({ method: "lineTo", args: [x, y] }); },
      stroke() { calls.push({ method: "stroke" }); },
      arc(x, y, r, sa, ea) { calls.push({ method: "arc", args: [x, y, r, sa, ea] }); },
      fill() { calls.push({ method: "fill" }); },
      fillRect(x, y, w, h) { calls.push({ method: "fillRect", args: [x, y, w, h] }); },
      strokeRect(x, y, w, h) { calls.push({ method: "strokeRect", args: [x, y, w, h] }); },
      translate(x, y) { calls.push({ method: "translate", args: [x, y] }); },
      scale(x, y) { calls.push({ method: "scale", args: [x, y] }); },
      fillText(text, x, y) { calls.push({ method: "fillText", args: [text, x, y] }); },
      measureText(text) { return { width: (text || "").length * 6 }; },
      canvas: { id: "rec-camera-preview", width: 640, height: 480 }
    };
  };

  const kp86 = Array.from({ length: 86 }, () => [0.5, 0.5, 0]);

  // Saat clear = true (default), clearRect dipanggil
  const ctxWithClear = createMockCtx();
  drawSkeleton86(ctxWithClear, kp86, 640, 480, { clear: true });
  assert.ok(ctxWithClear.calls.some((c) => c.method === "clearRect"));

  // Saat clear = false, clearRect TIDAK dipanggil (mencegah frame video terhapus)
  const ctxWithoutClear = createMockCtx();
  drawSkeleton86(ctxWithoutClear, kp86, 640, 480, { clear: false });
  assert.ok(!ctxWithoutClear.calls.some((c) => c.method === "clearRect"));
});

test("speakText dinonaktifkan sepenuhnya saat berada di panel-recorder dan aktif kembali di panel-translate", () => {
  const spoken = [];
  globalThis.window = {
    signBridgeApp: { currentAppTab: "panel-recorder" },
    speechSynthesis: {
      speak(u) { spoken.push(u); },
      cancel() {}
    }
  };

  // Saat di panel-recorder, speakText mengembalikan false dan TIDAK memicu TTS
  const resRecorder = speakText("Halo dunia", "id-ID");
  assert.equal(resRecorder, false);
  assert.equal(spoken.length, 0, "TTS tidak boleh dipanggil saat di panel-recorder");

  // Saat beralih ke panel-translate, speakText kembali aktif
  globalThis.window.signBridgeApp.currentAppTab = "panel-translate";
  globalThis.SpeechSynthesisUtterance = class {
    constructor(text) { this.text = text; }
  };
  const resTranslate = speakText("Halo dunia", "id-ID");
  assert.equal(resTranslate, true);
  assert.equal(spoken.length, 1);
  assert.equal(spoken[0].text, "Halo dunia");

  // Cleanup mock global
  delete globalThis.window;
  delete globalThis.SpeechSynthesisUtterance;
});

test("MultimodalCapture.pushFrame mencatat frame_index, timestamp_ms monotonik, valid_hand, dan keypoints", async () => {
  const cap = new MultimodalCapture();
  const kp = Array.from({ length: 86 }, () => [0.5, 0.5, 0]);
  const hand21 = Array.from({ length: 21 }, () => ({ x: 0.4, y: 0.5, z: 0 }));

  cap.active = true;
  cap.recordingStartMs = performance.now();
  cap.pushFrame(kp, hand21, null);
  await new Promise((r) => setTimeout(r, 15));
  cap.pushFrame(kp, null, null); // tidak ada tangan terdeteksi
  cap.active = false;

  assert.equal(cap.frameRecords.length, 2);
  assert.equal(cap.frameRecords[0].frame_index, 0);
  assert.equal(cap.frameRecords[0].valid_hand, true);
  assert.equal(cap.frameRecords[0].keypoints.length, 86);
  assert.equal(cap.frameRecords[1].frame_index, 1);
  assert.equal(cap.frameRecords[1].valid_hand, false);
  assert.ok(cap.frameRecords[1].timestamp_ms >= cap.frameRecords[0].timestamp_ms);

  const rec = new MultimodalRecorder();
  rec.addClip({
    signer: "S01",
    category: "gloss",
    target: "AIR",
    keypoints: cap.frames,
    frameRecords: cap.frameRecords,
    audioStatus: "missing",
    audioReason: "permission_denied"
  });
  const files = rec.buildFiles();
  const kpJson = JSON.parse(files.find((f) => f.name === "S01/gloss/AIR/take_01_kp.json").data);
  const metaJson = JSON.parse(files.find((f) => f.name === "S01/gloss/AIR/take_01_meta.json").data);
  assert.equal(kpJson.frame_records.length, 2);
  assert.equal(metaJson.frame_timestamps_ms.length, 2);
  assert.equal(metaJson.audio_status, "missing");
  assert.equal(metaJson.audio_missing_reason, "permission_denied");
  assert.equal(metaJson.modalities.audio, false);
});

test("MultimodalRecorder menolak target kosong, HALO, atau gloss di luar Dictionary B", () => {
  const rec = new MultimodalRecorder();
  const kp = Array.from({ length: 8 }, () => Array.from({ length: 86 }, () => [0.5, 0.5, 0]));

  assert.throws(() => rec.addClip({ signer: "S01", category: "gloss", target: "", keypoints: kp }), /wajib dipilih/i);
  assert.throws(() => rec.addClip({ signer: "S01", category: "gloss", target: "HALO", keypoints: kp }), /Dictionary B/i);
  assert.throws(() => rec.addClip({ signer: "S01", category: "gloss", target: "AIR", label: 99, keypoints: kp }), /tidak cocok/i);
  assert.equal(rec.clips.length, 0);
});

test("classifyMicrophoneError menandai izin ditolak sebagai missing tanpa memalsukan audio", () => {
  const denied = classifyMicrophoneError({ name: "NotAllowedError" });
  assert.equal(denied.status, "missing");
  assert.equal(denied.reason, "permission_denied");
  assert.match(denied.message, /ditolak/i);

  const notFound = classifyMicrophoneError({ name: "NotFoundError" });
  assert.equal(notFound.status, "missing");
  assert.equal(notFound.reason, "device_not_found");
});
