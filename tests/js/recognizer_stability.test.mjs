import test from "node:test";
import assert from "node:assert/strict";
import {
  isInSigningSpace,
  hasDetectedHands,
  computeHandMotionEnergy,
  SignRecognizer,
  SIGN_STATE
} from "../../web/js/recognizer.js";
import { classifyAlphabetGeometry, FingerspellRecognizer } from "../../web/js/fingerspell.js";
import { FingerspellMLP } from "../../web/js/fingerspell_mlp.js";
import { readFileSync } from "node:fs";
import { APP_CONFIG } from "../../web/js/config.js";

function makeDummyKeypoints(wristY = 0.5) {
  // 86 keypoints [x, y, z]
  const kp = Array.from({ length: 86 }, () => [0, 0, 0]);
  // Nose
  kp[0] = [0.5, 0.25, 0];
  // Shoulders
  kp[1] = [0.4, 0.4, 0];
  kp[2] = [0.6, 0.4, 0];
  // Left hand landmarks (9..29), 9 is wrist, 17 is MCP
  kp[9] = [0.35, wristY, 0];
  kp[17] = [0.35, wristY - 0.05, 0];
  // Right hand landmarks (30..50), 30 is wrist, 38 is MCP
  kp[30] = [0.65, wristY, 0];
  kp[38] = [0.65, wristY - 0.05, 0];
  return kp;
}

test("isInSigningSpace: deteksi posisi tangan aktif vs istirahat", () => {
  // Tangan diangkat di area dada (y = 0.48) -> harus TRUE (signing space)
  const activeKp = makeDummyKeypoints(0.48);
  assert.equal(isInSigningSpace(activeKp), true, "Tangan di dada harus berada dalam signing space");

  // Tangan di bawah / di atas meja / di pangkuan (y = 0.85) -> harus FALSE (resting)
  const restingKp = makeDummyKeypoints(0.85);
  assert.equal(isInSigningSpace(restingKp), false, "Tangan di pangkuan tidak boleh masuk signing space");

  // Keypoints kosong / null
  assert.equal(isInSigningSpace(null), false);
  assert.equal(isInSigningSpace([]), false);
});

test("hasDetectedHands: validasi keberadaan tangan", () => {
  const kp = makeDummyKeypoints(0.5);
  assert.equal(hasDetectedHands(kp), true);

  const emptyKp = Array.from({ length: 86 }, () => [0, 0, 0]);
  assert.equal(hasDetectedHands(emptyKp), false);
});

test("SignRecognizer: supresi false positive saat tangan diam di posisi istirahat", async () => {
  let predictionCount = 0;
  const recognizer = new SignRecognizer({
    onPrediction: () => {
      predictionCount++;
    }
  });

  const restingKp = makeDummyKeypoints(0.85);

  // Masukkan 30 frame tangan istirahat di meja (1 detik pada 30 FPS)
  for (let i = 0; i < 30; i++) {
    const res = await recognizer.pushFrame(restingKp, { hasVisibleHand: true });
    assert.equal(res, null, "Frame saat tangan istirahat tidak boleh memicu inferensi");
  }

  assert.equal(predictionCount, 0, "Tidak boleh ada prediksi yang ditembakkan saat tangan istirahat");
  assert.equal(recognizer.state, SIGN_STATE.IDLE, "State harus tetap IDLE");
});

test("SignRecognizer: supresi hasil berkeyakinan rendah (confidence threshold)", async () => {
  const recognizer = new SignRecognizer();
  recognizer.minConfidence = 0.60;

  // Mock session yang mengembalikan logits seragam (probabilitas rendah untuk setiap kelas)
  recognizer.session = {
    run: async () => ({
      logits: {
        data: new Float32Array(32).fill(0.1) // Probabilitas masing-masing ~1/32 = 0.03125
      }
    })
  };

  const rawSeq = Array.from({ length: 15 }, () => makeDummyKeypoints(0.45));
  const result = await recognizer.classifySequence(rawSeq);

  assert.equal(result.success, false, "Prediksi dengan confidence rendah harus bernilai success: false");
  assert.equal(result.gloss, null, "Gloss harus null ketika di bawah threshold");
  assert.ok(result.confidence < 0.60, "Confidence harus tercatat apa adanya tanpa manipulasi");
  assert.ok(result.candidateGloss !== null, "Kandidat kelas tetap dicatat untuk keperluan telemetri UI");
});

