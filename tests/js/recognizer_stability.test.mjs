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

  // FingerspellRecognizer temporal stability:
  let emitted = null;
  const recognizer = new FingerspellRecognizer({
    onPrediction: (pred) => {
      emitted = pred;
    }
  });

  // Kirim 6 frame (belum mencapai batas konsistensi 7 frame)
  for (let i = 0; i < 6; i++) {
    recognizer.pushHandFrame(handB);
  }
  assert.equal(emitted, null, "Belum boleh emit prediksi jika belum stabil 7 frame");

  // Kirim frame ke-7 sampai 9
  for (let i = 0; i < 3; i++) {
    recognizer.pushHandFrame(handB);
  }
  assert.ok(emitted !== null, "Harus emit prediksi setelah stabil 7+ frame");
  assert.equal(emitted.letter, "B", "Huruf yang di-emit harus B");
});

test("SignRecognizer: toleransi tracking dropout 1-2 frame (grace period) tanpa mereset activeBuffer", async () => {
  const recognizer = new SignRecognizer();
  recognizer.minConfidence = 0.35;

  // Masukkan frame dengan gerakan tangan aktif
  const kp1 = makeDummyKeypoints(0.45);
  const kp2 = makeDummyKeypoints(0.40);

  await recognizer.pushFrame(kp1, { hasVisibleHand: true });
  await recognizer.pushFrame(kp2, { hasVisibleHand: true });

  assert.equal(recognizer.state, SIGN_STATE.RECORDING, "Status harus berpindah ke RECORDING");
  assert.equal(recognizer.activeBuffer.length, 1, "Buffer harus menyimpan frame aktif");

  // Simulasi 1 frame tracking hilang sementara (misal tangan blur atau kedip)
  const emptyFrame = Array.from({ length: 86 }, () => [0, 0, 0]);
  await recognizer.pushFrame(emptyFrame, { hasVisibleHand: false });

  // Karena toleransi grace period (outOfSpaceFrames < 3), buffer tidak langsung di-reset!
  assert.equal(recognizer.activeBuffer.length, 1, "Grace period harus mempertahankan activeBuffer pada 1-frame dropout");
  assert.equal(recognizer.outOfSpaceFrames, 1, "outOfSpaceFrames tercatat 1");

  // Frame berikutnya tangan kembali terdeteksi
  const kp3 = makeDummyKeypoints(0.35);
  await recognizer.pushFrame(kp3, { hasVisibleHand: true });

  assert.equal(recognizer.outOfSpaceFrames, 0, "outOfSpaceFrames kembali direset ke 0 saat tangan kembali terdeteksi");
  assert.equal(recognizer.activeBuffer.length, 2, "Buffer bertambah secara kontinu");
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
