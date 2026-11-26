/**
 * web/js/xmf.js — Runtime browser SignBridge-XMF (Cross-Modal Attention Fusion Transformer).
 *
 * Satu model ONNX menerima 4 modalitas sekaligus:
 *   pose [1,T,86,3] · frames [1,F,3,112,112] (0..255) · audio [1,40000] · text [1,64] · modality_mask [1,4]
 * Normalisasi citra (ImageNet) & log-mel audio ada DI DALAM model, jadi browser cukup mengirim data mentah.
 * Fungsi preprocessing di bawah adalah cermin 1:1 dari signbridge/xmf/ops.py & config.py
 * (diuji paritasnya oleh tests/js/xmf.test.mjs dengan fixture dari Python).
 *
 * Integrasi:
 *   - XmfFrameStore      : simpan snapshot kamera per frame keypoint (WeakMap kp86 -> canvas)
 *   - XmfRecognizer      : turunan SignRecognizer (segmentasi isyarat sama), klasifikasi = XMF video+citra
 *   - XmfAlphabet        : pengenal huruf A-Z (crop tangan + landmark tangan) pengganti aturan geometri
 *   - XmfConceptQuery    : arah Dengar -> Tuli: ucapan (mikrofon) / ketikan -> konsep (ruang konsep yang sama)
 */

import { SignRecognizer } from "./recognizer.js";

// ---------------------------------------------------------------------------
// Fungsi murni (paritas Python)
// ---------------------------------------------------------------------------
export const PERSON_CROP_SIDE_X_SHOULDER = 3.6;
export const PERSON_CROP_CENTER_SHIFT = 0.35;
export const TEXT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,?!-'";

export function normalizeText(text) {
  return String(text ?? "").toLowerCase().replace(/_/g, " ").split(/\s+/).filter(Boolean).join(" ");
}

export function encodeText(text, maxLen = 64, alphabet = TEXT_ALPHABET) {
  const ids = new Array(maxLen).fill(0);
  if (!text) return ids;
  const norm = normalizeText(text);
  for (let i = 0; i < Math.min(norm.length, maxLen); i++) {
    const k = alphabet.indexOf(norm[i]);
    ids[i] = k >= 0 ? k + 2 : 1;
  }
  return ids;
}

export function uniformIndices(n, k) {
  const out = new Array(k).fill(0);
  if (n <= 0) return out;
  for (let i = 0; i < k; i++) out[i] = Math.min(Math.floor(((i + 0.5) * n) / k), n - 1);
  return out;
}

export function personBoxFromShoulders(l, r, width, height,
  side = PERSON_CROP_SIDE_X_SHOULDER, shift = PERSON_CROP_CENTER_SHIFT) {
  if (!l || !r) return null;
  const lx = l[0] * width, ly = l[1] * height, rx = r[0] * width, ry = r[1] * height;
  if (![lx, ly, rx, ry].every(Number.isFinite)) return null;
  const sw = Math.hypot(lx - rx, ly - ry);
  if (sw < 4) return null;
  return [0.5 * (lx + rx), 0.5 * (ly + ry) + shift * sw, side * sw];
}

function median(arr) {
  const s = [...arr].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : 0.5 * (s[m - 1] + s[m]);
}

export function medianBox(boxes, width, height) {
  const v = boxes.filter(Boolean);
  if (!v.length) return [width / 2, height / 2, Math.min(width, height)];
  return [0, 1, 2].map((j) => median(v.map((b) => b[j])));
}

export function handBox(hand21, width, height, margin = 0.25) {
  if (!hand21) return null;
  const pts = hand21.filter((p) => p && Number.isFinite(p[0]) && Number.isFinite(p[1]) && (p[0] !== 0 || p[1] !== 0));
  if (pts.length < 5) return null;
  const xs = pts.map((p) => p[0] * width), ys = pts.map((p) => p[1] * height);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const side = Math.max(x1 - x0, y1 - y0) * (1 + 2 * margin);
  if (side < 8) return null;
  return [(x0 + x1) / 2, (y0 + y1) / 2, side];
}

