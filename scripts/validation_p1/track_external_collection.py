"""
scripts/validation_p1/track_external_collection.py
Field data collection tracking and monitoring tool for BISINDO I1-P1 external validation.

Monitors real-world data collection progress across:
- 3 Signers: EXT_S01, EXT_S02, EXT_S03
- 26 Classes: A-Z
- 10 Photos per signer per class (Total: 780 photos)

Strict Rules:
- Only counts data with consent_status == 'CONSENT_SIGNED'.
- Validates signer_id in {'EXT_S01', 'EXT_S02', 'EXT_S03'}.
- Multi-fallback path resolution supporting dataset-relative, root-relative, and absolute paths.
- Manifest transparency separating actual manifest from template fallback.
- Detects and rejects duplicate images (by path and SHA-256 hash).
- Detects unregistered files on disk and missing manifest files.
- Status categories: NOT STARTED, IN PROGRESS, COMPLETE, NEEDS REVIEW.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]

TARGET_SIGNERS = ["EXT_S01", "EXT_S02", "EXT_S03"]
TARGET_CLASSES = [chr(i) for i in range(ord("A"), ord("Z") + 1)]  # A-Z
TARGET_PER_COMBINATION = 10
TOTAL_TARGET = len(TARGET_SIGNERS) * len(TARGET_CLASSES) * TARGET_PER_COMBINATION  # 780

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("collection_tracker")


def compute_sha256(path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def scan_disk_images(data_dir: Path) -> Dict[Path, Path]:
    """Scans data_dir for all physical image files.
    Returns mapping from resolved absolute Path to relative Path from ROOT.
    """
    images: Dict[Path, Path] = {}
    if not data_dir.exists():
        return images

    for p in data_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            resolved = p.resolve()
            try:
                rel = p.relative_to(ROOT)
            except ValueError:
                rel = p
            images[resolved] = rel
    return images


def resolve_image_path(raw_path: str, data_dir: Path) -> Path:
    """Resolves an image path supporting three formats with explicit priority:
    1. Absolute path: used directly.
    2. Relative to data_dir: checked first for relative paths.
    3. Relative to ROOT: checked second if not found in data_dir.
    4. Unresolved fallback:
       - If path starts with 'data/' -> candidate is ROOT / path
       - Otherwise -> candidate is data_dir / path

    Always returns a normalized resolved Path object.
    """
    raw_str = raw_path.strip()
    p = Path(raw_str)

    # 1. Absolute path
    if p.is_absolute():
        return p.resolve()

    # Normalize data_dir to absolute
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir

    # 2. Priority 1 for relative: check relative to data_dir
    cand_data = data_dir / p
    if cand_data.exists():
        return cand_data.resolve()

    # 3. Priority 2 for relative: check relative to repository ROOT
    cand_root = ROOT / p
    if cand_root.exists():
        return cand_root.resolve()

    # 4. If not found in either location, determine candidate by convention
    clean_posix = p.as_posix()
    if clean_posix.startswith("data/"):
        return cand_root.resolve()
    return cand_data.resolve()


def track_collection_progress(
    data_dir: Path,
    manifest_path: Optional[Path] = None,
    out_report: Optional[Path] = None,
    out_json: Optional[Path] = None,
) -> Dict[str, Any]:
    """Analyzes field data collection progress against the 780 photo target."""
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir

    # 1. Scan physical images on disk
    disk_images_map = scan_disk_images(data_dir)
    disk_resolved_set = set(disk_images_map.keys())

    # 2. Manifest identification & transparency logic (GAP-02)
    actual_manifest_path = data_dir / "external_manifest.csv"
    actual_manifest_exists = actual_manifest_path.exists()
    template_manifest_path = data_dir / "external_manifest_template.csv"
    template_manifest_exists = template_manifest_path.exists()

    if manifest_path is None:
        if actual_manifest_exists:
            manifest_mode = "ACTUAL_MANIFEST"
            active_manifest_path = actual_manifest_path
        elif template_manifest_exists:
            manifest_mode = "TEMPLATE_FALLBACK"
            active_manifest_path = template_manifest_path
        else:
            manifest_mode = "ACTUAL_MANIFEST_NOT_FOUND"
            active_manifest_path = actual_manifest_path
    else:
        if not manifest_path.is_absolute():
            manifest_path = ROOT / manifest_path
        manifest_mode = "EXPLICIT_CLI"
        active_manifest_path = manifest_path

    manifest_rows: List[Dict[str, str]] = []
    if active_manifest_path.exists():
        with open(active_manifest_path, "r", encoding="utf-8") as f:
            manifest_rows = list(csv.DictReader(f))

    # 3. Processing and tracking data structures
    valid_samples: List[Dict[str, Any]] = []
    seen_file_paths: Set[Path] = set()
    seen_hashes: Dict[str, str] = {}  # sha256 -> first_image_path

    # Anomalies
    unconsented_records: List[Dict[str, Any]] = []
    invalid_signer_records: List[Dict[str, Any]] = []
    invalid_label_records: List[Dict[str, Any]] = []
    missing_disk_records: List[Dict[str, Any]] = []
    duplicate_records: List[Dict[str, Any]] = []

    # Distribution counts
    comb_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    signer_counts: Dict[str, int] = defaultdict(int)
    label_counts: Dict[str, int] = defaultdict(int)

    total_manifest_raw_rows = len(manifest_rows)
    non_comment_rows = 0

    for idx, row in enumerate(manifest_rows):
        raw_p = (row.get("image_path") or row.get("path") or "").strip()
        if not raw_p or raw_p.startswith("#"):
            continue

        non_comment_rows += 1

        # Check signer identity
        sid = (row.get("signer_id") or "").strip().upper()
        if not sid:
            sid = (row.get("subject_id") or "").strip().upper()

        if sid not in TARGET_SIGNERS:
            invalid_signer_records.append({
                "row_index": idx + 1,
                "signer_id": sid or "(EMPTY)",
                "image_path": raw_p,
                "reason": f"Signer ID '{sid}' bukan penutur target resmi (harus salah satu dari {TARGET_SIGNERS})",
            })
            continue

        # Check label
        lbl = (row.get("label") or "").strip().upper()
        if lbl not in TARGET_CLASSES:
            invalid_label_records.append({
                "row_index": idx + 1,
                "label": lbl or "(EMPTY)",
                "image_path": raw_p,
                "reason": f"Label '{lbl}' bukan kelas huruf valid A-Z",
            })
            continue

        # Check consent (Strict hard gate)
        consent = (row.get("consent_status") or "").strip()
        if consent != "CONSENT_SIGNED":
            unconsented_records.append({
                "row_index": idx + 1,
                "signer_id": sid,
                "label": lbl,
                "image_path": raw_p,
                "consent_status": consent or "(EMPTY)",
                "reason": "Status consent bukan 'CONSENT_SIGNED'",
            })
            continue

        # Resolve path using the multi-fallback resolver (GAP-01)
        resolved_p = resolve_image_path(raw_p, data_dir=data_dir)

        if not resolved_p.exists():
            missing_disk_records.append({
                "row_index": idx + 1,
                "signer_id": sid,
                "label": lbl,
                "expected_path": str(resolved_p),
                "reason": "File citra tercatat di manifest tetapi tidak ditemukan di disk",
            })
            continue

        # Check path duplication
        if resolved_p in seen_file_paths:
            duplicate_records.append({
                "row_index": idx + 1,
                "signer_id": sid,
                "label": lbl,
                "image_path": str(resolved_p),
                "reason": "Duplikasi path file yang sama tercatat lebih dari satu kali di manifest",
            })
            continue

        # Check content SHA-256 hash duplication
        f_hash = compute_sha256(resolved_p)
        if f_hash in seen_hashes:
            duplicate_records.append({
                "row_index": idx + 1,
                "signer_id": sid,
                "label": lbl,
                "image_path": str(resolved_p),
                "hash": f_hash,
                "original_path": seen_hashes[f_hash],
                "reason": f"Duplikasi konten citra identik (SHA-256 sama dengan {seen_hashes[f_hash]})",
            })
            continue

        # Sample is strictly valid
        seen_file_paths.add(resolved_p)
        seen_hashes[f_hash] = str(resolved_p)

        comb_counts[(sid, lbl)] += 1
        signer_counts[sid] += 1
        label_counts[lbl] += 1

        valid_samples.append({
            "signer_id": sid,
            "label": lbl,
            "path": str(resolved_p),
            "hash": f_hash,
        })

    # 4. Check unregistered files on disk (files on disk not in seen_file_paths)
    unregistered_disk_files: List[str] = []
    for resolved_p, rel_p in disk_images_map.items():
        if resolved_p not in seen_file_paths:
            unregistered_disk_files.append(str(rel_p))

    total_valid = len(valid_samples)
    shortfall = max(0, TOTAL_TARGET - total_valid)
    progress_pct = round((total_valid / TOTAL_TARGET) * 100.0, 2)

    # 5. Incomplete combinations analysis (combinations with < 10 photos)
    incomplete_combinations: List[Dict[str, Any]] = []
    for s in TARGET_SIGNERS:
        for c in TARGET_CLASSES:
            cnt = comb_counts.get((s, c), 0)
            if cnt < TARGET_PER_COMBINATION:
                incomplete_combinations.append({
                    "signer_id": s,
                    "label": c,
                    "collected": cnt,
                    "target": TARGET_PER_COMBINATION,
                    "deficit": TARGET_PER_COMBINATION - cnt,
                })

    # 6. Status determination
    has_blocking_anomalies = (
        len(unconsented_records) > 0
        or len(invalid_signer_records) > 0
        or len(invalid_label_records) > 0
        or len(missing_disk_records) > 0
        or len(duplicate_records) > 0
        or len(unregistered_disk_files) > 0
    )

    if total_valid == 0 and len(disk_images_map) == 0 and non_comment_rows == 0:
        overall_status = "NOT STARTED"
        status_description = "Belum ada foto eksternal fisik yang dikumpulkan maupun didaftarkan di manifest."
    elif total_valid == TOTAL_TARGET and not has_blocking_anomalies:
        overall_status = "COMPLETE"
        status_description = "Seluruh target 780 foto telah terkumpul lengkap, tervalidasi, dan bebas anomali."
    elif has_blocking_anomalies:
        overall_status = "NEEDS REVIEW"
        status_description = (
            f"Ditemukan {len(unconsented_records)} unconsented, {len(missing_disk_records)} missing disk, "
            f"{len(unregistered_disk_files)} unregistered disk, {len(duplicate_records)} duplicate, "
            f"{len(invalid_signer_records)} invalid signer, {len(invalid_label_records)} invalid label."
        )
    else:
        overall_status = "IN PROGRESS"
        status_description = f"Pengumpulan sedang berjalan ({total_valid}/{TOTAL_TARGET} foto, {progress_pct}%)."

    # 7. Build summary dictionary
    summary: Dict[str, Any] = {
        "overall_status": overall_status,
        "status_description": status_description,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_info": {
            "actual_manifest_path": str(actual_manifest_path),
            "actual_manifest_exists": actual_manifest_exists,
            "template_manifest_path": str(template_manifest_path),
            "template_manifest_exists": template_manifest_exists,
            "active_manifest_path": str(active_manifest_path),
            "manifest_mode": manifest_mode,
            "status_label": (
                "TERSEDIA & AKTIF (external_manifest.csv ditemukan)"
                if actual_manifest_exists
                else "BELUM DIBUAT (Menggunakan external_manifest_template.csv sebagai fallback referensi)"
            ),
        },
        "total_target": TOTAL_TARGET,
        "total_valid_collected": total_valid,
        "total_shortfall": shortfall,
        "progress_percentage": progress_pct,
        "total_disk_images": len(disk_images_map),
        "total_manifest_raw_rows": total_manifest_raw_rows,
        "total_manifest_data_rows": non_comment_rows,
        "verified_consents_count": total_valid,
        "anomalies": {
            "unconsented_count": len(unconsented_records),
            "missing_disk_count": len(missing_disk_records),
            "unregistered_disk_count": len(unregistered_disk_files),
            "duplicate_count": len(duplicate_records),
            "invalid_signer_count": len(invalid_signer_records),
            "invalid_label_count": len(invalid_label_records),
        },
        "signer_progress": {
            s: {
                "collected": signer_counts[s],
                "target": 260,
                "shortfall": 260 - signer_counts[s],
                "pct": round((signer_counts[s] / 260) * 100.0, 2),
            }
            for s in TARGET_SIGNERS
        },
        "class_progress": {
            c: {
                "collected": label_counts[c],
                "target": 30,
                "shortfall": 30 - label_counts[c],
                "pct": round((label_counts[c] / 30) * 100.0, 2),
            }
            for c in TARGET_CLASSES
        },
        "incomplete_combinations_count": len(incomplete_combinations),
        "incomplete_combinations": incomplete_combinations,
        "unregistered_disk_files": unregistered_disk_files,
        "unconsented_records": unconsented_records,
        "missing_disk_records": missing_disk_records,
        "duplicate_records": duplicate_records,
    }

    # 8. Generate Markdown Report
    if out_report is not None:
        if not out_report.is_absolute():
            out_report = ROOT / out_report
        out_report.parent.mkdir(parents=True, exist_ok=True)
        report_md = _build_markdown_report(summary, data_dir)
        out_report.write_text(report_md, encoding="utf-8")
        logger.info("Laporan progres berhasil ditulis ke %s", out_report)

    # 9. Generate JSON Output
    if out_json is not None:
        if not out_json.is_absolute():
            out_json = ROOT / out_json
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info("Ringkasan JSON berhasil ditulis ke %s", out_json)

    return summary


def _build_markdown_report(summary: Dict[str, Any], data_dir: Path) -> str:
    """Formats progress summary dictionary into GitHub-flavored Markdown report."""
    status = summary["overall_status"]
    status_emoji = {
        "NOT STARTED": "⚪",
        "IN PROGRESS": "🟡",
        "COMPLETE": "🟢",
        "NEEDS REVIEW": "🔴",
    }.get(status, "🔵")

    minfo = summary["manifest_info"]
    actual_path_str = Path(minfo["actual_manifest_path"]).as_posix()
    template_path_str = Path(minfo["template_manifest_path"]).as_posix()
    active_path_str = Path(minfo["active_manifest_path"]).as_posix()
    actual_exists = minfo["actual_manifest_exists"]
    mode = minfo["manifest_mode"]

    lines = [
        "# LAPORAN PROGRES PENGUMPULAN DATA EKSTERNAL BISINDO (I1-P1)",
        "",
        f"**Status Progres**: `{status}` {status_emoji}  ",
        f"**Keterangan**: {summary['status_description']}  ",
        f"**Waktu Pembaruan (UTC)**: `{summary['timestamp_utc']}`  ",
        f"**Direktori Data**: `{data_dir.as_posix()}`  ",
        "",
        "### Identifikasi File Manifest",
        f"- **Manifest aktual**: `{actual_path_str}` — **`{'TERSEDIA & AKTIF 🟢' if actual_exists else 'BELUM DIBUAT ⏳'}`**",
        f"- **Template referensi**: `{template_path_str}` — **`{'STANDBY' if actual_exists else 'DIGUNAKAN SEBAGAI FALLBACK REFERENSI ⚪'}`**",
        f"- **File yang dibaca saat ini**: `{active_path_str}` (Mode: `{mode}`)",
        "",
    ]

    if not actual_exists and mode == "TEMPLATE_FALLBACK":
        lines.extend([
            "> [!IMPORTANT]",
            "> **MANIFEST AKTUAL: `external_manifest.csv` BELUM DIBUAT**  ",
            "> Sistem saat ini membaca `external_manifest_template.csv` murni sebagai fallback referensi skema.  ",
            "> Seluruh baris contoh di dalam template otomatis diabaikan. Untuk memulai pencatatan data riil, operator harus membuat file `external_manifest.csv` dan mengisinya dengan metadata foto nyata.",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## 1. RINGKASAN EKSEKUTIF PROGRES",
        "",
        "| Parameter Evaluasi | Target | Capaian Aktual | Kekurangan (Defisit) | Persentase | Status |",
        "|---|:---:|:---:|:---:|:---:|:---:|",
        f"| **Total Sampel Foto** | **{summary['total_target']}** | **{summary['total_valid_collected']}** | **{summary['total_shortfall']}** | **{summary['progress_percentage']}%** | `{status}` |",
        f"| Foto Penutur `EXT_S01` | 260 | {summary['signer_progress']['EXT_S01']['collected']} | {summary['signer_progress']['EXT_S01']['shortfall']} | {summary['signer_progress']['EXT_S01']['pct']}% | {'🟢 LENGKAP' if summary['signer_progress']['EXT_S01']['collected'] == 260 else '⏳ BELUM LENGKAP'} |",
        f"| Foto Penutur `EXT_S02` | 260 | {summary['signer_progress']['EXT_S02']['collected']} | {summary['signer_progress']['EXT_S02']['shortfall']} | {summary['signer_progress']['EXT_S02']['pct']}% | {'🟢 LENGKAP' if summary['signer_progress']['EXT_S02']['collected'] == 260 else '⏳ BELUM LENGKAP'} |",
        f"| Foto Penutur `EXT_S03` | 260 | {summary['signer_progress']['EXT_S03']['collected']} | {summary['signer_progress']['EXT_S03']['shortfall']} | {summary['signer_progress']['EXT_S03']['pct']}% | {'🟢 LENGKAP' if summary['signer_progress']['EXT_S03']['collected'] == 260 else '⏳ BELUM LENGKAP'} |",
        f"| Kombinasi Penutur-Huruf Lengkap | 78 sel | {78 - summary['incomplete_combinations_count']} sel | {summary['incomplete_combinations_count']} sel | {round(((78 - summary['incomplete_combinations_count']) / 78) * 100, 1)}% | {'🟢 LENGKAP' if summary['incomplete_combinations_count'] == 0 else '⏳ BELUM LENGKAP'} |",
        "",
        "---",
        "",
        "## 2. AUDIT INTEGRITAS & STATUS ANOMALI DATA",
        "",
        "Setiap foto wajib memenuhi informed consent bertanda `CONSENT_SIGNED`, terverifikasi fisiknya di disk, tidak terduplikasi, dan terdaftar dalam manifest.",
        "",
        "| Kategori Audit Integritas | Jumlah Kasus | Status | Keterangan Aturan |",
        "|---|:---:|:---:|---|",
        f"| **Consent Terverifikasi (`CONSENT_SIGNED`)** | **{summary['verified_consents_count']}** | {'🟢 NORMAL' if summary['verified_consents_count'] > 0 else '⚪ BELUM ADA DATA'} | Hanya data dengan persetujuan sah yang dihitung |",
        f"| **Data Ditolak (Consent Tidak Sah/Kosong)** | **{summary['anomalies']['unconsented_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['unconsented_count'] == 0 else '🔴 PERLU PERBAIKAN'} | Ditolak otomatis; dilarang masuk evaluasi |",
        f"| **File Tercatat tapi Tidak Ditemukan di Disk** | **{summary['anomalies']['missing_disk_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['missing_disk_count'] == 0 else '🔴 PERLU PERBAIKAN'} | Baris manifest merujuk path yang belum ada di disk |",
        f"| **File di Disk Belum Tercatat di Manifest** | **{summary['anomalies']['unregistered_disk_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['unregistered_disk_count'] == 0 else '🟡 PERLU REGISTRASI'} | File citra fisik ada tetapi belum didaftarkan di manifest |",
        f"| **Foto Duplikat Ditolak (Path / SHA-256)** | **{summary['anomalies']['duplicate_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['duplicate_count'] == 0 else '🔴 PERLU PERBAIKAN'} | Sampel identik tidak boleh dihitung ganda |",
        f"| **Penutur Tidak Dikenal / Tidak Valid** | **{summary['anomalies']['invalid_signer_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['invalid_signer_count'] == 0 else '🔴 PERLU PERBAIKAN'} | Wajib salah satu dari: EXT_S01, EXT_S02, EXT_S03 |",
        f"| **Label Huruf Tidak Valid** | **{summary['anomalies']['invalid_label_count']}** | {'🟢 AMAN (0)' if summary['anomalies']['invalid_label_count'] == 0 else '🔴 PERLU PERBAIKAN'} | Wajib huruf alfabet kapital A–Z |",
        "",
        "---",
        "",
        "## 3. PROGRES PER KELAS ALFABET (A–Z)",
        "",
        "Setiap huruf memerlukan 30 foto (10 foto × 3 penutur).",
        "",
        "| Huruf | Target Total | Terkumpul | Kekurangan | Capaian (%) | Status |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for c in TARGET_CLASSES:
        cp = summary["class_progress"][c]
        c_status = "🟢 LENGKAP" if cp["collected"] >= 30 else ("🟡 BERJALAN" if cp["collected"] > 0 else "⚪ KOSONG")
        lines.append(f"| **{c}** | 30 | {cp['collected']} | {cp['shortfall']} | {cp['pct']}% | {c_status} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. MATRIKS KOMBINASI PENUTUR × HURUF (78 KOMBINASI)",
        "",
        "Target masing-masing sel adalah **10 foto**.",
        "",
        "| Huruf | `EXT_S01` (Target 10) | `EXT_S02` (Target 10) | `EXT_S03` (Target 10) | Total Terkumpul (Target 30) | Status Baris |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for c in TARGET_CLASSES:
        c1 = next((ic["collected"] for ic in summary["incomplete_combinations"] if ic["signer_id"] == "EXT_S01" and ic["label"] == c), 10)
        c2 = next((ic["collected"] for ic in summary["incomplete_combinations"] if ic["signer_id"] == "EXT_S02" and ic["label"] == c), 10)
        c3 = next((ic["collected"] for ic in summary["incomplete_combinations"] if ic["signer_id"] == "EXT_S03" and ic["label"] == c), 10)
        tot = c1 + c2 + c3

        f1 = f"✅ {c1}/10" if c1 >= 10 else f"⚠️ {c1}/10 (-{10 - c1})"
        f2 = f"✅ {c2}/10" if c2 >= 10 else f"⚠️ {c2}/10 (-{10 - c2})"
        f3 = f"✅ {c3}/10" if c3 >= 10 else f"⚠️ {c3}/10 (-{10 - c3})"
        row_stat = "🟢 LENGKAP" if tot >= 30 else ("🟡 SEBAGIAN" if tot > 0 else "⚪ BELUM ADA")

        lines.append(f"| **{c}** | {f1} | {f2} | {f3} | **{tot}/30** | {row_stat} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. REKOMENDASI OPERATOR LAPANGAN",
        "",
        "> [!IMPORTANT]",
        "> **STATUS SAAT INI: BELUM ADA DATA FISIK EKSTERNAL (0 / 780)**  ",
        "> Seluruh folder A–Z dan template manifest telah disiapkan di `data/external/bisindo_validation/`. Jangan menjalankan evaluasi model sebelum foto fisik terkumpul dan terverifikasi.",
        "",
        "Langkah tindak lanjut pengumpulan data:",
        "1. **Rekrutmen 3 Signer**: Hubungi partisipan baru (`EXT_S01`, `EXT_S02`, `EXT_S03`) dan pastikan formulir informed consent ditandatangani (`CONSENT_SIGNED`).",
        "2. **Sesi Pemotretan**: Ambil foto sesuai [Panduan Operator](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md) dengan target 10 foto per huruf per penutur.",
        "3. **Penyimpanan Foto**: Simpan file di folder kelas masing-masing, misalnya `data/external/bisindo_validation/A/EXT_S01_A_01.jpg`.",
        "4. **Pengisian Manifest**: Daftarkan file ke `data/external/bisindo_validation/external_manifest.csv`.",
        "5. **Pemantauan Berkala**: Jalankan script tracker ini (`python scripts/validation_p1/track_external_collection.py`) untuk memantau pemenuhan kuota kuadran dan mendeteksi anomali secara real-time.",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track External BISINDO Data Collection Progress")
    parser.add_argument("--data-dir", type=str, default="data/external/bisindo_validation")
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--output-report", type=str, default="docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md")
    parser.add_argument("--output-json", type=str, default="docs/validation_p1/external_collection_progress.json")
    args = parser.parse_args()

    track_collection_progress(
        data_dir=Path(args.data_dir),
        manifest_path=Path(args.manifest) if args.manifest else None,
        out_report=Path(args.output_report) if args.output_report else None,
        out_json=Path(args.output_json) if args.output_json else None,
    )