test("classifyAlphabetGeometry & FingerspellRecognizer: pengenalan bentuk abjad jari 21 titik", () => {
  // Buat 21 titik tangan dengan 4 jari terbuka (B)
  const handB = Array.from({ length: 21 }, () => [0.5, 0.5, 0]);
  handB[0] = [0.5, 0.8, 0];  // wrist
  handB[9] = [0.5, 0.6, 0];  // middle MCP
  handB[2] = [0.45, 0.7, 0];
  handB[4] = [0.48, 0.68, 0]; // thumb
  handB[17] = [0.58, 0.65, 0];

  // 4 jari lurus ke atas (dist tip to wrist > dist pip to wrist)
  // Index
  handB[6] = [0.46, 0.55, 0];
  handB[8] = [0.46, 0.35, 0]; // tip
  // Middle
  handB[10] = [0.50, 0.55, 0];
  handB[12] = [0.50, 0.32, 0]; // tip
  // Ring
  handB[14] = [0.54, 0.55, 0];
  handB[16] = [0.54, 0.35, 0]; // tip
  // Pinky
  handB[18] = [0.58, 0.58, 0];
  handB[20] = [0.58, 0.40, 0]; // tip

  const letterB = classifyAlphabetGeometry(handB);
  assert.equal(letterB, "B", "Empat jari lurus terbuka harus dikenali sebagai huruf B");

  // Buat bentuk Y (ibu jari & kelingking terbuka, 3 jari tengah ditekuk)
  const handY = Array.from({ length: 21 }, () => [0.5, 0.5, 0]);
  handY[0] = [0.5, 0.8, 0]; // wrist
  handY[9] = [0.5, 0.6, 0]; // middle MCP
  handY[17] = [0.58, 0.65, 0];

  // Thumb open wide to the left
  handY[2] = [0.45, 0.75, 0];
  handY[4] = [0.30, 0.65, 0]; // thumb tip far from pinky base
  // Pinky open wide to the right
  handY[18] = [0.58, 0.62, 0];
  handY[20] = [0.68, 0.45, 0]; // pinky tip straight up

  // Middle 3 fingers folded
  handY[6] = [0.48, 0.62, 0];
  handY[8] = [0.48, 0.64, 0]; // index folded
  handY[10] = [0.50, 0.62, 0];
  handY[12] = [0.50, 0.64, 0]; // middle folded
  handY[14] = [0.52, 0.62, 0];
  handY[16] = [0.52, 0.64, 0]; // ring folded

  const letterY = classifyAlphabetGeometry(handY);
  assert.equal(letterY, "Y", "Bentuk jempol dan kelingking terbuka harus dikenali sebagai huruf Y");

  // (Aturan geometri di atas kini hanya riwayat; pengenalan memakai MLP — lihat tes di bawah.)
});

test("SignRecognizer: toleransi tracking dropout 1-2 frame (grace period) tanpa mereset activeBuffer", async () => {
  const recognizer = new SignRecognizer();
  const kp1 = makeDummyKeypoints(0.45);
  const kp2 = makeDummyKeypoints(0.40);
  await recognizer.pushFrame(kp1, { hasVisibleHand: true, timestamp: 0 });
  await recognizer.pushFrame(kp2, { hasVisibleHand: true, timestamp: 33 });
  assert.equal(recognizer.state, SIGN_STATE.RECORDING, "Status harus RECORDING sejak tangan masuk ruang isyarat");
  assert.equal(recognizer.activeBuffer.length, 2, "Segmen dimulai sejak tangan masuk ruang isyarat (meniru klip latih)");

  const emptyFrame = Array.from({ length: 86 }, () => [0, 0, 0]);
  await recognizer.pushFrame(emptyFrame, { hasVisibleHand: false, timestamp: 66 });
  assert.equal(recognizer.activeBuffer.length, 2, "Grace period mempertahankan buffer pada 1-frame dropout");
  assert.equal(recognizer.outOfSpaceFrames, 1);

  await recognizer.pushFrame(makeDummyKeypoints(0.35), { hasVisibleHand: true, timestamp: 99 });
  assert.equal(recognizer.outOfSpaceFrames, 0);
  assert.equal(recognizer.activeBuffer.length, 3, "Buffer bertambah secara kontinu");
});

