#!/usr/bin/env python3
"""
calculate_inter_rater_agreement.py

Script analisis metodologis untuk memvalidasi integritas file respons validator (Validator A & B),
menghitung reliabilitas antar-penilai (Inter-Rater Reliability),
mendukung protokol BLIND LETTER IDENTIFICATION (Phase 2C.8) dan mempertahankan kompatibilitas
mundur dengan protokol legacy (Phase 2C.6 / 2C.7).

Mendukung input berformat:
- CSV (.csv)
- Excel Workbook (.xlsx) dengan pembacaan otomatis sheet 'Lembar Penilaian'

Proyek : SignBridge ASEAN - Image Modality I1 (MobileNetV3-Small BISINDO A-Z)
Fase    : Phase 2C.8 (Validator Workbook Redesign & Blind Letter Identification)
"""

import argparse
import sys
import math
import shutil
import warnings
from pathlib import Path
import pandas as pd
import numpy as np

# =============================================================================
# KONSTANTA SKEMA & KATEGORI (PHASE 2C.8 STANDARD)
# =============================================================================

# Skema Standar V2 (Blind Letter Identification)
EXPECTED_COLUMNS_V2 = [
    "validator_code",
    "sample_id",
    "identified_letter",
    "decision",
    "regional_variation",
    "notes",
    "review_date",
]
VALID_DECISIONS_V2 = {"IDENTIFIED", "AMBIGUOUS", "UNDETERMINABLE"}
VALID_LETTERS = set([chr(c) for c in range(ord("A"), ord("Z") + 1)])
VALID_REGIONAL = {"YES", "NO", "UNSURE", ""}

# Skema Legacy V1 (Verification Rubric)
EXPECTED_COLUMNS_V1 = [
    "validator_code",
    "sample_id",
    "decision",
    "correct_letter",
    "regional_variation",
    "notes",
    "review_date",
]
VALID_DECISIONS_V1 = {"CORRECT", "INCORRECT", "AMBIGUOUS", "UNDETERMINABLE"}

# Pemetaan Kolom Excel Indonesia -> Standard Internal
EXCEL_COL_MAPPING = {
    "Kode Validator": "validator_code",
    "ID Sampel": "sample_id",
    "Huruf Teridentifikasi (A–Z)": "identified_letter",
    "Huruf Teridentifikasi (A-Z)": "identified_letter",
    "Huruf Teridentifikasi": "identified_letter",
    "Kejelasan Isyarat (Decision)": "decision",
    "Kejelasan Isyarat": "decision",
    "Decision": "decision",
    "Variasi Regional": "regional_variation",
    "Catatan / Keterangan Validator": "notes",
    "Catatan / Keterangan": "notes",
    "Catatan": "notes",
    "Tanggal Review (YYYY-MM-DD)": "review_date",
    "Tanggal Review": "review_date",
}

# Aliases untuk kompatibilitas mundur
EXPECTED_COLUMNS = EXPECTED_COLUMNS_V2
VALID_DECISIONS = VALID_DECISIONS_V2


# =============================================================================
# DEFINISI STATUS INGESTI & PENYIMPANAN RESMI (PHASE 2C.7 / 2C.8)
# =============================================================================

class ValidationStatusEnum:
    EMPTY_TEMPLATE = "EMPTY_TEMPLATE"
    INCOMPLETE_PENDING_COMPLETION = "INCOMPLETE_PENDING_COMPLETION"
    SCHEMA_ERROR = "SCHEMA_ERROR"
    VALID_COMPLETE_RESPONSE = "VALID_COMPLETE_RESPONSE"


class StorageStatusEnum:
    RAW_PRESERVED = "RAW_PRESERVED"
    QUARANTINED = "QUARANTINED"
    WORKING_COPY_CREATED = "WORKING_COPY_CREATED"


IngestionStatus = ValidationStatusEnum
StorageStatus = StorageStatusEnum


class ValidationStatus(str):
    """
    Subclass string untuk mempertahankan kompatibilitas mundur dengan assertion string
    (misal == 'VALID', 'STATUS_PENDING' in stat, dll) sembari menyertakan
    kategori status formal ValidationStatus, StorageStatus, schema_version, dan rincian pesan.
    """
    def __new__(
        cls,
        value,
        category,
        storage_status=StorageStatusEnum.RAW_PRESERVED,
        schema_version="SCHEMA_V2_BLIND_IDENTIFICATION",
        detail="",
    ):
        obj = str.__new__(cls, value)
        obj.category = category
        obj.validation_status = category
        obj.storage_status = storage_status
        obj.schema_version = schema_version
        obj.detail = detail
        return obj


# =============================================================================
# PEMETAAN KOHORT & KUNCI DEKRIPSI GROUND TRUTH INTERNAL (CONFIDENTIAL)
# Hanya digunakan oleh skrip analisis internal, tidak pernah diekspos ke validator!
# =============================================================================

COHORT_MAPPING = {
    "VAL-REV-001": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-002": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-003": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-004": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-005": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-006": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-007": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-008": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-009": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-010": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-011": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-012": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-013": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-014": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-015": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-016": "TRAIN_COHORT",
    "VAL-REV-017": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-018": "TRAIN_COHORT",
    "VAL-REV-019": "TRAIN_COHORT",
    "VAL-REV-020": "TRAIN_COHORT",
    "VAL-REV-021": "TRAIN_COHORT",
    "VAL-REV-022": "TRAIN_COHORT",
    "VAL-REV-023": "TRAIN_COHORT",
    "VAL-REV-024": "TRAIN_COHORT",
    "VAL-REV-025": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-026": "TRAIN_COHORT",
    "VAL-REV-027": "TRAIN_COHORT",
    "VAL-REV-028": "TRAIN_COHORT",
    "VAL-REV-029": "TRAIN_COHORT",
    "VAL-REV-030": "TRAIN_COHORT",
    "VAL-REV-031": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-032": "TEST_SET_DIAGNOSTIC_ONLY",
    "VAL-REV-033": "TRAIN_COHORT",
    "VAL-REV-034": "TRAIN_COHORT",
    "VAL-REV-035": "TRAIN_COHORT",
    "VAL-REV-036": "TRAIN_COHORT",
}

