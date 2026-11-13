"""
scripts/crop_hands.py — Modul 03 Langkah 11 (PDF Hal. 19):
Potong kotak tangan persegi (+25% margin) dan ubah ukuran ke 224x224 dari citra RGB mentah A-Z.

Keamanan Pipeline (Tahap A):
- Wajib membaca citra RGB asli dari `in_dir` (mis. `data/raw/image/bisindo_alphabet/<A..Z>/`).
- Seluruh pembuatan citra acak (`rng.integers`) dan landmark acak (`rng.uniform`) telah dihapus.
- Tidak pernah mengubah atau menimpa berkas citra sumber.
- Melempar FileNotFoundError / ValueError yang jelas bila direktori input kosong atau citra rusak.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE
from signbridge.image.crop import _bilinear_resize_rgb, crop_and_resize_hand

SUPPORTED_IMAGE_EXTENSIONS: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
MIN_HAND_LANDMARKS: int = 21


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_array_sha256(arr: np.ndarray) -> str:
    contig = np.ascontiguousarray(arr)
    h = hashlib.sha256()
    h.update(str(contig.shape).encode("utf-8"))
    h.update(str(contig.dtype).encode("utf-8"))
    h.update(contig.tobytes())
    return h.hexdigest()


def validate_hand_landmarks(landmarks: Any) -> np.ndarray:
    """
    Validasi ketat landmark tangan sebelum dikirim ke `crop_and_resize_hand()`.
    Menolak `None`, array kosong `(0, 3)`, jumlah titik `< 21`, koordinat `NaN`/`Inf`,
    atau bounding box degenerat (span == 0) agar kegagalan deteksi tidak pernah menghasilkan crop palsu.
    """
    if landmarks is None:
        raise ValueError("Landmark tangan bernilai None; menolak menghasilkan crop palsu.")
    pts = np.asarray(landmarks, dtype=np.float32)
    if pts.ndim != 2 or pts.shape[1] not in (2, 3):
        raise ValueError(
            f"Dimensi landmark tangan tidak valid: diharapkan [N, 2] atau [N, 3], diperoleh {pts.shape}."
        )
    if pts.shape[0] < MIN_HAND_LANDMARKS:
        raise ValueError(
            f"Jumlah titik landmark tangan kurang dari {MIN_HAND_LANDMARKS} (diperoleh {pts.shape[0]}); "
            "deteksi tangan tidak lengkap."
        )
    if not np.all(np.isfinite(pts[:, :2])):
        raise ValueError("Landmark tangan mengandung nilai NaN atau Inf yang tidak valid.")

    span_x = float(np.max(pts[:, 0]) - np.min(pts[:, 0]))
    span_y = float(np.max(pts[:, 1]) - np.min(pts[:, 1]))
    if max(span_x, span_y) <= 1e-5:
        raise ValueError("Landmark tangan degenerat (seluruh titik berada pada satu koordinat yang sama).")

    return pts


def load_rgb_image(img_path: Path) -> np.ndarray:
    """
    Baca berkas citra fisik dari `img_path` dan kembalikan array RGB uint8 [H, W, 3].
    Melempar FileNotFoundError bila berkas tidak ada, dan ValueError bila berkas 0-byte atau rusak.
    """
    img_path = Path(img_path)
    if not img_path.exists() or not img_path.is_file():
        raise FileNotFoundError(f"Berkas citra tidak ditemukan: {img_path}")
    if img_path.stat().st_size == 0:
        raise ValueError(f"Berkas citra berukuran 0 byte (rusak/kosong): {img_path}")

    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError(
            "Dependency 'Pillow' (PIL) belum terpasang untuk membaca citra RGB. "
            "Silakan instal dengan: pip install Pillow"
        ) from exc

    try:
        with Image.open(img_path) as im_verify:
            im_verify.verify()
        with Image.open(img_path) as im_load:
            rgb_im = im_load.convert("RGB")
            arr = np.asarray(rgb_im, dtype=np.uint8)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise ValueError(f"Berkas citra rusak atau gagal didekode sebagai RGB: {img_path} ({exc})") from exc

    if arr.ndim != 3 or arr.shape[2] != 3 or arr.shape[0] <= 0 or arr.shape[1] <= 0:
        raise ValueError(f"Dimensi citra RGB tidak valid untuk {img_path}: diperoleh {arr.shape}")

    return arr.copy()


def discover_alphabet_images(
    in_dir: Path,
    require_all_classes: bool = False,
) -> Dict[str, List[Path]]:
    """
    Pindai direktori `in_dir` untuk subdirektori kelas A–Z (`FINGERSPELL_26_LABELS`)
    dan kumpulkan berkas gambar asli per kelas.
    Mengabaikan berkas metadata tersembunyi macOS (`._*`).
    """
    in_dir = Path(in_dir)
    if not in_dir.exists():
        raise FileNotFoundError(f"Direktori sumber citra tidak ditemukan: {in_dir}")
    if not in_dir.is_dir():
        raise NotADirectoryError(f"Jalur sumber citra bukan sebuah direktori: {in_dir}")

    class_to_files: Dict[str, List[Path]] = {letter: [] for letter in FINGERSPELL_26_LABELS}
    missing_dirs: List[str] = []
    empty_classes: List[str] = []

    for letter in FINGERSPELL_26_LABELS:
        letter_dir = in_dir / letter
        if not letter_dir.exists() or not letter_dir.is_dir():
            missing_dirs.append(letter)
            continue

        files = sorted(
            p
            for p in letter_dir.iterdir()
            if p.is_file()
            and not p.name.startswith("._")
            and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        )
        if not files:
            empty_classes.append(letter)
        class_to_files[letter] = files

    total_found = sum(len(v) for v in class_to_files.values())
    if total_found == 0:
        raise FileNotFoundError(
            f"Tidak ditemukan berkas citra RGB ({', '.join(SUPPORTED_IMAGE_EXTENSIONS)}) "
            f"pada subdirektori kelas A-Z di dalam: {in_dir}"
        )

    if require_all_classes and (missing_dirs or empty_classes):
        problems = []
        if missing_dirs:
            problems.append(f"folder tidak ada: {missing_dirs}")
        if empty_classes:
            problems.append(f"folder kosong: {empty_classes}")
        raise ValueError(
            f"Distribusi kelas A-Z tidak lengkap di {in_dir} ({'; '.join(problems)})."
        )

    return class_to_files


def detect_hand_landmarks_strict(img_rgb: np.ndarray) -> np.ndarray:
    """
    Deteksi 21 titik tangan dari `img_rgb` menggunakan MediaPipe Hands secara ketat.
    - Jika modul `mediapipe` belum terpasang, lempar RuntimeError.
    - Jika tangan tidak terdeteksi pada citra, lempar ValueError (tidak pernah mengembalikan
      landmark kosong atau crop palsu).
    """
    if importlib.util.find_spec("mediapipe") is None:
        raise RuntimeError(
            "Dependency 'mediapipe' belum terpasang untuk mode crop berbasis landmark. "
            "Instal dengan: pip install mediapipe"
        )
    import mediapipe as mp  # type: ignore[import-not-found]

    with mp.solutions.hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.5,
    ) as hands:
        res = hands.process(img_rgb)
        if not res.multi_hand_landmarks:
            raise ValueError("MediaPipe Hands gagal mendeteksi tangan pada citra; menolak membuat crop palsu.")
        pts = [
            [float(lm.x), float(lm.y), float(lm.z)]
            for hand_lms in res.multi_hand_landmarks
            for lm in hand_lms.landmark
        ]
    return validate_hand_landmarks(pts)


def prepare_precentered_hand_image(
    img_rgb: np.ndarray,
    out_size: int = IMAGE_SIZE,
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Pendekatan eksplisit untuk dataset citra yang sudah terpusat dari sumbernya
    (seperti Mendeley BISINDO Alphabet v1 yang seluruh 4.466 citranya sudah berukuran 224x224x3 RGB).
    Tidak mengirimkan landmark dummy/kosong ke `crop_and_resize_hand()`, melainkan memotong
    kotak persegi tengah maksimal secara eksplisit dan mengubah ukuran ke [out_size, out_size, 3].
    """
    if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        raise ValueError(f"Citra input harus berdimensi [H, W, 3], diperoleh {img_rgb.shape}")
    h, w = int(img_rgb.shape[0]), int(img_rgb.shape[1])
    if h <= 0 or w <= 0:
        raise ValueError(f"Ukuran citra tidak valid: {img_rgb.shape}")

    side = min(h, w)
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    square_patch = img_rgb[y0 : y0 + side, x0 : x0 + side]
    resized = _bilinear_resize_rgb(square_patch, out_h=out_size, out_w=out_size)
    box = {"x0": int(x0), "y0": int(y0), "x1": int(x0 + side), "y1": int(y0 + side), "size": int(side)}
    return resized, box


