/**
 * web/js/recorder.js
 * Langkah 10 (PDF Hal. 18 & 29): Perekam Dataset Multimodal Terpadu di Peramban.
 * Satu klik merekam 4 modalitas BERPASANGAN untuk model fusion M6:
 *   - video : deret keypoint 86 titik dari kamera (MediaPipe Holistic) -> *_kp.json
 *   - citra : crop tangan 224x224 + portrait dari frame tangan terlengkap -> *_hand.jpg, *_portrait.jpg
 *   - audio : suara mikrofon, mono 16 kHz PCM 16-bit                    -> *.wav
 *   - teks  : kalimat konteks yang diketik perekam                       -> kolom `text` + *_meta.json
 * lalu membungkusnya ke berkas .zip standar tanpa kompresi (STORE ZIP), 100% luring.
 * Paket dibaca oleh scripts/build_multimodal_manifest.py.
 */

import { computeHandCropBox } from "./handcrop.js";
import { BISINDO_GLOSSES, FINGERSPELL_LABELS } from "./config.js";

function nowMs() {
  if (typeof performance !== "undefined" && typeof performance.now === "function") {
    return performance.now();
  }
  return Date.now();
}

export function classifyMicrophoneError(err) {
  const name = err?.name || "";
  if (name === "NotAllowedError" || name === "PermissionDeniedError" || name === "SecurityError") {
    return {
      status: "missing",
      reason: "permission_denied",
      message: "Izin mikrofon ditolak. Klip tetap direkam tanpa audio; aktifkan izin mikrofon browser lalu coba rekam ulang."
    };
  }
  if (name === "NotFoundError" || name === "DevicesNotFoundError") {
    return {
      status: "missing",
      reason: "device_not_found",
      message: "Perangkat mikrofon tidak ditemukan. Klip tetap direkam tanpa audio; sambungkan mikrofon lalu coba lagi."
    };
  }
  return {
    status: "missing",
    reason: "capture_error",
    message: `Gagal mengakses mikrofon (${err?.message || "kesalahan perangkat"}). Klip direkam tanpa audio.`
  };
}

function crc32(bytes) {
  let c = -1;
  for (let i = 0; i < bytes.length; i++) {
    c = (c >>> 8) ^ CRC_TABLE[(c ^ bytes[i]) & 0xff];
  }
  return (c ^ -1) >>> 0;
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c >>> 0;
  }
  return table;
})();

/**
 * Buat arsip ZIP (metode STORE) dari daftar berkas [{ name: string, data: Uint8Array }].
 */
export function buildStoreZip(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const file of files) {
    const nameBytes = encoder.encode(file.name);
    const dataBytes =
      file.data instanceof Uint8Array
        ? file.data
        : encoder.encode(typeof file.data === "string" ? file.data : JSON.stringify(file.data));
    const crc = crc32(dataBytes);
    const size = dataBytes.length;

    const localHeader = new Uint8Array(30 + nameBytes.length);
    const lv = new DataView(localHeader.buffer);
    lv.setUint32(0, 0x04034b50, true);
    lv.setUint16(4, 20, true);
    lv.setUint16(6, 0, true);
    lv.setUint16(8, 0, true); // STORE
    lv.setUint16(10, 0, true);
    lv.setUint16(12, 0, true);
    lv.setUint32(14, crc, true);
    lv.setUint32(18, size, true);
    lv.setUint32(22, size, true);
    lv.setUint16(26, nameBytes.length, true);
    lv.setUint16(28, 0, true);
    localHeader.set(nameBytes, 30);

    localParts.push(localHeader, dataBytes);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    const cv = new DataView(centralHeader.buffer);
    cv.setUint32(0, 0x02014b50, true);
    cv.setUint16(4, 20, true);
    cv.setUint16(6, 20, true);
    cv.setUint16(8, 0, true);
    cv.setUint16(10, 0, true);
    cv.setUint16(12, 0, true);
    cv.setUint16(14, 0, true);
    cv.setUint32(16, crc, true);
    cv.setUint32(20, size, true);
    cv.setUint32(24, size, true);
    cv.setUint16(28, nameBytes.length, true);
    cv.setUint16(30, 0, true);
    cv.setUint16(32, 0, true);
    cv.setUint16(34, 0, true);
    cv.setUint16(36, 0, true);
    cv.setUint32(38, 0, true);
    cv.setUint32(42, offset, true);
    centralHeader.set(nameBytes, 46);

    centralParts.push(centralHeader);
    offset += localHeader.length + size;
  }

  let centralSize = 0;
  for (const c of centralParts) centralSize += c.length;

  const eocd = new Uint8Array(22);
  const ev = new DataView(eocd.buffer);
  ev.setUint32(0, 0x06054b50, true);
  ev.setUint16(4, 0, true);
  ev.setUint16(6, 0, true);
  ev.setUint16(8, files.length, true);
  ev.setUint16(10, files.length, true);
  ev.setUint32(12, centralSize, true);
  ev.setUint32(16, offset, true);
  ev.setUint16(20, 0, true);

  const totalSize = offset + centralSize + eocd.length;
  const out = new Uint8Array(totalSize);
  let pos = 0;
  for (const p of localParts) {
    out.set(p, pos);
    pos += p.length;
  }
  for (const c of centralParts) {
    out.set(c, pos);
    pos += c.length;
  }
  out.set(eocd, pos);
  return out;
}