export function unionBox(boxes) {
  const v = boxes.filter(Boolean);
  if (!v.length) return null;
  const x0 = Math.min(...v.map((b) => b[0] - b[2] / 2)), x1 = Math.max(...v.map((b) => b[0] + b[2] / 2));
  const y0 = Math.min(...v.map((b) => b[1] - b[2] / 2)), y1 = Math.max(...v.map((b) => b[1] + b[2] / 2));
  return [(x0 + x1) / 2, (y0 + y1) / 2, Math.max(x1 - x0, y1 - y0)];
}

function handPresent(h) {
  return Array.isArray(h) && h.every((p) => p && p.every(Number.isFinite)) && h.some((p) => Math.abs(p[0]) + Math.abs(p[1]) > 1e-6);
}

/** kp86 mentah -> [86][3] tangan dinormalisasi pergelangan/telapak, hanya slot tangan terisi. */
export function normalizeHandsStatic(kp86) {
  const out = Array.from({ length: 86 }, () => [0, 0, 0]);
  for (const [a, b] of [[9, 30], [30, 51]]) {
    const h = kp86.slice(a, b);
    if (!handPresent(h)) continue;
    const w = h[0];
    const palm = Math.hypot(h[9][0] - w[0], h[9][1] - w[1]);
    if (palm < 1e-4) continue;
    for (let i = 0; i < 21; i++) out[a + i] = [0, 1, 2].map((c) => (h[i][c] - w[c]) / palm);
  }
  return out;
}

/** Urutkan tangan: paling kiri di gambar -> slot kiri (sama dengan preprocess.py). */
export function canonicalHands(kp86) {
  const hands = [kp86.slice(9, 30), kp86.slice(30, 51)].filter(handPresent);
  hands.sort((p, q) => p.reduce((s, v) => s + v[0], 0) / 21 - q.reduce((s, v) => s + v[0], 0) / 21);
  const out = kp86.map((p) => [...p]);
  const nan = () => Array.from({ length: 21 }, () => [NaN, NaN, NaN]);
  const [L, R] = hands.length === 1 ? [nan(), hands[0]] : hands.length >= 2 ? [hands[0], hands[1]] : [nan(), nan()];
  for (let i = 0; i < 21; i++) { out[9 + i] = L[i]; out[30 + i] = R[i]; }
  return { kp: out, hands };
}

export function resampleLinear(pcm, srIn, srOut = 16000) {
  if (srIn === srOut || pcm.length < 2) return Float32Array.from(pcm);
  const nOut = Math.round((pcm.length * srOut) / srIn);
  const out = new Float32Array(nOut);
  const step = (pcm.length - 1) / Math.max(nOut - 1, 1);
  for (let i = 0; i < nOut; i++) {
    const pos = i * step, i0 = Math.floor(pos), i1 = Math.min(i0 + 1, pcm.length - 1), t = pos - i0;
    out[i] = pcm[i0] * (1 - t) + pcm[i1] * t;
  }
  return out;
}

