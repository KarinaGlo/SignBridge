"""
Manifest & loader dataset multimodal M6 (NumPy). Wrapper PyTorch ada di train_multimodal.py.

Format manifest CSV (kolom = signbridge.multimodal.constants.MANIFEST_COLUMNS):
    clip_id, signer, category, gloss, label, kp_path, image_path, audio_path, text, split
Path relatif diselesaikan terhadap folder manifest. Kolom kosong = modalitas tidak tersedia.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from signbridge.multimodal.constants import MANIFEST_COLUMNS, NUM_MODALITIES
from signbridge.multimodal.features import encode_text, load_audio, load_image, load_pose


@dataclass
class MultimodalRecord:
    clip_id: str
    signer: str
    category: str
    gloss: str
    label: int
    kp_path: str = ""
    image_path: str = ""
    audio_path: str = ""
    text: str = ""
    split: str = "train"
    extra: Dict[str, str] = field(default_factory=dict)


def read_manifest(path: str | Path) -> List[MultimodalRecord]:
    path = Path(path)
    root = path.parent
    out: List[MultimodalRecord] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            def resolve(key: str) -> str:
                v = (row.get(key) or "").strip()
                if not v:
                    return ""
                p = Path(v)
                return str(p if p.is_absolute() else root / p)

            out.append(
                MultimodalRecord(
                    clip_id=row["clip_id"],
                    signer=row.get("signer", ""),
                    category=row.get("category", "gloss"),
                    gloss=row.get("gloss", ""),
                    label=int(row["label"]),
                    kp_path=resolve("kp_path"),
                    image_path=resolve("image_path"),
                    audio_path=resolve("audio_path"),
                    text=(row.get("text") or "").strip(),
                    split=(row.get("split") or "train").strip().lower(),
                )
            )
    return out


def write_manifest(records: Sequence[MultimodalRecord], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    root = path.parent.resolve()

    def rel(p: str) -> str:
        if not p:
            return ""
        pp = Path(p).resolve()
        try:
            return pp.relative_to(root).as_posix()
        except ValueError:
            return pp.as_posix()

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        w.writeheader()
        for r in records:
            w.writerow({
                "clip_id": r.clip_id, "signer": r.signer, "category": r.category, "gloss": r.gloss,
                "label": r.label, "kp_path": rel(r.kp_path), "image_path": rel(r.image_path),
                "audio_path": rel(r.audio_path), "text": r.text, "split": r.split,
            })


def stable_split(key: str, ratios=(0.7, 0.15, 0.15)) -> str:
    """Split deterministik berbasis hash (tidak bergantung urutan file)."""
    h = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    if h < ratios[0]:
        return "train"
    if h < ratios[0] + ratios[1]:
        return "val"
    return "test"


def assign_splits(records: List[MultimodalRecord], protocol: str = "sd", test_signer: Optional[str] = None) -> None:
    """
    sd : stratifikasi per (signer, label) -> take dibagi train/val/test secara deterministik.
    si : seluruh klip `test_signer` menjadi test (Leave-One-Signer-Out); sisanya train/val.
    """
    if protocol == "si":
        if not test_signer:
            raise ValueError("Protokol SI membutuhkan --test-signer.")
        for r in records:
            if r.signer == test_signer:
                r.split = "test"
            else:
                r.split = "val" if stable_split(r.clip_id, (0.85, 0.15, 0.0)) == "val" else "train"
        return
    groups: Dict[tuple, List[MultimodalRecord]] = {}
    for r in records:
        groups.setdefault((r.signer, r.label), []).append(r)
    for _, items in groups.items():
        items.sort(key=lambda r: hashlib.sha256(r.clip_id.encode()).hexdigest())
        n = len(items)
        n_test = max(1, round(0.15 * n)) if n >= 3 else 0
        n_val = max(1, round(0.15 * n)) if n >= 3 else 0
        for i, r in enumerate(items):
            r.split = "test" if i < n_test else ("val" if i < n_test + n_val else "train")


def has_any_modality(r: MultimodalRecord) -> bool:
    """True bila minimal satu modalitas tersedia (cek berkas, tanpa decode)."""
    return bool(
        (r.kp_path and Path(r.kp_path).exists())
        or (r.image_path and Path(r.image_path).exists())
        or (r.audio_path and Path(r.audio_path).exists())
        or r.text
    )


class MultimodalSampleLoader:
    """Memuat satu record menjadi dict array NumPy + modality_mask [4] (urutan: video, image, audio, text)."""

    def __init__(self, records: Sequence[MultimodalRecord]):
        self.records = list(records)

    def __len__(self) -> int:
        return len(self.records)

    def load(self, idx: int) -> Dict[str, np.ndarray]:
        r = self.records[idx]
        pose, has_pose = load_pose(r.kp_path)
        image, has_img = load_image(r.image_path)
        audio, has_audio = load_audio(r.audio_path)
        text, has_text = encode_text(r.text)
        mask = np.array([has_pose, has_img, has_audio, has_text], dtype=np.float32)
        assert mask.shape == (NUM_MODALITIES,)
        return {
            "pose": pose, "image": image, "audio": audio, "text": text,
            "modality_mask": mask, "label": np.int64(r.label),
        }

    def availability(self) -> Dict[str, int]:
        """Hitung berapa sampel memiliki tiap modalitas (cek cepat tanpa decode penuh)."""
        counts = {"video": 0, "image": 0, "audio": 0, "text": 0}
        for r in self.records:
            counts["video"] += int(bool(r.kp_path) and Path(r.kp_path).exists())
            counts["image"] += int(bool(r.image_path) and Path(r.image_path).exists())
            counts["audio"] += int(bool(r.audio_path) and Path(r.audio_path).exists())
            counts["text"] += int(bool(r.text))
        return counts
