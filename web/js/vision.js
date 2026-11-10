/**
 * web/js/vision.js
 * Ekstraksi MediaPipe Holistic di peramban, visualisasi Graph Spatio-Temporal 86 titik
 * (Wajah 35 titik, Badan/Pose 9 titik, Tangan Kiri 21 titik, Tangan Kanan 21 titik),
 * serta generator animasi referensi anatomis sesuai Database Fonologi (data/phonology.csv)
 * untuk 32 Kata BISINDO/FSL dan 26 Abjad Ejaan Jari (A-Z).
 */

import { PHONOLOGY_DB } from "./config.js";
import { NUM_NODES, selectFromHolistic } from "./features.js";

export const POSE_EDGES_86 = [
  [0, 1], [0, 2], [1, 2],
  [1, 3], [3, 5],
  [2, 4], [4, 6],
  [1, 7], [2, 8], [7, 8],
  [1, 8], [2, 7],
  [5, 9], [6, 30]
];

export const LEFT_HAND_EDGES_86 = [
  [9, 10], [10, 11], [11, 12], [12, 13],
  [9, 14], [14, 15], [15, 16], [16, 17],
  [9, 18], [18, 19], [19, 20], [20, 21],
  [9, 22], [22, 23], [23, 24], [24, 25],
  [9, 26], [26, 27], [27, 28], [28, 29],
  [10, 14], [14, 18], [18, 22], [22, 26], [9, 26]
];

export const RIGHT_HAND_EDGES_86 = [
  [30, 31], [31, 32], [32, 33], [33, 34],
  [30, 35], [35, 36], [36, 37], [37, 38],
  [30, 39], [39, 40], [40, 41], [41, 42],
  [30, 43], [43, 44], [44, 45], [45, 46],
  [30, 47], [47, 48], [48, 49], [49, 50],
  [31, 35], [35, 39], [39, 43], [43, 47], [30, 47]
];

export const FACE_EDGES_86 = [
  [51, 52], [52, 53], [53, 54], [54, 55], [55, 56], [56, 57],
  [57, 58], [58, 59], [59, 60], [60, 51],
  [61, 62], [62, 63], [63, 64], [64, 65], [65, 66], [66, 67], [67, 68], [68, 61],
  [69, 70], [70, 71], [71, 72], [72, 69],
  [73, 74], [74, 75], [75, 76], [76, 73],
  [69, 77], [73, 78],
  [79, 80], [80, 81], [81, 82], [82, 83], [83, 84], [84, 85], [85, 79],
  [0, 51], [0, 69], [0, 73]
];

export const SKELETON_EDGES_86 = [
  ...POSE_EDGES_86,
  ...LEFT_HAND_EDGES_86,
  ...RIGHT_HAND_EDGES_86,
  ...FACE_EDGES_86
];

const FINGERTIP_INDICES = new Set([13, 17, 21, 25, 29, 34, 38, 42, 46, 50]);

function drawGroupBoundingBox(ctx, points, label, color, pad = 12, isFlipped = false) {
  if (!points || points.length < 3) return;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of points) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  if (!Number.isFinite(minX) || maxX - minX < 4 || maxY - minY < 4) return;

  const bx = Math.max(4, minX - pad);
  const by = Math.max(20, minY - pad);
  const bw = Math.min(ctx.canvas.width - bx - 4, maxX - minX + pad * 2);
  const bh = Math.min(ctx.canvas.height - by - 4, maxY - minY + pad * 2);

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.6;
  ctx.setLineDash([5, 3]);
  ctx.strokeRect(bx, by, bw, bh);
  ctx.setLineDash([]);

  const cLen = Math.min(10, bw * 0.25, bh * 0.25);
  ctx.lineWidth = 2.6;
  ctx.beginPath();
  ctx.moveTo(bx, by + cLen);
  ctx.lineTo(bx, by);
  ctx.lineTo(bx + cLen, by);
  ctx.moveTo(bx + bw - cLen, by);
  ctx.lineTo(bx + bw, by);
  ctx.lineTo(bx + bw, by + cLen);
  ctx.moveTo(bx, by + bh - cLen);
  ctx.lineTo(bx, by + bh);
  ctx.lineTo(bx + cLen, by + bh);
  ctx.moveTo(bx + bw - cLen, by + bh);
  ctx.lineTo(bx + bw, by + bh);
  ctx.lineTo(bx + bw, by + bh - cLen);
  ctx.stroke();

  ctx.font = "bold 10px Inter, system-ui, sans-serif";
  const textW = ctx.measureText(label).width + 10;
  ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
  ctx.fillRect(bx, by - 16, textW, 15);
  ctx.fillStyle = color;

  if (isFlipped) {
    ctx.save();
    ctx.translate(bx + textW / 2, by - 8);
    ctx.scale(-1, 1);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, 0, 0);
    ctx.restore();
  } else {
    ctx.fillText(label, bx + 5, by - 5);
  }
  ctx.restore();
}