/** Potong hening & letakkan ucapan di tengah jendela n sampel (== ops.fit_audio). */
export function fitAudio(pcm, n = 40000, sr = 16000, threshDb = -35) {
  const out = new Float32Array(n);
  let x = Float32Array.from(pcm);
  if (!x.length) return out;
  let peak = 0;
  for (const v of x) peak = Math.max(peak, Math.abs(v));
  if (peak < 1e-5) return out;
  const hop = Math.floor(sr / 100);
  const nf = x.length >= hop ? Math.floor(x.length / hop) : 1;
  const keep = [];
  for (let f = 0; f < nf; f++) {
    let s = 0;
    const a = f * hop, b = x.length >= hop ? a + hop : x.length;
    for (let i = a; i < b; i++) s += x[i] * x[i];
    const rms = Math.sqrt(s / (b - a) + 1e-12);
    if (20 * Math.log10(rms / peak + 1e-12) > threshDb) keep.push(f);
  }
  if (keep.length) x = x.slice(keep[0] * hop, (keep[keep.length - 1] + 1) * hop);
  let m = 1e-5;
  for (const v of x) m = Math.max(m, Math.abs(v));
  const g = 0.9 / m;
  if (x.length >= n) {
    const s = Math.floor((x.length - n) / 2);
    for (let i = 0; i < n; i++) out[i] = x[s + i] * g;
    return out;
  }
  const off = Math.floor((n - x.length) / 2);
  for (let i = 0; i < x.length; i++) out[off + i] = x[i] * g;
  return out;
}

export function softmax(arr) {
  let mx = -Infinity;
  for (const v of arr) mx = Math.max(mx, v);
  const ex = Array.from(arr, (v) => Math.exp(v - mx));
  const s = ex.reduce((a, b) => a + b, 0);
  return ex.map((v) => v / s);
}

// ---------------------------------------------------------------------------
// Snapshot kamera & crop (browser)
// ---------------------------------------------------------------------------
function makeCanvas(w, h) {
  if (typeof OffscreenCanvas !== "undefined") return new OffscreenCanvas(w, h);
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  return c;
}

/** Simpan salinan frame kamera (diperkecil) untuk setiap frame keypoint. */
export class XmfFrameStore {
  constructor({ videoEl, width = 480, maxFrames = 160 } = {}) {
    this.videoEl = videoEl;
    this.width = width;
    this.map = new WeakMap();
    this.pool = [];
    this.ring = [];
    this.maxFrames = maxFrames;
    this.latest = null;
  }

  capture(kp86) {
    const v = typeof this.videoEl === "function" ? this.videoEl() : this.videoEl;
    if (!kp86 || !v || !v.videoWidth) return null;
    const h = Math.round((this.width * v.videoHeight) / v.videoWidth);
    let c = this.ring.length >= this.maxFrames ? this.ring.shift() : null;
    if (!c || c.width !== this.width || c.height !== h) c = makeCanvas(this.width, h);
    c.getContext("2d").drawImage(v, 0, 0, this.width, h);
    this.ring.push(c);
    this.map.set(kp86, c);
    this.latest = { kp86, canvas: c };
    return c;
  }

  get(kp86) { return this.map.get(kp86) || null; }
}

/** Crop persegi (cx, cy, side) dari canvas sumber ke side x side; luar gambar hitam. Hasil Float32 HWC->CHW 0..255. */
export function cropToCHW(srcCanvas, box, out = 112, dst = null, offset = 0) {
  const c = makeCanvas(out, out);
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, out, out);
  const [cx, cy, side] = box;
  const x0 = Math.round(cx - side / 2), y0 = Math.round(cy - side / 2), s = Math.max(1, Math.round(side));
  const sx0 = Math.max(0, x0), sy0 = Math.max(0, y0);
  const sx1 = Math.min(srcCanvas.width, x0 + s), sy1 = Math.min(srcCanvas.height, y0 + s);
  if (sx1 > sx0 && sy1 > sy0) {
    const k = out / s;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(srcCanvas, sx0, sy0, sx1 - sx0, sy1 - sy0, (sx0 - x0) * k, (sy0 - y0) * k, (sx1 - sx0) * k, (sy1 - sy0) * k);
  }
  const px = ctx.getImageData(0, 0, out, out).data;
  const plane = out * out;
  const res = dst || new Float32Array(3 * plane);
  for (let i = 0; i < plane; i++) {
    res[offset + i] = px[i * 4];
    res[offset + plane + i] = px[i * 4 + 1];
    res[offset + 2 * plane + i] = px[i * 4 + 2];
  }
  return res;
}

