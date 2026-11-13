// Pengenal abjad jari BISINDO A–Z dari landmark DUA tangan (MLP kecil, bobot JSON, tanpa ONNX).
// KEMBAR dari signbridge/fingerspell_landmarks.py — dijaga oleh tests/js/fingerspell_mlp.test.mjs.
export const N_FEAT = 127;

const xy = (p) => (Array.isArray(p) ? [Number(p[0]), Number(p[1])] : [Number(p?.x), Number(p?.y)]);

function validHand(h) {
  if (!h || h.length !== 21) return null;
  const pts = h.map(xy);
  let s = 0;
  for (const [x, y] of pts) { if (!Number.isFinite(x) || !Number.isFinite(y)) return null; s += Math.abs(x) + Math.abs(y); }
  return s > 0 ? pts : null;
}

/** hands: array berisi 1–2 tangan (21 titik [x,y] atau {x,y}, koordinat gambar 0..1). Return Float32Array(127). */
export function handFeatures(hands) {
  const f = new Float32Array(N_FEAT);
  const hs = (hands || []).map(validHand).filter(Boolean).sort((a, b) => a[0][0] - b[0][0]).slice(0, 2);
  if (!hs.length) return f;
  const a = hs[0];
  const pa = Math.max(Math.hypot(a[9][0] - a[0][0], a[9][1] - a[0][1]), 1e-6);
  for (let k = 0; k < 21; k++) { f[1 + 2 * k] = (a[k][0] - a[0][0]) / pa; f[2 + 2 * k] = (a[k][1] - a[0][1]) / pa; }
  if (hs.length === 2) {
    const b = hs[1];
    const pb = Math.max(Math.hypot(b[9][0] - b[0][0], b[9][1] - b[0][1]), 1e-6);
    f[0] = 1;
    for (let k = 0; k < 21; k++) {
      f[43 + 2 * k] = (b[k][0] - b[0][0]) / pb; f[44 + 2 * k] = (b[k][1] - b[0][1]) / pb;
      f[85 + 2 * k] = (b[k][0] - a[0][0]) / pa; f[86 + 2 * k] = (b[k][1] - a[0][1]) / pa;
    }
  }
  return f;
}

export class FingerspellMLP {
  constructor(w) {
    this.labels = w.labels; this.mean = Float64Array.from(w.mean); this.std = Float64Array.from(w.std);
    this.layers = w.layers.map((l) => ({ W: l.W, b: Float64Array.from(l.b), nIn: l.W.length, nOut: l.b.length }));
    this.meta = w.meta || {};
  }

  static async load(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`gagal memuat ${url}: HTTP ${r.status}`);
    return new FingerspellMLP(await r.json());
  }

  /** Float32Array(127) -> Float64Array(26) probabilitas */
  predictProba(feat) {
    let h = Float64Array.from(feat, (v, i) => (v - this.mean[i]) / this.std[i]);
    this.layers.forEach((L, li) => {
      const o = Float64Array.from(L.b);
      for (let i = 0; i < L.nIn; i++) { const hi = h[i]; if (hi === 0) continue; const row = L.W[i]; for (let j = 0; j < L.nOut; j++) o[j] += hi * row[j]; }
      if (li < this.layers.length - 1) for (let j = 0; j < L.nOut; j++) o[j] = Math.max(0, o[j]);
      h = o;
    });
    let m = -Infinity; for (const v of h) m = Math.max(m, v);
    let s = 0; const e = h.map((v) => { const x = Math.exp(v - m); s += x; return x; });
    return e.map((v) => v / s);
  }
}
