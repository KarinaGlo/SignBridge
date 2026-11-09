"""
scripts/extract_keypoints.py — Modul 01 Langkah 2 (PDF Hal. 14):
Ekstraksi offline 86 titik MediaPipe Holistic dari berkas video (.mp4/.webm/.mov) menjadi .npz
dan pembuatan manifest.csv sesuai Kontrak 1 (video_id,source,gloss,label,signer,kp_path,rgb_path,split_sd).

Keamanan Pipeline (Tahap A):
- Tanpa synthetic fallback (tidak pernah menghasilkan keypoint acak atau memanggil ensure_demo_dataset).
- Mendukung pemindaian ekstensi .mp4, .webm, dan .mov (case-insensitive: .MOV, .MP4, .WEBM).
- Menampilkan error eksplisit jika folder kosong, berkas video rusak/tidak ditemukan, atau
  dependency (opencv-python, mediapipe) belum terpasang.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import (
    BISINDO_32_GLOSSES,
    MANIFEST_COLUMNS,
    NUM_COORDS,
    NUM_KEYPOINTS,
    select_from_holistic,
)
from signbridge.data.video_metadata import (
    EXP_INCLUDED,
    FSL105_SOURCE_ALIASES,
    WLBISINDO_SOURCE_ALIASES,
    assign_wlbisindo_sd_splits,
    classify_sha256_duplicates,
    compute_file_sha256,
    extract_signer_id_from_text,
    is_wlbisindo_filename,
    parse_wlbisindo_filename,
    write_duplicate_report,
)

SUPPORTED_VIDEO_EXTENSIONS: Tuple[str, ...] = (".mp4", ".webm", ".mov")


def check_video_dependencies() -> Tuple[Any, Any]:
    """
    Pastikan opencv-python (cv2) dan mediapipe tersedia sebelum ekstraksi video dijalankan.
    Lempar RuntimeError dengan instruksi instalasi yang jelas bila salah satu belum terpasang.
    """
    missing: List[str] = []
    if importlib.util.find_spec("cv2") is None:
        missing.append("opencv-python (cv2)")
    if importlib.util.find_spec("mediapipe") is None:
        missing.append("mediapipe")

    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(
            f"Dependency wajib untuk ekstraksi keypoint video belum terpasang: {missing_str}. "
            "Silakan instal terlebih dahulu dengan: pip install opencv-python mediapipe"
        )

    import cv2  # type: ignore[import-not-found]
    import mediapipe as mp  # type: ignore[import-not-found]

    return cv2, mp


def discover_video_files(raw_dir: Path) -> List[Path]:
    """
    Pindai seluruh berkas video (.mp4, .webm, .mov; huruf besar maupun kecil) di dalam `raw_dir`.
    Mengabaikan berkas metadata tersembunyi macOS (`._*`).
    Lempar FileNotFoundError jika `raw_dir` tidak ditemukan atau tidak berisi berkas video.
    """
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        raise FileNotFoundError(f"Direktori video mentah tidak ditemukan: {raw_dir}")
    if not raw_dir.is_dir():
        raise NotADirectoryError(f"Jalur input video bukan sebuah direktori: {raw_dir}")

    video_files = sorted(
        p
        for p in raw_dir.rglob("*")
        if p.is_file()
        and not p.name.startswith("._")
        and p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    )
    if not video_files:
        exts = ", ".join(SUPPORTED_VIDEO_EXTENSIONS)
        raise FileNotFoundError(
            f"Tidak ditemukan berkas video ({exts}, case-insensitive) di dalam direktori: {raw_dir}"
        )
    return video_files


def load_optional_labels_csv(raw_dir: Path, labels_csv: Optional[Path] = None) -> Dict[str, Tuple[str, int]]:
    """
    Muat pemetaan folder/id -> (gloss_label, integer_id) dari `labels.csv` jika tersedia
    (misalnya pada FSL-105: `id,label,category`).
    """
    candidates: List[Path] = []
    if labels_csv is not None:
        candidates.append(Path(labels_csv))
    candidates.append(Path(raw_dir) / "labels.csv")
    candidates.append(Path(raw_dir).parent / "labels.csv")

    for cand in candidates:
        if cand.exists() and cand.is_file():
            mapping: Dict[str, Tuple[str, int]] = {}
            with cand.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    norm_row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
                    raw_id = norm_row.get("id", "")
                    raw_label = (norm_row.get("label") or norm_row.get("gloss") or "").upper()
                    if raw_id and raw_label:
                        if not raw_id.isdigit():
                            raise ValueError(f"ID kelas tidak valid pada {cand}: {raw_id!r}")
                        cls_idx = int(raw_id)
                        mapping[raw_id] = (raw_label, cls_idx)
                        mapping[raw_label] = (raw_label, cls_idx)
            if mapping:
                return mapping
    return {}


def resolve_video_gloss_and_label(
    video_path: Path,
    source: str = "bisindo",
    label_map: Optional[Dict[str, Tuple[str, int]]] = None,
) -> Tuple[str, int]:
    """
    Tentukan (gloss, label_id) dari struktur direktori atau `label_map` tanpa fallback modulo acak,
    serta larang pencampuran dataset BISINDO dan FSL-105.
    """
    src_norm = (source or "bisindo").strip().lower()
    folder_name = video_path.parent.name.strip()
    folder_upper = folder_name.upper()

    if src_norm in WLBISINDO_SOURCE_ALIASES:
        # Tahap A.2.2: WL-BISINDO memakai label space sumber terpisah (label0..label31 dari nama
        # berkas flat), BUKAN BISINDO_32_GLOSSES (concepts.csv). labels.csv asing ditolak.
        if label_map:
            raise ValueError(
                "Pencampuran dataset terdeteksi: source='wl_bisindo' memakai pemetaan resmi "
                "WLBISINDO_LABELS dan tidak boleh memakai labels.csv eksternal (mis. FSL-105)."
            )
        rec = parse_wlbisindo_filename(video_path)
        return rec.source_gloss, rec.source_label_id

    if src_norm == "bisindo":
        if label_map:
            non_bisindo = [g for g, _ in label_map.values() if g not in BISINDO_32_GLOSSES]
            if non_bisindo:
                raise ValueError(
                    f"Pencampuran dataset terdeteksi: source='bisindo' tidak boleh menggunakan labels.csv "
                    f"non-BISINDO (contoh label asing: {non_bisindo[0]!r})."
                )
        if folder_upper in BISINDO_32_GLOSSES:
            return folder_upper, BISINDO_32_GLOSSES.index(folder_upper)
        raise ValueError(
            f"Nama folder kelas '{folder_name}' untuk berkas video '{video_path}' tidak terdaftar dalam "
            f"32 gloss resmi BISINDO (source={source!r})."
        )

    if src_norm in ("fsl", "fsl_105", "fsl-105"):
        if not label_map:
            raise ValueError(
                f"Ekstraksi dataset FSL (source={source!r}) mewajibkan berkas labels.csv resmi FSL-105."
            )
        if folder_name in label_map:
            return label_map[folder_name]
        if folder_upper in label_map:
            return label_map[folder_upper]
        raise ValueError(
            f"Folder kelas '{folder_name}' untuk berkas video '{video_path}' tidak ditemukan di dalam labels.csv FSL-105."
        )

    if label_map:
        if folder_name in label_map:
            return label_map[folder_name]
        if folder_upper in label_map:
            return label_map[folder_upper]
        raise ValueError(
            f"Folder kelas '{folder_name}' untuk berkas video '{video_path}' tidak ditemukan di dalam labels.csv."
        )

    raise ValueError(
        f"Sumber dataset video '{source}' tidak memiliki pemetaan label yang valid untuk '{video_path}'."
    )


def load_official_split_map(raw_dir: Path) -> Dict[str, str]:
    """
    Muat pemetaan split resmi dari `train.csv`, `val.csv`, dan `test.csv` bila tersedia di `raw_dir`
    atau `raw_dir.parent` (seperti pada FSL-105: `vid_path,id_label`).
    Memastikan tidak ada video yang bocor di lebih dari satu split.
    """
    split_files = {
        "train": [Path(raw_dir) / "train.csv", Path(raw_dir).parent / "train.csv"],
        "val": [Path(raw_dir) / "val.csv", Path(raw_dir).parent / "val.csv"],
        "test": [Path(raw_dir) / "test.csv", Path(raw_dir).parent / "test.csv"],
    }
    key_to_split: Dict[str, str] = {}

    for split_name, candidates in split_files.items():
        for cand in candidates:
            if cand.exists() and cand.is_file():
                with cand.open("r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        norm_row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
                        vp = norm_row.get("vid_path") or norm_row.get("path") or norm_row.get("file") or ""
                        if not vp:
                            continue
                        norm_vp = vp.replace("\\", "/").strip("/").lower()
                        parts = norm_vp.split("/")
                        short_key = "/".join(parts[-2:]) if len(parts) >= 2 else norm_vp
                        for k in (norm_vp, short_key):
                            if k in key_to_split and key_to_split[k] != split_name:
                                raise ValueError(
                                    f"Kebocoran split video terdeteksi antara {key_to_split[k]} dan {split_name} "
                                    f"untuk berkas: {vp}"
                                )
                            key_to_split[k] = split_name
                break

    return key_to_split


def extract_signer_id(video_path: Path) -> str:
    """
    Ambil identitas signer dari nama berkas atau folder bila tercantum secara eksplisit
    (mis. `S01_HALO_01.mp4` atau `signer02_...`). Jika dataset tidak mencantumkan identitas
    signer pada nama berkas (seperti FSL-105 `clips/0/0.MOV`), kembalikan `'unannotated'`
    (bukan mengarang signer palsu dengan modulo `idx % 6`).

    Tahap A.2.2: regex lama `\\b(s\\d{1,3}|signer[_-]?\\d{1,3})\\b` gagal pada
    `signer0_label0_sample1.mp4` karena `_` adalah karakter kata sehingga tidak ada `\\b`.
    Kini memakai lookaround eksplisit di `extract_signer_id_from_text()`.
    """
    video_path = Path(video_path)
    if is_wlbisindo_filename(video_path):
        return parse_wlbisindo_filename(video_path).signer_id
    return extract_signer_id_from_text(video_path.stem, video_path.parent.name)


def extract_video_to_86_nodes(video_path: Path) -> np.ndarray:
    """
    Ekstrak [F, 86, 3] float32 dari berkas video fisik menggunakan MediaPipe Holistic.
    Tidak pernah menghasilkan keypoint acak/sintetis apabila berkas atau dependency bermasalah.
    """
    video_path = Path(video_path)
    if not video_path.exists() or not video_path.is_file():
        raise FileNotFoundError(f"Berkas video tidak ditemukan: {video_path}")
    if video_path.stat().st_size == 0:
        raise ValueError(f"Berkas video berukuran 0 byte (rusak/kosong): {video_path}")

    cv2, mp = check_video_dependencies()

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"Gagal membuka berkas video dengan OpenCV (format tidak didukung atau rusak): {video_path}")

    frames_kp: List[np.ndarray] = []
    try:
        with mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as holistic:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = holistic.process(rgb)

                def _lm_to_arr(lms: Any, count: int) -> Optional[np.ndarray]:
                    if lms is None:
                        return None
                    return np.array(
                        [[lm.x, lm.y, lm.z] for lm in lms.landmark[:count]],
                        dtype=np.float32,
                    )

                kp86 = select_from_holistic(
                    _lm_to_arr(res.pose_landmarks, 33),
                    _lm_to_arr(res.left_hand_landmarks, 21),
                    _lm_to_arr(res.right_hand_landmarks, 21),
                    _lm_to_arr(res.face_landmarks, 468),
                )
                frames_kp.append(kp86)
    finally:
        cap.release()

    if not frames_kp:
        raise ValueError(f"Tidak ada frame valid yang dapat diekstrak dari berkas video: {video_path}")

    stacked = np.stack(frames_kp, axis=0).astype(np.float32)
    if stacked.ndim != 3 or stacked.shape[1:] != (NUM_KEYPOINTS, NUM_COORDS):
        raise ValueError(
            f"Dimensi keypoint hasil ekstraksi tidak valid untuk {video_path}: "
            f"diharapkan [F, {NUM_KEYPOINTS}, {NUM_COORDS}], diperoleh {stacked.shape}"
        )
    return stacked


SOURCE_METADATA_COLUMNS: Tuple[str, ...] = (
    "video_id",
    "source",
    "source_path",
    "source_label_id",
    "source_gloss",
    "signer_id",
    "official_split",
    "split_sd",
    "sha256",
    "dup_status",
    "experiment_status",
)


def plan_extraction(
    raw_dir: Path,
    source: str = "bisindo",
    labels_csv: Optional[Path] = None,
    sha256_cache: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Tahap perencanaan murni (tanpa cv2/mediapipe, tanpa menulis ke disk):
    pindai video, tentukan gloss/label sumber, signer, split, SHA-256, dan status duplikasi.

    - WL-BISINDO: label & signer dari nama berkas; split SD deterministik per (signer, label).
    - FSL-105: split resmi dari train.csv/test.csv (tidak diubah); video tanpa split resmi dan
      grup SHA-256 lintas split dikarantina secara eksplisit (`experiment_status`).
    - Grup SHA-256 identik yang melintasi split mana pun selalu dikarantina (CROSS_SPLIT_DUPLICATE).
    """
    raw_dir = Path(raw_dir)
    src_norm = (source or "bisindo").strip().lower()

    # 1. Validasi keberadaan berkas video terlebih dahulu (lempar FileNotFoundError bila kosong)
    video_files = discover_video_files(raw_dir)
    label_map = load_optional_labels_csv(raw_dir, labels_csv=labels_csv) if src_norm not in WLBISINDO_SOURCE_ALIASES else {}

    # 2. Validasi label/gloss dan split untuk seluruh video sebelum mengekstrak
    official_splits = load_official_split_map(raw_dir)
    wl_sd_splits: Dict[str, str] = {}
    if src_norm in WLBISINDO_SOURCE_ALIASES:
        wl_sd_splits = assign_wlbisindo_sd_splits([parse_wlbisindo_filename(v) for v in video_files])

    default_splits = ("train", "train", "train", "val", "test")
    items: List[Dict[str, Any]] = []
    for idx, vf in enumerate(video_files):
        gloss, label = resolve_video_gloss_and_label(vf, source=source, label_map=label_map)
        signer = extract_signer_id(vf)
        short_key = f"{vf.parent.name}/{vf.name}".lower()
        full_key = f"clips/{short_key}"
        official = official_splits.get(full_key) or official_splits.get(short_key) or ""
        if src_norm in WLBISINDO_SOURCE_ALIASES:
            split_sd = wl_sd_splits[vf.name]
        elif src_norm in FSL105_SOURCE_ALIASES:
            split_sd = official  # kosong -> dikarantina, tidak dipilihkan split secara diam-diam
        else:
            split_sd = official or default_splits[idx % len(default_splits)]

        try:
            rel = vf.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            rel = vf.as_posix()
        cache_key = rel.lower()
        if sha256_cache is not None and cache_key in sha256_cache:
            sha = sha256_cache[cache_key]
        else:
            sha = compute_file_sha256(vf)
            if sha256_cache is not None:
                sha256_cache[cache_key] = sha

        items.append(
            {
                "path": vf,
                "source": source,
                "source_path": rel,
                "gloss": gloss,
                "label": int(label),
                "source_label_id": int(label),
                "source_gloss": gloss,
                "signer": signer,
                "signer_id": signer,
                "official_split": official,
                "split_sd": split_sd,
                "sha256": sha,
            }
        )

    classify_sha256_duplicates(items, split_key="split_sd")
    return items