INTERNAL_GROUND_TRUTH = {
    "VAL-REV-001": "K",
    "VAL-REV-002": "C",
    "VAL-REV-003": "Y",
    "VAL-REV-004": "R",
    "VAL-REV-005": "M",
    "VAL-REV-006": "O",
    "VAL-REV-007": "D",
    "VAL-REV-008": "N",
    "VAL-REV-009": "J",
    "VAL-REV-010": "E",
    "VAL-REV-011": "F",
    "VAL-REV-012": "N",
    "VAL-REV-013": "T",
    "VAL-REV-014": "E",
    "VAL-REV-015": "B",
    "VAL-REV-016": "Z",
    "VAL-REV-017": "O",
    "VAL-REV-018": "C",
    "VAL-REV-019": "Z",
    "VAL-REV-020": "V",
    "VAL-REV-021": "B",
    "VAL-REV-022": "C",
    "VAL-REV-023": "C",
    "VAL-REV-024": "D",
    "VAL-REV-025": "H",
    "VAL-REV-026": "Z",
    "VAL-REV-027": "Z",
    "VAL-REV-028": "O",
    "VAL-REV-029": "O",
    "VAL-REV-030": "M",
    "VAL-REV-031": "U",
    "VAL-REV-032": "A",
    "VAL-REV-033": "B",
    "VAL-REV-034": "L",
    "VAL-REV-035": "O",
    "VAL-REV-036": "Y",
}


# =============================================================================
# INGESTION & VALIDATION ENGINE
# =============================================================================

def load_and_validate_response(file_path: Path, expected_val_code: str):
    """
    Memuat dan memeriksa integritas skema file respons validator (CSV atau XLSX).
    Secara otomatis mendeteksi apakah berkas menggunakan:
    - SCHEMA_V2_BLIND_IDENTIFICATION (Standar Phase 2C.8)
    - SCHEMA_V1_LEGACY_VERIFICATION (Legacy Phase 2C.6 / 2C.7)
    Mengembalikan tuple (DataFrame, ValidationStatus).
    """
    if not file_path.exists():
        return None, ValidationStatus(
            f"FILE_NOT_FOUND: {file_path}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            detail=f"File {file_path} tidak ditemukan",
        )

    # 1. Pemuatan Data (CSV atau XLSX)
    try:
        if file_path.suffix.lower() == ".xlsx":
            # Baca sheet 'Lembar Penilaian' jika ada, fallback ke sheet pertama
            xl = pd.ExcelFile(file_path)
            sheet_name = "Lembar Penilaian" if "Lembar Penilaian" in xl.sheet_names else xl.sheet_names[0]
            # Di Lembar Penilaian, baris 1 adalah judul, baris 2 adalah header (header=1)
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
            # Normalisasi nama kolom dari bahasa Indonesia ke nama kolom internal
            col_renames = {}
            for c in df_raw.columns:
                c_str = str(c).strip()
                if c_str in EXCEL_COL_MAPPING:
                    col_renames[c] = EXCEL_COL_MAPPING[c_str]
            df = df_raw.rename(columns=col_renames)
            # Filter hanya kolom yang relevan
            cols_to_keep = [c for c in EXPECTED_COLUMNS_V2 if c in df.columns]
            if not cols_to_keep:
                cols_to_keep = [c for c in EXPECTED_COLUMNS_V1 if c in df.columns]
            df = df[cols_to_keep].copy() if cols_to_keep else df
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        return None, ValidationStatus(
            f"PARSE_ERROR: Gagal membaca file ({e})",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            detail=str(e),
        )

    # 2. Deteksi Versi Skema
    if "identified_letter" in df.columns:
        schema_version = "SCHEMA_V2_BLIND_IDENTIFICATION"
        expected_cols = EXPECTED_COLUMNS_V2
        valid_decisions = VALID_DECISIONS_V2
    elif "correct_letter" in df.columns:
        schema_version = "SCHEMA_V1_LEGACY_VERIFICATION"
        expected_cols = EXPECTED_COLUMNS_V1
        valid_decisions = VALID_DECISIONS_V1
    else:
        # Default fallback untuk pengecekan missing cols
        schema_version = "SCHEMA_V2_BLIND_IDENTIFICATION"
        expected_cols = EXPECTED_COLUMNS_V2
        valid_decisions = VALID_DECISIONS_V2

    # 3. Validasi struktur kolom
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        return None, ValidationStatus(
            f"SCHEMA_ERROR: Kolom wajib hilang pada {file_path.name}: {missing_cols}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"Kolom hilang: {missing_cols}",
        )

    extra_cols = [c for c in df.columns if c not in expected_cols]
    if extra_cols:
        return None, ValidationStatus(
            f"SCHEMA_ERROR: Kolom tak dikenal pada {file_path.name}: {extra_cols}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"Kolom asing: {extra_cols}",
        )

    # 4. Validasi jumlah baris (tepat 36 sampel)
    if len(df) != 36:
        return None, ValidationStatus(
            f"ROW_COUNT_MISMATCH: Jumlah sampel pada {file_path.name} tidak sesuai ({len(df)} != 36)",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"Jumlah baris: {len(df)} (harus 36)",
        )

    # 5. Validasi sample_id kelengkapan, keunikan, dan urutan
    expected_ids = [f"VAL-REV-{i:03d}" for i in range(1, 37)]
    actual_ids = list(df["sample_id"].astype(str).str.strip())

    if len(set(actual_ids)) != 36:
        duplicates = [sid for sid in set(actual_ids) if actual_ids.count(sid) > 1]
        return None, ValidationStatus(
            f"DUPLICATE_ID: Ditemukan sample_id duplikat pada {file_path.name}: {duplicates}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"ID duplikat: {duplicates}",
        )

    if actual_ids != expected_ids:
        missing_ids = set(expected_ids) - set(actual_ids)
        return None, ValidationStatus(
            f"ID_SEQUENCE_ERROR: Urutan atau kelengkapan sample_id tidak valid pada {file_path.name}. Hilang: {missing_ids}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"ID hilang/urutan salah: {missing_ids}",
        )

    # 6. Validasi validator code
    val_codes = set(df["validator_code"].dropna().astype(str).str.strip().unique())
    if not val_codes or val_codes != {expected_val_code}:
        return None, ValidationStatus(
            f"VALIDATOR_CODE_MISMATCH: validator_code tidak sesuai pada {file_path.name} ({val_codes} != {{{expected_val_code}}})",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"Kode validator: {val_codes} (harus {{{expected_val_code}}})",
        )

    # 7. Cek kelengkapan pengisian (Kosong Murni vs Terisi Sebagian)
    dec_series = df["decision"].astype(str).str.strip()
    empty_decisions = df["decision"].isna() | (dec_series == "") | (dec_series == "nan")
    num_empty = int(empty_decisions.sum())

    if num_empty == 36:
        return df, ValidationStatus(
            f"STATUS_PENDING: Seluruh keputusan (36/36) masih kosong pada {file_path.name}",
            category=ValidationStatusEnum.EMPTY_TEMPLATE,
            schema_version=schema_version,
            detail="Berkas template awal kosong murni (36/36 belum diisi)",
        )
    elif num_empty > 0:
        missing_samples = df.loc[empty_decisions, "sample_id"].tolist()
        return None, ValidationStatus(
            f"PARTIALLY_FILLED_ERROR: {num_empty}/36 keputusan belum diisi pada {file_path.name} (Sampel: {missing_samples[:5]}...)",
            category=ValidationStatusEnum.INCOMPLETE_PENDING_COMPLETION,
            schema_version=schema_version,
            detail=f"{num_empty} sampel belum terisi",
        )

    # 8. Validasi nilai enum keputusan
    invalid_mask = ~df["decision"].isin(valid_decisions)
    if invalid_mask.any():
        bad_samples = df.loc[invalid_mask, ["sample_id", "decision"]].to_dict(orient="records")
        return None, ValidationStatus(
            f"INVALID_ENUM_ERROR: Keputusan tidak valid pada {file_path.name}: {bad_samples}",
            category=ValidationStatusEnum.SCHEMA_ERROR,
            schema_version=schema_version,
            detail=f"Enum tidak valid untuk {schema_version}: {bad_samples}",
        )

    # 9. Validasi logis bersyarat per skema
    if schema_version == "SCHEMA_V2_BLIND_IDENTIFICATION":
        # Aturan V2:
        # a. Jika decision == 'IDENTIFIED', identified_letter wajib terisi huruf valid A-Z
        identified_mask = df["decision"] == "IDENTIFIED"
        if identified_mask.any():
            missing_letters = []
            invalid_letters = []
            for idx, row in df[identified_mask].iterrows():
                let = str(row.get("identified_letter", "")).strip().upper()
                if not let or let == "NAN":
                    missing_letters.append(row["sample_id"])
                elif let not in VALID_LETTERS:
                    invalid_letters.append((row["sample_id"], let))
            if missing_letters:
                return None, ValidationStatus(
                    f"MISSING_IDENTIFIED_LETTER: Keputusan IDENTIFIED tanpa huruf pada sampel: {missing_letters}",
                    category=ValidationStatusEnum.SCHEMA_ERROR,
                    schema_version=schema_version,
                    detail=f"IDENTIFIED tanpa huruf pada {missing_letters}",
                )
            if invalid_letters:
                return None, ValidationStatus(
                    f"INVALID_LETTER_ERROR: Huruf di luar A-Z pada sampel: {invalid_letters}",
                    category=ValidationStatusEnum.SCHEMA_ERROR,
                    schema_version=schema_version,
                    detail=f"Huruf tidak valid: {invalid_letters}",
                )

        # b. Jika decision == 'UNDETERMINABLE', identified_letter sebaiknya kosong
        undet_mask = df["decision"] == "UNDETERMINABLE"
        if undet_mask.any():
            for idx, row in df[undet_mask].iterrows():
                let = str(row.get("identified_letter", "")).strip().upper()
                if let and let != "NAN":
                    # Peringatan lunak: bersihkan huruf pada UNDETERMINABLE agar konsisten
                    df.at[idx, "identified_letter"] = ""

    elif schema_version == "SCHEMA_V1_LEGACY_VERIFICATION":
        # Aturan V1: INCORRECT wajib menyertakan correct_letter
        incorrect_mask = df["decision"] == "INCORRECT"
        if incorrect_mask.any():
            missing_letters = []
            for idx, row in df[incorrect_mask].iterrows():
                c_let = str(row.get("correct_letter", "")).strip().upper()
                if not c_let or c_let == "NAN":
                    missing_letters.append(row["sample_id"])
            if missing_letters:
                return None, ValidationStatus(
                    f"MISSING_CORRECT_LETTER: Keputusan INCORRECT tanpa huruf koreksi pada sampel: {missing_letters}",
                    category=ValidationStatusEnum.SCHEMA_ERROR,
                    schema_version=schema_version,
                    detail=f"INCORRECT tanpa huruf koreksi pada {missing_letters}",
                )

    df.attrs["schema_version"] = schema_version

    return df, ValidationStatus(
        "VALID",
        category=ValidationStatusEnum.VALID_COMPLETE_RESPONSE,
        schema_version=schema_version,
        detail=f"Seluruh 36 rekaman valid ({schema_version})",
    )