export const TARGET_SAMPLE_RATE = 16000;

/**
 * Resampling interpolasi linear — identik dengan signbridge.multimodal.features.resample_linear.
 */
export function resampleLinear(pcm, srIn, srOut = TARGET_SAMPLE_RATE) {
  const n = pcm.length;
  if (srIn === srOut || n === 0) return Float32Array.from(pcm);
  const nOut = Math.round((n * srOut) / srIn);
  if (nOut <= 1) return new Float32Array(Math.max(nOut, 0));
  const out = new Float32Array(nOut);
  const step = (n - 1) / (nOut - 1);
  for (let i = 0; i < nOut; i++) {
    const pos = i * step;
    const i0 = Math.floor(pos);
    const i1 = Math.min(n - 1, i0 + 1);
    const f = pos - i0;
    out[i] = pcm[i0] * (1 - f) + pcm[i1] * f;
  }
  return out;
}

/**
 * Float32 [-1, 1] mono -> berkas WAV PCM 16-bit little-endian (Uint8Array).
 */
export function encodeWavPCM16(pcm, sampleRate = TARGET_SAMPLE_RATE) {
  const n = pcm.length;
  const buf = new ArrayBuffer(44 + n * 2);
  const v = new DataView(buf);
  const writeStr = (off, s) => {
    for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i));
  };
  writeStr(0, "RIFF");
  v.setUint32(4, 36 + n * 2, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); // PCM
  v.setUint16(22, 1, true); // mono
  v.setUint32(24, sampleRate, true);
  v.setUint32(28, sampleRate * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  writeStr(36, "data");
  v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const s = Math.max(-1, Math.min(1, pcm[i]));
    v.setInt16(44 + i * 2, Math.round(s * 32767), true);
  }
  return new Uint8Array(buf);
}

/** Escape nilai CSV (kalimat bisa mengandung koma/kutip). */
export function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function canvasToJpegBytes(canvas, quality = 0.9) {
  return new Promise((resolve) => {
    canvas.toBlob(
      async (blob) => resolve(blob ? new Uint8Array(await blob.arrayBuffer()) : null),
      "image/jpeg",
      quality
    );
  });
}

/**
 * Penangkap klip multimodal asli dari kamera + mikrofon.
 * app.js memanggil pushFrame() dari callback MediaPipe selama `active`.
 */
export class MultimodalCapture {
  constructor({ videoEl } = {}) {
    this.videoEl = videoEl;
    this.active = false;
    this.recordingStartMs = null;
    this.audioStartMs = null;
    this.frames = [];
    this.frameRecords = [];
    this.bestHand = null; // { hand21, handCount, frameIdx }
    this.handSnapshot = null;
    this.portraitSnapshot = null;
  }

