/**
 * web/js/recognizer.js
 * Mesin Pengenalan Bahasa Isyarat BISINDO berbasis ONNX Runtime Web (student.onnx)
 * Tervalidasi 100% dengan Model M0 Student Baseline (best_model.pt).
 *
 * Prinsip Arsitektur Inferensi (Remediasi Tahap 3):
 * 1. Neural Network Primer: Kelas prediksi dan confidence ditentukan 100% oleh model ONNX M0.
 * 2. Isolasi Stokoe: Heuristik Stokoe TIDAK DIGUNAKAN untuk memilih kelas atau mengubah confidence.
 * 3. Transparansi Kegagalan: Jika model gagal dimuat atau runtime error, sistem menampilkan status error
 *    secara terbuka tanpa fallback manipulatif ke aturan heuristik.
 * 4. Sinkronisasi Penuh: 32 Kelas output terikat ketat dengan urutan neuron output [1, 32].
 */

import { APP_CONFIG, BISINDO_GLOSSES, CLASSROOM_CONCEPTS, PHONOLOGY_DB } from "./config.js";
import { NUM_COORDS, NUM_NODES, SEQ_LEN, preprocessKeypoints } from "./features.js";

export const SIGN_STATE = {
  IDLE: "IDLE",
  RECORDING: "RECORDING",
  CLASSIFYING: "CLASSIFYING",
  SENTENCE: "SENTENCE",
  SPEAKING: "SPEAKING"
};

function dist2D(a, b) {
  if (!a || !b) return 0;
  return Math.hypot((a[0] || 0) - (b[0] || 0), (a[1] || 0) - (b[1] || 0));
}

function isNonZeroPoint(pt) {
  return Boolean(pt && (Math.abs(pt[0]) > 1e-5 || Math.abs(pt[1]) > 1e-5));
}

/**
 * Periksa apakah minimal satu tangan (kiri 9..29 atau kanan 30..50) benar-benar terdeteksi di kamera.
 */
export function hasDetectedHands(kp86) {
  if (!kp86) return false;
  const leftValid = isNonZeroPoint(kp86[9]) && isNonZeroPoint(kp86[17]);
  const rightValid = isNonZeroPoint(kp86[30]) && isNonZeroPoint(kp86[38]);
  return leftValid || rightValid;
}

/**
 * Periksa apakah tangan berada dalam ruang isyarat aktif (signing space):
 * Dari sekitar dada bawah / ulu hati ke atas (bukan tangan jatuh di pangkuan / meja).
 * Batas bawah adaptif terhadap jarak kamera: jika pundak pengguna berada di bawah frame
 * (mis. midShoulderY >= 0.50 saat duduk dekat webcam), lowerBoundary diperluas ke 0.95.
 */
export function isInSigningSpace(kp86) {
  if (!kp86) return false;
  const lShoulder = kp86[1];
  const rShoulder = kp86[2];
  const midShoulderY = isNonZeroPoint(lShoulder) && isNonZeroPoint(rShoulder)
    ? (lShoulder[1] + rShoulder[1]) / 2
    : 0.45;

  // Batas bawah adaptif:
  // Jarak normal (midShoulderY < 0.50): midShoulderY + 0.38, max 0.85.
  // Jarak dekat (midShoulderY >= 0.50): perluas proporsional hingga max 0.95.
  const lowerBoundary = midShoulderY >= 0.50
    ? Math.min(0.95, midShoulderY + (1.0 - midShoulderY) * 0.82)
    : Math.min(0.85, midShoulderY + 0.38);

  const lWrist = kp86[9];
  const lIndexTip = kp86[17];
  const lMiddleTip = kp86[21];

  const rWrist = kp86[30];
  const rIndexTip = kp86[38];
  const rMiddleTip = kp86[42];

  const lActive =
    (isNonZeroPoint(lWrist) && lWrist[1] < lowerBoundary) ||
    (isNonZeroPoint(lIndexTip) && lIndexTip[1] < lowerBoundary) ||
    (isNonZeroPoint(lMiddleTip) && lMiddleTip[1] < lowerBoundary);

  const rActive =
    (isNonZeroPoint(rWrist) && rWrist[1] < lowerBoundary) ||
    (isNonZeroPoint(rIndexTip) && rIndexTip[1] < lowerBoundary) ||
    (isNonZeroPoint(rMiddleTip) && rMiddleTip[1] < lowerBoundary);

  return lActive || rActive;
}