def verify_image_manifest_no_leakage(manifest_path: Path) -> Dict[str, int]:
    """
    Periksa bahwa manifest citra tidak memiliki kebocoran gambar duplikat (berdasarkan `sha256`,
    `source_path`, maupun `path`) di antara split `train`, `val`, dan `test`.
    Lempar ValueError jika ditemukan gambar yang sama pada lebih dari satu split.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists() or not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest citra tidak ditemukan: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(f"Manifest citra kosong: {manifest_path}")

    split_to_hashes: Dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    split_to_sources: Dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    counts: Dict[str, int] = {"train": 0, "val": 0, "test": 0}

    for row in rows:
        sp = (row.get("split") or "").strip().lower()
        if sp not in split_to_hashes:
            raise ValueError(f"Nama split tidak dikenal pada manifest {manifest_path}: {sp!r}")
        counts[sp] += 1

        src_p = (row.get("source_path") or row.get("src_path") or row.get("path") or "").strip()
        if src_p:
            split_to_sources[sp].add(src_p)

        sha = (row.get("sha256") or row.get("src_sha256") or row.get("crop_sha256") or "").strip().lower()
        if not sha:
            p = Path((row.get("path") or "").strip())
            if p.exists() and p.is_file():
                sha = compute_array_sha256(np.load(str(p))) if p.suffix.lower() == ".npy" else compute_file_sha256(p)
        if sha:
            split_to_hashes[sp].add(sha)

    for s1, s2 in (("train", "val"), ("train", "test"), ("val", "test")):
        dup_src = split_to_sources[s1].intersection(split_to_sources[s2])
        if dup_src:
            raise ValueError(
                f"Kebocoran path gambar duplikat antar-split ({s1} vs {s2}) pada {manifest_path}: "
                f"{sorted(dup_src)[0]}"
            )
        dup_sha = split_to_hashes[s1].intersection(split_to_hashes[s2])
        if dup_sha:
            raise ValueError(
                f"Kebocoran konten gambar duplikat (SHA-256 identik) antar-split ({s1} vs {s2}) "
                f"pada {manifest_path}: sha256={sorted(dup_sha)[0]}"
            )

    return counts


def run_crop_hands(
    in_dir: Path,
    out_dir: Path,
    manifest_path: Path,
    require_all_classes: bool = False,
    max_per_class: Optional[int] = None,
    use_mediapipe: bool = False,
    deduplicate_sha256: bool = True,
) -> int:
    """
    Baca citra RGB asli dari `in_dir/<A..Z>/`, lakukan crop/persiapan 224x224,
    dan simpan ke `out_dir/<A..Z>/*.npy` beserta `manifest_path` tanpa mengubah berkas sumber.
    - Menolak duplikat SHA-256 lintas kelas/split agar tidak pernah bocor antara train/val/test.
    - Menetapkan split secara deterministik berbasis blok grup urut (60% train, 20% val, 20% test)
      agar foto berurutan dari sesi yang sama tidak saling bocor, sambil menjamin ketiga split
      terisi bila jumlah sampel memadai.
    """
    in_dir = Path(in_dir)
    out_dir = Path(out_dir)
    manifest_path = Path(manifest_path)

    if in_dir.exists() and out_dir.exists() and in_dir.resolve() == out_dir.resolve():
        raise ValueError(
            f"Direktori output ({out_dir}) tidak boleh sama dengan direktori sumber ({in_dir}) "
            "agar berkas asli tidak tertimpa."
        )

    class_to_files = discover_alphabet_images(in_dir, require_all_classes=require_all_classes)

    # Pra-pindai SHA-256 untuk mendeteksi gambar identik lintas kelas (seperti 2 pasang duplikat di Mendeley)
    sha_to_classes: Dict[str, set[str]] = {}
    file_to_sha: Dict[Path, str] = {}
    for letter, files in class_to_files.items():
        selected_files = files[: int(max_per_class)] if max_per_class is not None else files
        for src_path in selected_files:
            sha = compute_file_sha256(src_path)
            file_to_sha[src_path] = sha
            sha_to_classes.setdefault(sha, set()).add(letter)

    ambiguous_cross_class_shas = {sha for sha, cls_set in sha_to_classes.items() if len(cls_set) > 1}
    seen_shas_global: set[str] = set()

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []

    for label_idx, letter in enumerate(FINGERSPELL_26_LABELS):
        files = class_to_files.get(letter, [])
        if max_per_class is not None:
            files = files[: int(max_per_class)]
        if not files:
            continue

        # Saring duplikat SHA-256 lintas kelas atau dalam kelas bila deduplicate_sha256=True
        clean_files: List[Path] = []
        for src_path in files:
            sha = file_to_sha[src_path]
            if deduplicate_sha256 and (sha in ambiguous_cross_class_shas or sha in seen_shas_global):
                continue
            seen_shas_global.add(sha)
            clean_files.append(src_path)

        if not clean_files:
            continue

        letter_out_dir = out_dir / letter
        letter_out_dir.mkdir(parents=True, exist_ok=True)
        n_cls = len(clean_files)

        for sample_i, src_path in enumerate(clean_files):
            real_img = load_rgb_image(src_path)
            if use_mediapipe:
                hand_lm = detect_hand_landmarks_strict(real_img)
                cropped, box = crop_and_resize_hand(
                    real_img,
                    hand_lm,
                    out_size=IMAGE_SIZE,
                    margin=0.25,
                )
                crop_mode = "mediapipe_landmarks"
            else:
                cropped, box = prepare_precentered_hand_image(real_img, out_size=IMAGE_SIZE)
                crop_mode = "precentered_square"

            # Pembagian split berbasis blok kontigu per kelas (60% train, 20% val, 20% test)
            # untuk mencegah frame berurutan dalam satu burst kamera bocor antar-split
            if n_cls == 1:
                split = "train"
            elif n_cls == 2:
                split = "train" if sample_i == 0 else "test"
            elif n_cls < 5:
                split = ("train", "val", "test")[min(2, sample_i)]
            else:
                train_cut = max(1, int(round(n_cls * 0.60)))
                val_cut = max(train_cut + 1, int(round(n_cls * 0.80)))
                if sample_i < train_cut:
                    split = "train"
                elif sample_i < val_cut:
                    split = "val"
                else:
                    split = "test"

            image_id = f"{letter}_{sample_i:04d}_{src_path.stem}"
            npy_path = letter_out_dir / f"{letter}_{sample_i:04d}.npy"
            np.save(npy_path, cropped)

            rows.append(
                {
                    "image_id": image_id,
                    "letter": letter,
                    "label": label_idx,
                    "path": str(npy_path.as_posix()),
                    "source_path": str(src_path.as_posix()),
                    "sha256": file_to_sha[src_path],
                    "crop_mode": crop_mode,
                    "split": split,
                    "box_size": box["size"],
                }
            )

    if not rows:
        raise ValueError(f"Tidak ada citra valid yang berhasil diproses dari direktori: {in_dir}")

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_id",
                "letter",
                "label",
                "path",
                "source_path",
                "sha256",
                "crop_mode",
                "split",
                "box_size",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    verify_image_manifest_no_leakage(manifest_path)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop tangan 224x224 (+25% margin) untuk A-Z fingerspelling.")
    parser.add_argument("--in", dest="in_dir", type=str, default="data/raw/image/bisindo_alphabet")
    parser.add_argument("--out", type=str, default="data/images/mendeley_crops")
    parser.add_argument("--manifest", type=str, default="data/images/manifest_images_mendeley.csv")
    parser.add_argument("--require-all-classes", action="store_true", help="Wajibkan seluruh 26 kelas A-Z tersedia")
    parser.add_argument("--max-per-class", type=int, default=None, help="Batas opsional jumlah gambar per kelas")
    args = parser.parse_args()

    n = run_crop_hands(
        in_dir=Path(args.in_dir),
        out_dir=Path(args.out),
        manifest_path=Path(args.manifest),
        require_all_classes=args.require_all_classes,
        max_per_class=args.max_per_class,
    )
    print(f"[crop_hands] {n} citra tangan 224x224 ditulis ke {args.manifest}")


if __name__ == "__main__":
    main()