def quarantine_file(file_path: Path, quarantine_dir: Path, reason: str) -> Path:
    """
    Menyalin berkas yang tidak valid ke direktori karantina tanpa menghapus
    berkas sumber asli untuk menjaga rantai bukti forensik (chain of custody).
    """
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    target_path = quarantine_dir / f"QUARANTINED_{file_path.name}"
    shutil.copy2(file_path, target_path)
    return target_path


def create_working_copies_if_valid(
    path_a: Path,
    path_b: Path,
    dest_dir: Path = Path("docs/validation_p2/phase_2c"),
) -> tuple[bool, str]:
    """
    Membuat working copy hanya ketika kedua file respons terbukti VALID_COMPLETE_RESPONSE.
    Mencegah pencemaran working copy oleh template kosong, berkas parsial, atau berkas korup.
    """
    _, stat_a = load_and_validate_response(path_a, "VAL-A")
    _, stat_b = load_and_validate_response(path_b, "VAL-B")

    if stat_a.category != ValidationStatusEnum.VALID_COMPLETE_RESPONSE:
        return False, f"Penolakan Working Copy: File A berstatus {stat_a.category} ({stat_a})"
    if stat_b.category != ValidationStatusEnum.VALID_COMPLETE_RESPONSE:
        return False, f"Penolakan Working Copy: File B berstatus {stat_b.category} ({stat_b})"

    ext_a = path_a.suffix.lower()
    ext_b = path_b.suffix.lower()
    target_a = dest_dir / f"VALIDATOR_A_RESPONSE_ACTUAL{ext_a}"
    target_b = dest_dir / f"VALIDATOR_B_RESPONSE_ACTUAL{ext_b}"

    # Jika salah satu CSV, pastikan juga CSV actual tersedia untuk analisis downstream
    shutil.copy2(path_a, target_a)
    shutil.copy2(path_b, target_b)

    return True, f"Working copy berhasil dibuat:\n- {target_a}\n- {target_b}"


# =============================================================================
# STATISTICAL ENGINE & METRICS COMPUTATION
# =============================================================================