/**
 * Evaluasi jarak dan framing kamera pengguna untuk mendeteksi posisi terlalu dekat
 * atau tangan yang terpotong di batas frame.
 */
export function checkCameraFraming(kp86) {
  if (!kp86) return { ok: true, warning: null, midShoulderY: null };
  const lShoulder = kp86[1];
  const rShoulder = kp86[2];
  const hasShoulders = isNonZeroPoint(lShoulder) && isNonZeroPoint(rShoulder);
  const midShoulderY = hasShoulders ? (lShoulder[1] + rShoulder[1]) / 2 : null;

  if (midShoulderY !== null && midShoulderY > 0.55) {
    return {
      ok: false,
      warning: "Posisi terlalu dekat dengan kamera. Mundur sedikit agar dada dan kedua tangan terlihat utuh.",
      code: "TOO_CLOSE",
      midShoulderY
    };
  }

  const wrists = [kp86[9], kp86[30]].filter(isNonZeroPoint);
  for (const w of wrists) {
    if (w[1] > 0.96) {
      return {
        ok: false,
        warning: "Tangan berada di batas bawah layar. Mundur atau naikkan posisi tangan sedikit.",
        code: "HAND_TRUNCATED_BOTTOM",
        midShoulderY
      };
    }
  }

  return { ok: true, warning: null, midShoulderY };
}

/**
 * Hitung energi gerakan (kecepatan rata-rata L2 pada titik tangan yang terlihat)
 * antara dua frame berturut-turut [86][3].
 */
export function computeHandMotionEnergy(prevKp86, currKp86) {
  if (!prevKp86 || !currKp86) return 0.0;
  let sumDist = 0.0;
  let count = 0;

  for (let i = 9; i < 51; i++) {
    const p = prevKp86[i];
    const c = currKp86[i];
    if (!isNonZeroPoint(p) || !isNonZeroPoint(c)) continue;
    sumDist += dist2D(p, c);
    count++;
  }
  return count > 0 ? sumDist / count : 0.0;
}

/**
 * Analisis anatomi 21 titik tangan (handStart = 9 untuk kiri, 30 untuk kanan)
 * untuk menentukan handshape (0..7) sesuai data/phonology.csv.
 */
export function extractHandshapeCode(kp86, handStart = 30) {
  const wrist = kp86[handStart];
  if (!isNonZeroPoint(wrist)) return -1;

  const p = (offset) => kp86[handStart + offset];
  const palmSize = Math.max(0.04, dist2D(wrist, p(9)));

  // Jari terbuka jika jarak ujung jari (tip) ke pergelangan (wrist) jauh lebih besar dari PIP ke wrist
  const thumbOpen = dist2D(p(4), p(17)) > dist2D(p(2), p(17)) * 1.18;
  const indexOpen = dist2D(wrist, p(8)) > dist2D(wrist, p(6)) * 1.14;
  const middleOpen = dist2D(wrist, p(12)) > dist2D(wrist, p(10)) * 1.14;
  const ringOpen = dist2D(wrist, p(16)) > dist2D(wrist, p(14)) * 1.14;
  const pinkyOpen = dist2D(wrist, p(20)) > dist2D(wrist, p(18)) * 1.14;

  const pinchRatio = dist2D(p(4), p(8)) / palmSize;
  const spreadRatio = dist2D(p(8), p(20)) / palmSize;

  const openCount =
    (indexOpen ? 1 : 0) + (middleOpen ? 1 : 0) + (ringOpen ? 1 : 0) + (pinkyOpen ? 1 : 0);

  // Pemetaan ke 8 Handshape Stokoe di data/phonology.csv:
  // 1: Index-1 (Hanya jari telunjuk lurus)
  if (indexOpen && !middleOpen && !ringOpen && !pinkyOpen) return 1;
  // 6: V-2 (Telunjuk & jari tengah lurus)
  if (indexOpen && middleOpen && !ringOpen && !pinkyOpen) return 6;
  // 7: Y-Handshape (Jempol & kelingking terbuka, jari tengah tertutup)
  if (pinkyOpen && !indexOpen && !middleOpen) return 7;
  // 3: Thumb-Up (Hanya ibu jari terbuka, 4 jari lainnya mengepal)
  if (thumbOpen && openCount === 0) return 3;
  // 4: Pinch-O (Ujung jempol & telunjuk bertemu menguncup)
  if (pinchRatio < 0.48 && openCount <= 2) return 4;
  // 2: Fist-S (Kepalan tangan penuh)
  if (openCount === 0 && !thumbOpen) return 2;
  // 5: Open-5 (Kelima jari terbuka merenggang) vs 0: Flat-B (Telapak terbuka rapat)
  if (openCount >= 3) {
    return spreadRatio >= 0.88 && thumbOpen ? 5 : 0;
  }
  return 0;
}