def run_extraction(
    raw_dir: Path,
    out_dir: Path,
    manifest_path: Path,
    source: str = "bisindo",
    labels_csv: Optional[Path] = None,
) -> int:
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    manifest_path = Path(manifest_path)

    # 1-2. Perencanaan (validasi video, label, signer, split, SHA-256, karantina duplikat)
    planned = plan_extraction(raw_dir, source=source, labels_csv=labels_csv)
    resolved_items = [it for it in planned if it["experiment_status"] == EXP_INCLUDED]

    # 3. Pastikan dependency cv2 & mediapipe tersedia sebelum menulis ke disk
    check_video_dependencies()

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    meta_rows: List[Dict[str, Any]] = []

    for idx, it in enumerate(resolved_items):
        vf, gloss, label, signer, split_sd = it["path"], it["gloss"], it["label"], it["signer"], it["split_sd"]
        vid_id = f"{source}_{vf.parent.name}_{vf.stem}_{idx:04d}"

        kp = extract_video_to_86_nodes(vf)
        kp_file = out_dir / f"{vid_id}.npz"
        np.savez_compressed(kp_file, keypoints=kp, gloss=gloss, label=label, signer=signer)

        rows.append(
            {
                "video_id": vid_id,
                "source": source,
                "gloss": gloss,
                "label": label,
                "signer": signer,
                "kp_path": str(kp_file.as_posix()),
                "rgb_path": "",
                "split_sd": split_sd,
            }
        )
        meta_rows.append({**{k: it.get(k, "") for k in SOURCE_METADATA_COLUMNS}, "video_id": vid_id})

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(MANIFEST_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    # Sidecar metadata sumber (kontrak manifest lama MANIFEST_COLUMNS tidak diubah)
    meta_path = manifest_path.with_name(f"{manifest_path.stem}_source_metadata.csv")
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(SOURCE_METADATA_COLUMNS))
        writer.writeheader()
        writer.writerows(meta_rows)

    # Laporan duplikat SHA-256 (termasuk baris yang dikarantina)
    dup_rows = [
        {**it, "rel_path": it["source_path"], "official_split": it["official_split"] or it["split_sd"]}
        for it in planned
    ]
    write_duplicate_report(dup_rows, manifest_path.with_name(f"{manifest_path.stem}_sha256_duplicates.csv"))

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ekstraksi keypoint 86 titik MediaPipe Holistic.")
    parser.add_argument("--raw", type=str, default="data/raw/bisindo", help="Folder video mentah")
    parser.add_argument("--out", type=str, default="data/keypoints/bisindo", help="Folder luaran .npz")
    parser.add_argument("--manifest", type=str, default="data/manifest.csv", help="Jalur manifest CSV")
    parser.add_argument("--source", type=str, default="bisindo", help="Nama sumber dataset")
    parser.add_argument("--labels-csv", type=str, default=None, help="Jalur opsional ke labels.csv (mis. FSL-105)")
    parser.add_argument("--workers", type=int, default=4, help="Jumlah worker paralel")
    args = parser.parse_args()

    count = run_extraction(
        raw_dir=Path(args.raw),
        out_dir=Path(args.out),
        manifest_path=Path(args.manifest),
        source=args.source,
        labels_csv=Path(args.labels_csv) if args.labels_csv else None,
    )
    print(f"[extract_keypoints] Selesai memproses {count} entri -> {args.manifest}")


if __name__ == "__main__":
    main()


