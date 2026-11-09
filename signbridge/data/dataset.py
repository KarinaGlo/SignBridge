"""
dataset.py — SignDataset for pose keypoints (.npz/.npy), VideoMAE RGB tokens (.npy),
and phonological multitask annotations (phonology.csv).

Supports:
  - Signer-Dependent (SD) split via `split_sd` column (60/10/30)
  - Signer-Independent (SI / LOSO) split via `--protocol si --test-signer <signer>`
  - Per-(epoch, worker, sample) deterministic RNG seed for training augmentation
  - Phonology label encoding with -1 ignore index when unannotated
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    import torch
    from torch.utils.data import Dataset, get_worker_info

    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - lightweight runtime without PyTorch
    torch = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False

    class Dataset:  # type: ignore[no-redef]
        pass

    def get_worker_info() -> Any:  # type: ignore[misc]
        return None

from signbridge.constants import (
    BISINDO_32_GLOSSES,
    NUM_KEYPOINTS,
    NUM_COORDS,
    PHONOLOGY_COLUMNS,
    RGB_NUM_TOKENS,
    RGB_TOKEN_DIM,
    T_MAX,
    L_SHOULDER_IDX,
    R_SHOULDER_IDX,
    LEFT_HAND_START,
    RIGHT_HAND_END,
)
from signbridge.augment import augment_keypoints
from signbridge.features import preprocess_keypoints


def load_phonology_map(
    phonology_csv: str | Path | None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, int]]:
    """
    Load phonology.csv and map each gloss to integer class indices per phonological attribute.

    Returns
    -------
    gloss_to_phono : dict mapping gloss -> np.ndarray [6] int64 (-1 if missing)
    attr_num_classes : dict mapping attribute name -> number of unique classes
    """
    if phonology_csv is None or not Path(phonology_csv).exists():
        return {}, {col: 4 for col in PHONOLOGY_COLUMNS}

    path = Path(phonology_csv)
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("gloss"):
                rows.append(row)

    # Alias fallback agar kompatibel dengan header 4-kolom di data/phonology.csv
    # (`handshape`, `location`, `movement`, `two_handed`) maupun 6-kolom PHONOLOGY_COLUMNS.
    col_aliases: Dict[str, Tuple[str, ...]] = {
        "handshape_dom": ("handshape_dom", "handshape"),
        "handshape_nondom": ("handshape_nondom",),
        "location": ("location",),
        "movement": ("movement",),
        "orientation": ("orientation",),
        "handedness": ("handedness", "two_handed"),
    }

    def _get_col_val(row_dict: Dict[str, str], canonical_col: str) -> str:
        for candidate in col_aliases.get(canonical_col, (canonical_col,)):
            v = (row_dict.get(candidate) or "").strip()
            if v:
                return v
        return ""

    vocab: Dict[str, Dict[str, int]] = {col: {} for col in PHONOLOGY_COLUMNS}
    for row in rows:
        for col in PHONOLOGY_COLUMNS:
            val = _get_col_val(row, col)
            if val and val != "-1" and val.lower() != "none":
                if val not in vocab[col]:
                    vocab[col][val] = len(vocab[col])

    attr_num_classes = {col: max(2, len(vocab[col])) for col in PHONOLOGY_COLUMNS}
    gloss_to_phono: Dict[str, np.ndarray] = {}
    for row in rows:
        gloss = row["gloss"].strip()
        vec = np.full(len(PHONOLOGY_COLUMNS), -1, dtype=np.int64)
        for i, col in enumerate(PHONOLOGY_COLUMNS):
            val = _get_col_val(row, col)
            if val in vocab[col]:
                vec[i] = vocab[col][val]
        gloss_to_phono[gloss] = vec

    return gloss_to_phono, attr_num_classes


class SignDataset(Dataset):
    """
    Multimodal Sign Language Dataset for Pose Keypoints + VideoMAE RGB tokens + Phonology.

    Each item returns a dictionary:
      - "pose":      FloatTensor [64, 86, 3]
      - "mask":      BoolTensor  [64, 86]
      - "frame_mask":BoolTensor  [64]
      - "rgb":       FloatTensor [8, 768]
      - "label":     LongTensor  scalar
      - "phonology": LongTensor  [6] (-1 = ignore)
      - "signer":    str
      - "gloss":     str
      - "video_id":  str
    """

    def __init__(
        self,
        manifest_path: str | Path,
        data_root: str | Path = ".",
        split: str = "train",
        protocol: str = "sd",
        test_signer: str = "s3",
        source_filter: Optional[Sequence[str]] = None,
        phonology_csv: Optional[str | Path] = None,
        augment_cfg: Optional[Dict[str, Any]] = None,
        target_len: int = T_MAX,
        base_seed: int = 42,
        allow_mixed_sources: bool = False,
        allow_partial_class_coverage: bool = False,
    ) -> None:
        super().__init__()
        self.manifest_path = Path(manifest_path)
        self.data_root = Path(data_root)
        self.split = split.lower()
        self.protocol = protocol.lower()
        self.test_signer = str(test_signer)
        self.target_len = target_len
        self.base_seed = int(base_seed)
        self.allow_mixed_sources = bool(allow_mixed_sources)
        # Tahap A.2.2: protokol SI menolak split val/test yang tidak mencakup seluruh kelas
        # (mis. WL-BISINDO signer0 hanya label0..11) kecuali diizinkan eksplisit.
        self.allow_partial_class_coverage = bool(allow_partial_class_coverage)
        self.si_coverage_report: Dict[str, List[str]] = {}
        self.epoch: int = 0
        self.augment_cfg = augment_cfg or {}

        self.gloss_to_phono, self.phono_num_classes = load_phonology_map(phonology_csv)

        all_rows = self._read_manifest(
            self.manifest_path,
            source_filter=source_filter,
            allow_mixed_sources=self.allow_mixed_sources,
        )
        self.samples, self.classes, self.class_to_idx = self._filter_split(all_rows)

    def set_epoch(self, epoch: int) -> None:
        """Update epoch so each epoch gets a fresh deterministic augmentation stream."""
        self.epoch = int(epoch)

    @staticmethod
    def _read_manifest(
        manifest_path: Path,
        source_filter: Optional[Sequence[str]] = None,
        allow_mixed_sources: bool = False,
    ) -> List[Dict[str, str]]:
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        rows: List[Dict[str, str]] = []
        allowed_sources = {s.lower() for s in source_filter} if source_filter else None
        sources_seen: set[str] = set()
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = (row.get("source") or "bisindo").strip().lower()
                if allowed_sources and src not in allowed_sources:
                    continue
                sources_seen.add(src)
                rows.append(row)

        if not rows:
            raise ValueError(
                f"Manifest '{manifest_path}' tidak memiliki baris data untuk source_filter={source_filter!r}."
            )

        if len(sources_seen) > 1 and not allow_mixed_sources:
            raise ValueError(
                f"Pencampuran dataset lintas bahasa isyarat terdeteksi di manifest '{manifest_path}': "
                f"sources={sorted(sources_seen)}. BISINDO dan FSL-105 wajib dipisahkan (gunakan "
                f"source_filter eksplisit atau manifest terpisah)."
            )
        return rows

    def _filter_split(
        self, rows: List[Dict[str, str]]
    ) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int]]:
        # Build deterministic class list sorted by label id if present, else alphabetically
        gloss_set = sorted({(r.get("gloss") or "").strip() for r in rows if (r.get("gloss") or "").strip()})
        if not gloss_set:
            raise ValueError(f"Manifest '{self.manifest_path}' tidak memiliki kolom gloss yang valid.")
        class_to_idx: Dict[str, int] = {g: i for i, g in enumerate(gloss_set)}

        # Check if explicit integer labels are consistent
        explicit_map: Dict[str, int] = {}
        for line_idx, r in enumerate(rows, start=2):
            g = (r.get("gloss") or "").strip()
            lbl_str = (r.get("label") or "").strip()
            if not g:
                raise ValueError(f"Baris {line_idx} pada '{self.manifest_path}' memiliki gloss kosong.")
            if lbl_str:
                try:
                    lbl_val = int(lbl_str)
                except ValueError as exc:
                    raise ValueError(
                        f"Baris {line_idx} pada '{self.manifest_path}' memiliki label non-integer: {lbl_str!r}"
                    ) from exc
                if lbl_val < 0:
                    raise ValueError(
                        f"Baris {line_idx} pada '{self.manifest_path}' memiliki label negatif: {lbl_val}"
                    )
                if g in explicit_map and explicit_map[g] != lbl_val:
                    raise ValueError(
                        f"Inkonsistensi label untuk gloss '{g}' pada '{self.manifest_path}': "
                        f"{explicit_map[g]} vs {lbl_val}"
                    )
                explicit_map[g] = lbl_val

        if len(explicit_map) == len(gloss_set):
            class_to_idx = explicit_map
            gloss_set = [g for g, _ in sorted(explicit_map.items(), key=lambda kv: kv[1])]

        # Guard anti-kebocoran: video_id dan kp_path tidak boleh bocor lintas split
        vid_to_split: Dict[str, str] = {}
        kp_to_split: Dict[str, str] = {}

        selected: List[Dict[str, Any]] = []
        if self.protocol == "si":
            # Leave-one-signer-out (Signer-Independent) protocol
            raw_signers = [(r.get("signer") or r.get("signer_id") or "").strip() for r in rows]
            if any(not s or s.lower() in {"unannotated", "unknown", "none"} for s in raw_signers):
                raise ValueError(
                    f"Protokol Signer-Independent (si) pada '{self.manifest_path}' membutuhkan "
                    "anotasi signer_id yang valid (ditemukan signer kosong atau 'unannotated')."
                )
            all_signers = sorted(set(raw_signers))
            if self.test_signer not in all_signers:
                raise ValueError(
                    f"test_signer='{self.test_signer}' tidak ditemukan pada daftar signer "
                    f"manifest '{self.manifest_path}': {all_signers}"
                )
            non_test = [s for s in all_signers if s != self.test_signer]
            if not non_test:
                raise ValueError(
                    f"Protokol Signer-Independent (si) membutuhkan minimal 2 signer berbeda, "
                    f"tetapi hanya ditemukan {all_signers}."
                )
            val_signer = non_test[-1] if len(non_test) > 1 else None
            split_glosses: Dict[str, set] = {"train": set(), "val": set(), "test": set()}

            for idx, r in enumerate(rows):
                signer = (r.get("signer") or r.get("signer_id") or "").strip()
                if signer == self.test_signer:
                    row_split = "test"
                elif val_signer is not None and signer == val_signer:
                    row_split = "val"
                elif val_signer is None and idx % 7 == 0:
                    row_split = "val"
                else:
                    row_split = "train"
                split_glosses[row_split].add((r.get("gloss") or "").strip())

                vid_id = (r.get("video_id") or r.get("id") or "").strip()
                kp_rel = (r.get("kp_path") or r.get("keypoint_path") or "").strip()
                if vid_id:
                    prev = vid_to_split.get(vid_id)
                    if prev is not None and prev != row_split:
                        raise ValueError(
                            f"Kebocoran video_id '{vid_id}' lintas split ({prev} vs {row_split}) "
                            f"pada '{self.manifest_path}'."
                        )
                    vid_to_split[vid_id] = row_split
                if kp_rel:
                    prev_kp = kp_to_split.get(kp_rel)
                    if prev_kp is not None and prev_kp != row_split:
                        raise ValueError(
                            f"Kebocoran kp_path '{kp_rel}' lintas split ({prev_kp} vs {row_split}) "
                            f"pada '{self.manifest_path}'."
                        )
                    kp_to_split[kp_rel] = row_split

                if row_split == self.split:
                    selected.append(r)

            all_glosses = set(gloss_set)
            self.si_coverage_report = {
                sp: sorted(all_glosses - gl) for sp, gl in split_glosses.items() if gl
            }
            incomplete = {sp: miss for sp, miss in self.si_coverage_report.items() if miss}
            if incomplete and not self.allow_partial_class_coverage:
                raise ValueError(
                    f"Protokol Signer-Independent (si) dengan test_signer='{self.test_signer}' tidak valid: "
                    f"cakupan kelas tidak lengkap pada split {sorted(incomplete)} "
                    f"(gloss hilang: { {k: v[:5] for k, v in incomplete.items()} }). "
                    "Pilih test/val signer yang mencakup seluruh kelas atau set "
                    "allow_partial_class_coverage=True secara eksplisit (hasil tidak boleh diklaim SI penuh)."
                )
        else:
            # Signer-Dependent (SD) protocol
            for r in rows:
                row_split = (r.get("split_sd") or r.get("split") or "train").strip().lower()
                vid_id = (r.get("video_id") or r.get("id") or "").strip()
                kp_rel = (r.get("kp_path") or r.get("keypoint_path") or "").strip()
                if vid_id:
                    prev = vid_to_split.get(vid_id)
                    if prev is not None and prev != row_split:
                        raise ValueError(
                            f"Kebocoran video_id '{vid_id}' lintas split ({prev} vs {row_split}) "
                            f"pada '{self.manifest_path}'."
                        )
                    vid_to_split[vid_id] = row_split
                if kp_rel:
                    prev_kp = kp_to_split.get(kp_rel)
                    if prev_kp is not None and prev_kp != row_split:
                        raise ValueError(
                            f"Kebocoran kp_path '{kp_rel}' lintas split ({prev_kp} vs {row_split}) "
                            f"pada '{self.manifest_path}'."
                        )
                    kp_to_split[kp_rel] = row_split

                if row_split == self.split:
                    selected.append(r)

        if not selected:
            raise ValueError(
                f"Split '{self.split}' (protocol='{self.protocol}') tidak memiliki sampel (0 baris) "
                f"pada manifest '{self.manifest_path}'. Pipeline menolak menyalin ulang split lain."
            )

        processed: List[Dict[str, Any]] = []
        for r in selected:
            gloss = (r.get("gloss") or "").strip()
            if gloss not in class_to_idx:
                raise ValueError(f"Gloss '{gloss}' tidak terdaftar pada peta kelas manifest.")
            label = class_to_idx[gloss]
            kp_rel = (r.get("kp_path") or r.get("keypoint_path") or "").strip()
            if not kp_rel:
                raise ValueError(
                    f"Baris video_id={r.get('video_id')!r} pada '{self.manifest_path}' tidak memiliki kp_path."
                )
            rgb_rel = (r.get("rgb_path") or "").strip()
            processed.append(
                {
                    "video_id": (r.get("video_id") or r.get("id") or f"vid_{len(processed)}").strip(),
                    "source": (r.get("source") or "bisindo").strip().lower(),
                    "gloss": gloss,
                    "label": int(label),
                    "signer": (r.get("signer") or r.get("signer_id") or "unannotated").strip(),
                    "kp_path": kp_rel,
                    "rgb_path": rgb_rel,
                }
            )

        return processed, gloss_set, class_to_idx

    def __len__(self) -> int:
        return len(self.samples)

    def _resolve_path(self, rel_path: str) -> Path:
        p = Path(rel_path)
        if p.is_absolute() and p.exists():
            return p
        cand1 = self.data_root / p
        if cand1.exists():
            return cand1
        cand2 = self.manifest_path.parent / p
        if cand2.exists():
            return cand2
        cand3 = self.manifest_path.parent.parent / p
        return cand3

    def _load_kp(self, rel_path: str, label: int, idx: int) -> np.ndarray:
        if not rel_path:
            raise ValueError(f"Kolom kp_path kosong pada baris index={idx}")
        full_path = self._resolve_path(rel_path)
        if not full_path.exists():
            raise FileNotFoundError(
                f"Berkas keypoint fisik tidak ditemukan: {full_path} (rel_path={rel_path!r}). "
                "Synthetic keypoint fallback telah dinonaktifkan (Tahap A/A.1)."
            )
        if full_path.suffix == ".npz":
            with np.load(str(full_path)) as data:
                arr = data["kp"] if "kp" in data else data[list(data.keys())[0]]
                kp = arr.astype(np.float32)
        elif full_path.suffix == ".npy":
            kp = np.load(str(full_path)).astype(np.float32)
        else:
            raise ValueError(f"Format ekstensi keypoint tidak didukung ({full_path.suffix}): {full_path}")

        if kp.ndim != 3 or kp.shape[1:] != (NUM_KEYPOINTS, NUM_COORDS) or kp.shape[0] == 0:
            raise ValueError(
                f"Dimensi array keypoint tidak valid pada '{full_path}': "
                f"diharapkan [F>=1, {NUM_KEYPOINTS}, {NUM_COORDS}], diperoleh {kp.shape}"
            )
        if not np.any(np.isfinite(kp)):
            raise ValueError(f"Berkas keypoint '{full_path}' hanya berisi NaN/Inf (0 koordinat valid).")
        return kp

    def _load_rgb(self, rel_path: str, label: int, idx: int) -> np.ndarray:
        if rel_path:
            full_path = self._resolve_path(rel_path)
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Berkas fitur RGB fisik tidak ditemukan: {full_path} (rel_path={rel_path!r}). "
                    "Synthetic RGB token fallback telah dinonaktifkan (Tahap A/A.1)."
                )
            arr = np.load(str(full_path)).astype(np.float32)
            if arr.shape != (RGB_NUM_TOKENS, RGB_TOKEN_DIM):
                raise ValueError(
                    f"Dimensi fitur RGB tidak valid pada '{full_path}': "
                    f"diharapkan {(RGB_NUM_TOKENS, RGB_TOKEN_DIM)}, diperoleh {arr.shape}"
                )
            if not np.all(np.isfinite(arr)):
                raise ValueError(f"Berkas fitur RGB '{full_path}' mengandung nilai NaN/Inf.")
            return arr
        # Bila rgb_path kosong (model berbasis pose murni), kembalikan matriks nol netral
        # tanpa sinyal kelas sintetis (zero label leakage).
        return np.zeros((RGB_NUM_TOKENS, RGB_TOKEN_DIM), dtype=np.float32)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.samples[idx]
        raw_kp = self._load_kp(item["kp_path"], item["label"], idx)

        # Apply augmentation only on train split with unique (epoch, worker, idx) seed
        if self.split == "train" and self.augment_cfg.get("enabled", True):
            worker_info = get_worker_info()
            worker_id = worker_info.id if worker_info is not None else 0
            seed = (
                self.base_seed
                + self.epoch * 1_000_003
                + worker_id * 10_007
                + idx
            )
            rng = np.random.default_rng(seed)
            raw_kp = augment_keypoints(
                raw_kp,
                rng=rng,
                mirror_p=float(self.augment_cfg.get("mirror_p", 0.0)),
                rot_deg=float(self.augment_cfg.get("rot_deg", 12.0)),
                scale_range=tuple(self.augment_cfg.get("scale_range", (0.9, 1.1))),
                shift_range=float(self.augment_cfg.get("shift_range", 0.03)),
                noise_std=float(self.augment_cfg.get("noise_std", 0.003)),
                speed_range=tuple(self.augment_cfg.get("speed_range", (0.85, 1.15))),
                hand_dropout_p=float(self.augment_cfg.get("hand_dropout_p", 0.1)),
            )

        pose, mask = preprocess_keypoints(raw_kp, target_len=self.target_len, trim=True)
        frame_mask = np.any(mask, axis=-1)  # [64]
        rgb = self._load_rgb(item["rgb_path"], item["label"], idx)

        phono = self.gloss_to_phono.get(
            item["gloss"],
            np.full(len(PHONOLOGY_COLUMNS), -1, dtype=np.int64),
        )

        if _TORCH_AVAILABLE:
            return {
                "pose": torch.from_numpy(pose),               # [64, 86, 3] float32
                "mask": torch.from_numpy(mask),               # [64, 86] bool
                "frame_mask": torch.from_numpy(frame_mask),   # [64] bool
                "rgb": torch.from_numpy(rgb),                 # [8, 768] float32
                "label": torch.tensor(item["label"], dtype=torch.long),
                "phonology": torch.from_numpy(phono.copy()),  # [6] int64
                "signer": item["signer"],
                "gloss": item["gloss"],
                "video_id": item["video_id"],
            }
        return {
            "pose": pose,
            "mask": mask,
            "frame_mask": frame_mask,
            "rgb": rgb,
            "label": int(item["label"]),
            "phonology": phono.copy(),
            "signer": item["signer"],
            "gloss": item["gloss"],
            "video_id": item["video_id"],
        }


def ensure_demo_dataset(
    data_dir: str | Path = "data",
    glosses: Optional[Sequence[str]] = None,
    samples_per_gloss: int = 5,
    source: str = "bisindo",
) -> Path:
    """
    Ensure a valid `manifest.csv`, `.npz` keypoints, and `.npy` RGB tokens exist in `data_dir`
    so tests, local runs, and QUICK notebook mode work out of the box.
    """
    data_dir = Path(data_dir)
    manifest_path = data_dir / "manifest.csv"
    if manifest_path.exists():
        return manifest_path

    gloss_list = list(glosses) if glosses is not None else list(BISINDO_32_GLOSSES)
    kp_dir = data_dir / "keypoints" / source
    rgb_dir = data_dir / "rgb_tokens" / source
    kp_dir.mkdir(parents=True, exist_ok=True)
    rgb_dir.mkdir(parents=True, exist_ok=True)

    signers = ["s1", "s2", "s3", "s4", "s5"]
    splits = ["train", "train", "train", "val", "test"]
    rng = np.random.default_rng(42)

    rows: List[Dict[str, Any]] = []
    for label_id, gloss in enumerate(gloss_list):
        for s_idx in range(samples_per_gloss):
            signer = signers[s_idx % len(signers)]
            split_sd = splits[s_idx % len(splits)]
            vid_id = f"{source}_{label_id:02d}_{signer}_{s_idx:02d}"
            kp_rel = f"keypoints/{source}/{vid_id}.npz"
            rgb_rel = f"rgb_tokens/{source}/{vid_id}.npy"

            # Create synthetic keypoint sequence [24, 86, 3] float16
            F = 24
            kp = rng.normal(0.5, 0.03, size=(F, NUM_KEYPOINTS, NUM_COORDS)).astype(np.float32)
            kp[:, L_SHOULDER_IDX] = [0.4, 0.5, 0.0]
            kp[:, R_SHOULDER_IDX] = [0.6, 0.5, 0.0]
            t_axis = np.linspace(0, 2 * np.pi, F, dtype=np.float32)[:, None]
            phase = float(label_id) * 0.25
            kp[:, LEFT_HAND_START:RIGHT_HAND_END, 0] += 0.15 * np.sin(t_axis + phase)
            kp[:, LEFT_HAND_START:RIGHT_HAND_END, 1] += 0.15 * np.cos(t_axis + phase)
            np.savez_compressed(data_dir / kp_rel, kp=kp.astype(np.float16))

            # Create synthetic RGB tokens [8, 768] float16
            base = np.sin(np.arange(RGB_TOKEN_DIM, dtype=np.float32) * 0.05 + label_id * 0.3)
            rgb = (base[None, :] + rng.normal(0, 0.05, size=(RGB_NUM_TOKENS, RGB_TOKEN_DIM))).astype(np.float16)
            np.save(data_dir / rgb_rel, rgb)

            rows.append(
                {
                    "video_id": vid_id,
                    "source": source,
                    "gloss": gloss,
                    "label": label_id,
                    "signer": signer,
                    "kp_path": kp_rel,
                    "rgb_path": rgb_rel,
                    "split_sd": split_sd,
                }
            )

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video_id", "source", "gloss", "label", "signer", "kp_path", "rgb_path", "split_sd"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return manifest_path