/**
 * Tentukan lokasi tangan relatif terhadap tubuh pengguna:
 * 0=Kepala/Dahi, 1=Mulut/Dagu, 2=Dada, 3=Ruang Netral Depan, 4=Dua Telapak Bertemu
 */
export function extractLocationCode(kp86) {
  const nose = kp86[0];
  const lShoulder = kp86[1];
  const rShoulder = kp86[2];
  const rWrist = kp86[30];
  const lWrist = kp86[9];

  const midShoulderY = isNonZeroPoint(lShoulder) && isNonZeroPoint(rShoulder)
    ? (lShoulder[1] + rShoulder[1]) / 2
    : 0.5;

  const activeWrist = isNonZeroPoint(rWrist) ? rWrist : lWrist;
  if (!isNonZeroPoint(activeWrist)) return 3;

  // 4: Dua telapak tangan saling bertemu dekat di depan badan
  if (isNonZeroPoint(rWrist) && isNonZeroPoint(lWrist) && dist2D(rWrist, lWrist) < 0.16) {
    return 4;
  }

  // 0: Di atas hidung atau dekat dahi/pelipis
  if (isNonZeroPoint(nose) && activeWrist[1] < nose[1] + 0.05) {
    return 0;
  }

  // 1: Di area antara hidung dan bahu (mulut, pipi, dagu, leher)
  if (activeWrist[1] < midShoulderY - 0.04) {
    return 1;
  }

  // 2: Di depan dada
  if (activeWrist[1] < midShoulderY + 0.22) {
    return 2;
  }

  // 3: Ruang netral perut/depan
  return 3;
}

/**
 * Tentukan arah gerakan utama pada sekuens keypoint:
 * 0=Tahan Statis, 1=Maju/Naik, 2=Ayun Kiri-Kanan, 3=Angguk/Turun, 4=Putar/Buka-Tutup
 */
export function extractMovementCode(sequenceKp86) {
  if (!sequenceKp86 || sequenceKp86.length < 3) return 0;
  const first = sequenceKp86[0];
  const last = sequenceKp86[sequenceKp86.length - 1];

  const w1 = isNonZeroPoint(last[30]) ? last[30] : last[9];
  const w0 = isNonZeroPoint(first[30]) ? first[30] : first[9];
  if (!isNonZeroPoint(w1) || !isNonZeroPoint(w0)) return 0;

  const dx = w1[0] - w0[0];
  const dy = w1[1] - w0[1];
  const totalDist = Math.hypot(dx, dy);

  // Jika pergeseran pergelangan sangat kecil (< 0.04) -> Gerakan Statis (0)
  if (totalDist < 0.04) return 0;

  // Gerakan dominan horizontal (Ayun Kiri-Kanan = 2)
  if (Math.abs(dx) > Math.abs(dy) * 1.35) return 2;

  // Gerakan vertikal ke atas (Maju/Naik = 1)
  if (dy < -0.06) return 1;

  // Gerakan vertikal ke bawah (Angguk/Turun = 3)
  if (dy > 0.06) return 3;

  // Gerakan diagonal atau kurva (Putar/Buka-Tutup = 4)
  return 4;
}

/**
 * Tentukan apakah gerakan menggunakan dua tangan aktif (two_handed = 1) atau satu tangan (0).
 */
export function extractTwoHandedCode(kp86) {
  const leftValid = isNonZeroPoint(kp86[9]) && isNonZeroPoint(kp86[17]);
  const rightValid = isNonZeroPoint(kp86[30]) && isNonZeroPoint(kp86[38]);
  return leftValid && rightValid ? 1 : 0;
}

/**
 * Ekstraksi deskriptor fonologi lengkap dari sekuens keypoint.
 * Digunakan sebagai metadata anatomis diagnostik.
 */
export function extractSequencePhonology(sequenceKp86) {
  if (!sequenceKp86 || sequenceKp86.length === 0) {
    return { handshape: 0, location: 3, movement: 0, two_handed: 0, signature: "0-3-0-0" };
  }
  const midFrame = sequenceKp86[Math.floor(sequenceKp86.length / 2)];
  const handshape = extractHandshapeCode(midFrame);
  const location = extractLocationCode(midFrame);
  const movement = extractMovementCode(sequenceKp86);
  const two_handed = extractTwoHandedCode(midFrame);
  const signature = `${handshape}-${location}-${movement}-${two_handed}`;

  return { handshape, location, movement, two_handed, signature };
}

