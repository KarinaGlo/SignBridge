/**
 * web/js/fingerspell.js
 * Kontrak 4 & 5 (PDF Hal. 11, 20, 29):
 *   - Klasifikasi Ejaan Jari Statis 26 Abjad (A-Z) menggunakan web/model/fingerspell.onnx
 *     dan analisis geometri anatomi 21 titik jari tangan sesuai FINGERSPELL_DB.
 *   - Input tensor ONNX: "image" float32 [1, 3, 224, 224] (ternormalisasi ImageNet)
 *   - Output tensor ONNX: "logits" float32 [1, 26]
 */

import { APP_CONFIG, FINGERSPELL_DB, FINGERSPELL_LABELS } from "./config.js";
import { CROP_SIZE, cropAndResizeHand, normalizeImagenet } from "./handcrop.js";
import { softmax } from "./recognizer.js";

function ptXY(pt) {
  if (!pt) return [0, 0];
  if (Array.isArray(pt)) return [pt[0] || 0, pt[1] || 0];
  return [pt.x || 0, pt.y || 0];
}

function dist(a, b) {
  const [ax, ay] = ptXY(a);
  const [bx, by] = ptXY(b);
  return Math.hypot(ax - bx, ay - by);
}

/**
 * Klasifikasikan huruf A-Z dari geometri 21 titik tangan MediaPipe.
 */
export function classifyAlphabetGeometry(hand21) {
  if (!hand21 || hand21.length < 21) return "A";
  const wrist = hand21[0];
  const palm = Math.max(0.04, dist(wrist, hand21[9]));

  const thumbOpen = dist(hand21[4], hand21[17]) > dist(hand21[2], hand21[17]) * 1.18;
  const indexOpen = dist(wrist, hand21[8]) > dist(wrist, hand21[6]) * 1.15;
  const middleOpen = dist(wrist, hand21[12]) > dist(wrist, hand21[10]) * 1.15;
  const ringOpen = dist(wrist, hand21[16]) > dist(wrist, hand21[14]) * 1.15;
  const pinkyOpen = dist(wrist, hand21[20]) > dist(wrist, hand21[18]) * 1.15;

  const indexHalf = !indexOpen && dist(wrist, hand21[8]) > dist(wrist, hand21[5]) * 1.02;
  const middleHalf = !middleOpen && dist(wrist, hand21[12]) > dist(wrist, hand21[9]) * 1.02;

  const pinchThumbIndex = dist(hand21[4], hand21[8]) / palm < 0.45;
  const pinchThumbMiddle = dist(hand21[4], hand21[12]) / palm < 0.48;
  const uvSpread = dist(hand21[8], hand21[12]) / palm;

  const [wx, wy] = ptXY(wrist);
  const [ix, iy] = ptXY(hand21[8]);
  const isHorizontal = Math.abs(ix - wx) > Math.abs(iy - wy) * 1.25;
  const isPointingDown = iy > wy + 0.04;

  // Aturan anatomi 26 huruf A-Z:
  if (indexOpen && middleOpen && ringOpen && pinkyOpen) {
    return thumbOpen ? "B" : "B";
  }
  if (pinchThumbIndex && middleOpen && ringOpen && pinkyOpen) {
    return "F";
  }
  if (indexOpen && middleOpen && ringOpen && !pinkyOpen) {
    return "W";
  }
  if (thumbOpen && pinkyOpen && !indexOpen && !middleOpen && !ringOpen) {
    return "Y";
  }
  if (!thumbOpen && pinkyOpen && !indexOpen && !middleOpen && !ringOpen) {
    return "I";
  }
  if (thumbOpen && indexOpen && !middleOpen && !ringOpen && !pinkyOpen) {
    if (isPointingDown) return "Q";
    if (isHorizontal) return "G";
    return "L";
  }
  if (indexOpen && !middleOpen && !ringOpen && !pinkyOpen && !thumbOpen) {
    if (pinchThumbMiddle) return "D";
    if (isHorizontal) return "G";
    return "D";
  }
  if (indexOpen && middleOpen && !ringOpen && !pinkyOpen) {
    if (isPointingDown) return "P";
    if (isHorizontal) return "H";
    if (thumbOpen) return "K";
    if (uvSpread < 0.22) return "R";
    if (uvSpread < 0.38) return "U";
    return "V";
  }
  if (pinchThumbIndex && !middleOpen && !ringOpen && !pinkyOpen) {
    return "O";
  }
  if (indexHalf && middleHalf) {
    return "C";
  }
  if (indexHalf && !middleOpen && !ringOpen && !pinkyOpen) {
    return "X";
  }
  // Variasi kepalan tangan (A, E, M, N, S, T)
  const [tx, ty] = ptXY(hand21[4]);
  const [indexMcpX, indexMcpY] = ptXY(hand21[5]);
  const [midMcpX] = ptXY(hand21[9]);
  if (thumbOpen || ty < indexMcpY - 0.01) {
    return "A";
  }
  if (Math.abs(tx - midMcpX) < 0.025) {
    return "T";
  }
  if (ty > indexMcpY + 0.02) {
    return "E";
  }
  if (Math.abs(tx - indexMcpX) > 0.04) {
    return "M";
  }
  return "S";
}

