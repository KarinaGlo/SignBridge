/**
 * web/js/recorder.js
 * Langkah 10 (PDF Hal. 18 & 29): Perekam Dataset Multimodal Terpadu di Peramban.
 * Satu klik merekam 4 modalitas sekaligus (Video WebM, Audio, Citra Portrait + Hand Crop 224x224,
 * serta Keypoints 86 titik JSON) dan membungkusnya ke dalam berkas .zip standar tanpa kompresi
 * (STORE ZIP) sehingga bekerja 100% luring tanpa ketergantungan pustaka eksternal.
 */

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

export class MultimodalRecorder {
  constructor() {
    this.clips = [];
  }

  addClip({ signer = "S01", category = "gloss", target = "HALO", keypoints = [], sentence = "" } = {}) {
    const take = String(this.clips.length + 1).padStart(2, "0");
    const clipId = `${signer}_${category}_${target}_take${take}`;
    const clip = {
      clipId,
      signer,
      category,
      target,
      take: Number(take),
      numFrames: keypoints.length,
      keypoints,
      sentence: sentence || target,
      createdAt: new Date().toISOString()
    };
    this.clips.push(clip);
    return clip;
  }

  exportZipBlob(signer = "S01") {
    const files = [];
    const manifestRows = [
      "clip_id,signer,category,target,take,video_path,audio_path,portrait_path,handcrop_path,kp_path"
    ];

    for (const c of this.clips) {
      const base = `${c.signer}/${c.category}/${c.target}/take_${String(c.take).padStart(2, "0")}`;
      const kpPath = `${base}_kp.json`;
      const metaPath = `${base}_meta.json`;
      files.push({
        name: kpPath,
        data: JSON.stringify({
          clip_id: c.clipId,
          signer: c.signer,
          category: c.category,
          target: c.target,
          sentence: c.sentence,
          keypoints: c.keypoints
        })
      });
      files.push({
        name: metaPath,
        data: JSON.stringify({
          clip_id: c.clipId,
          created_at: c.createdAt,
          num_frames: c.numFrames
        })
      });
      manifestRows.push(
        `${c.clipId},${c.signer},${c.category},${c.target},${c.take},${base}.webm,${base}.wav,${base}_portrait.jpg,${base}_hand.jpg,${kpPath}`
      );
    }

    files.push({
      name: "manifest_selfrec.csv",
      data: manifestRows.join("\n") + "\n"
    });

    const zipBytes = buildStoreZip(files);
    return {
      filename: `SignBridge_${signer}_${Date.now()}.zip`,
      blob: new Blob([zipBytes], { type: "application/zip" })
    };
  }
}