/**
 * Softmax numerik stabil untuk logits Float32.
 */
export function softmax(logits) {
  let maxLogit = -Infinity;
  for (let i = 0; i < logits.length; i++) {
    if (logits[i] > maxLogit) maxLogit = logits[i];
  }
  let sumExp = 0.0;
  const exps = new Float32Array(logits.length);
  for (let i = 0; i < logits.length; i++) {
    const e = Math.exp(logits[i] - maxLogit);
    exps[i] = e;
    sumExp += e;
  }
  for (let i = 0; i < logits.length; i++) {
    exps[i] /= sumExp;
  }
  return exps;
}

export function flattenKeypoints(kp64) {
  const flat = new Float32Array(SEQ_LEN * NUM_NODES * NUM_COORDS);
  let idx = 0;
  for (let t = 0; t < SEQ_LEN; t++) {
    const frame = kp64[t] || [];
    for (let n = 0; n < NUM_NODES; n++) {
      const pt = frame[n] || [0, 0, 0];
      flat[idx++] = Number.isFinite(pt[0]) ? pt[0] : 0.0;
      flat[idx++] = Number.isFinite(pt[1]) ? pt[1] : 0.0;
      flat[idx++] = Number.isFinite(pt[2]) ? pt[2] : 0.0;
    }
  }
  return flat;
}

export class SignRecognizer {
  constructor({
    modelUrl = APP_CONFIG.studentModelUrl,
    labelsUrl = APP_CONFIG.labelsUrl,
    apiBaseUrl = APP_CONFIG.apiBaseUrl,
    onStateChange = () => {},
    onPrediction = () => {}
  } = {}) {
    this.modelUrl = modelUrl;
    this.labelsUrl = labelsUrl;
    this.apiBaseUrl = apiBaseUrl;
    this.onStateChange = onStateChange;
    this.onPrediction = onPrediction;

    this.session = null;
    this.labels = [...BISINDO_GLOSSES];
    this.state = SIGN_STATE.IDLE;
    this.activeBuffer = [];
    this.holdBuffer = [];
    this.prevFrame = null;
    this.stillCounter = 0;
    this.lastInferAt = -Infinity;
    this.lockedSignature = "";
    this.outOfSpaceFrames = 0;
    this.candidateConfidenceThreshold = APP_CONFIG.candidateConfidenceThreshold || 0.25;
    this.autoSpeakConfidenceThreshold = APP_CONFIG.autoSpeakConfidenceThreshold || APP_CONFIG.confidenceThreshold || 0.50;
    this.autoSpeakMarginThreshold = APP_CONFIG.autoSpeakMarginThreshold || APP_CONFIG.marginThreshold || 0.10;
    this.minConfidence = this.autoSpeakConfidenceThreshold;
    this.fps = 20;
    this.lastFrameTimestamp = 0;
    this.lastDebug = null;

    this.modelStatus = {
      ready: false,
      engine: "none",
      modelUrl: this.modelUrl,
      labelsCount: this.labels.length,
      error: null
    };
  }

  /**
   * Hitung batas jumlah frame secara adaptif terhadap FPS aktual
   * agar segmentasi gerakan konsisten di berbagai perangkat dan refresh rate.
   */
  getDynamicThresholds(fps = 20) {
    const safeFps = Math.max(10, Math.min(60, Number(fps) || 20));
    const minActive = Math.max(4, Math.round(safeFps * ((APP_CONFIG.minActiveDurationMs || 250) / 1000)));
    const pauseFrames = Math.max(3, Math.round(safeFps * ((APP_CONFIG.pauseDurationMs || 250) / 1000)));
    const maxActive = Math.min(64, Math.max(20, Math.round(safeFps * ((APP_CONFIG.maxActiveDurationMs || 2200) / 1000))));
    const holdFrames = Math.max(6, Math.round(safeFps * ((APP_CONFIG.holdDurationMs || 500) / 1000)));
    return { minActive, pauseFrames, maxActive, holdFrames, fps: safeFps };
  }