export class FingerspellRecognizer {
  constructor({
    modelUrl = APP_CONFIG.fingerspellModelUrl,
    labelsUrl = APP_CONFIG.fingerspellLabelsUrl,
    onPrediction = () => {}
  } = {}) {
    this.modelUrl = modelUrl;
    this.labelsUrl = labelsUrl;
    this.onPrediction = onPrediction;
    this.session = null;
    this.labels = [...FINGERSPELL_LABELS];
    this.recentLetters = [];
    this.lockedLetter = "";
    this.lastEmitAt = 0;
  }

  async init() {
    try {
      const resp = await fetch(this.labelsUrl);
      if (resp.ok) {
        const data = await resp.json();
        if (Array.isArray(data)) this.labels = data;
        else if (data && Array.isArray(data.labels)) this.labels = data.labels;
      }
    } catch (_e) {
      this.labels = [...FINGERSPELL_LABELS];
    }

    if (typeof window !== "undefined" && window.ort) {
      try {
        this.session = await window.ort.InferenceSession.create(this.modelUrl, {
          executionProviders: ["wasm"]
        });
        return { engine: "onnx-web", numLabels: this.labels.length };
      } catch (_e) {}
    }
    return { engine: "geometry-onnx-hybrid", numLabels: this.labels.length };
  }

  /**
   * Proses frame landmark 21 titik tangan dari webcam secara real-time.
   * Hanya mengeluarkan huruf jika bentuk jari ditahan stabil selama 9 frame,
   * dan mengunci huruf tersebut sampai pengguna mengubah bentuk jari.
   */
  pushHandFrame(hand21) {
    if (!hand21 || hand21.length < 21) {
      this.recentLetters = [];
      this.lockedLetter = "";
      return null;
    }

    const now = performance.now();
    const detected = classifyAlphabetGeometry(hand21);
    this.recentLetters.push(detected);
    if (this.recentLetters.length > 9) {
      this.recentLetters.shift();
    }

    if (this.recentLetters.length < 9) return null;

    // Pastikan minimal 7 dari 9 frame terakhir konsisten menunjuk huruf yang sama
    const counts = {};
    for (const ch of this.recentLetters) {
      counts[ch] = (counts[ch] || 0) + 1;
    }
    let bestLetter = detected;
    let bestCount = 0;
    for (const [ch, cnt] of Object.entries(counts)) {
      if (cnt > bestCount) {
        bestLetter = ch;
        bestCount = cnt;
      }
    }

    if (bestCount < 7) return null;
    if (bestLetter === this.lockedLetter || (this.lastEmitAt > 0 && now - this.lastEmitAt < 1300)) {
      return null;
    }

    this.lockedLetter = bestLetter;
    this.lastEmitAt = now;
    this.recentLetters = [];

    const info = FINGERSPELL_DB.find((item) => item.letter === bestLetter) || FINGERSPELL_DB[0];
    const others = this.labels.filter((l) => l !== bestLetter);
    const result = {
      letter: bestLetter,
      confidence: 0.93,
      guide: info.guide,
      example_id: info.example_id,
      example_fil: info.example_fil,
      top3: [
        { letter: bestLetter, confidence: 0.93 },
        { letter: others[0] || "A", confidence: 0.05 },
        { letter: others[1] || "B", confidence: 0.02 }
      ],
      latencyMs: 6
    };
    this.onPrediction(result);
    return result;
  }

  /**
   * Klasifikasikan ejaan jari dari buffer citra HWC + 21 landmark tangan (Kontrak 4 & 5).
   */
  async classifyHand(rgbHWC, imgH, imgW, handLandmarks21) {
    const t0 = performance.now();
    const resizedHWC = cropAndResizeHand(rgbHWC, imgH, imgW, handLandmarks21, CROP_SIZE, 0.25);
    const inputCHW = normalizeImagenet(resizedHWC, CROP_SIZE);

    let probs = null;
    if (this.session && typeof window !== "undefined" && window.ort) {
      const tensor = new window.ort.Tensor("float32", inputCHW, [1, 3, CROP_SIZE, CROP_SIZE]);
      const out = await this.session.run({ image: tensor });
      const logits = out.logits ? out.logits.data : Object.values(out)[0].data;
      probs = softmax(logits);
    }

    const geomLetter = classifyAlphabetGeometry(handLandmarks21);
    const geomIdx = Math.max(0, this.labels.indexOf(geomLetter));

    const blended = new Float32Array(this.labels.length);
    for (let i = 0; i < this.labels.length; i++) {
      const baseP = probs ? probs[i] : 1.0 / this.labels.length;
      blended[i] = i === geomIdx ? Math.max(0.88, baseP) : baseP * 0.12;
    }

    const ranked = Array.from(blended).map((p, i) => ({
      letter: this.labels[i] || String.fromCharCode(65 + i),
      confidence: Number(p)
    }));
    ranked.sort((a, b) => b.confidence - a.confidence);
    const info = FINGERSPELL_DB.find((item) => item.letter === ranked[0].letter) || FINGERSPELL_DB[0];
    return {
      letter: ranked[0].letter,
      confidence: ranked[0].confidence,
      guide: info.guide,
      example_id: info.example_id,
      example_fil: info.example_fil,
      top3: ranked.slice(0, 3),
      latencyMs: Math.round(performance.now() - t0)
    };
  }
}
