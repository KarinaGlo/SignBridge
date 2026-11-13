/**
 * web/js/fingerspell.js — Ejaan jari BISINDO A–Z.
 * Mesin aktif: MLP landmark dua tangan (web/model/fingerspell_mlp.json + web/js/fingerspell_mlp.js).
 * Model citra web/model/fingerspell.onnx TIDAK dipakai: hasil latihnya setara tebakan acak (akurasi 3,85% = 1/26,
 * runs/image_i1_mobilenetv3/result.json). Latih ulang model citra hanya untuk eksperimen perbandingan (Bab IV).
 */

import { APP_CONFIG, FINGERSPELL_DB, FINGERSPELL_LABELS } from "./config.js";
import { FingerspellMLP, handFeatures } from "./fingerspell_mlp.js";

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
/** @deprecated Aturan geometri satu tangan (gaya ASL). Tidak dipakai lagi; disimpan untuk riwayat & tes lama. */
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
  /**
   * Abjad jari BISINDO A–Z dari landmark DUA tangan memakai MLP terlatih (web/model/fingerspell_mlp.json,
   * dilatih oleh scripts/train_fingerspell_landmarks.py). Aturan geometri lama (classifyAlphabetGeometry)
   * TIDAK dipakai lagi: aturan itu hanya membaca satu tangan, sedangkan sebagian besar huruf BISINDO dua tangan.
   * Stabilisasi: rata-rata probabilitas 8 frame terakhir; huruf keluar sekali per "tahanan".
   */
  constructor({
    mlpUrl = APP_CONFIG.fingerspellMlpUrl || "./model/fingerspell_mlp.json",
    model = null,
    onPrediction = () => {},
    windowFrames = APP_CONFIG.fingerspellWindow || 8,
    minVotes = APP_CONFIG.fingerspellMinVotes || 6,
    minProb = APP_CONFIG.fingerspellMinProb || 0.55,
    cooldownMs = APP_CONFIG.fingerspellCooldownMs || 700
  } = {}) {
    this.mlpUrl = mlpUrl;
    this.model = model;
    this.onPrediction = onPrediction;
    this.labels = model ? model.labels : [...FINGERSPELL_LABELS];
    this.windowFrames = windowFrames; this.minVotes = minVotes; this.minProb = minProb; this.cooldownMs = cooldownMs;
    this.modelStatus = { ready: Boolean(model), engine: model ? "landmark-mlp" : "none" };
    this.reset();
  }

  reset() { this.history = []; this.lockedLetter = ""; this.lastEmitAt = 0; this.last = null; }

  async init() {
    if (this.model) return this.modelStatus;
    try {
      this.model = await FingerspellMLP.load(this.mlpUrl);
      this.labels = this.model.labels;
      this.modelStatus = { ready: true, engine: "landmark-mlp", numLabels: this.labels.length };
    } catch (e) {
      this.modelStatus = { ready: false, engine: "none", error: String(e.message || e) };
    }
    return this.modelStatus;
  }

  /** Kompatibilitas lama: satu tangan saja. Pakai pushHands(left, right) agar huruf dua tangan terbaca. */
  pushHandFrame(hand21) { return this.pushHands(hand21, null); }

  /** Dipanggil tiap frame dengan landmark tangan kiri & kanan (boleh null). */
  pushHands(left21, right21, now = (typeof performance !== "undefined" ? performance.now() : Date.now())) {
    const hands = [left21, right21].filter((h) => h && h.length >= 21);
    if (!hands.length || !this.model) { this.history = []; this.lockedLetter = ""; return null; }
    const proba = this.model.predictProba(handFeatures(hands));
    this.history.push(proba);
    if (this.history.length > this.windowFrames) this.history.shift();
    if (this.history.length < this.windowFrames) return null;

    const n = this.labels.length, avg = new Float64Array(n), votes = new Array(n).fill(0);
    for (const p of this.history) {
      let best = 0;
      for (let i = 0; i < n; i++) { avg[i] += p[i] / this.history.length; if (p[i] > p[best]) best = i; }
      votes[best] += 1;
    }
    const ranked = Array.from(avg).map((p, i) => ({ letter: this.labels[i], confidence: p })).sort((a, b) => b.confidence - a.confidence);
    const top = ranked[0], topVotes = votes[this.labels.indexOf(top.letter)];
    this.last = { letter: top.letter, confidence: top.confidence, votes: topVotes, top3: ranked.slice(0, 3) };
    if (top.confidence < this.minProb || topVotes < this.minVotes) return null;
    if (top.letter === this.lockedLetter) return null;                       // huruf sama masih ditahan
    if (this.lastEmitAt > 0 && now - this.lastEmitAt < this.cooldownMs) return null;

    this.lockedLetter = top.letter; this.lastEmitAt = now; this.history = [];
    const info = FINGERSPELL_DB.find((item) => item.letter === top.letter) || {};
    const result = {
      letter: top.letter, confidence: top.confidence, votes: topVotes, top3: ranked.slice(0, 3),
      twoHanded: hands.length === 2, guide: info.guide, example_id: info.example_id, example_fil: info.example_fil,
      engine: "landmark-mlp"
    };
    this.onPrediction(result);
    return result;
  }
}