  async init() {
    // 1. Muat mapping label 32 kelas
    try {
      const resp = await fetch(this.labelsUrl);
      if (resp.ok) {
        const data = await resp.json();
        if (Array.isArray(data) && data.length === 32) {
          this.labels = data.map((g) => String(g).toUpperCase());
        }
      }
    } catch (_err) {
      this.labels = [...BISINDO_GLOSSES];
    }

    this.modelStatus = {
      ready: false,
      engine: "none",
      modelUrl: this.modelUrl,
      labelsCount: this.labels.length,
      error: null
    };

    // 2. Periksa ketersediaan library ONNX Runtime Web di window
    if (typeof window === "undefined" || !window.ort) {
      this.modelStatus.error = "ONNX Runtime Web (window.ort) tidak tersedia di lingkungan browser.";
      console.warn("[SignRecognizer] " + this.modelStatus.error);
      return { ...this.modelStatus };
    }

    // Konfigurasi WebAssembly threading yang aman sesuai isolasi origin browser
    if (window.ort.env && window.ort.env.wasm) {
      window.ort.env.wasm.numThreads = Boolean(window.crossOriginIsolated) ? 4 : 1;
    }

    // 3. Buat sesi inferensi ONNX
    try {
      this.session = await window.ort.InferenceSession.create(this.modelUrl, {
        executionProviders: ["wasm"]
      });
      this.modelStatus.ready = true;
      this.modelStatus.engine = "onnx-web";
      console.info(`[SignRecognizer] Model M0 berhasil diinisialisasi: ${this.modelUrl} (${this.labels.length} kelas)`);
      return { ...this.modelStatus };
    } catch (err) {
      this.session = null;
      this.modelStatus.ready = false;
      this.modelStatus.engine = "failed";
      this.modelStatus.error = `Gagal memuat session ONNX (${this.modelUrl}): ${err?.message || err}`;
      console.error("[SignRecognizer] " + this.modelStatus.error);
      return { ...this.modelStatus };
    }
  }

  setState(nextState, meta = {}) {
    this.state = nextState;
    this.onStateChange({ state: this.state, ...meta });
  }

  /**
   * Batas segmentasi (dalam frame) adaptif terhadap FPS. Semua angka dari APP_CONFIG (lihat config.js).
   */
  getSegmentThresholds(fps = 20) {
    const f = Math.max(10, Math.min(60, Number(fps) || 20));
    const n = (ms, min) => Math.max(min, Math.round((f * ms) / 1000));
    return {
      preRoll: n(APP_CONFIG.segmentPreRollMs ?? 300, 3),        // frame tangan terlihat SEBELUM masuk ruang isyarat
      restFrames: n(APP_CONFIG.segmentRestMs ?? 250, 3),        // tangan turun/keluar selama ini -> isyarat selesai
      stillFrames: n(APP_CONFIG.segmentHoldEndMs ?? 1000, 8),   // diam selama ini SETELAH bergerak -> isyarat selesai
      maxFrames: n(APP_CONFIG.segmentMaxMs ?? 4000, 40),        // batas atas panjang klip
      minFrames: n(APP_CONFIG.segmentMinMs ?? 400, 6),          // klip lebih pendek dari ini diabaikan
      minMotionFrames: n(APP_CONFIG.segmentMinMotionMs ?? 150, 3), // tanpa gerak cukup -> bukan isyarat kata (mungkin abjad)
      fps: f
    };
  }

