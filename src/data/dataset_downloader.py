"""
DatasetDownloader — unduh dan validasi dataset WL-BISINDO dan WLASL.

Requirements: 1.1, 2.1, 2.4, 2.5
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DownloadResult:
    """Hasil proses download dataset."""
    success: bool
    files_downloaded: int
    files_failed: int
    validation_errors: list[str] = field(default_factory=list)
    report_path: Optional[Path] = None
    failed_urls: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Proporsi file yang berhasil diunduh."""
        total = self.files_downloaded + self.files_failed
        if total == 0:
            return 1.0
        return self.files_downloaded / total


@dataclass
class ValidationReport:
    """Laporan validasi integritas dataset WL-BISINDO."""
    is_valid: bool
    total_glosses: int
    glosses_with_errors: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def num_errors(self) -> int:
        return len(self.errors)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class DataValidationError(Exception):
    """Dilempar jika validasi integritas dataset gagal."""


class DownloadAbortedError(Exception):
    """Dilempar jika tingkat keberhasilan download di bawah ambang batas."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# URL manifest JSON resmi WLASL dari repositori paper asli
WLASL_MANIFEST_URL = (
    "https://raw.githubusercontent.com/dxli94/WLASL/master/start_kit/WLASL_v0.3.json"
)

# Jumlah percobaan ulang untuk setiap file
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2.0  # detik
DEFAULT_TIMEOUT = 60       # detik per request

# Ambang batas keberhasilan WLASL (Req 2.4)
WLASL_SUCCESS_THRESHOLD = 0.80

# Metadata WLASL yang diharapkan (Req 2.1)
WLASL_MIN_VIDEOS = 21_083
WLASL_EXPECTED_GLOSSES = 2_006
WLASL_EXPECTED_SIGNERS = 119


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe_filename(url: str) -> str:
    """Ambil nama file aman dari URL."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name if name else "file"


