"""
signbridge/xmf/preprocess.py — TAHAP 3 (PREPROCESSING TERPADU): satu proses, satu rekaman per sampel,
ke-4 modalitas diproses BERSAMAAN dengan kunci sampel yang sama.

Untuk setiap klip gloss (signer{S}_label{L}_sample{N}):
    video  : mp4 -> MediaPipe Holistic -> 86 titik/frame -> trim/normalisasi bahu/resample -> [64, 86, 3]
    citra  : 16 frame citra dari klip YANG SAMA (atau diambil dari mp4 bila upload belum lengkap)
             -> MediaPipe Pose per frame -> kotak badan-atas median per klip -> crop 112x112 -> uint8 [16,112,112,3]
    audio  : pasangan ucapan konsep yang sama dari bank audio (split sama) -> gelombang 16 kHz [40000]
    teks   : pasangan kalimat konsep yang sama dari bank teks -> id karakter [64]
    -> data/xmf/processed/gloss/<sample_id>.npz  (pose, frames, audio, text, mask, label, ...)

Untuk setiap foto alfabet:
    citra  : MediaPipe Hands -> crop tangan (+25 %) -> uint8 [1,112,112,3]
    video  : landmark tangan dari FOTO YANG SAMA -> normalisasi pergelangan/telapak -> [1, 86, 3]
    audio/teks : pasangan konsep (nama huruf) dari bank.

Normalisasi intensitas citra (ImageNet) dan log-mel audio TIDAK dilakukan di sini, melainkan di dalam
graf model (ONNX), supaya browser mengirim data mentah dan hasilnya identik dengan training.

Mode cicil: sampel yang .npz-nya sudah ada dilewati; jalankan ulang setelah upload Drive bertambah.
Gunakan --refresh-citra untuk memproses ulang klip yang sebelumnya memakai video_fallback.

Contoh:
    python -m signbridge.xmf.preprocess --task gloss --workers 4
    python -m signbridge.xmf.preprocess --task alphabet
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from signbridge.xmf.config import (
    M_AUDIO, M_IMAGE, M_TEXT, M_VIDEO, NUM_COORDS, NUM_MODALITIES, NUM_NODES, SHAPES,
    classes_for, encode_text, texts_for,
)
from signbridge.xmf.ops import (
    crop_square, hand_box, median_box, normalize_hands_static, person_box_from_shoulders,
    stable_hash, uniform_indices, union_box,
)

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_COLUMNS = [
    "sample_id", "task", "label", "class_name", "signer", "group", "npz_path",
    "has_video", "has_image", "has_audio", "has_text", "image_source",
    "split_sd", "split_si", "split_final", "split",
]


# ---------------------------------------------------------------------------
# Pemasangan audio/teks (deterministik per sampel -> val/test reprodusibel)
# ---------------------------------------------------------------------------
class ConceptBank:
    def __init__(self, task: str, bank_path: Optional[Path]):
        self.task = task
        self.texts = texts_for(task)
        self.classes = classes_for(task)
        self.wave = None
        if bank_path and bank_path.exists():
            z = np.load(bank_path, allow_pickle=False)
            self.wave, self.label, self.split = z["wave"], z["label"], z["split"]

    def audio_for(self, sample_id: str, label: int, split: str) -> Tuple[np.ndarray, bool]:
        n = SHAPES[self.task].audio_samples
        if self.wave is None:
            return np.zeros(n, np.float16), False
        idx = np.where((self.label == label) & (self.split == split))[0]
        if len(idx) == 0:
            idx = np.where(self.label == label)[0]
        if len(idx) == 0:
            return np.zeros(n, np.float16), False
        return self.wave[idx[stable_hash("a:" + sample_id) % len(idx)]], True

    def text_for(self, sample_id: str, label: int) -> Tuple[np.ndarray, str]:
        variants = self.texts[self.classes[label]]
        t = variants[stable_hash("t:" + sample_id) % len(variants)]
        return np.array(encode_text(t, SHAPES[self.task].text_len), dtype=np.int16), t


# ---------------------------------------------------------------------------
# MediaPipe helpers (diimpor malas agar modul lain bisa diuji tanpa mediapipe)
# ---------------------------------------------------------------------------
def _mp():
    try:
        import cv2  # noqa: F401
        import mediapipe as mp
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Butuh mediapipe==0.10.11 dan opencv-python (pip install -r requirements-xmf.txt)") from e
    return mp


def _arr(lms, count: int) -> Optional[np.ndarray]:
    if lms is None:
        return None
    return np.array([[p.x, p.y, p.z] for p in lms.landmark[:count]], dtype=np.float32)


def video_holistic(video_path: Path) -> Tuple[np.ndarray, List[np.ndarray]]:
    """Satu kali decode mp4 -> (keypoint mentah [F,86,3], daftar frame RGB uint8)."""
    import cv2

    from signbridge.constants import select_from_holistic

    mp = _mp()
    cap = cv2.VideoCapture(str(video_path))
    kps, frames = [], []
    with mp.solutions.holistic.Holistic(static_image_mode=False, model_complexity=1,
                                        min_detection_confidence=0.5, min_tracking_confidence=0.5) as hol:
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            r = hol.process(rgb)
            kps.append(select_from_holistic(_arr(r.pose_landmarks, 33), _arr(r.left_hand_landmarks, 21),
                                            _arr(r.right_hand_landmarks, 21), _arr(r.face_landmarks, 468)))
            frames.append(rgb)
    cap.release()
    if not kps:
        raise ValueError(f"video kosong/rusak: {video_path}")
    return np.stack(kps).astype(np.float32), frames


def shoulders_from_image(pose_model, rgb: np.ndarray):
    r = pose_model.process(rgb)
    if r.pose_landmarks is None:
        return None
    lm = r.pose_landmarks.landmark
    return (lm[11].x, lm[11].y), (lm[12].x, lm[12].y)


def _read_rgb(path: str) -> np.ndarray:
    from PIL import Image

    with Image.open(ROOT / path if not Path(path).is_absolute() else path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Satu sampel GLOSS
# ---------------------------------------------------------------------------
def process_gloss(row: Dict, out_dir: Path, bank_path: Optional[str]) -> Dict:
    from signbridge.features import preprocess_keypoints

    sh = SHAPES["gloss"]
    mp = _mp()
    bank = ConceptBank("gloss", Path(bank_path) if bank_path else None)
    sid, label = row["sample_id"], int(row["label"])

    # VIDEO (+ frame RGB untuk fallback citra) — satu kali decode
    pose = np.zeros((sh.pose_frames, NUM_NODES, NUM_COORDS), np.float32)
    has_video, vid_frames, raw_kp = False, [], None
    if row["video_path"]:
        raw_kp, vid_frames = video_holistic(ROOT / row["video_path"])
        pose, _ = preprocess_keypoints(raw_kp, target_len=sh.pose_frames, trim=True)
        pose = np.nan_to_num(pose, nan=0.0).astype(np.float32)
        has_video = True

    # CITRA dari klip yang sama
    citra = [p for p in row["citra_paths"].split(";") if p]
    if len(citra) >= sh.image_frames:
        imgs = [_read_rgb(citra[i]) for i in uniform_indices(len(citra), sh.image_frames)]
        source = "citra"
    elif vid_frames:
        imgs = [vid_frames[i] for i in uniform_indices(len(vid_frames), sh.image_frames)]
        source = "video_fallback"
    else:
        imgs, source = [], "missing"

    frames = np.zeros((sh.image_frames, sh.image_side, sh.image_side, 3), np.uint8)
    if imgs:
        h, w = imgs[0].shape[:2]
        with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1) as pm:
            boxes = []
            for im in imgs:
                s = shoulders_from_image(pm, im)
                boxes.append(person_box_from_shoulders(s[0], s[1], w, h) if s else None)
        box = median_box(boxes, w, h)
        frames = np.stack([crop_square(im, box, sh.image_side) for im in imgs])

    split = row.get("split_sd", "train")
    audio, has_audio = bank.audio_for(sid, label, split)
    text, text_str = bank.text_for(sid, label)
    mask = np.zeros(NUM_MODALITIES, np.float32)
    mask[[M_VIDEO, M_IMAGE, M_AUDIO, M_TEXT]] = [has_video, bool(imgs), has_audio, True]

    npz = out_dir / f"{sid}.npz"
    np.savez_compressed(npz, pose=pose.astype(np.float16), frames=frames, audio=audio.astype(np.float16),
                        text=text, mask=mask, label=np.int64(label), text_str=np.array(text_str))
    return {
        "sample_id": sid, "task": "gloss", "label": label, "class_name": row["gloss"],
        "signer": row["signer"], "group": f"signer{row['signer']}", "npz_path": str(npz.relative_to(ROOT)),
        "has_video": int(has_video), "has_image": int(bool(imgs)), "has_audio": int(has_audio), "has_text": 1,
        "image_source": source, "split_sd": row["split_sd"], "split_si": row["split_si"],
        "split_final": row["split_final"], "split": row["split_sd"],
    }


# ---------------------------------------------------------------------------
# Satu sampel ALFABET
# ---------------------------------------------------------------------------
def process_alphabet(row: Dict, out_dir: Path, bank_path: Optional[str]) -> Dict:
    sh = SHAPES["alphabet"]
    mp = _mp()
    bank = ConceptBank("alphabet", Path(bank_path) if bank_path else None)
    sid, label = row["sample_id"], int(row["label"])
    rgb = _read_rgb(row["image_path"])
    h, w = rgb.shape[:2]

    kp = np.full((NUM_NODES, NUM_COORDS), np.nan, np.float32)
    hands = []
    with mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.3) as hm:
        r = hm.process(rgb)
        for lms in (r.multi_hand_landmarks or []):
            hands.append(_arr(lms, 21))
    # Kanonik: tangan paling kiri di gambar -> slot kiri (sama dengan xmf.js), hindari ambiguitas handedness
    hands.sort(key=lambda a: float(np.nanmean(a[:, 0])))
    if len(hands) == 1:
        kp[30:51] = hands[0]
    elif len(hands) >= 2:
        kp[9:30], kp[30:51] = hands[0], hands[1]
    pose = normalize_hands_static(kp)[None]                      # [1, 86, 3]
    box = union_box([hand_box(hd, w, h) for hd in hands]) or (w / 2, h / 2, float(min(w, h)))
    frames = crop_square(rgb, box, sh.image_side)[None]          # [1, 112, 112, 3]

    split = row["split"]
    audio, has_audio = bank.audio_for(sid, label, split)
    text, text_str = bank.text_for(sid, label)
    mask = np.array([1.0 if hands else 0.0, 1.0, float(has_audio), 1.0], np.float32)

    npz = out_dir / (sid.replace("/", "__") + ".npz")
    np.savez_compressed(npz, pose=pose.astype(np.float16), frames=frames, audio=audio.astype(np.float16),
                        text=text, mask=mask, label=np.int64(label), text_str=np.array(text_str))
    return {
        "sample_id": sid, "task": "alphabet", "label": label, "class_name": row["letter"], "signer": "",
        "group": row["group"], "npz_path": str(npz.relative_to(ROOT)), "has_video": int(bool(hands)),
        "has_image": 1, "has_audio": int(has_audio), "has_text": 1,
        "image_source": "hand_crop" if hands else "center_crop",
        "split_sd": split, "split_si": split, "split_final": row["split_final"], "split": split,
    }


# ---------------------------------------------------------------------------
def run(task: str, manifest: Path, out_root: Path, bank: Optional[Path], workers: int,
        limit: Optional[int], refresh_citra: bool) -> Path:
    out_dir = out_root / task
    out_dir.mkdir(parents=True, exist_ok=True)
    with manifest.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if limit:
        rows = rows[:limit]

    proc_csv = out_root / f"{task}_processed.csv"
    done: Dict[str, Dict] = {}
    if proc_csv.exists():
        with proc_csv.open(encoding="utf-8") as f:
            done = {r["sample_id"]: r for r in csv.DictReader(f) if (ROOT / r["npz_path"]).exists()}

    todo = []
    for r in rows:
        prev = done.get(r["sample_id"])
        if prev is None:
            todo.append(r)
        elif refresh_citra and prev.get("image_source") == "video_fallback" and r.get("image_source") == "citra":
            todo.append(r)
    fn = process_gloss if task == "gloss" else process_alphabet
    print(f"[preprocess] {task}: {len(rows)} sampel, {len(rows) - len(todo)} sudah ada, {len(todo)} diproses")

    t0, errors = time.time(), []
    bank_s = str(bank) if bank else None
    if workers > 1:
        with ProcessPoolExecutor(workers) as ex:
            futs = {ex.submit(fn, r, out_dir, bank_s): r["sample_id"] for r in todo}
            for i, fu in enumerate(as_completed(futs), 1):
                try:
                    done[futs[fu]] = fu.result()
                except Exception as e:  # noqa: BLE001
                    errors.append((futs[fu], str(e)))
                if i % 50 == 0:
                    print(f"  {i}/{len(todo)}  {time.time() - t0:.0f}s")
    else:
        for i, r in enumerate(todo, 1):
            try:
                done[r["sample_id"]] = fn(r, out_dir, bank_s)
            except Exception as e:  # noqa: BLE001
                errors.append((r["sample_id"], str(e)))
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}  {time.time() - t0:.0f}s")

    with proc_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PROCESSED_COLUMNS)
        w.writeheader()
        for sid in sorted(done):
            w.writerow({c: done[sid].get(c, "") for c in PROCESSED_COLUMNS})
    rep = {"task": task, "n": len(done), "errors": errors[:50], "n_errors": len(errors),
           "seconds": round(time.time() - t0, 1)}
    (out_root / f"{task}_preprocess_report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"[preprocess] selesai: {len(done)} rekaman, {len(errors)} error -> {proc_csv}")
    return proc_csv


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["gloss", "alphabet"], default="gloss")
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "data/xmf/processed")
    ap.add_argument("--bank", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--refresh-citra", action="store_true")
    a = ap.parse_args(argv)
    manifest = a.manifest or ROOT / "data/xmf/ingest" / f"{a.task}_manifest.csv"
    bank = a.bank or ROOT / "data/xmf/bank" / f"{a.task}_audio.npz"
    if not bank.exists():
        print(f"[preprocess] PERINGATAN: bank audio {bank} belum ada -> modalitas audio ditandai hilang. "
              "Jalankan dulu: python -m signbridge.xmf.audio_bank --task", a.task)
    run(a.task, manifest, a.out, bank, a.workers, a.limit, a.refresh_citra)


if __name__ == "__main__":
    main()
