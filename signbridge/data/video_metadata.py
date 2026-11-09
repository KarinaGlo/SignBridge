"""
signbridge/data/video_metadata.py — Metadata sumber video yang terisolasi per dataset (Tahap A.2.2).

Modul ini murni Python (tanpa cv2 / mediapipe / torch) sehingga dapat diuji tanpa dependency berat.

Isi:
1. WL-BISINDO (BISINDO, lisensi CC BY-NC 4.0 — non-komersial, atribusi wajib):
   - `WLBISINDO_LABELS`: pemetaan resmi label numerik 0..31 -> gloss sumber.
     Label space ini TERPISAH dari `BISINDO_32_GLOSSES` (`data/bridge/concepts.csv`);
     hanya 10 gloss yang beririsan langsung (`WLBISINDO_CONCEPT_OVERLAP`).
   - `parse_wlbisindo_filename()`: parser `signer<S>_label<L>_sample<K>.<ext>`.
   - Pembentukan split Signer-Dependent (SD) dan Signer-Independent (SI) beserta validasi
     cakupan kelas per split.
2. Pengenalan signer generik `extract_signer_id_from_text()` (perbaikan bug regex `\\b`).
3. FSL-105 (Filipino Sign Language, BUKAN BISINDO):
   - Pemeriksaan duplikat berbasis SHA-256 isi berkas, penandaan `CROSS_SPLIT_DUPLICATE`,
     dan karantina eksplisit pada manifest eksperimen tanpa mengubah `train.csv`/`test.csv`.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Identitas sumber dataset
# ---------------------------------------------------------------------------

WLBISINDO_SOURCE = "wl_bisindo"
FSL105_SOURCE = "fsl_105"
WLBISINDO_SOURCE_ALIASES = frozenset({"wl_bisindo", "wl-bisindo", "wlbisindo"})
FSL105_SOURCE_ALIASES = frozenset({"fsl", "fsl_105", "fsl-105"})

WLBISINDO_LICENSE = "CC BY-NC 4.0"
WLBISINDO_ATTRIBUTION = (
    "WL-BISINDO — Grace Oktaviani Kindy, Glenn Leonali, Henry Lucky "
    "(Kaggle glennleonali/wl-bisindo; GitHub AceKinnn/WL-BISINDO). Non-commercial use only."
)

# Pemetaan label resmi WL-BISINDO (ID numerik pada nama berkas -> gloss sumber).
WLBISINDO_LABELS: Dict[int, str] = {
    0: "AIR",
    1: "BELAJAR",
    2: "CARI",
    3: "HARI",
    4: "INGAT",
    5: "LAGI",
    6: "MAAF",
    7: "MAKAN",
    8: "MOTOR",
    9: "SAYA",
    10: "TERIMA_KASIH",
    11: "TULI",
    12: "APA",
    13: "SIAPA",
    14: "KAPAN",
    15: "DIMANA",
    16: "MENGAPA",
    17: "BAGAIMANA",
    18: "MERAH",
    19: "KUNING",
    20: "HIJAU",
    21: "HITAM",
    22: "DENGAR",
    23: "BERANGKAT",
    24: "DATANG",
    25: "TEMAN",
    26: "KELUARGA",
    27: "RUMAH",
    28: "PAGI",
    29: "SIANG",
    30: "SORE",
    31: "MALAM",
}
WLBISINDO_NUM_CLASSES = 32
assert len(WLBISINDO_LABELS) == WLBISINDO_NUM_CLASSES
assert sorted(WLBISINDO_LABELS) == list(range(WLBISINDO_NUM_CLASSES))

# Gloss yang beririsan langsung dengan 32 konsep SignBridge (data/bridge/concepts.csv).
# Informasi saja — TIDAK digunakan untuk memaksa pemetaan label.
WLBISINDO_CONCEPT_OVERLAP = frozenset(
    {"BELAJAR", "MAAF", "SAYA", "TERIMA_KASIH", "APA", "SIAPA", "KAPAN", "DIMANA", "BAGAIMANA", "TEMAN"}
)

VIDEO_EXTENSIONS: Tuple[str, ...] = (".mp4", ".webm", ".mov")
UNANNOTATED_SIGNER = "unannotated"

# ---------------------------------------------------------------------------
# Pengenalan signer generik (perbaikan bug regex `\b`)
# ---------------------------------------------------------------------------
# Regex lama `\b(s\d{1,3}|signer[_-]?\d{1,3})\b` gagal pada `signer0_label0_sample1` karena
# `_` termasuk karakter kata (\w) sehingga tidak ada batas kata `\b` antara `0` dan `_`.
# Perbaikan: gunakan lookaround eksplisit — token tidak boleh didahului huruf/angka dan
# angka signer tidak boleh langsung diikuti angka lain. Underscore/strip/titik diperlakukan
# sebagai pemisah yang sah.
_SIGNER_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(signer[_-]?\d{1,3}|s\d{1,3})(?![0-9])",
    flags=re.IGNORECASE,
)


def extract_signer_id_from_text(*tokens: str) -> str:
    """
    Kembalikan identitas signer eksplisit dari token teks (stem berkas / nama folder),
    mis. `signer0_label0_sample1` -> `SIGNER0`, `S01_video` -> `S01`, `s1_video` -> `S1`.
    Jika tidak ada penanda signer eksplisit, kembalikan `'unannotated'` (tidak pernah
    mengarang signer dari urutan/indeks berkas).
    """
    for token in tokens:
        if not token:
            continue
        m = _SIGNER_TOKEN_RE.search(str(token))
        if m:
            return m.group(1).upper().replace("-", "_")
    return UNANNOTATED_SIGNER


# ---------------------------------------------------------------------------
# WL-BISINDO: parser nama berkas
# ---------------------------------------------------------------------------

_WLBISINDO_STEM_RE = re.compile(
    r"^signer(?P<signer>\d{1,3})_label(?P<label>-?\d{1,4})_sample(?P<sample>\d{1,4})$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class WLBisindoRecord:
    """Metadata satu klip WL-BISINDO yang diturunkan murni dari nama berkas sumber."""

    filename: str
    signer_index: int
    signer_id: str
    source_label_id: int
    source_gloss: str
    sample_id: int
    source: str = WLBISINDO_SOURCE


def is_wlbisindo_filename(name: str | Path) -> bool:
    stem = Path(str(name).replace("\\", "/")).stem
    return _WLBISINDO_STEM_RE.match(stem) is not None


def parse_wlbisindo_filename(name: str | Path) -> WLBisindoRecord:
    """
    Parse `signer<S>_label<L>_sample<K>.<mp4|webm|mov>` (case-insensitive).
    Melempar ValueError informatif untuk ekstensi bukan video, pola tidak cocok,
    atau label di luar rentang resmi 0..31.
    """
    p = Path(str(name).replace("\\", "/"))
    if p.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError(
            f"Berkas '{p.name}' bukan video WL-BISINDO yang didukung "
            f"(ekstensi {p.suffix!r}; diharapkan salah satu dari {VIDEO_EXTENSIONS})."
        )
    m = _WLBISINDO_STEM_RE.match(p.stem)
    if m is None:
        raise ValueError(
            f"Nama berkas '{p.name}' tidak mengikuti pola WL-BISINDO "
            "'signer<ID>_label<ID>_sample<ID>.mp4'."
        )
    label_id = int(m.group("label"))
    if label_id not in WLBISINDO_LABELS:
        raise ValueError(
            f"Label WL-BISINDO di luar rentang resmi 0..{WLBISINDO_NUM_CLASSES - 1} pada "
            f"'{p.name}': label={label_id}."
        )
    signer_index = int(m.group("signer"))
    return WLBisindoRecord(
        filename=p.name,
        signer_index=signer_index,
        signer_id=f"SIGNER{signer_index}",
        source_label_id=label_id,
        source_gloss=WLBISINDO_LABELS[label_id],
        sample_id=int(m.group("sample")),
    )


def build_wlbisindo_records(names: Iterable[str | Path]) -> List[WLBisindoRecord]:
    """Parse seluruh nama berkas; tolak nama ganda (case-insensitive) agar tidak ada overwrite diam-diam."""
    records: List[WLBisindoRecord] = []
    seen: Set[str] = set()
    for n in names:
        rec = parse_wlbisindo_filename(n)
        key = rec.filename.lower()
        if key in seen:
            raise ValueError(f"Nama berkas WL-BISINDO ganda terdeteksi: {rec.filename}")
        seen.add(key)
        records.append(rec)
    if not records:
        raise ValueError("Tidak ada berkas WL-BISINDO yang dapat diparse.")
    return records


def list_wlbisindo_zip_members(zip_path: str | Path) -> List[str]:
    """
    Baca daftar nama berkas video dari central directory ZIP WL-BISINDO TANPA mengekstrak isi.
    """
    import zipfile

    zp = Path(zip_path)
    if not zp.is_file():
        raise FileNotFoundError(f"Arsip WL-BISINDO tidak ditemukan: {zp}")
    with zipfile.ZipFile(zp, "r") as zf:
        return [
            info.filename
            for info in zf.infolist()
            if not info.is_dir() and Path(info.filename).suffix.lower() in VIDEO_EXTENSIONS
        ]


def signer_class_coverage(records: Sequence[WLBisindoRecord]) -> Dict[str, List[int]]:
    """Kembalikan {signer_id: daftar source_label_id terurut} sesuai metadata sumber."""
    cov: Dict[str, Set[int]] = {}
    for r in records:
        cov.setdefault(r.signer_id, set()).add(r.source_label_id)
    return {s: sorted(v) for s, v in sorted(cov.items())}


# ---------------------------------------------------------------------------
# Validasi cakupan kelas & pembentukan split SD / SI
# ---------------------------------------------------------------------------


def validate_split_class_coverage(
    split_to_labels: Mapping[str, Iterable[int]],
    num_classes: int = WLBISINDO_NUM_CLASSES,
) -> Dict[str, Dict[str, object]]:
    """
    Untuk setiap split, laporkan kelas yang tersedia/hilang dan apakah cakupan lengkap.
    """
    expected = set(range(num_classes))
    report: Dict[str, Dict[str, object]] = {}
    for split, labels in split_to_labels.items():
        present = set(int(x) for x in labels)
        missing = sorted(expected - present)
        report[split] = {
            "num_classes_present": len(present & expected),
            "missing_labels": missing,
            "complete": not missing,
        }
    return report


def assign_wlbisindo_sd_splits(
    records: Sequence[WLBisindoRecord],
    ratios: Tuple[float, float, float] = (0.6, 0.1, 0.3),
) -> Dict[str, str]:
    """
    Signer-Dependent (SD): setiap kelompok (signer, label) dibagi deterministik berdasarkan
    `sample_id` terurut (bukan acak, bukan frame-level) ke train/val/test, sehingga setiap
    signer muncul di semua split. Klip yang sama tidak pernah berada di lebih dari satu split.
    """
    if abs(sum(ratios) - 1.0) > 1e-6 or any(r < 0 for r in ratios):
        raise ValueError(f"Rasio split SD tidak valid: {ratios}")
    groups: Dict[Tuple[str, int], List[WLBisindoRecord]] = {}
    for r in records:
        groups.setdefault((r.signer_id, r.source_label_id), []).append(r)

    assignment: Dict[str, str] = {}
    for _, grp in sorted(groups.items()):
        grp_sorted = sorted(grp, key=lambda x: x.sample_id)
        n = len(grp_sorted)
        n_train = int(round(n * ratios[0]))
        n_val = int(round(n * ratios[1]))
        if n >= 3:
            n_train = max(1, n_train)
            n_val = max(1, n_val)
            n_val = min(n_val, n - n_train - 1)
        n_train = min(n_train, n)
        for i, rec in enumerate(grp_sorted):
            if i < n_train:
                split = "train"
            elif i < n_train + n_val:
                split = "val"
            else:
                split = "test"
            assignment[rec.filename] = split
    return assignment


def build_wlbisindo_si_split(
    records: Sequence[WLBisindoRecord],
    test_signers: Sequence[str],
    val_signers: Sequence[str] = (),
    require_full_coverage: bool = True,
) -> Tuple[Dict[str, str], Dict[str, object]]:
    """
    Signer-Independent (SI): seluruh klip signer pada `test_signers` -> test, `val_signers` -> val,
    sisanya -> train. Signer tidak pernah muncul di lebih dari satu split.

    Mengembalikan (assignment, report). `report['si_valid']` hanya True bila train, val (jika ada),
    dan test masing-masing mencakup ke-32 kelas. Bila `require_full_coverage=True` dan cakupan
    tidak lengkap, lempar ValueError (mis. signer0 sebagai satu-satunya test signer hanya
    mencakup label 0..11).
    """
    test_set = {s.upper() for s in test_signers}
    val_set = {s.upper() for s in val_signers}
    if not test_set:
        raise ValueError("Protokol SI membutuhkan minimal satu test signer.")
    overlap = test_set & val_set
    if overlap:
        raise ValueError(f"Signer tidak boleh berada di test dan val sekaligus: {sorted(overlap)}")
    all_signers = {r.signer_id for r in records}
    unknown = (test_set | val_set) - all_signers
    if unknown:
        raise ValueError(f"Signer tidak dikenal pada metadata WL-BISINDO: {sorted(unknown)}")
    train_signers = all_signers - test_set - val_set
    if not train_signers:
        raise ValueError("Protokol SI membutuhkan minimal satu signer untuk train.")

    assignment: Dict[str, str] = {}
    split_labels: Dict[str, Set[int]] = {"train": set(), "test": set()}
    if val_set:
        split_labels["val"] = set()
    for r in records:
        if r.signer_id in test_set:
            split = "test"
        elif r.signer_id in val_set:
            split = "val"
        else:
            split = "train"
        assignment[r.filename] = split
        split_labels[split].add(r.source_label_id)

    coverage = validate_split_class_coverage(split_labels, WLBISINDO_NUM_CLASSES)
    si_valid = all(bool(v["complete"]) for v in coverage.values())
    report: Dict[str, object] = {
        "protocol": "SI",
        "train_signers": sorted(train_signers),
        "val_signers": sorted(val_set),
        "test_signers": sorted(test_set),
        "coverage": coverage,
        "si_valid": si_valid,
    }
    if require_full_coverage and not si_valid:
        incomplete = {k: v["missing_labels"] for k, v in coverage.items() if not v["complete"]}
        raise ValueError(
            "Evaluasi Signer-Independent WL-BISINDO tidak valid: cakupan kelas tidak lengkap pada "
            f"split {sorted(incomplete)} (label hilang: {incomplete})."
        )
    return assignment, report


# ---------------------------------------------------------------------------
# SHA-256 & duplikasi lintas split (umum + FSL-105)
# ---------------------------------------------------------------------------

DUP_UNIQUE = "UNIQUE"
DUP_WITHIN_SPLIT = "WITHIN_SPLIT_DUPLICATE"
DUP_CROSS_SPLIT = "CROSS_SPLIT_DUPLICATE"
EXP_INCLUDED = "INCLUDED"
EXP_QUARANTINED_CROSS_SPLIT = "QUARANTINED_CROSS_SPLIT_DUPLICATE"
EXP_QUARANTINED_NO_SPLIT = "QUARANTINED_NO_OFFICIAL_SPLIT"


def compute_file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_sha256_duplicates(rows: List[Dict[str, object]], split_key: str = "split") -> List[Dict[str, object]]:
    """
    Tambahkan kolom `dup_group_size`, `dup_status`, `cross_class_duplicate`, dan `experiment_status`
    pada setiap baris (harus memiliki `sha256`, `split_key`, `source_label_id`).

    Kebijakan eksplisit (tidak memilih split secara diam-diam):
    - Grup SHA-256 yang muncul di >1 split -> semua anggotanya `CROSS_SPLIT_DUPLICATE` dan
      DIKARANTINA (`QUARANTINED_CROSS_SPLIT_DUPLICATE`) dari manifest eksperimen.
    - Grup duplikat di split yang sama -> `WITHIN_SPLIT_DUPLICATE`, dilaporkan, tetap INCLUDED.
    - Baris tanpa split resmi -> `QUARANTINED_NO_OFFICIAL_SPLIT`.
    """
    groups: Dict[str, List[Dict[str, object]]] = {}
    for r in rows:
        groups.setdefault(str(r["sha256"]), []).append(r)
    for _, members in groups.items():
        splits = {str(m.get(split_key) or "") for m in members}
        labels = {str(m.get("source_label_id")) for m in members}
        if len(members) == 1:
            status = DUP_UNIQUE
        elif len(splits) > 1:
            status = DUP_CROSS_SPLIT
        else:
            status = DUP_WITHIN_SPLIT
        for m in members:
            m["dup_group_size"] = len(members)
            m["dup_status"] = status
            m["cross_class_duplicate"] = len(members) > 1 and len(labels) > 1
            if not m.get(split_key):
                m["experiment_status"] = EXP_QUARANTINED_NO_SPLIT
            elif status == DUP_CROSS_SPLIT:
                m["experiment_status"] = EXP_QUARANTINED_CROSS_SPLIT
            else:
                m["experiment_status"] = EXP_INCLUDED
    return rows


def assert_no_sha256_split_leakage(
    rows: Iterable[Mapping[str, object]],
    split_key: str = "split",
    only_included: bool = True,
) -> None:
    """Lempar ValueError bila satu SHA-256 muncul di lebih dari satu split pada manifest eksperimen."""
    sha_to_split: Dict[str, str] = {}
    for r in rows:
        if only_included and r.get("experiment_status", EXP_INCLUDED) != EXP_INCLUDED:
            continue
        sha = str(r.get("sha256") or "")
        sp = str(r.get(split_key) or "")
        if not sha:
            continue
        prev = sha_to_split.get(sha)
        if prev is not None and prev != sp:
            raise ValueError(f"Kebocoran konten video (SHA-256 identik) lintas split {prev} vs {sp}: sha256={sha}")
        sha_to_split[sha] = sp


def _norm_rel(p: str) -> str:
    return p.replace("\\", "/").strip("/").lower()


def load_fsl105_official_splits(fsl_root: str | Path) -> Dict[str, Tuple[str, int, str]]:
    """
    Baca (read-only) `train.csv` & `test.csv` resmi FSL-105 -> {"clips/<id>/<n>.mov": (split, id_label, label)}.
    """
    root = Path(fsl_root)
    out: Dict[str, Tuple[str, int, str]] = {}
    for split in ("train", "val", "test"):
        csv_path = root / f"{split}.csv"
        if not csv_path.is_file():
            continue
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                vp = (row.get("vid_path") or "").strip()
                if not vp:
                    continue
                key = _norm_rel(vp)
                if key in out and out[key][0] != split:
                    raise ValueError(f"Kebocoran path FSL-105 antara {out[key][0]} dan {split}: {vp}")
                out[key] = (split, int((row.get("id_label") or "-1").strip()), (row.get("label") or "").strip())
    if not out:
        raise FileNotFoundError(f"train.csv/test.csv resmi FSL-105 tidak ditemukan di {root}")
    return out


def build_fsl105_duplicate_report(
    fsl_root: str | Path,
    sha256_cache: Optional[Dict[str, str]] = None,
) -> List[Dict[str, object]]:
    """
    Hitung SHA-256 setiap video `clips/<id>/*.MOV` FSL-105, gabungkan dengan split resmi
    (tanpa mengubah CSV), lalu klasifikasikan duplikat. Mengembalikan satu baris per video.
    """
    root = Path(fsl_root)
    clips = root / "clips"
    if not clips.is_dir():
        raise FileNotFoundError(f"Direktori klip FSL-105 tidak ditemukan: {clips}")
    official = load_fsl105_official_splits(root)
    videos = sorted(
        p for p in clips.rglob("*") if p.is_file() and not p.name.startswith("._") and p.suffix.lower() in VIDEO_EXTENSIONS
    )
    if not videos:
        raise FileNotFoundError(f"Tidak ada video FSL-105 di {clips}")
    rows: List[Dict[str, object]] = []
    for v in videos:
        rel = v.relative_to(root).as_posix()
        key = rel.lower()
        if sha256_cache is not None and key in sha256_cache:
            sha = sha256_cache[key]
        else:
            sha = compute_file_sha256(v)
            if sha256_cache is not None:
                sha256_cache[key] = sha
        split, label_id, gloss = official.get(key, ("", int(v.parent.name) if v.parent.name.isdigit() else -1, ""))
        rows.append(
            {
                "source": FSL105_SOURCE,
                "rel_path": rel,
                "source_label_id": label_id,
                "source_gloss": gloss,
                "official_split": split,
                "sha256": sha,
            }
        )
    return classify_sha256_duplicates(rows, split_key="official_split")


FSL105_REPORT_COLUMNS: List[str] = [
    "source",
    "rel_path",
    "source_label_id",
    "source_gloss",
    "official_split",
    "sha256",
    "dup_group_size",
    "dup_status",
    "cross_class_duplicate",
    "experiment_status",
]


def write_duplicate_report(rows: Iterable[Mapping[str, object]], out_csv: str | Path, only_duplicates: bool = True) -> int:
    out = Path(out_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    sel = [r for r in rows if not only_duplicates or r.get("dup_status") != DUP_UNIQUE]
    sel.sort(key=lambda r: (str(r.get("sha256")), str(r.get("rel_path"))))
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FSL105_REPORT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(sel)
    return len(sel)