  pushFrame(kp86, rightHand21, leftHand21) {
    if (!this.active || !kp86) return;
    const tNow = nowMs();
    if (this.recordingStartMs === null) {
      this.recordingStartMs = tNow;
    }
    const timestampMs = Math.max(0, Math.round((tNow - this.recordingStartMs) * 100) / 100);
    const kpCopy = kp86.map((p) => [p[0] || 0, p[1] || 0, p[2] || 0]);
    const frameIndex = this.frames.length;
    this.frames.push(kpCopy);

    const rCount = rightHand21 ? rightHand21.filter((p) => p && Math.abs(p.x ?? p[0]) > 1e-5).length : 0;
    const lCount = leftHand21 ? leftHand21.filter((p) => p && Math.abs(p.x ?? p[0]) > 1e-5).length : 0;
    const validHand = rCount > 0 || lCount > 0;
    this.frameRecords.push({
      frame_index: frameIndex,
      timestamp_ms: timestampMs,
      valid_hand: validHand,
      keypoints: kpCopy
    });

    const hand = rightHand21 && rightHand21.length ? rightHand21 : leftHand21;
    const count = hand ? hand.filter((p) => p && (Math.abs(p.x ?? p[0]) > 1e-5)).length : 0;
    if (count > 0 && (!this.bestHand || count >= this.bestHand.handCount)) {
      this.bestHand = { hand21: hand, handCount: count, frameIdx: frameIndex };
      this._snapshot(hand);
    }
  }

  _snapshot(hand21) {
    const v = (this.videoEl && this.videoEl.videoWidth)
      ? this.videoEl
      : (typeof document !== "undefined"
          ? (document.getElementById("rec-camera-video") || document.getElementById("camera-video"))
          : null);
    if (!v || !v.videoWidth || typeof document === "undefined") return;
    const W = v.videoWidth;
    const H = v.videoHeight;
    const full = document.createElement("canvas");
    full.width = W;
    full.height = H;
    full.getContext("2d").drawImage(v, 0, 0, W, H);
    const box = computeHandCropBox(hand21.map((p) => (Array.isArray(p) ? p : [p.x, p.y])), W, H, 0.25);
    const hc = document.createElement("canvas");
    hc.width = 224;
    hc.height = 224;
    hc.getContext("2d").drawImage(full, box.x0, box.y0, box.x1 - box.x0, box.y1 - box.y0, 0, 0, 224, 224);
    const pc = document.createElement("canvas");
    pc.width = 320;
    pc.height = Math.round((320 * H) / W);
    pc.getContext("2d").drawImage(full, 0, 0, pc.width, pc.height);
    this.handSnapshot = hc;
    this.portraitSnapshot = pc;
  }