  /**
   * Masukkan 1 frame keypoint [86][3] dari kamera.
   *
   * SEGMENTASI MENIRU KLIP LATIH WL-BISINDO: tiap video latih berisi satu isyarat UTUH (tangan naik -> isyarat
   * -> tahan -> tangan turun), dipangkas di frame pertama/terakhir yang ada tangannya (trim_inactive). Versi lama
   * hanya merekam frame yang sedang bergerak cepat dan mengirim 12 frame tangan diam sebagai "isyarat statis";
   * keduanya tidak pernah dilihat model saat latihan sehingga pola sering salah dikenali.
   * Sekarang satu segmen = sejak tangan masuk ruang isyarat (+ pre-roll) sampai tangan turun, atau diam lama
   * setelah bergerak, atau batas maksimum.
   */
  async pushFrame(kp86, { hasVisibleHand = true, timestamp = null } = {}) {
    const hasHand = Boolean(hasVisibleHand && hasDetectedHands(kp86));
    const inSpace = hasHand && isInSigningSpace(kp86);
    const now = typeof timestamp === "number" ? timestamp : performance.now();

    if (this.lastFrameTimestamp && now > this.lastFrameTimestamp) {
      const dt = now - this.lastFrameTimestamp;
      if (dt > 8 && dt < 400) {
        const instantFps = 1000 / dt;
        this.fps = this.fps ? this.fps * 0.85 + instantFps * 0.15 : instantFps;
      }
    }
    this.lastFrameTimestamp = now;
    const th = this.getSegmentThresholds(this.fps || 20);
    this.preRoll = this.preRoll || [];

    if (!inSpace) {
      this.lastEnergy = 0;
      this.prevFrame = null;
      if (this.state === SIGN_STATE.RECORDING) {
        this.outOfSpaceFrames += 1;
        if (hasHand) this.activeBuffer.push(kp86);              // fase tangan turun juga ada di klip latih
        if (this.outOfSpaceFrames < th.restFrames) return null;   // toleransi tracking hilang sesaat
        return await this._finishSegment("hands-rest", now, th);
      }
      this.outOfSpaceFrames += 1;
      this.spellingHold = false;                                  // tangan turun -> boleh isyarat kata lagi
      if (hasHand) { this.preRoll.push(kp86); if (this.preRoll.length > th.preRoll) this.preRoll.shift(); }
      else this.preRoll = [];
      if (this.state !== SIGN_STATE.IDLE) this.setState(SIGN_STATE.IDLE, { reason: "hands-resting", frames: 0, energy: 0 });
      return null;
    }

    this.outOfSpaceFrames = 0;
    const energy = computeHandMotionEnergy(this.prevFrame, kp86);
    this.prevFrame = kp86;
    this.lastEnergy = energy;
    if (this.spellingHold) return null;                          // pengguna sedang mengeja huruf

    if (this.state !== SIGN_STATE.RECORDING) {
      this.activeBuffer = [...this.preRoll, kp86];
      this.preRoll = [];
      this.motionFrames = 0;
      this.stillCounter = 0;
      this.setState(SIGN_STATE.RECORDING, { frames: this.activeBuffer.length, energy });
      return null;
    }

    this.activeBuffer.push(kp86);
    if (energy >= APP_CONFIG.motionStartThreshold) { this.motionFrames += 1; this.stillCounter = 0; }
    else this.stillCounter += 1;

    if (this.motionFrames >= th.minMotionFrames && this.stillCounter >= th.stillFrames) {
      return await this._finishSegment("hold-end", now, th);
    }
    if (this.activeBuffer.length >= th.maxFrames) return await this._finishSegment("max-length", now, th);
    this.setState(SIGN_STATE.RECORDING, { frames: this.activeBuffer.length, energy });
    return null;
  }

  async _finishSegment(reason, now, th) {
    const seq = this.activeBuffer;
    const motion = this.motionFrames || 0;
    this.activeBuffer = [];
    this.motionFrames = 0;
    this.stillCounter = 0;
    this.outOfSpaceFrames = 0;
    if (seq.length < th.minFrames || motion < th.minMotionFrames) {
      this.setState(SIGN_STATE.IDLE, { reason: seq.length < th.minFrames ? "segment-too-short" : "no-motion", frames: seq.length });
      return null;
    }
    this.lastInferAt = now;
    this.lastSegment = { reason, frames: seq.length, motionFrames: motion };
    return await this.classifySequence(seq);
  }

  /** Batalkan segmen berjalan (mis. pengguna ternyata mengeja abjad jari). Aktif lagi setelah tangan turun. */
  cancelSegment(reason = "fingerspelling") {
    this.activeBuffer = [];
    this.motionFrames = 0;
    this.stillCounter = 0;
    this.spellingHold = true;
    this.setState(SIGN_STATE.IDLE, { reason });
  }

  /** Probabilitas softmax model untuk satu sekuens mentah [F][86][3]. */
  async _runModel(rawSequence) {
    const kp64 = preprocessKeypoints(rawSequence, SEQ_LEN, true);
    const flat = flattenKeypoints(kp64);
    const expected = SEQ_LEN * NUM_NODES * NUM_COORDS;
    if (!flat || flat.length !== expected) throw new Error(`Dimensi input Float32 tidak valid: ${flat ? flat.length : 0} (diharapkan ${expected}).`);
    const TensorClass = (typeof window !== "undefined" && window.ort && window.ort.Tensor) ||
      class FallbackTensor { constructor(type, data, dims) { this.type = type; this.data = data; this.dims = dims; } };
    const outputs = await this.session.run({ keypoints: new TensorClass("float32", flat, [1, SEQ_LEN, NUM_NODES, NUM_COORDS]) });
    const logits = outputs.logits ? outputs.logits.data : Object.values(outputs)[0]?.data;
    if (!logits || logits.length !== 32) throw new Error(`Ukuran logits tidak valid: ${logits ? logits.length : 0} (diharapkan 32 kelas).`);
    for (let i = 0; i < logits.length; i++) if (!Number.isFinite(logits[i])) throw new Error(`Output logits non-finite pada indeks ${i}.`);
    return softmax(logits);
  }

