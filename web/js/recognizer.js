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
    this.lastInferAt = 0;
    this.lockedSignature = "";
    this.minConfidence = APP_CONFIG.confidenceThreshold || 0.55;

    this.modelStatus = {
      ready: false,
      engine: "none",
      modelUrl: this.modelUrl,
      labelsCount: this.labels.length,
      error: null
    };
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
   * Masukkan 1 frame keypoint [86][3] dari kamera.
   * Hanya memproses jika tangan benar-benar terlihat di kamera (hasDetectedHands).
   * Mengunci hasil (lockedSignature) setelah satu isyarat dikenali agar TIDAK berganti-ganti kata sendiri.
   */
  async pushFrame(kp86, { hasVisibleHand = true } = {}) {
    // 1. Jika tidak ada tangan di depan kamera -> Reset ke IDLE dan buka kunci untuk isyarat berikutnya
    if (!hasVisibleHand || !hasDetectedHands(kp86)) {
      this.activeBuffer = [];
      this.holdBuffer = [];
      this.stillCounter = 0;
      this.prevFrame = null;
      this.lockedSignature = "";
      if (this.state !== SIGN_STATE.IDLE) {
        this.setState(SIGN_STATE.IDLE, { frames: 0, energy: 0 });
      }
      return null;
    }

    const energy = computeHandMotionEnergy(this.prevFrame, kp86);
    this.prevFrame = kp86;
    const now = performance.now();

    // Periksa apakah postur tangan saat ini masih sama dengan isyarat yang baru saja diucapkan
    const currentPhono = extractSequencePhonology([kp86]);
    if (this.lockedSignature && currentPhono.signature === this.lockedSignature && energy < 0.024) {
      // Pengguna masih menahan tangan yang sama -> JANGAN mengulang atau mengganti kata!
      return null;
    }

    // Jika pengguna menggerakkan tangan secara sengaja (energy >= motionStartThreshold)
    if (energy >= APP_CONFIG.motionStartThreshold) {
      this.lockedSignature = ""; // Buka kunci karena ada gerakan baru
      this.holdBuffer = [];
      this.activeBuffer.push(kp86);
      this.stillCounter = 0;
      this.setState(SIGN_STATE.RECORDING, { frames: this.activeBuffer.length, energy });

      // Jika sudah mencapai batas frame maksimum gerakan, langsung klasifikasikan
      if (this.activeBuffer.length >= APP_CONFIG.maxActiveFrames && now - this.lastInferAt >= 1200) {
        const seqToClassify = this.activeBuffer.slice();
        this.activeBuffer = [];
        this.lastInferAt = now;
        return await this.classifySequence(seqToClassify);
      }
      return null;
    }

    // Jika sedang merekam gerakan aktif lalu tangan berhenti sejenak (jeda selesai berisyarat)
    if (this.state === SIGN_STATE.RECORDING && this.activeBuffer.length > 0) {
      this.activeBuffer.push(kp86);
      this.stillCounter += 1;

      if (this.stillCounter >= APP_CONFIG.pauseFramesToClassify) {
        if (this.activeBuffer.length >= APP_CONFIG.minActiveFrames && now - this.lastInferAt >= 1000) {
          const seqToClassify = this.activeBuffer.slice();
          this.activeBuffer = [];
          this.stillCounter = 0;
          this.lastInferAt = now;
          return await this.classifySequence(seqToClassify);
        } else {
          this.activeBuffer = [];
          this.stillCounter = 0;
          this.setState(SIGN_STATE.IDLE, { energy });
        }
      }
      return null;
    }

    // 2. Dukungan Isyarat Statis (seperti SAYA menunjuk dada)
    if (currentPhono.signature !== this.lockedSignature && now - this.lastInferAt >= 1400) {
      this.holdBuffer.push(kp86);
      if (this.holdBuffer.length >= (APP_CONFIG.holdFramesToClassify || 10)) {
        const seqToClassify = this.holdBuffer.slice();
        this.holdBuffer = [];
        this.lastInferAt = now;
        return await this.classifySequence(seqToClassify);
      }
    }

    return null;
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

    // 2. Dukungan testing terarah (Manual Override)
    if (overrideGloss) {
      const cleanOverride = String(overrideGloss).toUpperCase();
      const concept = CLASSROOM_CONCEPTS.find((c) => c.bisindo === cleanOverride) || CLASSROOM_CONCEPTS[0];
      const others = this.labels.filter((g) => g.toUpperCase() !== cleanOverride);
      const top3 = [
        { index: this.labels.indexOf(cleanOverride), gloss: cleanOverride, fsl: concept.fsl, confidence: 0.96 },
        { index: this.labels.indexOf(others[0]), gloss: others[0] || "SAYA", fsl: "ME", confidence: 0.03 },
        { index: this.labels.indexOf(others[1]), gloss: others[1] || "BELAJAR", fsl: "STUDY", confidence: 0.01 }
      ];
      const result = {
        success: true,
        source: "manual-override",
        gloss: cleanOverride,
        fsl: concept.fsl,
        id_text: concept.id_text,
        fil_text: concept.fil_text,
        guide: concept.guide,
        confidence: 0.96,
        top3,
        phonology: obs,
        latencyMs: Math.max(4, Math.round(performance.now() - t0))
      };
      this.setState(SIGN_STATE.SENTENCE, result);
      this.onPrediction(result);
      return result;
    }

    // 3. Pemeriksaan ketersediaan model ONNX
    if (!this.session || typeof window === "undefined" || !window.ort) {
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

    // 4. Preprocessing sekuens keypoint [64, 86, 3]
    const kp64 = preprocessKeypoints(rawSequence, SEQ_LEN, true);
    const flat = flattenKeypoints(kp64);

    const expectedLength = 1 * SEQ_LEN * NUM_NODES * NUM_COORDS; // 64 * 86 * 3 = 16,512 Float32
    if (!flat || flat.length !== expectedLength) {
      const errMessage = `Dimensi input Float32 tidak valid: ${flat ? flat.length : 0} (diharapkan ${expectedLength}).`;
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

    // 5. Eksekusi inferensi ONNX Runtime Web
    let logitsData = null;
    try {
      const tensor = new window.ort.Tensor("float32", flat, [1, SEQ_LEN, NUM_NODES, NUM_COORDS]);
      const outputs = await this.session.run({ keypoints: tensor });
      logitsData = outputs.logits ? outputs.logits.data : Object.values(outputs)[0]?.data;

      if (!logitsData || logitsData.length !== 32) {
        throw new Error(`Ukuran logits tidak valid: ${logitsData ? logitsData.length : 0} (diharapkan 32 kelas).`);
      }

      for (let i = 0; i < logitsData.length; i++) {
        if (!Number.isFinite(logitsData[i])) {
          throw new Error(`Output logits mengandung nilai non-finite (NaN / Infinity) pada indeks ${i}.`);
        }
      }
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

    // 6. Normalisasi Softmax murni pada logits neural network M0
    const onnxProbs = softmax(logitsData);

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

    const top3 = indexed.slice(0, 3);
    const best = top3[0];
    const latencyMs = Math.max(5, Math.round(performance.now() - t0));

    const result = {
      success: true,
      source: "onnx-m0-neural",
      gloss: best.gloss,
      fsl: best.fsl,
      id_text: best.id_text,
      fil_text: best.fil_text,
      guide: best.guide,
      phonology: obs, // Fitur fonologi Stokoe hanya sebagai metadata diagnostik
      confidence: best.confidence,
      top3,
      latencyMs
    };

    this.setState(SIGN_STATE.SENTENCE, result);
    this.onPrediction(result);
    return result;
  }
}