// ---------------------------------------------------------------- segmentasi meniru klip latih
function movingKp(t, wristY = 0.45) {
  const kp = makeDummyKeypoints(wristY);
  const dx = 0.08 * Math.sin(t / 3);
  for (let i = 9; i < 51; i++) if (kp[i][0] || kp[i][1]) kp[i] = [kp[i][0] + dx, kp[i][1] - Math.abs(dx), 0];
  return kp;
}
function countingSession() {
  const calls = [];
  return { calls, run: async (feeds) => { calls.push(feeds.keypoints.dims); const l = new Float32Array(32); l[7] = 5; return { logits: { data: l } }; } };
}

test("Segmentasi: satu isyarat utuh (naik -> gerak -> turun) = satu klasifikasi berisi seluruh isyarat", async () => {
  const preds = [];
  const rec = new SignRecognizer({ onPrediction: (p) => preds.push(p) });
  rec.session = countingSession();
  let t = 0; const step = () => (t += 33);
  for (let i = 0; i < 10; i++) await rec.pushFrame(makeDummyKeypoints(0.9), { timestamp: step() });   // istirahat
  for (let i = 0; i < 4; i++) await rec.pushFrame(makeDummyKeypoints(0.84), { timestamp: step() });   // tangan naik (di bawah ruang isyarat)
  for (let i = 0; i < 30; i++) await rec.pushFrame(movingKp(i), { timestamp: step() });               // isyarat
  assert.equal(preds.length, 0, "belum boleh klasifikasi selama isyarat berlangsung");
  for (let i = 0; i < 12; i++) await rec.pushFrame(makeDummyKeypoints(0.9), { timestamp: step() });  // tangan turun
  assert.equal(preds.length, 1, "tepat satu klasifikasi per isyarat");
  assert.equal(preds[0].gloss, "MAKAN");
  assert.ok(rec.lastSegment.frames >= 30, `segmen harus memuat seluruh isyarat (+pre-roll), dapat ${rec.lastSegment.frames}`);
  assert.equal(rec.session.calls.length, 3, "test-time augmentation: 3 potongan waktu");
});

test("Segmentasi: tangan diam di ruang isyarat (abjad/tahan) TIDAK diklasifikasi sebagai kata", async () => {
  const preds = [];
  const rec = new SignRecognizer({ onPrediction: (p) => preds.push(p) });
  rec.session = countingSession();
  let t = 0;
  for (let i = 0; i < 80; i++) await rec.pushFrame(makeDummyKeypoints(0.45), { timestamp: (t += 33) });
  for (let i = 0; i < 12; i++) await rec.pushFrame(makeDummyKeypoints(0.9), { timestamp: (t += 33) });
  assert.equal(preds.length, 0, "tanpa gerak = bukan isyarat kata");
});

test("Segmentasi: cancelSegment (sedang mengeja) menahan klasifikasi kata sampai tangan turun", async () => {
  const preds = [];
  const rec = new SignRecognizer({ onPrediction: (p) => preds.push(p) });
  rec.session = countingSession();
  let t = 0;
  for (let i = 0; i < 10; i++) await rec.pushFrame(movingKp(i), { timestamp: (t += 33) });
  rec.cancelSegment("fingerspelling");
  for (let i = 0; i < 20; i++) await rec.pushFrame(movingKp(i), { timestamp: (t += 33) });
  for (let i = 0; i < 12; i++) await rec.pushFrame(makeDummyKeypoints(0.9), { timestamp: (t += 33) });
  assert.equal(preds.length, 0, "segmen yang dibatalkan tidak boleh menghasilkan kata");
  for (let i = 0; i < 30; i++) await rec.pushFrame(movingKp(i), { timestamp: (t += 33) });
  for (let i = 0; i < 12; i++) await rec.pushFrame(makeDummyKeypoints(0.9), { timestamp: (t += 33) });
  assert.equal(preds.length, 1, "setelah tangan turun, isyarat kata berikutnya kembali dikenali");
});

