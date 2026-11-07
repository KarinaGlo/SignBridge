/**
 * web/js/features.js
 * Kontrak 3 (PDF Hal. 11 & 15): Paritas Preprocessing Keypoint Python <-> JS
 * Identik secara matematis (max diff < 1e-5) dengan signbridge/features.py:
 *   1. selectFromHolistic(pose33, left21, right21, face468) -> [86][3]
 *   2. trimInactive(kp) -> [T'][86][3]
 *   3. normalizePose(kp) -> [T'][86][3]
 *   4. resampleFrames(kp, targetLen = 64) -> [64][86][3]
 *   5. preprocessKeypoints(kp, targetLen = 64, doTrim = true) -> [64][86][3]
 */

export const POSE_IDX = [0, 11, 12, 13, 14, 15, 16, 23, 24];
export const FACE_IDX = [
  0, 13, 14, 17, 37, 39, 40, 61, 78, 80, 81, 82, 84, 87,
  88, 91, 95, 146,
  178, 291,
  70, 63, 105, 66,
  300, 293, 334, 296,
  33, 133, 159,
  362, 263, 386,
  1
];

export const NUM_POSE = 9;
export const NUM_HAND = 21;
export const NUM_FACE = 35;
export const NUM_NODES = 86;
export const NUM_COORDS = 3;
export const SEQ_LEN = 64;

export const IDX_NOSE = 0;
export const IDX_L_SHOULDER = 1;
export const IDX_R_SHOULDER = 2;
export const SLICE_POSE = [0, 9];
export const SLICE_L_HAND = [9, 30];
export const SLICE_R_HAND = [30, 51];
export const SLICE_HANDS = [9, 51];
export const SLICE_FACE = [51, 86];

function toCoord3(pt, missingValue = NaN) {
  if (!pt) return [missingValue, missingValue, missingValue];
  if (Array.isArray(pt)) {
    return [
      Math.fround(Number(pt[0])),
      Math.fround(Number(pt[1])),
      Math.fround(Number(pt[2]))
    ];
  }
  return [
    Math.fround(Number(pt.x)),
    Math.fround(Number(pt.y)),
    Math.fround(Number(pt.z))
  ];
}

/**
 * Ekstrak 86 titik kanonis dari hasil MediaPipe Holistic per frame.
 * Urutan node: [0:9] pose, [9:30] tangan kiri, [30:51] tangan kanan, [51:86] wajah.
 */
export function selectFromHolistic(pose33, leftHand21, rightHand21, face468) {
  const out = new Array(NUM_NODES);
  for (let i = 0; i < NUM_POSE; i++) {
    const idx = POSE_IDX[i];
    out[i] = pose33 && pose33[idx] ? toCoord3(pose33[idx], NaN) : [NaN, NaN, NaN];
  }
  for (let i = 0; i < NUM_HAND; i++) {
    out[9 + i] = leftHand21 && leftHand21[i] ? toCoord3(leftHand21[i], NaN) : [NaN, NaN, NaN];
  }
  for (let i = 0; i < NUM_HAND; i++) {
    out[30 + i] = rightHand21 && rightHand21[i] ? toCoord3(rightHand21[i], NaN) : [NaN, NaN, NaN];
  }
  for (let i = 0; i < NUM_FACE; i++) {
    const idx = FACE_IDX[i];
    out[51 + i] = face468 && face468[idx] ? toCoord3(face468[idx], NaN) : [NaN, NaN, NaN];
  }
  return out;
}

function cloneFrame(frame) {
  const out = new Array(NUM_NODES);
  for (let v = 0; v < NUM_NODES; v++) {
    const pt = frame[v];
    if (!pt) {
      out[v] = [0.0, 0.0, 0.0];
    } else {
      out[v] = [
        Number.isFinite(pt[0]) ? Math.fround(pt[0]) : NaN,
        Number.isFinite(pt[1]) ? Math.fround(pt[1]) : NaN,
        Number.isFinite(pt[2]) ? Math.fround(pt[2]) : NaN
      ];
    }
  }
  return out;
}