  /**
   * Rekam selama durationMs. Mengembalikan { keypoints, wav, handJpg, portraitJpg, numFrames, audioSeconds }.
   */
  async capture(durationMs = 2500) {
    this.frames = [];
    this.frameRecords = [];
    this.recordingStartMs = null;
    this.audioStartMs = null;
    this.bestHand = null;
    this.handSnapshot = null;
    this.portraitSnapshot = null;

    let stream = null;
    let ctx = null;
    let node = null;
    let muteGain = null;
    let audioStatus = "recorded";
    let audioReason = null;
    let audioErrorMessage = null;
    const chunks = [];
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } });
      const AC = window.AudioContext || window.webkitAudioContext;
      ctx = new AC();
      const src = ctx.createMediaStreamSource(stream);
      node = ctx.createScriptProcessor(4096, 1, 1);
      node.onaudioprocess = (e) => {
        if (this.active) {
          if (this.audioStartMs === null) {
            this.audioStartMs = Math.max(0, Math.round((nowMs() - (this.recordingStartMs ?? nowMs())) * 100) / 100);
          }
          chunks.push(Float32Array.from(e.inputBuffer.getChannelData(0)));
        }
      };
      // Loopback audio dicegah dengan GainNode berbobot 0:
      // ScriptProcessorNode tetap aktif di peramban tanpa mengeluarkan suara ke speaker.
      muteGain = ctx.createGain();
      muteGain.gain.value = 0;
      src.connect(node);
      node.connect(muteGain);
      muteGain.connect(ctx.destination);
    } catch (err) {
      // Mikrofon ditolak/tidak ada: kamera tetap jalan, audio ditandai missing dengan alasan jelas (tanpa audio palsu)
      const info = classifyMicrophoneError(err);
      audioStatus = info.status;
      audioReason = info.reason;
      audioErrorMessage = info.message;
    }

    this.recordingStartMs = nowMs();
    this.active = true;
    await new Promise((r) => setTimeout(r, durationMs));
    this.active = false;

    let wav = null;
    let audioSeconds = 0;
    if (ctx) {
      const total = chunks.reduce((a, c) => a + c.length, 0);
      const pcm = new Float32Array(total);
      let off = 0;
      for (const c of chunks) {
        pcm.set(c, off);
        off += c.length;
      }
      const pcm16k = resampleLinear(pcm, ctx.sampleRate, TARGET_SAMPLE_RATE);
      audioSeconds = pcm16k.length / TARGET_SAMPLE_RATE;
      if (pcm16k.length > 0) {
        wav = encodeWavPCM16(pcm16k, TARGET_SAMPLE_RATE);
      } else if (audioStatus === "recorded") {
        audioStatus = "missing";
        audioReason = "empty_audio_stream";
        audioErrorMessage = "Tidak ada sampel audio yang terekam dari mikrofon. Klip disimpan tanpa audio.";
      }
      try {
        node.disconnect();
        if (muteGain) muteGain.disconnect();
        await ctx.close();
      } catch (_e) {}
    }
    if (stream) stream.getTracks().forEach((t) => t.stop());

    const handJpg = this.handSnapshot ? await canvasToJpegBytes(this.handSnapshot) : null;
    const portraitJpg = this.portraitSnapshot ? await canvasToJpegBytes(this.portraitSnapshot, 0.85) : null;
    return {
      keypoints: this.frames,
      frameRecords: this.frameRecords,
      audioStartOffsetMs: this.audioStartMs,
      wav,
      audioStatus: wav ? "recorded" : audioStatus,
      audioReason: wav ? null : audioReason,
      audioErrorMessage: wav ? null : audioErrorMessage,
      handJpg,
      portraitJpg,
      numFrames: this.frames.length,
      audioSeconds
    };
  }
}

export const MANIFEST_HEADER =
  "clip_id,signer,category,target,label,take,kp_path,handcrop_path,portrait_path,audio_path,text";

export class MultimodalRecorder {
  constructor() {
    this.clips = [];
  }

  /**
   * Tambah klip. `keypoints` = deret [F][86][3] dari kamera; wav/handJpg/portraitJpg = Uint8Array atau null.
   */
  addClip({
    signer = "S01",
    category = "gloss",
    target = "",
    label = -1,
    keypoints = [],
    frameRecords = null,
    audioStartOffsetMs = null,
    audioStatus = null,
    audioReason = null,
    sentence = "",
    wav = null,
    handJpg = null,
    portraitJpg = null
  } = {}) {
    const cleanTarget = String(target || "").trim().toUpperCase().replace(/[^A-Z0-9_]/g, "_");
    if (!cleanTarget) {
      throw new Error("Target gloss atau huruf wajib dipilih sebelum menyimpan klip.");
    }
    let resolvedLabel = label;
    if (category === "gloss") {
      const idx = BISINDO_GLOSSES.indexOf(cleanTarget);
      if (idx === -1) {
        throw new Error(`Gloss '${cleanTarget}' tidak terdaftar pada Dictionary B (BISINDO_32_GLOSSES).`);
      }
      if (resolvedLabel !== -1 && resolvedLabel !== idx) {
        throw new Error(`Label ${resolvedLabel} tidak cocok dengan indeks Dictionary B untuk '${cleanTarget}' (${idx}).`);
      }
      resolvedLabel = idx;
    } else if (category === "letter") {
      const idx = FINGERSPELL_LABELS.indexOf(cleanTarget);
      if (idx === -1) {
        throw new Error(`Huruf '${cleanTarget}' tidak valid untuk kategori ejaan jari (A-Z).`);
      }
      if (resolvedLabel !== -1 && resolvedLabel !== idx) {
        throw new Error(`Label ${resolvedLabel} tidak cocok dengan indeks huruf '${cleanTarget}' (${idx}).`);
      }
      resolvedLabel = idx;
    } else {
      throw new Error(`Kategori '${category}' tidak didukung.`);
    }

    const take = String(this.clips.length + 1).padStart(2, "0");
    const cleanSigner = String(signer || "S01").toUpperCase().replace(/[^A-Z0-9]/g, "");
    const clipId = `SB_${cleanSigner}_${cleanTarget}_T${take}`;
    const normalizedFrames = Array.isArray(frameRecords) && frameRecords.length === keypoints.length
      ? frameRecords
      : null;
    const clip = {
      clipId,
      sampleId: clipId,
      signer,
      category,
      target: cleanTarget,
      label: resolvedLabel,
      take: Number(take),
      numFrames: keypoints.length,
      keypoints,
      frameRecords: normalizedFrames,
      audioStartOffsetMs,
      audioStatus: wav ? "recorded" : (audioStatus || "missing"),
      audioReason: wav ? null : (audioReason || "not_provided"),
      sentence: sentence || "",
      wav,
      handJpg,
      portraitJpg,
      createdAt: new Date().toISOString()
    };
    this.clips.push(clip);
    return clip;
  }