test("SignRecognizer: ambang batas 0.35 menerima prediksi valid dengan margin kuat", async () => {
  const recognizer = new SignRecognizer();
  recognizer.minConfidence = 0.35;

  // Mock session ONNX yang mengembalikan kelas 0 (AIR) dengan confidence ~40% dan runner-up ~15%
  recognizer.session = {
    run: async () => {
      const logits = new Float32Array(32).fill(0.0);
      logits[0] = 3.2; // Kelas AIR ~40%
      logits[1] = 2.2; // Kelas BELAJAR ~15%
      return { logits: { data: logits } };
    }
  };

  const rawSeq = Array.from({ length: 15 }, () => makeDummyKeypoints(0.45));
  const result = await recognizer.classifySequence(rawSeq);

  assert.equal(result.success, true, "Prediksi dengan confidence ~40% dan margin kuat harus berhasil (success: true)");
  assert.equal(result.gloss, "AIR", "Gloss yang terpilih harus AIR");
  assert.ok(result.confidence >= 0.35, "Confidence harus >= 0.35");
  assert.ok(result.margin >= 0.08, "Margin harus >= 0.08");
  assert.equal(result.rejectionReason, "accepted");
});

test("isInSigningSpace: deteksi tangan aktif ketika ujung jari terangkat meski pergelangan di batas bawah", () => {
  // Posisi bahu di y = 0.45, pergelangan tangan di y = 0.79 (dekat batas), tetapi jari telunjuk terangkat di y = 0.60
  const kp = makeDummyKeypoints(0.79);
  kp[17] = [0.35, 0.60, 0]; // left index fingertip terangkat di dada
  assert.equal(isInSigningSpace(kp), true, "Ujung jari telunjuk terangkat harus dianggap dalam signing space");
});

test("isInSigningSpace: adaptif terhadap posisi kamera dekat (midShoulderY >= 0.50)", () => {
  // Posisi bahu di y = 0.65 (pengguna duduk sangat dekat webcam seperti di video pengujian)
  const kpClose = makeDummyKeypoints(0.82);
  kpClose[1] = [0.4, 0.65, 0];
  kpClose[2] = [0.6, 0.65, 0];
  // Tangan berada di y = 0.82 (di dada bawah/perut atas saat dekat)
  kpClose[9] = [0.35, 0.82, 0];
  kpClose[17] = [0.35, 0.80, 0];
  kpClose[30] = [0.65, 0.82, 0];
  kpClose[38] = [0.65, 0.80, 0];

  assert.equal(
    isInSigningSpace(kpClose),
    true,
    "Tangan di dada bawah saat posisi bahu dekat kamera (y=0.65) harus tetap masuk ruang isyarat"
  );
});

test("checkCameraFraming: mendeteksi posisi terlalu dekat dan tangan terpotong di tepi", async () => {
  const { checkCameraFraming } = await import("../../web/js/recognizer.js");

  // Posisi pundak terlalu dekat (midShoulderY = 0.65 > 0.55)
  const kpClose = makeDummyKeypoints(0.80);
  kpClose[1] = [0.4, 0.65, 0];
  kpClose[2] = [0.6, 0.65, 0];
  const framingClose = checkCameraFraming(kpClose);
  assert.equal(framingClose.ok, false);
  assert.equal(framingClose.code, "TOO_CLOSE");

  // Posisi normal
  const kpNormal = makeDummyKeypoints(0.50);
  const framingNormal = checkCameraFraming(kpNormal);
  assert.equal(framingNormal.ok, true);
  assert.equal(framingNormal.warning, null);
});

test("SignRecognizer: dua tingkat ambang batas (candidate vs auto-speak)", async () => {
  const recognizer = new SignRecognizer();
  recognizer.candidateConfidenceThreshold = 0.25;
  recognizer.autoSpeakConfidenceThreshold = 0.50;
  recognizer.autoSpeakMarginThreshold = 0.10;
  recognizer.minConfidence = 0.50;

  // Kasus 1: Confidence 0.38 (di atas candidate 0.25, di bawah auto-speak 0.50)
  // Harus menghasilkan candidateAvailable: true, tetapi canAutoSpeak: false
  recognizer.session = {
    run: async () => {
      const logits = new Float32Array(32).fill(0.0);
      logits[0] = 3.0; // ~38%
      logits[1] = 1.8; // ~12%
      return { logits: { data: logits } };
    }
  };

  const rawSeq = Array.from({ length: 15 }, () => makeDummyKeypoints(0.45));
  const res1 = await recognizer.classifySequence(rawSeq);

  assert.equal(res1.canAutoSpeak, false, "Confidence 38% tidak boleh auto-speak");
  assert.equal(res1.candidateAvailable, true, "Confidence 38% harus tampil sebagai kandidat klik UI");
  assert.equal(res1.candidateGloss, "AIR");
  assert.equal(res1.rejectionReason, "needs_confirmation");

  // Kasus 2: Confidence 0.62 dengan margin kuat (di atas auto-speak 0.50)
  recognizer.session = {
    run: async () => {
      const logits = new Float32Array(32).fill(0.0);
      logits[0] = 4.5; // ~62%
      logits[1] = 1.0; // ~4%
      return { logits: { data: logits } };
    }
  };

  const res2 = await recognizer.classifySequence(rawSeq);
  assert.equal(res2.canAutoSpeak, true, "Confidence 62% harus auto-speak");
  assert.equal(res2.success, true);
  assert.equal(res2.gloss, "AIR");
  assert.equal(res2.rejectionReason, "accepted");
});