// ---------------------------------------------------------------------------
// Model ONNX
// ---------------------------------------------------------------------------
export class XmfModel {
  constructor(task, { baseUrl = "./model" } = {}) {
    this.task = task;
    this.url = `${baseUrl}/xmf_${task}.onnx`;
    this.metaUrl = `${baseUrl}/xmf_${task}.json`;
    this.session = null;
    this.meta = null;
  }

  async init() {
    const ort = window.ort;
    if (!ort) throw new Error("ONNX Runtime Web (window.ort) tidak tersedia");
    const r = await fetch(this.metaUrl);
    if (!r.ok) throw new Error(`metadata ${this.metaUrl} tidak ditemukan (HTTP ${r.status})`);
    this.meta = await r.json();
    this.session = await ort.InferenceSession.create(this.url, { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
    return this.meta;
  }

  get ready() { return Boolean(this.session && this.meta); }

  /** Semua argumen opsional; yang null otomatis di-mask (modalitas hilang). */
  async run({ pose = null, frames = null, audio = null, text = null } = {}) {
    const ort = window.ort, m = this.meta;
    const T = m.pose_frames, F = m.image_frames, S = m.image_side, N = m.audio_samples, L = m.text_len;
    const mask = Float32Array.from([pose ? 1 : 0, frames ? 1 : 0, audio ? 1 : 0, text ? 1 : 0]);
    if (!mask.some(Boolean)) throw new Error("minimal satu modalitas harus tersedia");
    const ids = text ? encodeText(text, L, m.text_alphabet) : new Array(L).fill(0);
    const feeds = {
      pose: new ort.Tensor("float32", pose || new Float32Array(T * 86 * 3), [1, T, 86, 3]),
      frames: new ort.Tensor("float32", frames || new Float32Array(F * 3 * S * S), [1, F, 3, S, S]),
      audio: new ort.Tensor("float32", audio || new Float32Array(N), [1, N]),
      text: new ort.Tensor("int64", BigInt64Array.from(ids.map(BigInt)), [1, L]),
      modality_mask: new ort.Tensor("float32", mask, [1, 4]),
    };
    const t0 = performance.now();
    const o = await this.session.run(feeds);
    const probs = softmax(o.logits.data);
    const C = probs.length;
    const modProbs = [0, 1, 2, 3].map((k) => (mask[k] ? softmax(o.modality_logits.data.slice(k * C, (k + 1) * C)) : null));
    const ranked = probs.map((p, i) => ({ index: i, label: m.classes[i], confidence: p })).sort((a, b) => b.confidence - a.confidence);
    return {
      probs, ranked, top: ranked[0],
      modalityWeights: Object.fromEntries(m.modalities.map((k, i) => [k, o.modality_weights.data[i]])),
      modalityTop: modProbs.map((p, k) => (p ? { modality: m.modalities[k], label: m.classes[p.indexOf(Math.max(...p))], confidence: Math.max(...p) } : null)).filter(Boolean),
      mask: Array.from(mask), latencyMs: Math.round(performance.now() - t0),
    };
  }
}

// ---------------------------------------------------------------------------
// GLOSS: turunan SignRecognizer -> segmentasi isyarat lama, klasifikasi XMF (video + citra)
// ---------------------------------------------------------------------------
function hasHand(kp) {
  for (let i = 9; i < 51; i++) {
    const p = kp[i];
    if (p && Number.isFinite(p[0]) && Math.abs(p[0]) + Math.abs(p[1]) > 1e-6) return true;
  }
  return false;
}

export class XmfRecognizer extends SignRecognizer {
  constructor({ frameStore, baseUrl = "./model", onPrediction = () => {}, ...rest } = {}) {
    super({ ...rest, onPrediction: (res) => onPrediction(this._decorate(res)) });
    this.frameStore = frameStore;
    this.xmf = new XmfModel("gloss", { baseUrl });
    this.contextText = null;     // opsional: teks konteks (mis. kata target di Mode Latihan)
    this.lastFusion = null;
    this.engine = "m0";
  }

  async init() {
    try {
      const meta = await this.xmf.init();
      this.labels = meta.classes.map((g) => String(g).toUpperCase());
      this.session = { run: (feeds) => this._runXmf(feeds) };   // adaptor: dipanggil classifySequence induk
      this.engine = "xmf";
      this.modelStatus = { ready: true, engine: "onnx-xmf", modelUrl: this.xmf.url, labelsCount: this.labels.length,
        error: null, metrics: meta.metrics || null };
      console.info(`[XMF] model fusion siap: ${this.xmf.url} (${this.labels.length} kelas)`);
      return { ...this.modelStatus };
    } catch (err) {
      console.warn(`[XMF] gagal memuat model fusion (${err.message}); kembali ke M0.`);
      return super.init();
    }
  }

  async classifySequence(rawSequence, overrideGloss = null) {
    this._pendingSeq = rawSequence;
    return super.classifySequence(rawSequence, overrideGloss);
  }

  _framesFor(seq) {
    const m = this.xmf.meta, F = m.image_frames, S = m.image_side;
    let a = 0, b = seq.length - 1;
    while (a < b && !hasHand(seq[a])) a++;
    while (b > a && !hasHand(seq[b])) b--;
    const span = seq.slice(a, b + 1);
    const snaps = span.map((kp) => (this.frameStore ? this.frameStore.get(kp) : null));
    if (!snaps.some(Boolean)) return null;
    // isi snapshot yang hilang dengan tetangga terdekat
    for (let i = 0; i < snaps.length; i++) {
      if (snaps[i]) continue;
      for (let d = 1; d < snaps.length; d++) {
        if (snaps[i - d]) { snaps[i] = snaps[i - d]; break; }
        if (snaps[i + d]) { snaps[i] = snaps[i + d]; break; }
      }
    }
    const idx = uniformIndices(span.length, F);
    const W = snaps[idx[0]].width, H = snaps[idx[0]].height;
    const boxes = idx.map((i) => personBoxFromShoulders(span[i][1], span[i][2], W, H,
      m.person_crop.side_x_shoulder, m.person_crop.center_shift));
    const box = medianBox(boxes, W, H);
    const out = new Float32Array(F * 3 * S * S);
    idx.forEach((i, f) => cropToCHW(snaps[i], box, S, out, f * 3 * S * S));
    return out;
  }

  async _runXmf(feeds) {
    const pose = feeds.keypoints.data;                               // [1,64,86,3] dari preprocessKeypoints
    const frames = this._pendingSeq ? this._framesFor(this._pendingSeq) : null;
    const r = await this.xmf.run({ pose, frames, text: this.contextText });
    this.lastFusion = { weights: r.modalityWeights, perModality: r.modalityTop, mask: r.mask, latencyMs: r.latencyMs };
    // kembalikan logit dalam bentuk log-prob agar softmax induk menghasilkan probabilitas yang sama
    return { logits: { data: Float32Array.from(r.probs, (p) => Math.log(Math.max(p, 1e-9))) } };
  }

  _decorate(res) {
    if (res && this.engine === "xmf" && res.source === "onnx-m0-neural") {
      res.source = "onnx-xmf-fusion";
      res.fusion = this.lastFusion;
    }
    return res;
  }
}

// ---------------------------------------------------------------------------
// ALFABET: crop tangan + landmark tangan dari frame yang sama -> XMF alfabet
// ---------------------------------------------------------------------------
export class XmfAlphabet {
  constructor({ frameStore, baseUrl = "./model", onPrediction = () => {}, minConfidence = 0.55 } = {}) {
    this.frameStore = frameStore;
    this.model = new XmfModel("alphabet", { baseUrl });
    this.onPrediction = onPrediction;
    this.minConfidence = minConfidence;
    this.votes = [];
    this.locked = "";
    this.busy = false;
    this.lastRun = 0;
    this.lastEmit = 0;
  }

  async init() {
    try { await this.model.init(); return { engine: "onnx-xmf", numLabels: this.model.meta.classes.length }; }
    catch (e) { console.warn(`[XMF] model alfabet tidak tersedia: ${e.message}`); return { engine: "none" }; }
  }

  get ready() { return this.model.ready; }

  /** Panggil tiap frame dengan kp86 mentah. Mengembalikan huruf saat 4 dari 5 prediksi terakhir konsisten. */
  async push(kp86) {
    if (!this.ready || this.busy || !kp86) return null;
    const now = performance.now();
    if (now - this.lastRun < 120) return null;
    const { kp, hands } = canonicalHands(kp86);
    if (!hands.length) { this.votes = []; this.locked = ""; return null; }
    const snap = this.frameStore ? this.frameStore.get(kp86) : null;
    this.busy = true; this.lastRun = now;
    try {
      const S = this.model.meta.image_side;
      let frames = null;
      if (snap) {
        const box = unionBox(hands.map((h) => handBox(h, snap.width, snap.height, this.model.meta.hand_crop_margin)));
        if (box) frames = cropToCHW(snap, box, S);
      }
      const pose = Float32Array.from(normalizeHandsStatic(kp).flat());
      const r = await this.model.run({ pose, frames });
      this.votes.push(r.top.confidence >= this.minConfidence ? r.top.label : "?");
      if (this.votes.length > 5) this.votes.shift();
      const best = r.top.label;
      const agree = this.votes.filter((v) => v === best).length;
      if (agree >= 4 && best !== this.locked && now - this.lastEmit > 1000) {
        this.locked = best; this.lastEmit = now; this.votes = [];
        const res = { letter: best, confidence: r.top.confidence, top3: r.ranked.slice(0, 3).map((t) => ({ letter: t.label, confidence: t.confidence })),
          source: "onnx-xmf-fusion", fusion: { weights: r.modalityWeights }, latencyMs: r.latencyMs };
        this.onPrediction(res);
        return res;
      }
      return null;
    } finally { this.busy = false; }
  }
}

// ---------------------------------------------------------------------------
// Arah Dengar -> Tuli: ucapan / ketikan -> konsep (ruang konsep yang sama dengan isyarat)
// ---------------------------------------------------------------------------
export class XmfConceptQuery {
  constructor(model) { this.model = model; }

  /** Rekam mikrofon `seconds` detik (16 kHz mono) -> Float32Array. */
  static async recordMic(seconds = 2.5) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    const ctx = new AudioContext();
    const src = ctx.createMediaStreamSource(stream);
    const proc = ctx.createScriptProcessor(4096, 1, 1);
    const chunks = [];
    proc.onaudioprocess = (e) => chunks.push(Float32Array.from(e.inputBuffer.getChannelData(0)));
    src.connect(proc); proc.connect(ctx.destination);
    await new Promise((r) => setTimeout(r, seconds * 1000));
    proc.disconnect(); src.disconnect(); stream.getTracks().forEach((t) => t.stop());
    const n = chunks.reduce((s, c) => s + c.length, 0);
    const pcm = new Float32Array(n);
    let o = 0;
    for (const c of chunks) { pcm.set(c, o); o += c.length; }
    const sr = ctx.sampleRate;
    await ctx.close();
    return resampleLinear(pcm, sr, 16000);
  }

  async fromSpeech(pcm16k) { return this.model.run({ audio: fitAudio(pcm16k, this.model.meta.audio_samples) }); }

  async fromText(text) { return this.model.run({ text }); }

  async fromSpeechAndText(pcm16k, text) {
    return this.model.run({ audio: fitAudio(pcm16k, this.model.meta.audio_samples), text });
  }
}