def compute_bootstrap_kappa(
    y_a: list,
    y_b: list,
    labels: list,
    n_replications: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict:
    """
    Menghitung 95% Confidence Interval untuk Cohen's Kappa menggunakan
    Paired Bootstrap Resampling berpasangan per sample_id.
    """
    rng = np.random.RandomState(seed)
    n = len(y_a)
    y_a_arr = np.array(y_a)
    y_b_arr = np.array(y_b)

    kappas = []
    undefined_count = 0

    for _ in range(n_replications):
        idx = rng.randint(0, n, size=n)
        sample_a = y_a_arr[idx]
        sample_b = y_b_arr[idx]

        pe = sum((np.sum(sample_a == l) / n) * (np.sum(sample_b == l) / n) for l in labels)
        po = np.sum(sample_a == sample_b) / n

        if abs(1.0 - pe) < 1e-9:
            undefined_count += 1
            continue

        k = (po - pe) / (1.0 - pe)
        if np.isnan(k):
            undefined_count += 1
        else:
            kappas.append(k)

    if kappas:
        low_pct = (alpha / 2.0) * 100.0
        high_pct = (1.0 - alpha / 2.0) * 100.0
        ci_low = float(np.percentile(kappas, low_pct))
        ci_high = float(np.percentile(kappas, high_pct))
        mean_k = float(np.mean(kappas))
        std_k = float(np.std(kappas))
        status = "CALCULATED"
        ci_tuple = (round(ci_low, 4), round(ci_high, 4))
    else:
        ci_tuple = None
        mean_k = None
        std_k = None
        status = "UNDEFINED_ZERO_VARIANCE_IN_ALL_BOOTSTRAPS"

    return {
        "n_replications": n_replications,
        "valid_replications": len(kappas),
        "undefined_replications": undefined_count,
        "bootstrap_seed": seed,
        "bootstrap_ci_95": ci_tuple,
        "bootstrap_mean": round(mean_k, 4) if mean_k is not None else None,
        "bootstrap_std": round(std_k, 4) if std_k is not None else None,
        "bootstrap_status": status,
    }


def compute_metrics(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    bootstrap_reps: int = 2000,
    bootstrap_seed: int = 42,
):
    """
    Menghitung metrik reliabilitas inter-rater:
    - Mendukung SCHEMA_V2_BLIND_IDENTIFICATION (Phase 2C.8):
      1. Independent Letter Identification Agreement (Val A vs Val B)
      2. Gesture Clarity Agreement (IDENTIFIED, AMBIGUOUS, UNDETERMINABLE) + Paired Bootstrap CI
      3. Regional Variation Agreement
      4. Internal Ground-Truth Comparison (Research Audit)
      5. Ekstraksi Kasus Adjudikasi Validator C
    - Mendukung SCHEMA_V1_LEGACY_VERIFICATION untuk kompatibilitas mundur.
    """
    from sklearn.metrics import cohen_kappa_score, confusion_matrix

    ids_a = list(df_a["sample_id"].astype(str).str.strip())
    ids_b = list(df_b["sample_id"].astype(str).str.strip())
    if ids_a != ids_b:
        raise ValueError("SAMPLE_ALIGNMENT_ERROR: Sample ID Validator A dan B tidak selaras!")

    total_n = len(df_a)
    is_v2 = "identified_letter" in df_a.columns and "identified_letter" in df_b.columns

    # =========================================================================
    # ANALISIS SKEMA V2 (BLIND LETTER IDENTIFICATION - STANDAR 2C.8)
    # =========================================================================
    if is_v2:
        # A. INDEPENDENT LETTER AGREEMENT (VAL A VS VAL B)
        letters_a = [str(x).strip().upper() if pd.notna(x) and str(x).strip().upper() != "NAN" else "" for x in df_a["identified_letter"]]
        letters_b = [str(x).strip().upper() if pd.notna(x) and str(x).strip().upper() != "NAN" else "" for x in df_b["identified_letter"]]

        both_letters_mask = [bool(a and b) for a, b in zip(letters_a, letters_b)]
        n_both_letters = sum(both_letters_mask)

        letter_matches = [bool(a == b and a != "") for a, b in zip(letters_a, letters_b)]
        n_letter_matches = sum(letter_matches)
        n_letter_divergent = n_both_letters - n_letter_matches

        letter_agreement_rate = (n_letter_matches / n_both_letters) if n_both_letters > 0 else None
        overall_letter_match_rate = n_letter_matches / total_n

        # Letter confusion matrix untuk sampel yang keduanya mengisi huruf
        unique_letters_eval = sorted(list(set([a for a in letters_a if a] + [b for b in letters_b if b])))
        if unique_letters_eval:
            filtered_a = [a for a, m in zip(letters_a, both_letters_mask) if m]
            filtered_b = [b for b, m in zip(letters_b, both_letters_mask) if m]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                letter_cm = confusion_matrix(filtered_a, filtered_b, labels=unique_letters_eval).tolist()
        else:
            letter_cm = []

        letter_discrepant_ids = [
            ids_a[i] for i in range(total_n)
            if (letters_a[i] != letters_b[i]) and (letters_a[i] != "" or letters_b[i] != "")
        ]

        # B. GESTURE CLARITY / DECISION AGREEMENT (IDENTIFIED, AMBIGUOUS, UNDETERMINABLE)
        y_a = df_a["decision"].tolist()
        y_b = df_b["decision"].tolist()
        clarity_labels = sorted(list(VALID_DECISIONS_V2))

        clarity_agreements = [a == b for a, b in zip(y_a, y_b)]
        p_o_clarity = sum(clarity_agreements) / total_n

        freq_a = {l: y_a.count(l) for l in clarity_labels}
        freq_b = {l: y_b.count(l) for l in clarity_labels}
        p_e_clarity = sum((freq_a[l] / total_n) * (freq_b[l] / total_n) for l in clarity_labels)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kappa_clarity = cohen_kappa_score(y_a, y_b, labels=clarity_labels)

        kappa_ci_95 = None
        kappa_se = None
        kappa_status = "CALCULATED"

        if np.isnan(kappa_clarity) or abs(1.0 - p_e_clarity) < 1e-9:
            kappa_clarity = None
            kappa_status = "UNDEFINED_ZERO_VARIANCE (Tingkat kesepakatan 100%, varians rating nihil)"
        else:
            var_k = (p_o_clarity * (1.0 - p_o_clarity)) / (total_n * ((1.0 - p_e_clarity) ** 2)) if (1.0 - p_e_clarity) > 0 else 0
            if var_k > 0:
                kappa_se = math.sqrt(var_k)
                ci_low = max(-1.0, kappa_clarity - 1.96 * kappa_se)
                ci_high = min(1.0, kappa_clarity + 1.96 * kappa_se)
                kappa_ci_95 = (round(ci_low, 4), round(ci_high, 4))
            else:
                kappa_se = 0.0
                kappa_ci_95 = (round(kappa_clarity, 4), round(kappa_clarity, 4))

        boot_res = compute_bootstrap_kappa(
            y_a, y_b, clarity_labels, n_replications=bootstrap_reps, seed=bootstrap_seed
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clarity_cm = confusion_matrix(y_a, y_b, labels=clarity_labels).tolist()

        # C. REGIONAL VARIATION AGREEMENT
        reg_a = [str(x).strip().upper() if pd.notna(x) else "" for x in df_a.get("regional_variation", [""] * total_n)]
        reg_b = [str(x).strip().upper() if pd.notna(x) else "" for x in df_b.get("regional_variation", [""] * total_n)]
        reg_matches = sum(1 for a, b in zip(reg_a, reg_b) if a == b)
        reg_agreement_rate = reg_matches / total_n

        # D. INTERNAL GROUND-TRUTH COMPARISON (RESEARCH AUDIT ONLY)
        gt_comparison = []
        for i in range(total_n):
            sid = ids_a[i]
            gt = INTERNAL_GROUND_TRUTH.get(sid, "")
            let_a = letters_a[i]
            let_b = letters_b[i]
            cohort = COHORT_MAPPING.get(sid, "UNKNOWN")

            match_a = (let_a == gt) if let_a else False
            match_b = (let_b == gt) if let_b else False
            consensus_match = (let_a == let_b == gt) if (let_a and let_b) else False
            potential_error = (let_a == let_b != gt) if (let_a and let_b and let_a != "") else False

            gt_comparison.append({
                "sample_id": sid,
                "cohort": cohort,
                "ground_truth": gt,
                "val_a_letter": let_a,
                "val_b_letter": let_b,
                "val_a_match_gt": match_a,
                "val_b_match_gt": match_b,
                "consensus_match_gt": consensus_match,
                "potential_dataset_error": potential_error,
            })

        n_val_a_gt = sum(1 for c in gt_comparison if c["val_a_match_gt"])
        n_val_b_gt = sum(1 for c in gt_comparison if c["val_b_match_gt"])
        n_consensus_gt = sum(1 for c in gt_comparison if c["consensus_match_gt"])
        potential_error_samples = [c["sample_id"] for c in gt_comparison if c["potential_dataset_error"]]

        # E. ADJUDICATION CASES (TRIGGERS ESKALASI VALIDATOR C)
        discrepancies = []
        for i in range(total_n):
            sid = ids_a[i]
            dec_a = y_a[i]
            dec_b = y_b[i]
            let_a = letters_a[i]
            let_b = letters_b[i]
            r_a = reg_a[i]
            r_b = reg_b[i]
            notes_a = str(df_a.iloc[i].get("notes", "")).strip()
            notes_b = str(df_b.iloc[i].get("notes", "")).strip()
            cohort = COHORT_MAPPING.get(sid, "UNKNOWN")
            gt = INTERNAL_GROUND_TRUTH.get(sid, "")

            reasons = []
            if let_a != let_b and (let_a != "" or let_b != ""):
                reasons.append(f"Letter divergence (Val A: '{let_a}' vs Val B: '{let_b}')")
            if dec_a != dec_b:
                reasons.append(f"Clarity divergence ({dec_a} vs {dec_b})")
            if dec_a in {"AMBIGUOUS", "UNDETERMINABLE"} or dec_b in {"AMBIGUOUS", "UNDETERMINABLE"}:
                reasons.append(f"Ambiguity/Indeterminacy flag ({dec_a} / {dec_b})")
            if r_a and r_b and (r_a != r_b):
                reasons.append(f"Regional variation divergence ({r_a} vs {r_b})")
            if (let_a == let_b != "") and (let_a != gt):
                reasons.append(f"Consensus differs from Ground Truth ('{let_a}' != GT '{gt}')")

            if reasons:
                discrepancies.append({
                    "sample_id": sid,
                    "cohort": cohort,
                    "val_a_decision": dec_a,
                    "val_a_letter": let_a,
                    "val_a_regional": r_a,
                    "val_b_decision": dec_b,
                    "val_b_letter": let_b,
                    "val_b_regional": r_b,
                    "reasons": "; ".join(reasons),
                    "notes_a": notes_a if notes_a != "nan" else "",
                    "notes_b": notes_b if notes_b != "nan" else "",
                })

        # Breakdown Kohort
        train_mask = [COHORT_MAPPING.get(s) == "TRAIN_COHORT" for s in ids_a]
        test_mask = [COHORT_MAPPING.get(s) == "TEST_SET_DIAGNOSTIC_ONLY" for s in ids_a]

        def cohort_stats_v2(mask):
            c_a = [letters_a[i] for i, m in enumerate(mask) if m]
            c_b = [letters_b[i] for i, m in enumerate(mask) if m]
            c_matches = sum(1 for a, b in zip(c_a, c_b) if a == b and a != "")
            c_both = sum(1 for a, b in zip(c_a, c_b) if a and b)
            c_agr = (c_matches / c_both) if c_both > 0 else 0.0
            return c_agr, len(c_a), c_matches, c_both

        train_agr, n_train, tr_m, tr_b = cohort_stats_v2(train_mask)
        test_agr, n_test, te_m, te_b = cohort_stats_v2(test_mask)

        return {
            "schema_version": "SCHEMA_V2_BLIND_IDENTIFICATION",
            "total_samples": total_n,
            "letter_identification_agreement": {
                "both_identified_count": n_both_letters,
                "matches_count": n_letter_matches,
                "divergent_count": n_letter_divergent,
                "agreement_rate": letter_agreement_rate,
                "overall_sample_rate": overall_letter_match_rate,
                "divergent_sample_ids": letter_discrepant_ids,
                "confusion_matrix": letter_cm,
                "labels": unique_letters_eval,
            },
            "gesture_clarity_agreement": {
                "observed_agreement": p_o_clarity,
                "p_e": p_e_clarity,
                "cohen_kappa": kappa_clarity,
                "cohen_kappa_se": kappa_se,
                "cohen_kappa_ci_95": kappa_ci_95,
                "cohen_kappa_status": kappa_status,
                "bootstrap": boot_res,
                "confusion_matrix": clarity_cm,
                "labels": clarity_labels,
                "marginal_a": freq_a,
                "marginal_b": freq_b,
            },
            # Alias untuk kompatibilitas ke downstream code
            "decision_agreement": {
                "observed_agreement": p_o_clarity,
                "p_e": p_e_clarity,
                "cohen_kappa": kappa_clarity,
                "cohen_kappa_se": kappa_se,
                "cohen_kappa_ci_95": kappa_ci_95,
                "cohen_kappa_status": kappa_status,
                "bootstrap": boot_res,
                "confusion_matrix": clarity_cm,
                "labels": clarity_labels,
                "marginal_a": freq_a,
                "marginal_b": freq_b,
            },
            "regional_variation_agreement": {
                "observed_agreement": reg_agreement_rate,
                "matches_count": reg_matches,
            },
            "ground_truth_comparison": {
                "val_a_matches": n_val_a_gt,
                "val_b_matches": n_val_b_gt,
                "consensus_matches": n_consensus_gt,
                "potential_dataset_error_count": len(potential_error_samples),
                "potential_dataset_error_sample_ids": potential_error_samples,
                "details": gt_comparison,
            },
            "denominators": {
                "total_evaluated": total_n,
                "both_identified_count": n_both_letters,
                "both_letter_matches_count": n_letter_matches,
                "letter_divergent_count": n_letter_divergent,
                "letter_divergent_ids": letter_discrepant_ids,
                "clarity_matches_count": sum(clarity_agreements),
            },
            "discrepancies": discrepancies,
            "num_discrepancies": len(discrepancies),
            "cohort_breakdown": {
                "TRAIN_COHORT": {"count": n_train, "agreement": train_agr, "matches": tr_m, "both_identified": tr_b},
                "TEST_SET_DIAGNOSTIC_ONLY": {"count": n_test, "agreement": test_agr, "matches": te_m, "both_identified": te_b},
            },
        }

    # =========================================================================
    # ANALISIS SKEMA V1 (LEGACY COMPATIBILITY MODE)
    # =========================================================================
    else:
        y_a = df_a["decision"].tolist()
        y_b = df_b["decision"].tolist()
        agreements = [a == b for a, b in zip(y_a, y_b)]
        p_o = sum(agreements) / total_n

        labels = sorted(list(VALID_DECISIONS_V1))
        freq_a = {l: y_a.count(l) for l in labels}
        freq_b = {l: y_b.count(l) for l in labels}
        p_e = sum((freq_a[l] / total_n) * (freq_b[l] / total_n) for l in labels)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kappa = cohen_kappa_score(y_a, y_b, labels=labels)

        kappa_ci_95 = None
        kappa_se = None
        kappa_status = "CALCULATED"

        if np.isnan(kappa) or abs(1.0 - p_e) < 1e-9:
            kappa = None
            kappa_status = "UNDEFINED_ZERO_VARIANCE"
        else:
            var_k = (p_o * (1.0 - p_o)) / (total_n * ((1.0 - p_e) ** 2)) if (1.0 - p_e) > 0 else 0
            if var_k > 0:
                kappa_se = math.sqrt(var_k)
                ci_low = max(-1.0, kappa - 1.96 * kappa_se)
                ci_high = min(1.0, kappa + 1.96 * kappa_se)
                kappa_ci_95 = (round(ci_low, 4), round(ci_high, 4))
            else:
                kappa_se = 0.0
                kappa_ci_95 = (round(kappa, 4), round(kappa, 4))

        boot_res = compute_bootstrap_kappa(
            y_a, y_b, labels, n_replications=bootstrap_reps, seed=bootstrap_seed
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cm = confusion_matrix(y_a, y_b, labels=labels).tolist()

        # Correct letter agreement for both INCORRECT
        both_incorrect_cases = []
        for idx in range(total_n):
            dec_a = df_a.iloc[idx]["decision"]
            dec_b = df_b.iloc[idx]["decision"]
            if dec_a == "INCORRECT" and dec_b == "INCORRECT":
                sid = df_a.iloc[idx]["sample_id"]
                let_a = str(df_a.iloc[idx].get("correct_letter", "")).strip().upper()
                let_b = str(df_b.iloc[idx].get("correct_letter", "")).strip().upper()
                if let_a == "NAN":
                    let_a = ""
                if let_b == "NAN":
                    let_b = ""
                matches = (let_a == let_b) and (len(let_a) > 0)
                both_incorrect_cases.append({
                    "sample_id": sid,
                    "cohort": COHORT_MAPPING.get(sid, "UNKNOWN"),
                    "let_a": let_a,
                    "let_b": let_b,
                    "matches": matches,
                })

        n_both_incorrect = len(both_incorrect_cases)
        n_letter_matches = sum(1 for c in both_incorrect_cases if c["matches"])
        n_letter_divergent = n_both_incorrect - n_letter_matches
        letter_agreement_rate = (n_letter_matches / n_both_incorrect) if n_both_incorrect > 0 else None
        letter_discrepant_ids = [c["sample_id"] for c in both_incorrect_cases if not c["matches"]]

        # Discrepancies
        discrepancies = []
        for idx in range(total_n):
            sid = df_a.iloc[idx]["sample_id"]
            dec_a = df_a.iloc[idx]["decision"]
            dec_b = df_b.iloc[idx]["decision"]
            let_a = str(df_a.iloc[idx].get("correct_letter", "")).strip().upper()
            let_b = str(df_b.iloc[idx].get("correct_letter", "")).strip().upper()
            cohort = COHORT_MAPPING.get(sid, "UNKNOWN")
            reasons = []
            if dec_a != dec_b:
                reasons.append(f"Decision divergence ({dec_a} vs {dec_b})")
            if dec_a == "INCORRECT" and dec_b == "INCORRECT" and let_a != let_b:
                reasons.append(f"Alternative letter mismatch ({let_a} vs {let_b})")
            if dec_a in {"AMBIGUOUS", "UNDETERMINABLE"} or dec_b in {"AMBIGUOUS", "UNDETERMINABLE"}:
                reasons.append(f"Ambiguity/Indeterminacy flag ({dec_a} / {dec_b})")
            if reasons:
                discrepancies.append({
                    "sample_id": sid,
                    "cohort": cohort,
                    "val_a_decision": dec_a,
                    "val_a_letter": let_a,
                    "val_a_regional": "",
                    "val_b_decision": dec_b,
                    "val_b_letter": let_b,
                    "val_b_regional": "",
                    "reasons": "; ".join(reasons),
                    "notes_a": "",
                    "notes_b": "",
                })

        # Breakdown
        train_mask = [COHORT_MAPPING.get(s) == "TRAIN_COHORT" for s in ids_a]
        test_mask = [COHORT_MAPPING.get(s) == "TEST_SET_DIAGNOSTIC_ONLY" for s in ids_a]

        def cohort_stats_v1(mask):
            sub_a = [y_a[i] for i, m in enumerate(mask) if m]
            sub_b = [y_b[i] for i, m in enumerate(mask) if m]
            if not sub_a:
                return 0.0, None, 0
            agr = sum(a == b for a, b in zip(sub_a, sub_b)) / len(sub_a)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kap = cohen_kappa_score(sub_a, sub_b, labels=labels)
            if np.isnan(kap):
                kap = None
            return agr, kap, len(sub_a)

        train_agr, train_kap, n_train = cohort_stats_v1(train_mask)
        test_agr, test_kap, n_test = cohort_stats_v1(test_mask)

        both_correct_ids = [ids_a[i] for i in range(total_n) if y_a[i] == "CORRECT" and y_b[i] == "CORRECT"]
        both_incorrect_ids = [c["sample_id"] for c in both_incorrect_cases]
        decision_divergent_ids = [ids_a[i] for i in range(total_n) if y_a[i] != y_b[i]]
        ambiguous_or_undet_ids = [ids_a[i] for i in range(total_n) if y_a[i] in {"AMBIGUOUS", "UNDETERMINABLE"} or y_b[i] in {"AMBIGUOUS", "UNDETERMINABLE"}]

        return {
            "schema_version": "SCHEMA_V1_LEGACY_VERIFICATION",
            "total_samples": total_n,
            "decision_agreement": {
                "observed_agreement": p_o,
                "p_e": p_e,
                "cohen_kappa": kappa,
                "cohen_kappa_se": kappa_se,
                "cohen_kappa_ci_95": kappa_ci_95,
                "cohen_kappa_status": kappa_status,
                "bootstrap": boot_res,
                "confusion_matrix": cm,
                "labels": labels,
                "marginal_a": freq_a,
                "marginal_b": freq_b,
            },
            "correct_letter_agreement": {
                "both_incorrect_count": n_both_incorrect,
                "matches_count": n_letter_matches,
                "divergent_count": n_letter_divergent,
                "agreement_rate": letter_agreement_rate,
                "divergent_sample_ids": letter_discrepant_ids,
                "cases": both_incorrect_cases,
                "labels": sorted(list(set([c["let_a"] for c in both_incorrect_cases] + [c["let_b"] for c in both_incorrect_cases]))),
                "confusion_matrix": [],
            },
            "denominators": {
                "total_evaluated": total_n,
                "both_correct_count": len(both_correct_ids),
                "both_correct_ids": both_correct_ids,
                "both_incorrect_count": n_both_incorrect,
                "both_incorrect_ids": both_incorrect_ids,
                "decision_divergent_count": len(decision_divergent_ids),
                "decision_divergent_ids": decision_divergent_ids,
                "ambiguous_or_undeterminable_count": len(ambiguous_or_undet_ids),
                "ambiguous_or_undeterminable_ids": ambiguous_or_undet_ids,
                "letter_matches_count": n_letter_matches,
                "letter_divergent_count": n_letter_divergent,
                "letter_divergent_ids": letter_discrepant_ids,
            },
            "discrepancies": discrepancies,
            "num_discrepancies": len(discrepancies),
            "cohort_breakdown": {
                "TRAIN_COHORT": {"count": n_train, "agreement": train_agr, "kappa": train_kap},
                "TEST_SET_DIAGNOSTIC_ONLY": {"count": n_test, "agreement": test_agr, "kappa": test_kap},
            },
        }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Analisis Inter-Rater Reliability Blind Letter Identification SignBridge I1")
    parser.add_argument(
        "--val-a",
        type=Path,
        default=Path("docs/validation_p2/phase_2c/VALIDATOR_A_WORKBOOK.xlsx"),
        help="Jalur file respons Validator A (.xlsx atau .csv)",
    )
    parser.add_argument(
        "--val-b",
        type=Path,
        default=Path("docs/validation_p2/phase_2c/VALIDATOR_B_WORKBOOK.xlsx"),
        help="Jalur file respons Validator B (.xlsx atau .csv)",
    )
    parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=2000,
        help="Jumlah replikasi paired bootstrap untuk CI 95%% (default: 2000)",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=42,
        help="Random seed untuk bootstrap resampling (default: 42)",
    )
    args = parser.parse_args()

    # Fallback to CSV if default xlsx not found
    val_a_path = args.val_a
    val_b_path = args.val_b
    if not val_a_path.exists():
        fallback_csv_a = Path("docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv")
        if fallback_csv_a.exists():
            val_a_path = fallback_csv_a
    if not val_b_path.exists():
        fallback_csv_b = Path("docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv")
        if fallback_csv_b.exists():
            val_b_path = fallback_csv_b

    print("================================================================================")
    print(" SIGNBRIDGE I1 — PHASE 2C.8 BLIND LETTER IDENTIFICATION ANALYZER")
    print("================================================================================")
    print(f"File Validator A: {val_a_path}")
    print(f"File Validator B: {val_b_path}")

    df_a, status_a = load_and_validate_response(val_a_path, "VAL-A")
    df_b, status_b = load_and_validate_response(val_b_path, "VAL-B")

    schema_a = getattr(status_a, "schema_version", "UNKNOWN")
    schema_b = getattr(status_b, "schema_version", "UNKNOWN")

    print(f"\nStatus Validasi Integritas File:")
    print(f"- Validator A: [{status_a.validation_status}] (Skema: {schema_a}) | {status_a}")
    print(f"- Validator B: [{status_b.validation_status}] (Skema: {schema_b}) | {status_b}")

    if status_a.category == ValidationStatusEnum.EMPTY_TEMPLATE or status_b.category == ValidationStatusEnum.EMPTY_TEMPLATE:
        print("\n[INFO] STATUS SISTEM: WAITING_FOR_VALIDATOR_RESPONSES")
        print("Template lembar kerja berstatus EMPTY_TEMPLATE dan siap diisi secara mandiri oleh validator.")
        print("Perhitungan metriks reliabilitas akan dieksekusi secara otomatis segera setelah respons nyata tersedia.")
        return 0

    if status_a.category != ValidationStatusEnum.VALID_COMPLETE_RESPONSE or status_b.category != ValidationStatusEnum.VALID_COMPLETE_RESPONSE:
        print("\n[ERROR] Validasi input gagal. Berkas tidak memenuhi kriteria VALID_COMPLETE_RESPONSE.")
        if status_a.category == ValidationStatusEnum.INCOMPLETE_PENDING_COMPLETION or status_b.category == ValidationStatusEnum.INCOMPLETE_PENDING_COMPLETION:
            print("[PERINGATAN] Berkas respons berstatus INCOMPLETE_PENDING_COMPLETION. Harap kembalikan ke validator untuk dilengkapi.")
        return 1

    try:
        results = compute_metrics(
            df_a,
            df_b,
            bootstrap_reps=args.bootstrap_reps,
            bootstrap_seed=args.bootstrap_seed,
        )
    except Exception as e:
        print(f"\n[ERROR] Gagal menghitung metrik reliabilitas: {e}")
        return 1

    ver = results["schema_version"]
    print(f"\nMode Analisis Aktif: {ver}")

    if ver == "SCHEMA_V2_BLIND_IDENTIFICATION":
        let_res = results["letter_identification_agreement"]
        clarity_res = results["gesture_clarity_agreement"]
        gt_res = results["ground_truth_comparison"]
        boot = clarity_res["bootstrap"]

        print("\n--------------------------------------------------------------------------------")
        print(" 1. KESEPAKATAN IDENTIFIKASI HURUF MANDIRI (INDEPENDENT LETTER AGREEMENT)")
        print("--------------------------------------------------------------------------------")
        print(f"Total Sampel Dievaluasi         : {results['total_samples']}")
        print(f"Sampel Keduanya Mengidentifikasi: {let_res['both_identified_count']} sampel")
        print(f"Huruf Sama Persis (Matches)     : {let_res['matches_count']} sampel")
        print(f"Huruf Berbeda (Divergent)       : {let_res['divergent_count']} sampel")
        if let_res["agreement_rate"] is not None:
            print(f"Tingkat Kesepakatan Huruf       : {let_res['agreement_rate']:.4f} ({let_res['agreement_rate']*100:.2f}%)")
        print(f"Tingkat Kecocokan Total Sampel  : {let_res['overall_sample_rate']:.4f} ({let_res['overall_sample_rate']*100:.2f}%)")
        if let_res["divergent_sample_ids"]:
            print(f"Sampel Divergensi Huruf         : {let_res['divergent_sample_ids']}")

        print("\n--------------------------------------------------------------------------------")
        print(" 2. KESEPAKATAN KEJELASAN ISYARAT (GESTURE CLARITY / DECISION AGREEMENT)")
        print("--------------------------------------------------------------------------------")
        print(f"Observed Agreement (P_o)        : {clarity_res['observed_agreement']:.4f} ({clarity_res['observed_agreement']*100:.2f}%)")
        print(f"Chance Expected Agreement (P_e) : {clarity_res['p_e']:.4f} ({clarity_res['p_e']*100:.2f}%)")
        if clarity_res["cohen_kappa"] is not None:
            print(f"Nominal Cohen's Kappa           : {clarity_res['cohen_kappa']:.4f}")
            if clarity_res["cohen_kappa_ci_95"] is not None:
                print(f"Kappa 95% CI (Asymptotic Fleiss): [{clarity_res['cohen_kappa_ci_95'][0]:.4f}, {clarity_res['cohen_kappa_ci_95'][1]:.4f}] (SE: {clarity_res['cohen_kappa_se']:.4f})")
            if boot["bootstrap_ci_95"] is not None:
                print(f"Kappa 95% CI (Paired Bootstrap) : [{boot['bootstrap_ci_95'][0]:.4f}, {boot['bootstrap_ci_95'][1]:.4f}] (B={boot['valid_replications']}/{boot['n_replications']}, Seed={boot['bootstrap_seed']})")
                print(f"  * Bootstrap Mean = {boot['bootstrap_mean']:.4f}, Std Error = {boot['bootstrap_std']:.4f}")
        else:
            print(f"Nominal Cohen's Kappa           : {clarity_res['cohen_kappa_status']}")

        print("\n--------------------------------------------------------------------------------")
        print(" 3. PERBANDINGAN GROUND TRUTH INTERNAL (RESEARCH AUDIT)")
        print("--------------------------------------------------------------------------------")
        print(f"Kecocokan Val A vs Ground Truth : {gt_res['val_a_matches']}/{results['total_samples']} ({gt_res['val_a_matches']/results['total_samples']*100:.2f}%)")
        print(f"Kecocokan Val B vs Ground Truth : {gt_res['val_b_matches']}/{results['total_samples']} ({gt_res['val_b_matches']/results['total_samples']*100:.2f}%)")
        print(f"Konsensus Validasi vs GT        : {gt_res['consensus_matches']}/{results['total_samples']} ({gt_res['consensus_matches']/results['total_samples']*100:.2f}%)")
        if gt_res["potential_dataset_error_sample_ids"]:
            print(f"[PERINGATAN] Indikasi Label Salah pada Dataset: {gt_res['potential_dataset_error_sample_ids']}")
            print("  (Kedua validator sepakat huruf yang sama, namun berbeda dari label bawaan dataset!)")

        print("\n--------------------------------------------------------------------------------")
        print(" 4. BREAKDOWN BERDASARKAN KOHORT METODOLOGIS")
        print("--------------------------------------------------------------------------------")
        for cohort, st in results["cohort_breakdown"].items():
            print(f"  * {cohort} (N={st['count']}): Letter Matches={st['matches']}/{st['both_identified']} ({st['agreement']*100:.2f}%)")

        print("\n--------------------------------------------------------------------------------")
        print(f" 5. DAFTAR KASUS ESKALASI ADJUDIKASI VALIDATOR C (TOTAL: {results['num_discrepancies']})")
        print("--------------------------------------------------------------------------------")
        if results["discrepancies"]:
            for d in results["discrepancies"]:
                print(f"  - [{d['sample_id']}] ({d['cohort']}) Val A: '{d['val_a_letter']}' ({d['val_a_decision']}) | Val B: '{d['val_b_letter']}' ({d['val_b_decision']})")
                print(f"    Alasan: {d['reasons']}")
        else:
            print("  (Nihil - Seluruh sampel sepakat sempurna)")

    else:
        # Tampilan Legacy Schema V1
        dec_res = results["decision_agreement"]
        let_res = results["correct_letter_agreement"]
        print("\n[LEGACY MODE] Hasil Decision Agreement 4 Kategori:")
        print(f"Observed Agreement (P_o): {dec_res['observed_agreement']:.4f}")
        if dec_res["cohen_kappa"] is not None:
            print(f"Cohen's Kappa (kappa)   : {dec_res['cohen_kappa']:.4f}")
        print(f"Kasus Adjudikasi        : {results['num_discrepancies']} sampel")

    return 0


if __name__ == "__main__":
    sys.exit(main())