function frameHasHand(frameKp) {
  let sumAbs = 0.0;
  let anyFinite = false;
  for (let v = SLICE_HANDS[0]; v < SLICE_HANDS[1]; v++) {
    const pt = frameKp[v];
    if (!pt) continue;
    for (let c = 0; c < 3; c++) {
      const val = Number(pt[c]);
      if (Number.isFinite(val)) {
        anyFinite = true;
        sumAbs += Math.abs(val);
      }
    }
  }
  return anyFinite && sumAbs > 1e-6;
}

/**
 * Pangkas frame awal & akhir yang tidak memiliki aktivitas tangan.
 * Identik dengan signbridge.features.trim_inactive.
 */
export function trimInactive(kp) {
  const F = kp ? kp.length : 0;
  if (F === 0) {
    const zeroFrame = new Array(NUM_NODES);
    for (let v = 0; v < NUM_NODES; v++) zeroFrame[v] = [0.0, 0.0, 0.0];
    return [zeroFrame];
  }

  let firstValid = -1;
  let lastValid = -1;
  for (let t = 0; t < F; t++) {
    if (frameHasHand(kp[t])) {
      if (firstValid === -1) firstValid = t;
      lastValid = t;
    }
  }

  if (firstValid === -1) {
    return kp.map(cloneFrame);
  }
  return kp.slice(firstValid, lastValid + 1).map(cloneFrame);
}

function isPointFinite(pt) {
  return (
    pt != null &&
    Number.isFinite(Number(pt[0])) &&
    Number.isFinite(Number(pt[1])) &&
    Number.isFinite(Number(pt[2]))
  );
}

/**
 * Normalisasi berpusat bahu dan skala lebar bahu per frame.
 * Identik dengan signbridge.features.normalize_pose.
 */
export function normalizePose(kp) {
  const F = kp ? kp.length : 0;
  const out = new Array(F);

  let prevCenter = [0.5, 0.5, 0.0];
  let prevScale = 0.25;

  for (let t = 0; t < F; t++) {
    const frame = kp[t];
    const bL = frame[IDX_L_SHOULDER];
    const bR = frame[IDX_R_SHOULDER];
    if (isPointFinite(bL) && isPointFinite(bR)) {
      const dx = Math.fround(bL[0]) - Math.fround(bR[0]);
      const dy = Math.fround(bL[1]) - Math.fround(bR[1]);
      const dz = Math.fround(bL[2]) - Math.fround(bR[2]);
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (dist >= 1e-4) {
        prevCenter = [
          Math.fround(0.5 * (Math.fround(bL[0]) + Math.fround(bR[0]))),
          Math.fround(0.5 * (Math.fround(bL[1]) + Math.fround(bR[1]))),
          Math.fround(0.5 * (Math.fround(bL[2]) + Math.fround(bR[2])))
        ];
        prevScale = dist;
        break;
      }
    }
  }

  for (let t = 0; t < F; t++) {
    const frame = kp[t];
    const bL = frame[IDX_L_SHOULDER];
    const bR = frame[IDX_R_SHOULDER];
    let center = prevCenter;
    let scale = prevScale;

    if (isPointFinite(bL) && isPointFinite(bR)) {
      const dx = Math.fround(bL[0]) - Math.fround(bR[0]);
      const dy = Math.fround(bL[1]) - Math.fround(bR[1]);
      const dz = Math.fround(bL[2]) - Math.fround(bR[2]);
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (dist >= 1e-4) {
        center = [
          Math.fround(0.5 * (Math.fround(bL[0]) + Math.fround(bR[0]))),
          Math.fround(0.5 * (Math.fround(bL[1]) + Math.fround(bR[1]))),
          Math.fround(0.5 * (Math.fround(bL[2]) + Math.fround(bR[2])))
        ];
        scale = dist;
        prevCenter = center;
        prevScale = scale;
      }
    }

    const invScale = Math.fround(1.0 / scale);
    const normFrame = new Array(NUM_NODES);
    for (let v = 0; v < NUM_NODES; v++) {
      const pt = frame[v];
      if (isPointFinite(pt)) {
        normFrame[v] = [
          Math.fround((Math.fround(pt[0]) - center[0]) * invScale),
          Math.fround((Math.fround(pt[1]) - center[1]) * invScale),
          Math.fround((Math.fround(pt[2]) - center[2]) * invScale)
        ];
      } else {
        normFrame[v] = [0.0, 0.0, 0.0];
      }
    }
    out[t] = normFrame;
  }
  return out;
}