  /**
   * Test-time augmentation: rata-rata probabilitas dari beberapa potongan waktu segmen (utuh, awal dipangkas,
   * akhir dipangkas). Membuat hasil tahan terhadap batas potongan live yang tidak pernah tepat sama dengan klip latih.
   */
  async _runModelTTA(rawSequence) {
    const crops = APP_CONFIG.ttaCrops || [[0, 1], [0.12, 1], [0, 0.88]];
    const F = rawSequence.length;
    const acc = new Float64Array(32);
    let used = 0;
    for (const [a, b] of crops) {
      const s = Math.floor(a * F), e = Math.max(s + 1, Math.ceil(b * F));
      if (e - s < Math.min(F, 6)) continue;
      const p = await this._runModel(rawSequence.slice(s, e));
      for (let i = 0; i < 32; i++) acc[i] += p[i];
      used += 1;
    }
    if (!used) return await this._runModel(rawSequence);
    return Float32Array.from(acc, (v) => v / used);
  }

  /**
   * Catatan Audit M0: Heuristik Stokoe ini dinonaktifkan dari penentuan prediksi kelas
   * karena mapping fonologi belum tervalidasi terhadap 32 kosakata WL-BISINDO.
   * Fungsi dipertahankan sebagai utilitas eksperimental offline/diagnostik saja.
   */
  _scorePhonologyDatabase(rawSequence, onnxProbs) {
    const obs = extractSequencePhonology(rawSequence);
    const scores = new Float32Array(this.labels.length);
    for (let i = 0; i < this.labels.length; i++) {
      const gloss = String(this.labels[i]).toUpperCase();
      const target = PHONOLOGY_DB[gloss];
      let score = onnxProbs ? onnxProbs[i] : 0.0;
      if (target) {
        if (target.handshape === obs.handshape) score += 0.42;
        if (target.location === obs.location) score += 0.30;
        if (target.two_handed === obs.two_handed) score += 0.16;
        if (target.movement === obs.movement) score += 0.12;
      }
      scores[i] = score;
    }
    return { scores, obs };
  }

