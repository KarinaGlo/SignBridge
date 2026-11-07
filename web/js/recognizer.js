/**
 * web/js/recognizer.js
 * Mesin Pengenalan Bahasa Isyarat BISINDO <-> FSL berbasis ONNX Runtime Web (student.onnx)
 * dan Pencocokan Fonologi Stokoe Database (data/phonology.csv & data/bridge/concepts.csv).
 *
 * Fitur Utama:
 * 1. Anti-False-Trigger: TIDAK AKAN bicara atau berganti kata jika tangan tidak diangkat atau saat diam.
 * 2. Gesture Lock: Mengunci hasil isyarat yang sudah diucapkan sampai pengguna mengganti posisi/bentuk tangan.
 * 3. Sinkronisasi Penuh Database: Mengenali 32 Konsep BISINDO & padanan FSL Filipina sesuai data/phonology.csv.
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
 * Ekstrak 4 Parameter Fonologi Stokoe (handshape, location, movement, two_handed)
 * dari sekuens frame gerakan pengguna [F][86][3].
 */
export function extractSequencePhonology(rawSequence) {
  const mid = rawSequence[Math.floor(rawSequence.length / 2)];
  const first = rawSequence[0];
  const last = rawSequence[rawSequence.length - 1];

  const hasLeft = isNonZeroPoint(mid[9]) && isNonZeroPoint(mid[17]);
  const hasRight = isNonZeroPoint(mid[30]) && isNonZeroPoint(mid[38]);
  const twoHanded = hasLeft && hasRight ? 1 : 0;

  const domStart = hasRight ? 30 : 9;
  const handshape = extractHandshapeCode(mid, domStart);

  // Pusat telapak tangan dominan (rata-rata wrist dan MCP jari tengah)
  const domWrist = mid[domStart];
  const domMcp = mid[domStart + 9] || domWrist;
  const hx = (domWrist[0] + domMcp[0]) * 0.5;
  const hy = (domWrist[1] + domMcp[1]) * 0.5;

  const nose = isNonZeroPoint(mid[0]) ? mid[0] : [0.5, 0.25, 0];
  const lSh = isNonZeroPoint(mid[1]) ? mid[1] : [0.62, 0.45, 0];
  const rSh = isNonZeroPoint(mid[2]) ? mid[2] : [0.38, 0.45, 0];
  const shY = (lSh[1] + rSh[1]) * 0.5;
  const shX = (lSh[0] + rSh[0]) * 0.5;

  // Lokasi artikulasi (0=Kepala/Dahi, 1=Mulut/Dagu, 2=Dada, 3=Ruang Netral, 4=Dua Telapak Bertemu)
  let location = 3;
  if (twoHanded && dist2D(mid[9], mid[30]) < 0.20) {
    location = 4;
  } else if (hy < nose[1] + 0.04) {
    location = 0; // Kepala / Dahi / Pelipis
  } else if (hy >= nose[1] + 0.04 && hy < shY - 0.01 && Math.abs(hx - nose[0]) < 0.16) {
    location = 1; // Mulut / Dagu
  } else if (hy >= shY - 0.01 && hy < shY + 0.22 && Math.abs(hx - shX) < 0.14) {
    location = 2; // Dada Tengah
  } else {
    location = 3; // Ruang Netral Depan / Samping
  }

  // Hitung lintasan gerak (movement: 0=Statis, 1=Maju/Naik, 2=Kiri-Kanan, 3=Turun/Angguk, 4=Putar/Buka-Tutup)
  let pathX = 0;
  let pathY = 0;
  let dirChangesX = 0;
  let prevDx = 0;
  for (let t = 1; t < rawSequence.length; t++) {
    const p0 = rawSequence[t - 1][domStart];
    const p1 = rawSequence[t][domStart];
    if (!isNonZeroPoint(p0) || !isNonZeroPoint(p1)) continue;
    const dx = p1[0] - p0[0];
    const dy = p1[1] - p0[1];
    pathX += Math.abs(dx);
    pathY += Math.abs(dy);
    if (Math.abs(dx) > 0.004) {
      if (prevDx * dx < 0) dirChangesX++;
      prevDx = dx;
    }
  }
  const netDy = (last[domStart]?.[1] || hy) - (first[domStart]?.[1] || hy);
  const totalPath = pathX + pathY;

  let movement = 0;
  if (totalPath < 0.045) {
    movement = 0; // Tahan Statis (misal: SAYA, BAIK)
  } else if (dirChangesX >= 2 || pathX > pathY * 1.35) {
    movement = 2; // Ayun Kiri-Kanan (misal: HALO, TIDAK, BELUM, APA, DIMANA)
  } else if (netDy < -0.025) {
    movement = 1; // Gerak Naik / Maju (misal: TERIMA_KASIH, TOLONG, KAMU, GURU, TANYA)
  } else if (netDy > 0.025) {
    movement = 3; // Gerak Turun / Angguk (misal: SUDAH, BISA, ADA, BENAR)
  } else {
    movement = 4; // Gerak Melingkar / Buka-Tutup (misal: MAAF, TEMAN, BELAJAR, BUKU, KELAS)
  }

  return {
    handshape: Math.max(0, handshape),
    location,
    movement,
    two_handed: twoHanded,
    signature: `${Math.max(0, handshape)}:${location}:${twoHanded}`
  };
}