  /** Ringkasan kelengkapan modalitas (untuk ditampilkan di UI). */
  summary() {
    const s = { clips: this.clips.length, video: 0, image: 0, audio: 0, text: 0, complete: 0 };
    for (const c of this.clips) {
      const v = c.keypoints.length > 0;
      const i = !!c.handJpg;
      const a = !!c.wav;
      const t = !!c.sentence.trim();
      s.video += v;
      s.image += i;
      s.audio += a;
      s.text += t;
      s.complete += v && i && a && t;
    }
    return s;
  }

  buildFiles() {
    const files = [];
    const rows = [MANIFEST_HEADER];
    for (const c of this.clips) {
      const base = `${c.signer}/${c.category}/${c.target}/take_${String(c.take).padStart(2, "0")}`;
      const kpPath = c.keypoints.length ? `${base}_kp.json` : "";
      const handPath = c.handJpg ? `${base}_hand.jpg` : "";
      const portraitPath = c.portraitJpg ? `${base}_portrait.jpg` : "";
      const audioPath = c.wav ? `${base}.wav` : "";
      if (kpPath) {
        const kpPayload = {
          clip_id: c.clipId,
          sample_id: c.sampleId || c.clipId,
          signer: c.signer,
          category: c.category,
          target: c.target,
          sentence: c.sentence,
          keypoints: c.keypoints
        };
        if (c.frameRecords) {
          kpPayload.frame_records = c.frameRecords;
        }
        files.push({
          name: kpPath,
          data: JSON.stringify(kpPayload)
        });
      }
      if (handPath) files.push({ name: handPath, data: c.handJpg });
      if (portraitPath) files.push({ name: portraitPath, data: c.portraitJpg });
      if (audioPath) files.push({ name: audioPath, data: c.wav });
      const metaPayload = {
        clip_id: c.clipId,
        sample_id: c.sampleId || c.clipId,
        created_at: c.createdAt,
        num_frames: c.numFrames,
        label: c.label,
        text: c.sentence,
        audio_status: c.audioStatus,
        audio_missing_reason: c.audioReason,
        modalities: { video: !!kpPath, image: !!handPath, audio: !!audioPath, text: !!c.sentence.trim() }
      };
      if (c.frameRecords) {
        metaPayload.frame_timestamps_ms = c.frameRecords.map((fr) => ({
          frame_index: fr.frame_index,
          timestamp_ms: fr.timestamp_ms,
          valid_hand: fr.valid_hand
        }));
      }
      if (c.audioStartOffsetMs !== null && c.audioStartOffsetMs !== undefined) {
        metaPayload.audio_start_offset_ms = c.audioStartOffsetMs;
      }
      files.push({
        name: `${base}_meta.json`,
        data: JSON.stringify(metaPayload)
      });
      rows.push(
        [c.clipId, c.signer, c.category, c.target, c.label, c.take, kpPath, handPath, portraitPath, audioPath, c.sentence]
          .map(csvEscape)
          .join(",")
      );
    }
    files.push({ name: "manifest_selfrec.csv", data: rows.join("\n") + "\n" });
    return files;
  }

  exportZipBlob(signer = "S01") {
    const zipBytes = buildStoreZip(this.buildFiles());
    return {
      filename: `SignBridge_${signer}_${Date.now()}.zip`,
      blob: new Blob([zipBytes], { type: "application/zip" })
    };
  }
}