def _download_file_with_retry(
    url: str,
    dest: Path,
    retries: int = DEFAULT_RETRY_ATTEMPTS,
    delay: float = DEFAULT_RETRY_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> bool:
    """
    Unduh satu file dengan retry logic.

    Returns True jika berhasil, False jika semua percobaan gagal.
    File dianggap corrupt jika ukurannya 0 byte (Req 2.4).
    """
    sess = session or requests.Session()

    for attempt in range(1, retries + 1):
        try:
            response = sess.get(url, timeout=timeout, stream=True)
            if response.status_code != 200:
                logger.warning(
                    "HTTP %s saat mengunduh %s (percobaan %d/%d)",
                    response.status_code, url, attempt, retries,
                )
                if attempt < retries:
                    time.sleep(delay * attempt)
                continue

            # Tulis ke file sementara lalu rename (atomic-ish)
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, "wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    fh.write(chunk)

            # Periksa apakah file corrupt (Req 2.4: ukuran file 0 byte)
            if tmp.stat().st_size == 0:
                tmp.unlink(missing_ok=True)
                logger.warning(
                    "File corrupt (0 byte) dari %s (percobaan %d/%d)",
                    url, attempt, retries,
                )
                if attempt < retries:
                    time.sleep(delay * attempt)
                continue

            tmp.rename(dest)
            return True

        except requests.RequestException as exc:
            logger.warning(
                "Error jaringan saat mengunduh %s (percobaan %d/%d): %s",
                url, attempt, retries, exc,
            )
            if attempt < retries:
                time.sleep(delay * attempt)

    return False


# ---------------------------------------------------------------------------
# DatasetDownloader
# ---------------------------------------------------------------------------

class DatasetDownloader:
    """Unduh dan validasi dataset WL-BISINDO dan WLASL.

    Requirements: 1.1, 2.1, 2.4, 2.5
    """

    def __init__(
        self,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: int = DEFAULT_TIMEOUT,
        wlasl_success_threshold: float = WLASL_SUCCESS_THRESHOLD,
    ) -> None:
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.wlasl_success_threshold = wlasl_success_threshold
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # WL-BISINDO (Kaggle)
    # ------------------------------------------------------------------

    def download_wl_bisindo(
        self, kaggle_identifier: str, output_dir: Path
    ) -> DownloadResult:
        """
        Unduh dataset WL-BISINDO dari Kaggle.

        Parameters
        ----------
        kaggle_identifier:
            Identifier dataset Kaggle, contoh: ``"username/wl-bisindo"`` atau
            ``"dataset/wl-bisindo"``.
        output_dir:
            Direktori tujuan tempat dataset akan diekstrak.

        Returns
        -------
        DownloadResult
            success, files_downloaded, validation_errors, report_path

        Requirements: 1.1
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Memulai download WL-BISINDO dari Kaggle: %s", kaggle_identifier)

        validation_errors: list[str] = []
        files_downloaded = 0

        try:
            # Kaggle CLI: kaggle datasets download -d <identifier> -p <path> --unzip
            cmd = [
                "kaggle", "datasets", "download",
                "-d", kaggle_identifier,
                "-p", str(output_dir),
                "--unzip",
                "--force",
            ]

            for attempt in range(1, self.retry_attempts + 1):
                logger.info(
                    "Kaggle download percobaan %d/%d ...", attempt, self.retry_attempts
                )
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600,  # 1 jam
                )
                if result.returncode == 0:
                    logger.info("WL-BISINDO berhasil diunduh ke %s", output_dir)
                    break
                else:
                    logger.warning(
                        "Kaggle CLI gagal (attempt %d/%d): %s",
                        attempt, self.retry_attempts, result.stderr.strip(),
                    )
                    if attempt < self.retry_attempts:
                        time.sleep(self.retry_delay * attempt)
            else:
                # Semua percobaan gagal
                err_msg = (
                    f"Gagal mengunduh WL-BISINDO setelah {self.retry_attempts} "
                    f"percobaan. Error Kaggle CLI: {result.stderr.strip()}"
                )
                validation_errors.append(err_msg)
                logger.error(err_msg)

                report_path = self._generate_markdown_report(
                    dataset_name="WL-BISINDO",
                    output_dir=output_dir,
                    files_downloaded=0,
                    files_failed=1,
                    glosses=0,
                    signers=0,
                    failed_files=[kaggle_identifier],
                )
                return DownloadResult(
                    success=False,
                    files_downloaded=0,
                    files_failed=1,
                    validation_errors=validation_errors,
                    report_path=report_path,
                )

            # Hitung file yang berhasil diunduh
            video_extensions = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
            files_downloaded = sum(
                1
                for f in output_dir.rglob("*")
                if f.is_file() and f.suffix.lower() in video_extensions
            )

            # Kumpulkan jumlah gloss dan signer dari struktur direktori
            glosses, signers = self._count_wl_bisindo_structure(output_dir)

            report_path = self._generate_markdown_report(
                dataset_name="WL-BISINDO",
                output_dir=output_dir,
                files_downloaded=files_downloaded,
                files_failed=0,
                glosses=glosses,
                signers=signers,
                failed_files=[],
            )

            logger.info(
                "WL-BISINDO: %d video, %d gloss, %d signer",
                files_downloaded, glosses, signers,
            )

            return DownloadResult(
                success=True,
                files_downloaded=files_downloaded,
                files_failed=0,
                validation_errors=validation_errors,
                report_path=report_path,
            )

        except FileNotFoundError:
            err = (
                "Kaggle CLI tidak ditemukan. Pastikan `kaggle` terinstal dan "
                "tersedia di PATH. Instal dengan: pip install kaggle"
            )
            logger.error(err)
            validation_errors.append(err)
            return DownloadResult(
                success=False,
                files_downloaded=0,
                files_failed=1,
                validation_errors=validation_errors,
            )
        except subprocess.TimeoutExpired:
            err = "Kaggle download timeout setelah 1 jam."
            logger.error(err)
            validation_errors.append(err)
            return DownloadResult(
                success=False,
                files_downloaded=files_downloaded,
                files_failed=1,
                validation_errors=validation_errors,
            )

    def _count_wl_bisindo_structure(self, data_dir: Path) -> tuple[int, int]:
        """
        Hitung jumlah gloss (subdirektori level-1) dan signer unik
        dari struktur direktori WL-BISINDO.

        Struktur yang diharapkan: data_dir / <gloss> / <signer_id> / <video.mp4>
        atau data_dir / <gloss> / <video.mp4> (flat per gloss).
        """
        if not data_dir.exists():
            return 0, 0

        gloss_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
        glosses = len(gloss_dirs)

        signer_ids: set[str] = set()
        for gdir in gloss_dirs:
            for item in gdir.iterdir():
                if item.is_dir():
                    signer_ids.add(item.name)

        # Fallback: jika tidak ada subdirektori signer, gunakan nama file video
        if not signer_ids:
            for gdir in gloss_dirs:
                for vf in gdir.glob("*.mp4"):
                    # Konvensi nama: <gloss>_<signer_id>_<sample>.mp4
                    parts = vf.stem.split("_")
                    if len(parts) >= 2:
                        signer_ids.add(parts[1])

        return glosses, len(signer_ids)

    # ------------------------------------------------------------------
    # WLASL
    # ------------------------------------------------------------------

    def download_wlasl(self, output_dir: Path) -> DownloadResult:
        """
        Unduh dataset WLASL dengan retry logic dan validasi file.

        Langkah:
        1. Unduh manifest JSON (daftar video + URL).
        2. Unduh setiap video dengan retry logic.
        3. Catat file gagal ke log.
        4. Hentikan jika < 80% file berhasil (Req 2.4).
        5. Hasilkan laporan Markdown (Req 2.5).

        Parameters
        ----------
        output_dir:
            Direktori tujuan untuk menyimpan video WLASL.

        Returns
        -------
        DownloadResult
            success, files_downloaded, files_failed, failed_urls, report_path

        Requirements: 2.1, 2.4, 2.5
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        log_dir = output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        failed_log_path = log_dir / "wlasl_failed_downloads.log"

        logger.info("Memulai download WLASL ke %s", output_dir)

        # --- Langkah 1: Unduh manifest JSON ---
        manifest = self._fetch_wlasl_manifest(output_dir)
        if manifest is None:
            err = "Gagal mengunduh manifest WLASL."
            return DownloadResult(
                success=False,
                files_downloaded=0,
                files_failed=1,
                validation_errors=[err],
            )

        # --- Langkah 2: Bangun daftar (url, dest_path) dari manifest ---
        video_tasks = self._parse_wlasl_manifest(manifest, output_dir)
        total = len(video_tasks)
        logger.info("Manifest WLASL: %d video ditemukan", total)

        if total == 0:
            err = "Manifest WLASL tidak memiliki entri video."
            return DownloadResult(
                success=False,
                files_downloaded=0,
                files_failed=0,
                validation_errors=[err],
            )

        # --- Langkah 3: Unduh setiap video ---
        files_downloaded = 0
        files_failed = 0
        failed_urls: list[str] = []

        with open(failed_log_path, "w", encoding="utf-8") as fail_log:
            fail_log.write(
                f"# WLASL Failed Downloads — {datetime.now().isoformat()}\n"
                "# Format: <url> | <dest_path> | <reason>\n\n"
            )

            for idx, (url, dest) in enumerate(video_tasks, start=1):
                if idx % 500 == 0 or idx == total:
                    logger.info("Progress: %d/%d video diproses", idx, total)

                # Lewati jika sudah ada dan tidak corrupt
                if dest.exists() and dest.stat().st_size > 0:
                    files_downloaded += 1
                    continue

                success = _download_file_with_retry(
                    url=url,
                    dest=dest,
                    retries=self.retry_attempts,
                    delay=self.retry_delay,
                    timeout=self.timeout,
                    session=self._session,
                )

                if success:
                    files_downloaded += 1
                else:
                    files_failed += 1
                    failed_urls.append(url)
                    # Catat ke log (Req 2.4)
                    fail_log.write(
                        f"{url} | {dest} | gagal setelah {self.retry_attempts} percobaan\n"
                    )
                    logger.warning("Gagal mengunduh: %s", url)

        # --- Langkah 4: Periksa ambang batas keberhasilan (Req 2.4) ---
        success_rate = files_downloaded / total if total > 0 else 1.0
        logger.info(
            "WLASL download selesai: %d berhasil, %d gagal (%.1f%%)",
            files_downloaded, files_failed, success_rate * 100,
        )

        aborted = False
        if success_rate < self.wlasl_success_threshold:
            msg = (
                f"Proses dihentikan: hanya {success_rate * 100:.1f}% file berhasil "
                f"(ambang minimum: {self.wlasl_success_threshold * 100:.0f}%). "
                f"{files_failed} dari {total} file gagal diunduh. "
                f"Lihat log: {failed_log_path}"
            )
            logger.error(msg)
            aborted = True

        # --- Langkah 5: Hitung statistik untuk laporan ---
        glosses, signers = self._count_wlasl_structure(manifest)

        # --- Langkah 6: Hasilkan laporan Markdown (Req 2.5) ---
        report_path = self._generate_markdown_report(
            dataset_name="WLASL",
            output_dir=output_dir,
            files_downloaded=files_downloaded,
            files_failed=files_failed,
            glosses=glosses,
            signers=signers,
            failed_files=failed_urls[:100],  # hanya 100 pertama agar laporan tidak terlalu panjang
            extra_info={
                "success_rate_pct": f"{success_rate * 100:.1f}%",
                "threshold_pct": f"{self.wlasl_success_threshold * 100:.0f}%",
                "manifest_url": WLASL_MANIFEST_URL,
                "failed_log": str(failed_log_path),
                "aborted": str(aborted),
            },
        )

        if aborted:
            raise DownloadAbortedError(
                f"Download WLASL dihentikan karena tingkat keberhasilan "
                f"({success_rate * 100:.1f}%) di bawah ambang batas "
                f"({self.wlasl_success_threshold * 100:.0f}%). "
                f"Laporan: {report_path}"
            )

        return DownloadResult(
            success=True,
            files_downloaded=files_downloaded,
            files_failed=files_failed,
            validation_errors=[],
            report_path=report_path,
            failed_urls=failed_urls,
        )

    def _fetch_wlasl_manifest(self, output_dir: Path) -> Optional[list[dict]]:
        """
        Unduh manifest JSON WLASL.

        Jika file manifest sudah ada di output_dir, gunakan yang sudah ada.
        """
        manifest_path = output_dir / "WLASL_v0.3.json"

        if manifest_path.exists() and manifest_path.stat().st_size > 0:
            logger.info("Menggunakan manifest WLASL yang sudah ada: %s", manifest_path)
        else:
            logger.info("Mengunduh manifest WLASL dari %s", WLASL_MANIFEST_URL)
            ok = _download_file_with_retry(
                url=WLASL_MANIFEST_URL,
                dest=manifest_path,
                retries=self.retry_attempts,
                delay=self.retry_delay,
                timeout=self.timeout,
                session=self._session,
            )
            if not ok:
                logger.error("Gagal mengunduh manifest WLASL.")
                return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Gagal membaca manifest WLASL: %s", exc)
            return None

    def _parse_wlasl_manifest(
        self, manifest: list[dict], output_dir: Path
    ) -> list[tuple[str, Path]]:
        """
        Ekstrak daftar (url, dest_path) dari manifest WLASL JSON.

        Format manifest WLASL (WLASL_v0.3.json):
        [
          {
            "gloss": "book",
            "instances": [
              {
                "video_id": "00001",
                "url": "https://...",
                ...
              },
              ...
            ]
          },
          ...
        ]
        """
        tasks: list[tuple[str, Path]] = []

        for gloss_entry in manifest:
            gloss = gloss_entry.get("gloss", "unknown")
            instances = gloss_entry.get("instances", [])

            for inst in instances:
                url = inst.get("url", "")
                video_id = inst.get("video_id", "")

                if not url or not video_id:
                    continue

                # Tentukan ekstensi dari URL
                ext = Path(urlparse(url).path).suffix or ".mp4"
                dest = output_dir / gloss / f"{video_id}{ext}"
                tasks.append((url, dest))

        return tasks

    def _count_wlasl_structure(self, manifest: list[dict]) -> tuple[int, int]:
        """Hitung jumlah gloss dan signer unik dari manifest WLASL."""
        glosses = len(manifest)
        signer_ids: set[str] = set()

        for gloss_entry in manifest:
            for inst in gloss_entry.get("instances", []):
                signer_id = inst.get("signer_id")
                if signer_id is not None:
                    signer_ids.add(str(signer_id))

        return glosses, len(signer_ids)

    # ------------------------------------------------------------------
    # Validasi integritas WL-BISINDO
    # ------------------------------------------------------------------

    def validate_wl_bisindo_integrity(self, data_dir: Path) -> ValidationReport:
        """
        Verifikasi 32 gloss × 50 video (10 sampel × 5 signer).

        Raises DataValidationError jika ada ketidaksesuaian.

        Requirements: 1.2, 1.3
        """
        data_dir = Path(data_dir)
        errors: list[str] = []
        glosses_with_errors: list[str] = []

        EXPECTED_GLOSSES = 32
        EXPECTED_VIDEOS_PER_GLOSS = 50  # 10 sampel × 5 signer

        if not data_dir.exists():
            raise DataValidationError(
                f"Direktori dataset tidak ditemukan: {data_dir}"
            )

        video_extensions = {".mp4", ".avi", ".mov", ".webm", ".mkv"}

        gloss_dirs = sorted(
            [d for d in data_dir.iterdir() if d.is_dir()]
        )
        actual_glosses = len(gloss_dirs)

        if actual_glosses != EXPECTED_GLOSSES:
            errors.append(
                f"Jumlah gloss tidak sesuai: ditemukan {actual_glosses}, "
                f"diharapkan {EXPECTED_GLOSSES}."
            )

        for gdir in gloss_dirs:
            videos = [
                f for f in gdir.rglob("*")
                if f.is_file() and f.suffix.lower() in video_extensions
            ]
            count = len(videos)
            if count != EXPECTED_VIDEOS_PER_GLOSS:
                msg = (
                    f"Gloss '{gdir.name}': ditemukan {count} video, "
                    f"diharapkan {EXPECTED_VIDEOS_PER_GLOSS} "
                    f"(10 sampel × 5 signer)."
                )
                errors.append(msg)
                glosses_with_errors.append(gdir.name)

        # Tulis laporan kesalahan ke file jika ada error (Req 1.3)
        if errors:
            error_file = data_dir.parent / "validation_errors.txt"
            error_file.parent.mkdir(parents=True, exist_ok=True)
            with open(error_file, "w", encoding="utf-8") as fh:
                fh.write(
                    f"# WL-BISINDO Validation Errors — {datetime.now().isoformat()}\n\n"
                )
                for err in errors:
                    fh.write(f"- {err}\n")
            logger.error(
                "Validasi WL-BISINDO gagal: %d error ditulis ke %s",
                len(errors), error_file,
            )

            report = ValidationReport(
                is_valid=False,
                total_glosses=actual_glosses,
                glosses_with_errors=glosses_with_errors,
                errors=errors,
            )
            raise DataValidationError(
                f"Validasi WL-BISINDO gagal: {len(errors)} error ditemukan. "
                f"Lihat data/validation_errors.txt untuk detail."
            )

        logger.info("Validasi WL-BISINDO berhasil: 32 gloss × 50 video.")
        return ValidationReport(
            is_valid=True,
            total_glosses=actual_glosses,
            glosses_with_errors=[],
            errors=[],
        )

    # ------------------------------------------------------------------
    # Laporan Markdown (Req 2.5)
    # ------------------------------------------------------------------

    def _generate_markdown_report(
        self,
        dataset_name: str,
        output_dir: Path,
        files_downloaded: int,
        files_failed: int,
        glosses: int,
        signers: int,
        failed_files: list[str],
        extra_info: Optional[dict] = None,
    ) -> Path:
        """
        Hasilkan laporan persiapan data dalam format Markdown.

        Requirements: 2.5
        """
        report_path = output_dir / f"{dataset_name.lower()}_preparation_report.md"
        total = files_downloaded + files_failed
        success_rate = (files_downloaded / total * 100) if total > 0 else 100.0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            f"# Laporan Persiapan Dataset — {dataset_name}",
            "",
            f"**Tanggal:** {timestamp}",
            "",
            "---",
            "",
            "## Ringkasan",
            "",
            f"| Metrik                     | Nilai                |",
            f"|----------------------------|----------------------|",
            f"| Jumlah video berhasil      | {files_downloaded:>20,} |",
            f"| Jumlah file gagal          | {files_failed:>20,} |",
            f"| Total file                 | {total:>20,} |",
            f"| Tingkat keberhasilan       | {success_rate:>19.1f}% |",
            f"| Jumlah gloss tercakup      | {glosses:>20,} |",
            f"| Jumlah signer              | {signers:>20,} |",
            "",
        ]

        if extra_info:
            lines += [
                "## Informasi Tambahan",
                "",
            ]
            for key, val in extra_info.items():
                lines.append(f"- **{key}:** {val}")
            lines.append("")

        if failed_files:
            lines += [
                "## File Gagal (maks. 100 ditampilkan)",
                "",
                "```",
            ]
            lines.extend(failed_files[:100])
            lines += [
                "```",
                "",
            ]

        lines += [
            "---",
            "",
            f"*Laporan dibuat secara otomatis oleh SignBridge DatasetDownloader.*",
        ]

        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

        logger.info("Laporan Markdown disimpan ke: %s", report_path)
        return report_path