  /**
   * Jalankan inferensi pada sekuens keypoint [F][86][3] -> Top-3 prediksi gloss BISINDO & FSL.
   * Sumber prediksi: 100% Neural Network ONNX M0 Student Baseline.
   */
  async classifySequence(rawSequence, overrideGloss = null) {
    this.setState(SIGN_STATE.CLASSIFYING, { frames: rawSequence ? rawSequence.length : 0 });
    const t0 = performance.now();

    // 1. Ekstraksi fonologi Stokoe HANYA untuk metadata anatomis diagnostik
    const obs = extractSequencePhonology(rawSequence);
    this.lockedSignature = obs.signature;

    // (Dihapus: "manual override" yang mengembalikan gloss pilihan dengan keyakinan 96% tanpa menjalankan model.)
    if (overrideGloss) console.warn("[SignRecognizer] overrideGloss diabaikan: semua hasil harus berasal dari model.");

    // 3. Pemeriksaan ketersediaan model ONNX
    const canRunSession = Boolean(this.session && typeof this.session.run === "function");
    if (!canRunSession) {
      const errMessage = this.modelStatus?.error || "Model ONNX M0 belum dimuat atau tidak tersedia di runtime.";
      const errorResult = {
        success: false,
        source: "none",
        error: errMessage,
        gloss: null,
        fsl: null,
        id_text: "Model M0 Tidak Tersedia",
        fil_text: "Hindi magagamit ang modelo",
        guide: "",
        confidence: 0.0,
        top3: [],
        phonology: obs,
        latencyMs: Math.max(1, Math.round(performance.now() - t0))
      };
      this.setState(SIGN_STATE.IDLE, { error: errMessage });
      this.onPrediction(errorResult);
      return errorResult;
    }

    // 4–6. Preprocessing (trim -> normalisasi bahu -> resample 64) + inferensi ONNX + softmax, dengan TTA
    let onnxProbs = null;
    try {
      onnxProbs = await this._runModelTTA(rawSequence);
    } catch (inferErr) {
      const errMessage = `Eksekusi model ONNX gagal: ${inferErr.message || inferErr}`;
      const errorResult = {
        success: false,
        source: "error",
        error: errMessage,
        gloss: null,
        confidence: 0.0,
        top3: [],
        phonology: obs,
        latencyMs: Math.round(performance.now() - t0)
      };
      this.setState(SIGN_STATE.IDLE, { error: errMessage });
      this.onPrediction(errorResult);
      return errorResult;
    }

    // 7. Pemetaan probabilitas ke 32 kelas WL-BISINDO resmi
    const indexed = Array.from(onnxProbs).map((prob, idx) => {
      const g = String(this.labels[idx] || `GLOSS_${idx}`).toUpperCase();
      const c = CLASSROOM_CONCEPTS.find((item) => item.bisindo === g);
      return {
        index: idx,
        gloss: g,
        fsl: c ? c.fsl : g,
        id_text: c ? c.id_text : g,
        fil_text: c ? c.fil_text : g,
        guide: c ? c.guide : "",
        confidence: Number(prob) // Probabilitas softmax murni dari model M0
      };
    });

    indexed.sort((a, b) => b.confidence - a.confidence);

    const top5 = indexed.slice(0, 5);
    const top3 = indexed.slice(0, 3);
    const best = top3[0];
    const latencyMs = Math.max(5, Math.round(performance.now() - t0));

    const candidateConf = this.candidateConfidenceThreshold || 0.25;
    const autoSpeakConf = this.minConfidence !== undefined ? this.minConfidence : (this.autoSpeakConfidenceThreshold || 0.50);
    const autoSpeakMargin = this.autoSpeakMarginThreshold || 0.10;
    const margin = top3.length > 1 ? best.confidence - top3[1].confidence : best.confidence;

    const canAutoSpeak = best.confidence >= autoSpeakConf && margin >= autoSpeakMargin;
    const candidateAvailable = best.confidence >= candidateConf;

    let rejectionReason = null;
    if (!canAutoSpeak) {
      if (best.confidence < candidateConf) {
        rejectionReason = "below_confidence";
      } else if (best.confidence < autoSpeakConf) {
        rejectionReason = "needs_confirmation";
      } else if (margin < autoSpeakMargin) {
        rejectionReason = "below_margin";
      }
    }

    const result = {
      success: canAutoSpeak,
      canAutoSpeak,
      candidateAvailable,
      source: "onnx-m0-neural",
      gloss: canAutoSpeak ? best.gloss : null,
      fsl: canAutoSpeak ? best.fsl : null,
      id_text: canAutoSpeak ? best.id_text : null,
      fil_text: canAutoSpeak ? best.fil_text : null,
      guide: canAutoSpeak ? best.guide : "",
      candidateGloss: best.gloss,
      candidateConfidence: best.confidence,
      confidence: best.confidence,
      margin,
      top3,
      top5: top5.map((t) => ({ gloss: t.gloss, confidence: t.confidence })),
      rejectionReason: rejectionReason || "accepted",
      phonology: obs, // Fitur fonologi Stokoe hanya sebagai metadata diagnostik
      latencyMs
    };

    this.lastDebug = {
      timestamp: Date.now(),
      success: canAutoSpeak,
      canAutoSpeak,
      candidateAvailable,
      rejectionReason: rejectionReason || "accepted",
      gloss: best.gloss,
      confidence: best.confidence,
      margin,
      candidateConf,
      autoSpeakConf,
      autoSpeakMargin,
      latencyMs,
      top5: top5.map((t) => ({ gloss: t.gloss, prob: Math.round(t.confidence * 1000) / 1000 })),
      rawFrames: rawSequence ? rawSequence.length : 0
    };

    if (typeof window !== "undefined" && window.signbridgeDebug) {
      window.signbridgeDebug.lastClassification = { ...this.lastDebug };
    }

    if (canAutoSpeak) {
      this.lockedSignature = obs.signature;
      this.setState(SIGN_STATE.SENTENCE, result);
    } else {
      this.setState(SIGN_STATE.IDLE, {
        reason: rejectionReason,
        candidate: best.gloss,
        confidence: best.confidence,
        margin,
        candidateAvailable
      });
    }

    this.onPrediction(result);
    return result;
  }
}