export function drawSkeleton86(ctx, kp86, width, height, { mirror = false, hudText = "", isMirroredCanvas = undefined } = {}) {
  if (!ctx || !kp86) return;
  ctx.clearRect(0, 0, width, height);

  const isFlipped = isMirroredCanvas !== undefined
    ? isMirroredCanvas
    : Boolean(ctx.canvas && (ctx.canvas.id === "camera-canvas" || ctx.canvas.closest?.(".camera-viewport-wrap")));

  const toXY = (pt) => {
    if (!pt || !Number.isFinite(pt[0]) || !Number.isFinite(pt[1])) return null;
    if (Math.abs(pt[0]) < 1e-6 && Math.abs(pt[1]) < 1e-6) return null;
    const x = (mirror ? 1.0 - pt[0] : pt[0]) * width;
    const y = pt[1] * height;
    return [x, y];
  };

  // 1. Graph Wajah (Face Mesh 35 titik)
  ctx.save();
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = "rgba(167, 139, 250, 0.72)";
  for (const [u, v] of FACE_EDGES_86) {
    const p1 = toXY(kp86[u]);
    const p2 = toXY(kp86[v]);
    if (!p1 || !p2) continue;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();
  }
  ctx.restore();

  // 2. Graph Badan / Pose (9 titik)
  ctx.save();
  ctx.lineCap = "round";
  for (const [u, v] of POSE_EDGES_86) {
    const p1 = toXY(kp86[u]);
    const p2 = toXY(kp86[v]);
    if (!p1 || !p2) continue;
    ctx.strokeStyle = "rgba(14, 165, 233, 0.35)";
    ctx.lineWidth = 6.0;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();

    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 2.6;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();
  }
  ctx.restore();

  // 3. Graph Tangan Kiri (21 titik)
  ctx.save();
  ctx.lineCap = "round";
  for (const [u, v] of LEFT_HAND_EDGES_86) {
    const p1 = toXY(kp86[u]);
    const p2 = toXY(kp86[v]);
    if (!p1 || !p2) continue;
    ctx.strokeStyle = "rgba(16, 185, 129, 0.35)";
    ctx.lineWidth = 6.5;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();

    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 2.8;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();
  }
  ctx.restore();

  // 4. Graph Tangan Kanan (21 titik)
  ctx.save();
  ctx.lineCap = "round";
  for (const [u, v] of RIGHT_HAND_EDGES_86) {
    const p1 = toXY(kp86[u]);
    const p2 = toXY(kp86[v]);
    if (!p1 || !p2) continue;
    ctx.strokeStyle = "rgba(245, 158, 11, 0.38)";
    ctx.lineWidth = 6.5;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();

    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 2.8;
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    ctx.lineTo(p2[0], p2[1]);
    ctx.stroke();
  }
  ctx.restore();

  const leftHandPts = [];
  const rightHandPts = [];
  const facePts = [];

  for (let i = 0; i < NUM_NODES; i++) {
    const p = toXY(kp86[i]);
    if (!p) continue;

    if (i < 9) {
      ctx.beginPath();
      ctx.fillStyle = "#0284c7";
      ctx.arc(p[0], p[1], 5.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.fillStyle = "#e0f2fe";
      ctx.arc(p[0], p[1], 2.6, 0, Math.PI * 2);
      ctx.fill();
    } else if (i < 30) {
      leftHandPts.push(p);
      const isTip = FINGERTIP_INDICES.has(i);
      const isWrist = i === 9;
      ctx.beginPath();
      ctx.fillStyle = isTip ? "#ecfdf5" : "#10b981";
      ctx.arc(p[0], p[1], isTip ? 5.2 : isWrist ? 5.5 : 3.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.lineWidth = 1.6;
      ctx.strokeStyle = "#047857";
      ctx.stroke();
    } else if (i < 51) {
      rightHandPts.push(p);
      const isTip = FINGERTIP_INDICES.has(i);
      const isWrist = i === 30;
      ctx.beginPath();
      ctx.fillStyle = isTip ? "#fffbeb" : "#f59e0b";
      ctx.arc(p[0], p[1], isTip ? 5.2 : isWrist ? 5.5 : 3.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.lineWidth = 1.6;
      ctx.strokeStyle = "#b45309";
      ctx.stroke();
    } else {
      facePts.push(p);
      ctx.beginPath();
      ctx.fillStyle = "rgba(196, 181, 253, 0.9)";
      ctx.arc(p[0], p[1], 2.2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  drawGroupBoundingBox(ctx, facePts, "WAJAH [35 NODE]", "#c4b5fd", 10, isFlipped);
  drawGroupBoundingBox(ctx, leftHandPts, "TANGAN KIRI [21 NODE]", "#34d399", 14, isFlipped);
  drawGroupBoundingBox(ctx, rightHandPts, "TANGAN KANAN [21 NODE]", "#fbbf24", 14, isFlipped);

  const hasHand = leftHandPts.length > 0 || rightHandPts.length > 0;
  const defaultHud = hasHand
    ? "GRAPH ST-GCN AKTIF: Tangan Terdeteksi — Peragakan Isyarat BISINDO/FSL atau Abjad A-Z"
    : "MENUNGGU TANGAN: Angkat 1 atau 2 tangan ke depan kamera untuk mulai berisyarat";

  ctx.save();
  ctx.fillStyle = "rgba(15, 23, 42, 0.84)";
  ctx.fillRect(8, height - 32, width - 16, 24);
  ctx.font = "bold 11px Inter, system-ui, sans-serif";
  ctx.fillStyle = hasHand ? "#34d399" : "#fbbf24";
  const text = hudText || defaultHud;
  if (isFlipped) {
    ctx.save();
    ctx.translate(width / 2, height - 20);
    ctx.scale(-1, 1);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, 0, 0);
    ctx.restore();
  } else {
    ctx.fillText(text, 14, height - 16);
  }
  ctx.restore();
}

/**
 * Bangun konfigurasi 21 titik jari tangan berdasarkan handshape (0..7) atau abjad (A..Z).
 */
export function buildAnatomicalHand21(wx, wy, isRightHand = true, handshapeCode = 0) {
  const pts = new Array(21);
  pts[0] = [wx, wy, -0.08];

  // Tentukan jari mana yang terbuka [thumb, index, middle, ring, pinky] (0.35 = mengepal, 1.0 = lurus)
  let ext = [0.9, 1.0, 1.0, 1.0, 1.0];
  let spread = 0.24;

  if (typeof handshapeCode === "string" && handshapeCode.length === 1) {
    // Abjad A-Z
    const ch = handshapeCode.toUpperCase();
    const mapAZ = {
      A: [0.95, 0.35, 0.35, 0.35, 0.35],
      B: [0.40, 1.05, 1.05, 1.05, 1.05],
      C: [0.75, 0.72, 0.72, 0.72, 0.72],
      D: [0.55, 1.08, 0.45, 0.45, 0.45],
      E: [0.45, 0.42, 0.42, 0.42, 0.42],
      F: [0.55, 0.55, 1.05, 1.05, 1.05],
      G: [0.90, 1.00, 0.35, 0.35, 0.35],
      H: [0.40, 1.00, 1.00, 0.35, 0.35],
      I: [0.40, 0.35, 0.35, 0.35, 1.05],
      J: [0.40, 0.35, 0.35, 0.35, 1.05],
      K: [0.85, 1.05, 1.05, 0.35, 0.35],
      L: [1.10, 1.08, 0.35, 0.35, 0.35],
      M: [0.40, 0.45, 0.45, 0.45, 0.35],
      N: [0.40, 0.45, 0.45, 0.35, 0.35],
      O: [0.65, 0.65, 0.65, 0.65, 0.65],
      P: [0.80, 1.00, 0.95, 0.35, 0.35],
      Q: [0.85, 0.95, 0.35, 0.35, 0.35],
      R: [0.40, 1.05, 1.05, 0.35, 0.35],
      S: [0.50, 0.32, 0.32, 0.32, 0.32],
      T: [0.60, 0.40, 0.35, 0.35, 0.35],
      U: [0.40, 1.05, 1.05, 0.35, 0.35],
      V: [0.40, 1.08, 1.08, 0.35, 0.35],
      W: [0.40, 1.05, 1.08, 1.05, 0.35],
      X: [0.40, 0.70, 0.35, 0.35, 0.35],
      Y: [1.10, 0.35, 0.35, 0.35, 1.08],
      Z: [0.40, 1.08, 0.35, 0.35, 0.35]
    };
    ext = mapAZ[ch] || ext;
    spread = ch === "B" || ch === "U" ? 0.14 : ch === "V" || ch === "W" || ch === "Y" ? 0.36 : 0.24;
  } else {
    // Handshape Fonologi 0..7 sesuai data/phonology.csv
    switch (Number(handshapeCode)) {
      case 0: // Flat-B (4 jari lurus rapat)
        ext = [0.55, 1.02, 1.05, 1.02, 0.96];
        spread = 0.15;
        break;
      case 1: // Index-1 (Hanya telunjuk lurus)
        ext = [0.45, 1.10, 0.35, 0.35, 0.35];
        spread = 0.22;
        break;
      case 2: // Fist-S (Mengepal)
        ext = [0.50, 0.35, 0.35, 0.35, 0.35];
        spread = 0.18;
        break;
      case 3: // Thumb-Up (Jempol)
        ext = [1.15, 0.35, 0.35, 0.35, 0.35];
        spread = 0.25;
        break;
      case 4: // Pinch-O (Menguncup)
        ext = [0.65, 0.65, 0.55, 0.50, 0.45];
        spread = 0.12;
        break;
      case 5: // Open-5 (5 jari mekar)
        ext = [1.05, 1.05, 1.08, 1.05, 1.00];
        spread = 0.35;
        break;
      case 6: // V-2 (Telunjuk & Tengah)
        ext = [0.45, 1.08, 1.08, 0.35, 0.35];
        spread = 0.34;
        break;
      case 7: // Y-Handshape (Jempol & Kelingking)
        ext = [1.10, 0.35, 0.35, 0.35, 1.08];
        spread = 0.38;
        break;
    }
  }

  const baseAngle = -Math.PI / 2;
  for (let finger = 0; finger < 5; finger++) {
    const dir = isRightHand ? 1 : -1;
    const angle = baseAngle + dir * (finger - 2) * spread;
    const lenScale = ext[finger];
    for (let joint = 1; joint <= 4; joint++) {
      const idx = 1 + finger * 4 + (joint - 1);
      const radius = 0.022 * joint * lenScale;
      pts[idx] = [
        Math.min(0.95, Math.max(0.05, wx + radius * Math.cos(angle))),
        Math.min(0.95, Math.max(0.05, wy + radius * Math.sin(angle))),
        -0.08 - 0.005 * joint
      ];
    }
  }
  return pts;
}

/**
 * Bangkitkan animasi referensi 86 titik yang akurat sesuai Database Fonologi (data/phonology.csv)
 * untuk ke-32 kata BISINDO/FSL maupun ke-26 Abjad Ejaan Jari (A-Z).
 */
export function generateReferenceSignKeypoints(targetName = "HALO", numFrames = 64) {
  const key = String(targetName || "HALO").toUpperCase();
  const phono = PHONOLOGY_DB[key] || { handshape: 0, location: 3, movement: 2, two_handed: 0 };
  const isAlphabet = key.length === 1 && key >= "A" && key <= "Z";

  // Lokasi target tangan kanan berdasarkan parameter location di database
  let baseRX = 0.36;
  let baseRY = 0.48;
  if (isAlphabet) {
    baseRX = 0.38;
    baseRY = 0.42;
  } else if (phono.location === 0) {
    // Kepala / Dahi
    baseRX = 0.40;
    baseRY = 0.24;
  } else if (phono.location === 1) {
    // Mulut / Dagu
    baseRX = 0.46;
    baseRY = 0.33;
  } else if (phono.location === 2) {
    // Dada
    baseRX = 0.47;
    baseRY = 0.48;
  } else if (phono.location === 4) {
    // Kedua telapak bertemu di tengah
    baseRX = 0.45;
    baseRY = 0.48;
  }

  let baseLX = phono.two_handed ? (phono.location === 4 ? 0.55 : 0.62) : 0.66;
  let baseLY = phono.two_handed ? baseRY : 0.72;

  const frames = new Array(numFrames);
  for (let t = 0; t < numFrames; t++) {
    const u = t / Math.max(1, numFrames - 1);
    const frame = new Array(NUM_NODES);

    // Hitung perpindahan (movement) sesuai database: 0=tahan, 1=maju/naik, 2=kiri-kanan, 3=angguk/turun, 4=melingkar
    let dx = 0;
    let dy = 0;
    if (!isAlphabet) {
      if (phono.movement === 1) {
        dy = -0.04 * Math.sin(Math.PI * u);
      } else if (phono.movement === 2) {
        dx = 0.05 * Math.sin(2 * Math.PI * 1.5 * u);
      } else if (phono.movement === 3) {
        dy = 0.045 * Math.sin(2 * Math.PI * u);
      } else if (phono.movement === 4) {
        dx = 0.04 * Math.cos(2 * Math.PI * u);
        dy = 0.04 * Math.sin(2 * Math.PI * u);
      }
    } else if (key === "J" || key === "Z") {
      dx = 0.04 * Math.sin(2 * Math.PI * u);
      dy = 0.04 * u;
    }

    const nose = [0.50, 0.24, 0.0];
    const lSh = [0.62, 0.44, 0.0];
    const rSh = [0.38, 0.44, 0.0];
    const rWristX = baseRX + dx;
    const rWristY = baseRY + dy;
    const lWristX = phono.two_handed ? baseLX - dx : baseLX;
    const lWristY = phono.two_handed ? baseLY + dy : baseLY;

    frame[0] = nose;
    frame[1] = lSh;
    frame[2] = rSh;
    frame[3] = [(lSh[0] + lWristX) * 0.5 + 0.04, (lSh[1] + lWristY) * 0.5 + 0.05, -0.04];
    frame[4] = [(rSh[0] + rWristX) * 0.5 - 0.04, (rSh[1] + rWristY) * 0.5 + 0.05, -0.05];
    frame[5] = [lWristX, lWristY, -0.08];
    frame[6] = [rWristX, rWristY, -0.09];
    frame[7] = [0.59, 0.80, 0.0];
    frame[8] = [0.41, 0.80, 0.0];

    const shapeCode = isAlphabet ? key : phono.handshape;
    const rHand21 = buildAnatomicalHand21(rWristX, rWristY, true, shapeCode);
    const lHand21 = buildAnatomicalHand21(lWristX, lWristY, false, phono.two_handed ? shapeCode : 0);

    for (let h = 0; h < 21; h++) {
      frame[9 + h] = lHand21[h];
      frame[30 + h] = rHand21[h];
    }

    // 35 titik wajah
    for (let f = 0; f < 35; f++) {
      if (f < 10) {
        const ang = (f / 10) * Math.PI * 2;
        frame[51 + f] = [nose[0] + 0.026 * Math.cos(ang), nose[1] + 0.048 + 0.012 * Math.sin(ang), -0.02];
      } else if (f < 18) {
        const ang = ((f - 10) / 8) * Math.PI * 2;
        frame[51 + f] = [nose[0] + 0.016 * Math.cos(ang), nose[1] + 0.048 + 0.007 * Math.sin(ang), -0.02];
      } else if (f < 22) {
        const ang = ((f - 18) / 4) * Math.PI * 2;
        frame[51 + f] = [nose[0] - 0.032 + 0.012 * Math.cos(ang), nose[1] - 0.024 + 0.007 * Math.sin(ang), -0.02];
      } else if (f < 26) {
        const ang = ((f - 22) / 4) * Math.PI * 2;
        frame[51 + f] = [nose[0] + 0.032 + 0.012 * Math.cos(ang), nose[1] - 0.024 + 0.007 * Math.sin(ang), -0.02];
      } else if (f === 26) {
        frame[51 + f] = [nose[0] - 0.035, nose[1] - 0.044, -0.02];
      } else if (f === 27) {
        frame[51 + f] = [nose[0] + 0.035, nose[1] - 0.044, -0.02];
      } else {
        const ang = ((f - 28) / 7) * Math.PI * 2;
        frame[51 + f] = [nose[0] + 0.068 * Math.cos(ang), nose[1] + 0.005 + 0.082 * Math.sin(ang), -0.01];
      }
    }

    frames[t] = frame;
  }
  return frames;
}

export class VisionManager {
  constructor({ videoEl, canvasEl, onFrameKeypoints = () => {} } = {}) {
    this.videoEl = videoEl;
    this.canvasEl = canvasEl;
    this.ctx = canvasEl ? canvasEl.getContext("2d") : null;
    this.onFrameKeypoints = onFrameKeypoints;
    this.stream = null;
    this.holistic = null;
    this.holisticReady = false;
    this.holisticBusy = false;
    this.running = false;
    this.rafId = null;
    this.lastRightHand21 = null;
    this.lastLeftHand21 = null;
    this.hudText = "";
  }

  setHudText(text) {
    this.hudText = text || "";
  }

  async startCamera() {
    if (this.running) return true;
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: false
      });
      if (this.videoEl) {
        this.videoEl.srcObject = this.stream;
        await this.videoEl.play();
      }
      this._initHolisticIfAvailable();
      this.running = true;
      this._loop();
      return true;
    } catch (_err) {
      return false;
    }
  }

  stopCamera() {
    this.running = false;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
  }

  _initHolisticIfAvailable() {
    if (typeof window !== "undefined" && window.Holistic) {
      try {
        this.holistic = new window.Holistic({
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`
        });
        this.holistic.setOptions({
          modelComplexity: 1,
          smoothLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });
        this.holistic.onResults((results) => {
          this.holisticReady = true;

          // Gunakan HANYA tangan yang benar-benar terdeteksi di kamera!
          // Jangan membuat gerakan jari palsu saat tangan tidak diangkat ke depan kamera.
          const left21 = results.leftHandLandmarks || null;
          const right21 = results.rightHandLandmarks || null;
          const hasVisibleHand = Boolean(left21 || right21);

          this.lastLeftHand21 = left21;
          this.lastRightHand21 = right21;

          const kp86 = selectFromHolistic(
            results.poseLandmarks,
            left21,
            right21,
            results.faceLandmarks
          );

          // Jika wajah terdeteksi lewat pose hidung tetapi faceMesh belum keluar, gambar kontur wajah stabil
          if (!results.faceLandmarks && kp86[0] && (kp86[0][0] !== 0 || kp86[0][1] !== 0)) {
            const refFace = generateReferenceSignKeypoints("HALO", 1)[0];
            const dx = kp86[0][0] - refFace[0][0];
            const dy = kp86[0][1] - refFace[0][1];
            for (let f = 51; f < 86; f++) {
              kp86[f] = [refFace[f][0] + dx, refFace[f][1] + dy, refFace[f][2]];
            }
          }

          if (this.ctx && this.canvasEl) {
            drawSkeleton86(this.ctx, kp86, this.canvasEl.width, this.canvasEl.height, {
              hudText: hasVisibleHand ? this.hudText : ""
            });
          }
          this.onFrameKeypoints({
            kp86,
            rightHand21: right21,
            leftHand21: left21,
            hasVisibleHand,
            rawResults: results
          });
        });
      } catch (_e) {
        this.holistic = null;
      }
    }
  }

  _loop() {
    if (!this.running) return;
    if (this.videoEl && this.videoEl.readyState >= 2) {
      if (this.holistic && !this.holisticBusy) {
        this.holisticBusy = true;
        Promise.resolve(this.holistic.send({ image: this.videoEl }))
          .catch(() => {})
          .finally(() => {
            this.holisticBusy = false;
          });
      }
    }
    this.rafId = requestAnimationFrame(() => this._loop());
  }
}