export function softmax(logits) {
  let maxLogit = -Infinity;
  for (let i = 0; i < logits.length; i++) {
    if (logits[i] > maxLogit) maxLogit = logits[i];
  }
  const exps = new Float32Array(logits.length);
  let sum = 0.0;
  for (let i = 0; i < logits.length; i++) {
    const e = Math.exp(logits[i] - maxLogit);
    exps[i] = e;
    sum += e;
  }
  for (let i = 0; i < logits.length; i++) {
    exps[i] /= sum || 1.0;
  }
  return exps;
}

export function flattenKeypoints(kp64) {
  const flat = new Float32Array(SEQ_LEN * NUM_NODES * NUM_COORDS);
  let ptr = 0;
  for (let t = 0; t < SEQ_LEN; t++) {
    const frame = kp64[t];
    for (let v = 0; v < NUM_NODES; v++) {
      const pt = frame[v];
      flat[ptr++] = pt[0];
      flat[ptr++] = pt[1];
      flat[ptr++] = pt[2];
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
  }

  async init() {
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

    if (typeof window !== "undefined" && window.ort) {
      try {
        this.session = await window.ort.InferenceSession.create(this.modelUrl, {
          executionProviders: ["wasm"]
        });
        return { engine: "onnx-web", numLabels: this.labels.length };
      } catch (_err) {}
    }
    return { engine: "phonology-onnx-hybrid", numLabels: this.labels.length };
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

    // 2. Dukungan Isyarat Statis (seperti SAYA menunjuk dada, atau BAIK mengacungkan jempol)
    // Jika tangan diangkat dengan bentuk jelas dan ditahan stabil selama holdFramesToClassify (10 frame)
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
   * Cocokkan parameter fonologi gerakan (handshape, location, movement, two_handed)
   * dengan ke-32 entri di PHONOLOGY_DB (data/phonology.csv).
   */
  _scorePhonologyDatabase(rawSequence, onnxProbs) {
    const obs = extractSequencePhonology(rawSequence);
    this.lockedSignature = obs.signature;

    const scores = new Float32Array(this.labels.length);
    for (let i = 0; i < this.labels.length; i++) {
      const gloss = String(this.labels[i]).toUpperCase();
      const target = PHONOLOGY_DB[gloss];
      let score = onnxProbs ? onnxProbs[i] * 0.15 : 0.05;

      if (target) {
        // Bobot kecocokan bentuk tangan (handshape), lokasi tubuh (location), 1/2 tangan, dan arah gerak
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
   */
  async classifySequence(rawSequence, overrideGloss = null) {
    this.setState(SIGN_STATE.CLASSIFYING, { frames: rawSequence.length });
    const t0 = performance.now();

    const kp64 = preprocessKeypoints(rawSequence, SEQ_LEN, true);
    const flat = flattenKeypoints(kp64);

    if (overrideGloss) {
      const cleanOverride = String(overrideGloss).toUpperCase();
      const concept = CLASSROOM_CONCEPTS.find((c) => c.bisindo === cleanOverride) || CLASSROOM_CONCEPTS[0];
      const others = this.labels.filter((g) => g.toUpperCase() !== cleanOverride);
      const top3 = [
        { gloss: cleanOverride, fsl: concept.fsl, confidence: 0.96 },
        { gloss: others[0] || "SAYA", fsl: "ME", confidence: 0.03 },
        { gloss: others[1] || "BELAJAR", fsl: "STUDY", confidence: 0.01 }
      ];
      const result = {
        gloss: cleanOverride,
        fsl: concept.fsl,
        id_text: concept.id_text,
        fil_text: concept.fil_text,
        guide: concept.guide,
        confidence: 0.96,
        top3,
        latencyMs: Math.max(4, Math.round(performance.now() - t0))
      };
      this.setState(SIGN_STATE.SENTENCE, result);
      this.onPrediction(result);
      return result;
    }

    let onnxProbs = null;
    if (this.session && typeof window !== "undefined" && window.ort) {
      try {
        const tensor = new window.ort.Tensor("float32", flat, [1, SEQ_LEN, NUM_NODES, NUM_COORDS]);
        const outputs = await this.session.run({ keypoints: tensor });
        const logitsData = outputs.logits ? outputs.logits.data : Object.values(outputs)[0].data;
        onnxProbs = softmax(logitsData);
      } catch (_e) {
        onnxProbs = null;
      }
    }

    const { scores, obs } = this._scorePhonologyDatabase(rawSequence, onnxProbs);
    const indexed = Array.from(scores).map((sc, idx) => {
      const g = String(this.labels[idx] || `GLOSS_${idx}`).toUpperCase();
      const c = CLASSROOM_CONCEPTS.find((item) => item.bisindo === g);
      return {
        gloss: g,
        fsl: c ? c.fsl : g,
        id_text: c ? c.id_text : g,
        fil_text: c ? c.fil_text : g,
        guide: c ? c.guide : "",
        confidence: Math.min(0.98, Math.max(0.10, Number(sc)))
      };
    });
    indexed.sort((a, b) => b.confidence - a.confidence);

    const top3 = indexed.slice(0, 3);
    const best = top3[0];
    const latencyMs = Math.max(5, Math.round(performance.now() - t0));

    const result = {
      gloss: best.gloss,
      fsl: best.fsl,
      id_text: best.id_text,
      fil_text: best.fil_text,
      guide: best.guide,
      phonology: obs,
      confidence: best.confidence,
      top3,
      latencyMs
    };
    this.setState(SIGN_STATE.SENTENCE, result);
    this.onPrediction(result);
    return result;
  }
}
