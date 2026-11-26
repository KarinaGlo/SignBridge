"""
signbridge/xmf/ingest.py — TAHAP 2 (INGESTION): satukan sumber mentah menjadi SATU manifest per tugas.

Struktur sumber (salinan folder Google Drive "WL-BISINDO"):
    <drive_root>/video/signer{S}_label{L}_sample{N}.mp4          (1.600 klip WL-BISINDO)
    <drive_root>/citra/<nama_folder>/signer{S}_label{L}_sample{N}_f{00..15}.jpg
                                                                  (16 frame DARI KLIP YANG SAMA)
    <drive_root>/alfabet/<A..Z>/<huruf>_<latar>_<merek>_<tipe>.jpg (foto huruf, tervalidasi Kawan Tuli)
    [opsional] data/raw/audio/<KONSEP>/*.wav                       (rekaman suara relawan)

Keluaran (data/xmf/ingest/):
    gloss_manifest.csv     1 baris = 1 klip; kolom video_path + daftar 16 path citra (berpasangan)
    alphabet_manifest.csv  1 baris = 1 foto huruf
    ingest_report.json     cakupan data, ketidakcocokan nama folder, klip tanpa citra, dll.

Label SELALU dari nama file (lihat catatan di config.py). Mendukung "cicil": jalankan ulang kapan saja
setelah upload bertambah; klip yang citranya belum lengkap ditandai `image_source=video_fallback`.

Contoh:
    python -m signbridge.xmf.ingest --drive-root data/raw/wlbisindo_drive
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from signbridge.xmf.config import GLOSSES, LETTERS, parse_alphabet_name, parse_wlb_name

ROOT = Path(__file__).resolve().parents[2]
VIDEO_EXT = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
EXPECTED_CITRA_PER_CLIP = 16

GLOSS_COLUMNS = [
    "sample_id", "task", "signer", "label", "gloss", "sample",
    "video_path", "citra_paths", "n_citra", "image_source",
    "split_sd", "split_si", "split_final",
]
ALPHA_COLUMNS = ["sample_id", "task", "label", "letter", "group", "image_path", "split", "split_final"]


def _rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p.resolve())


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------
def _load_repo_sd_split() -> Dict[str, str]:
    """Pakai split signer-dependent lama (data/manifest_wl_bisindo.csv) agar sebanding dengan M0."""
    path = ROOT / "data" / "manifest_wl_bisindo.csv"
    out: Dict[str, str] = {}
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = parse_wlb_name(row.get("video_id", ""))
                if key and row.get("split_sd"):
                    out[key.clip_id] = row["split_sd"].strip()
    return out


def split_sd_rule(sample: int) -> str:
    return "test" if sample in (9, 10) else ("val" if sample == 8 else "train")


def split_si(signer: int, sample: int, test_signer: int) -> str:
    """Signer-independent: 1 penanda disimpan untuk test; val = sampel 9-10 penanda lain."""
    if signer == test_signer:
        return "test"
    return "val" if sample in (9, 10) else "train"


def split_final(sample: int) -> str:
    """Model deploy: semua penanda dipakai, sisakan sampel 10 sebagai val untuk early-stopping."""
    return "val" if sample == 10 else "train"


def _group_bucket(group: str) -> int:
    return int(hashlib.sha1(group.encode("utf-8")).hexdigest(), 16) % 100


# ---------------------------------------------------------------------------
# Gloss (video + citra)
# ---------------------------------------------------------------------------
def ingest_gloss(drive_root: Path, test_signer: int) -> Dict:
    video_dir, citra_dir = drive_root / "video", drive_root / "citra"
    videos: Dict[str, Path] = {}
    for p in sorted(video_dir.rglob("*")) if video_dir.exists() else []:
        if p.suffix.lower() in VIDEO_EXT:
            k = parse_wlb_name(p.name)
            if k:
                videos[k.clip_id] = p

    citra: Dict[str, Dict[int, Path]] = defaultdict(dict)
    folder_vs_label = Counter()
    for p in sorted(citra_dir.rglob("*")) if citra_dir.exists() else []:
        if p.suffix.lower() not in IMAGE_EXT:
            continue
        k = parse_wlb_name(p.name)
        if not k or k.frame is None:
            continue
        citra[k.clip_id][k.frame] = p
        folder_vs_label[(p.parent.name, k.gloss)] += 1

    keys = {}
    for cid in set(videos) | set(citra):
        keys[cid] = parse_wlb_name(cid)

    repo_sd = _load_repo_sd_split()
    rows: List[Dict] = []
    for cid in sorted(keys, key=lambda c: (keys[c].label, keys[c].signer, keys[c].sample)):
        k = keys[cid]
        frames = citra.get(cid, {})
        ordered = [frames[i] for i in sorted(frames)]
        has_video = cid in videos
        if len(ordered) >= EXPECTED_CITRA_PER_CLIP:
            src = "citra"
        elif has_video:
            src = "video_fallback"   # upload citra belum lengkap -> frame diambil dari mp4 yang sama
        else:
            src = "citra_partial"
        if not has_video and not ordered:
            continue
        rows.append({
            "sample_id": cid, "task": "gloss", "signer": k.signer, "label": k.label, "gloss": k.gloss,
            "sample": k.sample,
            "video_path": _rel(videos[cid]) if has_video else "",
            "citra_paths": ";".join(_rel(p) for p in ordered),
            "n_citra": len(ordered), "image_source": src,
            "split_sd": repo_sd.get(cid, split_sd_rule(k.sample)),
            "split_si": split_si(k.signer, k.sample, test_signer),
            "split_final": split_final(k.sample),
        })

    mismatch = sorted(
        {f"{folder} -> {gloss}" for (folder, gloss), n in folder_vs_label.items()
         if folder.replace("_", "").upper() != gloss.replace("_", "")}
    )
    return {
        "rows": rows,
        "report": {
            "videos_found": len(videos),
            "clips_with_citra": sum(1 for r in rows if r["n_citra"] > 0),
            "clips_with_full_citra": sum(1 for r in rows if r["n_citra"] >= EXPECTED_CITRA_PER_CLIP),
            "citra_images_found": sum(len(v) for v in citra.values()),
            "clips_missing_video": sum(1 for r in rows if not r["video_path"]),
            "image_source": dict(Counter(r["image_source"] for r in rows)),
            "per_signer": dict(sorted(Counter(f"signer{r['signer']}" for r in rows).items())),
            "per_gloss": {g: sum(1 for r in rows if r["gloss"] == g) for g in GLOSSES},
            "citra_folder_name_mismatch": mismatch,
            "note": "Label diambil dari nama file (labelN). Nama folder citra diabaikan.",
        },
    }


# ---------------------------------------------------------------------------
# Alfabet (foto)
# ---------------------------------------------------------------------------
def ingest_alphabet(drive_root: Path) -> Dict:
    adir = drive_root / "alfabet"
    rows: List[Dict] = []
    for p in sorted(adir.rglob("*")) if adir.exists() else []:
        if p.suffix.lower() not in IMAGE_EXT:
            continue
        parsed = parse_alphabet_name(p.name, p.parent.name)
        if not parsed:
            continue
        letter, group = parsed
        b = _group_bucket(group)
        rows.append({
            "sample_id": f"{letter}/{p.stem}", "task": "alphabet", "label": LETTERS.index(letter),
            "letter": letter, "group": group, "image_path": _rel(p),
            "split": "train" if b < 70 else ("val" if b < 85 else "test"),
            "split_final": "val" if b >= 92 else "train",
        })
    return {
        "rows": rows,
        "report": {
            "images_found": len(rows),
            "groups": len({r["group"] for r in rows}),
            "per_letter": {L: sum(1 for r in rows if r["letter"] == L) for L in LETTERS},
            "per_split": dict(Counter(r["split"] for r in rows)),
            "note": "Split berbasis grup perangkat/kontributor agar foto sumber yang sama tidak bocor ke test.",
        },
    }


def _write(path: Path, rows: List[Dict], cols: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive-root", type=Path, default=ROOT / "data/raw/wlbisindo_drive")
    ap.add_argument("--out", type=Path, default=ROOT / "data/xmf/ingest")
    ap.add_argument("--test-signer", type=int, default=4, help="penanda yang disimpan untuk uji signer-independent")
    args = ap.parse_args(argv)

    if not args.drive_root.exists():
        raise SystemExit(
            f"Folder sumber tidak ditemukan: {args.drive_root}\n"
            "Salin folder Drive 'WL-BISINDO' (video/, citra/, alfabet/) ke sana — lihat scripts/xmf_sync_drive.sh"
        )
    g = ingest_gloss(args.drive_root, args.test_signer)
    a = ingest_alphabet(args.drive_root)
    _write(args.out / "gloss_manifest.csv", g["rows"], GLOSS_COLUMNS)
    _write(args.out / "alphabet_manifest.csv", a["rows"], ALPHA_COLUMNS)
    report = {"drive_root": str(args.drive_root), "test_signer": args.test_signer,
              "gloss": g["report"], "alphabet": a["report"]}
    (args.out / "ingest_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    gr, ar = g["report"], a["report"]
    print(f"[ingest] gloss   : {len(g['rows'])} klip | video={gr['videos_found']} | "
          f"citra lengkap={gr['clips_with_full_citra']} | sumber citra={gr['image_source']}")
    if gr["citra_folder_name_mismatch"]:
        print(f"[ingest] PERINGATAN: {len(gr['citra_folder_name_mismatch'])} folder citra bernama tidak sesuai "
              "label resmi -> label diambil dari nama file. Contoh:", gr["citra_folder_name_mismatch"][:3])
    print(f"[ingest] alfabet : {ar['images_found']} foto, {ar['groups']} grup perangkat, split={ar['per_split']}")
    print(f"[ingest] tulis   : {args.out}")


if __name__ == "__main__":
    main()