/**
 * Resample sekuens keypoint ke tepat targetLen (64) frame.
 * Indeks deterministik: min(floor((i + 0.5) * F / targetLen), F - 1).
 */
export function resampleFrames(kp, targetLen = SEQ_LEN) {
  const F = kp ? kp.length : 0;
  const out = new Array(targetLen);
  if (F === 0) {
    for (let i = 0; i < targetLen; i++) {
      const zeroFrame = new Array(NUM_NODES);
      for (let v = 0; v < NUM_NODES; v++) zeroFrame[v] = [0.0, 0.0, 0.0];
      out[i] = zeroFrame;
    }
    return out;
  }

  for (let i = 0; i < targetLen; i++) {
    const idx = Math.min(Math.floor(((i + 0.5) * F) / targetLen), F - 1);
    out[i] = cloneFrame(kp[idx]);
  }
  return out;
}

/**
 * Pipeline penuh: trimInactive -> normalizePose -> resampleFrames(64).
 */
export function preprocessKeypoints(kp, targetLen = SEQ_LEN, doTrim = true) {
  if (!kp || kp.length === 0) {
    return resampleFrames([], targetLen);
  }
  const trimmed = doTrim ? trimInactive(kp) : kp.map(cloneFrame);
  const normed = normalizePose(trimmed);
  return resampleFrames(normed, targetLen);
}

/**
 * Konversi array [64][86][3] menjadi Float32Array flat berukuran 64 * 86 * 3 = 16512
 * untuk input tensor ONNX [1, 64, 86, 3].
 */
export function flattenKeypoints(kp64) {
  const flat = new Float32Array(SEQ_LEN * NUM_NODES * NUM_COORDS);
  let offset = 0;
  for (let t = 0; t < SEQ_LEN; t++) {
    const frame = kp64[t];
    for (let v = 0; v < NUM_NODES; v++) {
      const pt = frame[v];
      flat[offset++] = Number.isFinite(pt[0]) ? pt[0] : 0.0;
      flat[offset++] = Number.isFinite(pt[1]) ? pt[1] : 0.0;
      flat[offset++] = Number.isFinite(pt[2]) ? pt[2] : 0.0;
    }
  }
  return flat;
}

/**
 * Ekstrak dari list frame Holistic atau array [F][86][3] lalu normalisasi ke [64][86][3].
 */
export function extractAndNormalize(frames, targetLen = SEQ_LEN, doTrim = true) {
  if (!frames || frames.length === 0) {
    return resampleFrames([], targetLen);
  }
  const converted = frames.map((f) => {
    if (Array.isArray(f) && f.length === NUM_NODES) {
      return cloneFrame(f);
    }
    return selectFromHolistic(f.pose, f.leftHand || f.left_hand, f.rightHand || f.right_hand, f.face);
  });
  return preprocessKeypoints(converted, targetLen, doTrim);
}

/**
 * Hitung energi gerak tangan antar dua frame [86][3] untuk deteksi batas isyarat.
 */
export function computeHandMotionEnergy(prevFrame, currFrame) {
  if (!prevFrame || !currFrame) return 0.0;
  let sum = 0.0;
  let valid = 0;
  for (let v = SLICE_HANDS[0]; v < SLICE_HANDS[1]; v++) {
    const p = prevFrame[v];
    const c = currFrame[v];
    if (!isPointFinite(p) || !isPointFinite(c)) continue;
    const pActive = p[0] * p[0] + p[1] * p[1] > 1e-8;
    const cActive = c[0] * c[0] + c[1] * c[1] > 1e-8;
    if (pActive && cActive) {
      sum += Math.hypot(c[0] - p[0], c[1] - p[1]);
      valid++;
    }
  }
  return valid > 0 ? sum / valid : 0.0;
}