test("SignRecognizer: getDynamicThresholds menghitung frame sesuai FPS", () => {
  const recognizer = new SignRecognizer();

  // Pada 15 FPS (perangkat lambat/low-end webcam)
  const t15 = recognizer.getDynamicThresholds(15);
  assert.equal(t15.minActive, 4); // 250ms -> 3.75 -> 4
  assert.equal(t15.pauseFrames, 4); // 250ms -> 3.75 -> 4
  assert.ok(t15.maxActive <= 40);

  // Pada 30 FPS (kamera standar 30 FPS)
  const t30 = recognizer.getDynamicThresholds(30);
  assert.equal(t30.minActive, 8); // 250ms -> 7.5 -> 8
  assert.equal(t30.pauseFrames, 8); // 250ms -> 7.5 -> 8
  assert.ok(t30.maxActive >= 50);
});


// ---------------------------------------------------------------- abjad jari BISINDO (MLP landmark dua tangan)
const mlp = new FingerspellMLP(JSON.parse(readFileSync(new URL("../../web/model/fingerspell_mlp.json", import.meta.url))));
const realSamples = JSON.parse(readFileSync(new URL("./fixtures/fingerspell_real_samples.json", import.meta.url)));

test("FingerspellRecognizer (MLP): sampel landmark BISINDO asli A–Z dikenali (>= 90%)", () => {
  let ok = 0;
  for (const s of realSamples) {
    const rec = new FingerspellRecognizer({ model: mlp });
    let out = null;
    for (let i = 0; i < 8; i++) out = rec.pushHands(s.hands[0], s.hands[1] || null, i * 33) || out;
    if (out && out.letter === s.label) ok += 1;
  }
  assert.ok(ok / realSamples.length >= 0.9, `akurasi ${ok}/${realSamples.length}`);
});

test("FingerspellRecognizer (MLP): stabil — belum keluar sebelum 8 frame, keluar sekali per tahanan, keyakinan asli", () => {
  const s = realSamples.find((x) => x.label === "B");
  const emitted = [];
  const rec = new FingerspellRecognizer({ model: mlp, onPrediction: (p) => emitted.push(p) });
  for (let i = 0; i < 7; i++) rec.pushHands(s.hands[0], s.hands[1] || null, i * 33);
  assert.equal(emitted.length, 0, "belum boleh keluar sebelum 8 frame");
  for (let i = 7; i < 40; i++) rec.pushHands(s.hands[0], s.hands[1] || null, i * 33);
  assert.equal(emitted.length, 1, "huruf yang ditahan hanya keluar sekali");
  assert.equal(emitted[0].letter, "B");
  assert.ok(emitted[0].confidence > 0.5 && emitted[0].confidence <= 1 && emitted[0].confidence !== 0.93);
  rec.pushHands(null, null, 2000);                    // tangan turun -> kunci dilepas
  for (let i = 0; i < 8; i++) rec.pushHands(s.hands[0], s.hands[1] || null, 3000 + i * 33);
  assert.equal(emitted.length, 2, "setelah tangan turun, huruf yang sama boleh keluar lagi");
});

test("FingerspellRecognizer (MLP): huruf dua tangan memakai kedua tangan", () => {
  const two = realSamples.filter((x) => x.hands.length === 2);
  assert.ok(two.length > 10);
  let ok = 0;
  for (const s of two) {
    const rec = new FingerspellRecognizer({ model: mlp });
    let out = null;
    for (let i = 0; i < 8; i++) out = rec.pushHands(s.hands[0], s.hands[1], i * 33) || out;
    if (out && out.letter === s.label && out.twoHanded) ok += 1;
  }
  assert.ok(ok / two.length >= 0.9, `dua tangan ${ok}/${two.length}`);
});
