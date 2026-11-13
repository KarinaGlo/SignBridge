"""
tests/test_pipeline_safety_audit.py — Pengujian Keamanan Pipeline & Penghapusan Synthetic Fallback (Tahap A).

Membuktikan secara otomatis bahwa:
1. Tidak ada synthetic fallback pada video, image, audio, maupun text.
2. Input kosong atau berkas hilang menghasilkan error eksplisit (FileNotFoundError / ValueError).
3. Dependency video yang belum terpasang (opencv-python / mediapipe) menghasilkan RuntimeError yang jelas.
4. Ekstensi video .MOV, .mov, .mp4, .MP4, .webm, .WEBM terdeteksi (dan file tersembunyi ._* diabaikan).
5. Input dataset fisik asli di workspace (FSL-105 2.130 .MOV, BISINDO Alphabet 4.466 RGB A-Z,
   Google FLEURS id_id 350 .wav, dan TSV/Tatoeba teks) ditemukan dan dibaca dengan benar.
6. Piksel hasil crop_hands benar-benar berasal dari berkas citra RGB sumber (bukan rng.integers).
7. Loader audio tidak membuat gelombang sinus sintetis dan melaporkan NOT AVAILABLE untuk audio kelas.
8. Loader teks membaca pasangan dari TSV asli, menolak korpus monolingual Tatoeba sebagai
   pasangan gloss-to-sentence, dan mencegah kebocoran test set (test_manual.tsv) ke train/val.
"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import wave

import scripts.build_text_corpus as build_text_corpus
import scripts.crop_hands as crop_hands
import scripts.extract_keypoints as extract_keypoints
import scripts.extract_rgb_features as extract_rgb_features
import scripts.prepare_kelas_audio as prepare_kelas_audio
from signbridge.audio.train_asr import (
    WhisperASRWrapper,
    compute_log_mel_spectrogram,
    load_audio_dataset_records,
    load_wav_waveform,
    verify_audio_splits_disjoint,
)
from signbridge.data.dataset import SignDataset
from signbridge.image.train_image import FingerspellDataset
from signbridge.text.train_text import (
    _load_tsv_pairs,
    build_text_vocabulary,
    encode_pairs_from_vocab,
    encode_pairs_with_vocab,
    load_and_verify_text_splits,
    load_monolingual_tatoeba_tsv,
)


class TestPipelineSafetyAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="signbridge_safety_test_"))

    def tearDown(self) -> None:
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. VIDEO: scripts/extract_keypoints.py
    # ------------------------------------------------------------------
    def test_01_video_no_synthetic_fallback_and_empty_dir_error(self) -> None:
        """Pastikan extract_keypoints tidak lagi memiliki ensure_demo_dataset dan gagal jelas pada folder kosong."""
        self.assertFalse(
            hasattr(extract_keypoints, "ensure_demo_dataset"),
            "ensure_demo_dataset tidak boleh diimpor di scripts/extract_keypoints.py",
        )

        missing_dir = self.tmp_dir / "non_existent_video_dir"
        with self.assertRaises(FileNotFoundError):
            extract_keypoints.discover_video_files(missing_dir)

        empty_dir = self.tmp_dir / "empty_video_dir"
        empty_dir.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(FileNotFoundError):
            extract_keypoints.discover_video_files(empty_dir)

        with self.assertRaises(FileNotFoundError):
            extract_keypoints.run_extraction(
                raw_dir=empty_dir,
                out_dir=self.tmp_dir / "out_kp",
                manifest_path=self.tmp_dir / "manifest.csv",
            )

    def test_02_video_extensions_mov_case_insensitive_and_fsl105_discovery(self) -> None:
        """Pastikan ekstensi .MOV, .mov, .mp4, .MP4, .webm, .WEBM terdeteksi dan file ._* diabaikan."""
        raw_vid = self.tmp_dir / "raw_videos"
        (raw_vid / "HALO").mkdir(parents=True, exist_ok=True)
        names = ["a.MOV", "b.mov", "c.mp4", "d.MP4", "e.webm", "f.WEBM", "._hidden.MOV", "notes.txt"]
        for name in names:
            (raw_vid / "HALO" / name).write_bytes(b"FAKE_VIDEO_HEADER")

        found = extract_keypoints.discover_video_files(raw_vid)
        found_names = [p.name for p in found]
        self.assertEqual(found_names, ["a.MOV", "b.mov", "c.mp4", "d.MP4", "e.webm", "f.WEBM"])

        # Verifikasi dataset fisik asli FSL-105 (2.130 berkas .MOV di 105 folder kelas)
        fsl_clips_dir = ROOT / "data" / "raw" / "video" / "fsl_105" / "clips"
        fsl_labels_csv = ROOT / "data" / "raw" / "video" / "fsl_105" / "labels.csv"
        if fsl_clips_dir.exists():
            fsl_videos = extract_keypoints.discover_video_files(fsl_clips_dir)
            self.assertEqual(len(fsl_videos), 2130)
            label_map = extract_keypoints.load_optional_labels_csv(fsl_clips_dir, fsl_labels_csv)
            self.assertEqual(len({v[1] for v in label_map.values()}), 105)
            gloss0, lbl0 = extract_keypoints.resolve_video_gloss_and_label(
                fsl_videos[0], source="fsl", label_map=label_map
            )
            self.assertIsInstance(gloss0, str)
            self.assertTrue(len(gloss0) > 0)
            self.assertTrue(0 <= lbl0 < 105)

    def test_03_video_unknown_gloss_and_missing_dependency_errors(self) -> None:
        """Pastikan folder gloss tidak dikenal ditolak (bukan modulo idx % 32) & dependency dicek eksplisit."""
        bad_folder = self.tmp_dir / "UNKNOWN_GLOSS_999" / "clip.MOV"
        bad_folder.parent.mkdir(parents=True, exist_ok=True)
        bad_folder.write_bytes(b"NON_EMPTY_BYTES")

        with self.assertRaises(ValueError):
            extract_keypoints.resolve_video_gloss_and_label(bad_folder, source="bisindo", label_map={})

        zero_file = self.tmp_dir / "HALO" / "zero.mp4"
        zero_file.parent.mkdir(parents=True, exist_ok=True)
        zero_file.write_bytes(b"")
        with self.assertRaises(ValueError):
            extract_keypoints.extract_video_to_86_nodes(zero_file)

        # Uji penanganan dependency jika cv2/mediapipe tidak tersedia (via mock)
        with patch("importlib.util.find_spec", return_value=None):
            with self.assertRaises(RuntimeError) as ctx:
                extract_keypoints.check_video_dependencies()
            self.assertIn("pip install opencv-python mediapipe", str(ctx.exception))

        # Uji berkas video korup/tidak valid pada environment aktif (wajib melempar ValueError eksplisit)
        valid_dummy_path = self.tmp_dir / "HALO" / "nonempty.mp4"
        valid_dummy_path.write_bytes(b"NON_EMPTY_VIDEO_BYTES")
        with self.assertRaises(ValueError):
            extract_keypoints.extract_video_to_86_nodes(valid_dummy_path)

    # ------------------------------------------------------------------
    # 2. IMAGE: scripts/crop_hands.py & FingerspellDataset
    # ------------------------------------------------------------------
    def test_04_image_empty_and_corrupt_input_errors(self) -> None:
        """Pastikan crop_hands dan FingerspellDataset menolak folder kosong, manifest hilang, dan gambar rusak."""
        empty_img_dir = self.tmp_dir / "empty_images"
        empty_img_dir.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(FileNotFoundError):
            crop_hands.discover_alphabet_images(empty_img_dir)

        with self.assertRaises(FileNotFoundError):
            crop_hands.run_crop_hands(
                in_dir=empty_img_dir,
                out_dir=self.tmp_dir / "crops_out",
                manifest_path=self.tmp_dir / "manifest_img.csv",
            )

        # File gambar rusak (bukan JPEG/PNG valid) wajib melempar ValueError
        corrupt_dir = self.tmp_dir / "corrupt_images" / "A"
        corrupt_dir.mkdir(parents=True, exist_ok=True)
        corrupt_jpg = corrupt_dir / "corrupt.jpg"
        corrupt_jpg.write_bytes(b"NOT_A_VALID_JPEG_FILE_HEADER")
        with self.assertRaises(ValueError):
            crop_hands.load_rgb_image(corrupt_jpg)

        # FingerspellDataset wajib menolak manifest yang tidak ada (tanpa fallback gelombang sinus)
        with self.assertRaises(FileNotFoundError):
            FingerspellDataset(manifest_path=self.tmp_dir / "missing_manifest.csv", split="train")

    def test_05_image_crops_match_real_source_rgb_pixels(self) -> None:
        """Pastikan gambar RGB hasil crop_hands 100% berasal dari file sumber asli (dan tidak mengubah sumber)."""
        real_bisindo_dir = ROOT / "data" / "raw" / "image" / "bisindo_alphabet"
        self.assertTrue(real_bisindo_dir.exists(), "Dataset fisik BISINDO Alphabet harus tersedia")

        discovered = crop_hands.discover_alphabet_images(real_bisindo_dir, require_all_classes=True)
        self.assertEqual(len(discovered), 26)
        total_images = sum(len(v) for v in discovered.values())
        self.assertEqual(total_images, 4466)

        # Uji run_crop_hands dengan max_per_class=1 dari dataset Mendeley asli ke folder sementara
        out_crops = self.tmp_dir / "mendeley_crops_test"
        out_manifest = self.tmp_dir / "manifest_mendeley_test.csv"
        src_sample_a = discovered["A"][0]
        src_bytes_before = src_sample_a.read_bytes()

        processed_count = crop_hands.run_crop_hands(
            in_dir=real_bisindo_dir,
            out_dir=out_crops,
            manifest_path=out_manifest,
            require_all_classes=True,
            max_per_class=1,
        )
        self.assertEqual(processed_count, 26)
        self.assertEqual(src_sample_a.read_bytes(), src_bytes_before, "Berkas citra sumber tidak boleh berubah")

        # Karena citra Mendeley sudah berukuran 224x224x3 RGB, hasil crop tengah tanpa landmark harus identik
        # 100% dengan piksel asli dari berkas JPEG sumber!
        expected_rgb = crop_hands.load_rgb_image(src_sample_a)
        saved_npy = np.load(out_crops / "A" / "A_0000.npy")
        self.assertEqual(saved_npy.shape, (224, 224, 3))
        np.testing.assert_array_equal(
            saved_npy,
            expected_rgb,
            err_msg="Piksel .npy hasil crop_hands harus berasal langsung dari citra RGB sumber asli!",
        )

        # Verifikasi FingerspellDataset membaca .npy asli tersebut
        ds_train = FingerspellDataset(manifest_path=out_manifest, split="train")
        self.assertEqual(len(ds_train), 26)
        chw, lbl = ds_train.load_normalized_chw(0)
        self.assertEqual(chw.shape, (3, 224, 224))
        self.assertEqual(lbl, 0)

    # ------------------------------------------------------------------
    # 3. AUDIO: signbridge/audio/train_asr.py & scripts/prepare_kelas_audio.py
    # ------------------------------------------------------------------
    def test_06_audio_no_synthetic_sine_and_reports_not_available(self) -> None:
        """Pastikan prepare_kelas_audio tidak membuat WAV sintetis dan melaporkan NOT AVAILABLE untuk audio kelas."""
        self.assertFalse(
            hasattr(prepare_kelas_audio, "write_sine_wav"),
            "write_sine_wav wajib dihapus dari scripts/prepare_kelas_audio.py",
        )

        audio_dir = ROOT / "data" / "audio"
        meta_csv = audio_dir / "metadata.csv"
        meta_bytes_before = meta_csv.read_bytes()

        status_report = prepare_kelas_audio.inspect_kelas_audio_status(audio_dir)
        self.assertEqual(status_report["status"], "NOT AVAILABLE")
        self.assertEqual(status_report["total_expected"], 60)
        self.assertEqual(status_report["available_count"], 0)
        self.assertEqual(status_report["missing_count"], 60)

        with self.assertRaises(FileNotFoundError) as ctx:
            prepare_kelas_audio.prepare_audio_files(audio_dir, strict=True)
        self.assertIn("NOT AVAILABLE", str(ctx.exception))

        # Pastikan tidak ada folder data/audio/wavs atau file WAV palsu yang dibuat, dan metadata.csv tidak berubah
        self.assertFalse((audio_dir / "wavs").exists(), "Tidak boleh membuat folder wavs/ berisi audio palsu")
        self.assertEqual(meta_csv.read_bytes(), meta_bytes_before, "metadata.csv tidak boleh berubah")

        with self.assertRaises(FileNotFoundError) as ctx_loader:
            load_audio_dataset_records(meta_csv, strict=True)
        self.assertIn("NOT AVAILABLE", str(ctx_loader.exception))

    def test_07_audio_reads_real_fleurs_id_id_wavs(self) -> None:
        """Pastikan loader audio dapat membaca berkas WAV IEEE float 16kHz asli dari Google FLEURS id_id."""
        fleurs_dev_tsv = ROOT / "data" / "audio" / "fleurs" / "id_id" / "dev.tsv"
        self.assertTrue(fleurs_dev_tsv.exists(), "dev.tsv Google FLEURS id_id harus tersedia")

        records = load_audio_dataset_records(fleurs_dev_tsv, strict=True, max_records=5)
        self.assertEqual(len(records), 5)
        for rec in records:
            self.assertEqual(rec["sample_rate"], 16000)
            self.assertGreater(rec["num_samples"], 1600)
            self.assertGreater(rec["duration_sec"], 0.1)
            self.assertTrue(Path(rec["wav_path"]).exists())

        wav0, sr0 = load_wav_waveform(records[0]["wav_path"])
        mel0 = compute_log_mel_spectrogram(wav0, sample_rate=sr0, n_mels=80)
        self.assertEqual(mel0.shape[0], 80)
        self.assertGreater(mel0.shape[1], 10)
        self.assertTrue(np.all(np.isfinite(mel0)))

    # ------------------------------------------------------------------
    # 4. TEXT: signbridge/text/train_text.py & scripts/build_text_corpus.py
    # ------------------------------------------------------------------
    def test_08_text_loads_real_tsv_and_rejects_tatoeba_as_gloss_pairs(self) -> None:
        """Pastikan loader teks membaca TSV asli, menolak file hilang/rusak, dan menolak Tatoeba sebagai gloss-to-sentence."""
        with self.assertRaises(FileNotFoundError):
            _load_tsv_pairs(self.tmp_dir / "non_existent.tsv")

        # Pastikan Tatoeba (28.418 kalimat monolingual) DITOLAK bila dimuat sebagai pasangan gloss-to-sentence
        tatoeba_path = ROOT / "data" / "text" / "tatoeba" / "ind_sentences.tsv"
        self.assertTrue(tatoeba_path.exists())
        with self.assertRaises(ValueError) as ctx_tat:
            _load_tsv_pairs(tatoeba_path)
        self.assertIn("monolingual Tatoeba", str(ctx_tat.exception))

        # Namun dapat dimuat melalui fungsi khusus monolingual dengan jumlah tepat 28.418 baris
        monolingual_rows = load_monolingual_tatoeba_tsv(tatoeba_path)
        self.assertEqual(len(monolingual_rows), 28418)
        self.assertEqual(monolingual_rows[0]["lang"], "ind")

        # Verifikasi ketiga split TSV asli (170 train, 30 val, 105 test_manual)
        splits = load_and_verify_text_splits(
            train_path=ROOT / "data" / "text" / "train.tsv",
            val_path=ROOT / "data" / "text" / "val.tsv",
            test_path=ROOT / "data" / "text" / "test_manual.tsv",
        )
        self.assertEqual(len(splits["train"]), 170)
        self.assertEqual(len(splits["val"]), 30)
        self.assertEqual(len(splits["test"]), 105)

        src_ids, tgt_ids = encode_pairs_from_vocab(splits["train"])
        self.assertEqual(src_ids.shape[0], 170)
        self.assertEqual(tgt_ids.shape[0], 170)

    def test_09_text_prevents_test_set_leakage_into_train_or_val(self) -> None:
        """Pastikan load_and_verify_text_splits langsung melempar ValueError jika kalimat test bocor ke train/val."""
        train_tmp = self.tmp_dir / "train_leak.tsv"
        val_tmp = self.tmp_dir / "val_clean.tsv"
        test_tmp = self.tmp_dir / "test_manual.tsv"

        with test_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["HALO GURU", "Halo Bapak dan Ibu Guru."])

        with val_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["SAYA BACA BUKU", "Saya sedang membaca buku."])

        # Sisipkan kalimat dari test_tmp ke dalam train_tmp
        with train_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["HALO GURU", "Halo Bapak dan Ibu Guru."])

        with self.assertRaises(ValueError) as ctx_leak:
            load_and_verify_text_splits(train_path=train_tmp, val_path=val_tmp, test_path=test_tmp)
        self.assertIn("leakage", str(ctx_leak.exception))

        # Pastikan build_text_corpus.verify_existing_text_corpus lulus tanpa mengubah file asli
        stats = build_text_corpus.verify_existing_text_corpus(ROOT)
        self.assertEqual(stats["train"], 170)
        self.assertEqual(stats["val"], 30)
        self.assertEqual(stats["manual_test"], 105)
        self.assertEqual(stats["sentences"], 200)
        self.assertEqual(stats["tatoeba_monolingual"], 28418)

    # ------------------------------------------------------------------
    # 5. TAHAP A.1 DEEP VALIDATION TESTS (10..18)
    # ------------------------------------------------------------------
    def test_10_image_without_valid_landmarks_rejected(self) -> None:
        """Gambar dalam mode landmark wajib gagal eksplisit bila landmark None, kosong, <21 titik, atau NaN."""
        with self.assertRaises(ValueError):
            crop_hands.validate_hand_landmarks(None)

        with self.assertRaises(ValueError):
            crop_hands.validate_hand_landmarks(np.zeros((0, 3), dtype=np.float32))

        with self.assertRaises(ValueError):
            crop_hands.validate_hand_landmarks(np.ones((15, 3), dtype=np.float32))

        nan_lm = np.ones((21, 3), dtype=np.float32)
        nan_lm[5, 0] = np.nan
        with self.assertRaises(ValueError):
            crop_hands.validate_hand_landmarks(nan_lm)

        collapsed_lm = np.full((21, 3), 0.5, dtype=np.float32)
        with self.assertRaises(ValueError):
            crop_hands.validate_hand_landmarks(collapsed_lm)

        # Mode use_mediapipe=True: jika dependency hilang -> RuntimeError; jika terpasang tapi tangan nihil -> ValueError
        with patch("importlib.util.find_spec", return_value=None):
            with self.assertRaises(RuntimeError):
                crop_hands.detect_hand_landmarks_strict(np.zeros((224, 224, 3), dtype=np.uint8))

        sample_dir = self.tmp_dir / "img_lm_test" / "A"
        sample_dir.mkdir(parents=True, exist_ok=True)
        img_arr = np.full((224, 224, 3), 128, dtype=np.uint8)
        Image.fromarray(img_arr).save(sample_dir / "a1.jpg")
        with self.assertRaises(ValueError):
            crop_hands.run_crop_hands(
                in_dir=self.tmp_dir / "img_lm_test",
                out_dir=self.tmp_dir / "img_lm_out",
                manifest_path=self.tmp_dir / "img_lm_manifest.csv",
                require_all_classes=False,
                use_mediapipe=True,
            )

    def test_11_image_duplicate_across_splits_and_cross_class_sha256_filtered(self) -> None:
        """Pastikan duplikat gambar lintas split ditolak dan 2 pasang duplikat SHA-256 lintas kelas Mendeley terdeteksi."""
        dup_manifest = self.tmp_dir / "dup_image_manifest.csv"
        crop_a = self.tmp_dir / "crop_a.npy"
        crop_b = self.tmp_dir / "crop_b.npy"
        np.save(crop_a, np.zeros((224, 224, 3), dtype=np.uint8))
        np.save(crop_b, np.ones((224, 224, 3), dtype=np.uint8))

        with dup_manifest.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["path", "source_path", "sha256", "letter", "label", "split"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "path": str(crop_a),
                    "source_path": "data/raw/image/bisindo_alphabet/A/img1.jpg",
                    "sha256": "deadbeef1234",
                    "letter": "A",
                    "label": 0,
                    "split": "train",
                }
            )
            writer.writerow(
                {
                    "path": str(crop_b),
                    "source_path": "data/raw/image/bisindo_alphabet/A/img1_copy.jpg",
                    "sha256": "deadbeef1234",  # SHA-256 identik bocor ke test!
                    "letter": "A",
                    "label": 0,
                    "split": "test",
                }
            )

        with self.assertRaises(ValueError) as ctx:
            crop_hands.verify_image_manifest_no_leakage(dup_manifest)
        self.assertIn("sha256", str(ctx.exception))

        with self.assertRaises(ValueError):
            FingerspellDataset(manifest_path=dup_manifest, split="train")

    def test_12_audio_wav_without_transcription_and_split_leakage_rejected(self) -> None:
        """WAV tanpa transkripsi, duplikasi WAV lintas split, dan dummy transcription Whisper wajib ditolak."""
        wav_path = self.tmp_dir / "valid_16k.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(16000, dtype=np.int16).tobytes())

        empty_txt_csv = self.tmp_dir / "empty_transcript.csv"
        with empty_txt_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "text"])
            writer.writeheader()
            writer.writerow({"file": wav_path.name, "text": "   "})

        with self.assertRaises(ValueError) as ctx:
            load_audio_dataset_records(empty_txt_csv, audio_root=self.tmp_dir, strict=True)
        self.assertIn("tanpa transkripsi", str(ctx.exception))

        # Uji anti-kebocoran split audio
        m_train = self.tmp_dir / "audio_train.csv"
        m_test = self.tmp_dir / "audio_test.csv"
        for m_path in (m_train, m_test):
            with m_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["file", "text"])
                writer.writeheader()
                writer.writerow({"file": wav_path.name, "text": "Selamat pagi"})

        with self.assertRaises(ValueError) as ctx_leak:
            verify_audio_splits_disjoint(train_manifest=m_train, test_manifest=m_test)
        self.assertIn("Kebocoran berkas WAV terdeteksi", str(ctx_leak.exception))

        # Pastikan WhisperASRWrapper tidak lagi mengembalikan kalimat dummy "Selamat pagi anak-anak..."
        asr = WhisperASRWrapper(model_name="openai/whisper-small", decoder_fn=None)
        with self.assertRaises(RuntimeError) as ctx_asr:
            asr.transcribe_waveform(np.ones(16000, dtype=np.float32) * 0.1)
        self.assertIn("transkripsi dummy", str(ctx_asr.exception))

    def test_13_audio_wav_with_wrong_sample_rate_rejected(self) -> None:
        """WAV dengan sample rate bukan 16.000 Hz (mis. 8.000 Hz atau 44.100 Hz) wajib ditolak."""
        for bad_sr in (8000, 44100):
            bad_wav = self.tmp_dir / f"bad_{bad_sr}.wav"
            with wave.open(str(bad_wav), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(bad_sr)
                wf.writeframes(np.zeros(bad_sr, dtype=np.int16).tobytes())

            with self.assertRaises(ValueError) as ctx_sr:
                load_wav_waveform(bad_wav, expected_sr=16000)
            self.assertIn("Sample rate WAV tidak sesuai", str(ctx_sr.exception))

    def test_14_video_corrupt_or_missing_keypoints_and_rgb_rejected_in_signdataset(self) -> None:
        """Pastikan SignDataset dan extract_rgb_features menolak file hilang/rusak tanpa synthetic fallback."""
        manifest_csv = self.tmp_dir / "video_manifest.csv"
        with manifest_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["video_id", "source", "gloss", "label", "signer", "kp_path", "rgb_path", "split_sd"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "video_id": "vid_001",
                    "source": "bisindo",
                    "gloss": "HALO",
                    "label": 0,
                    "signer": "S01",
                    "kp_path": "missing_kp.npz",
                    "rgb_path": "",
                    "split_sd": "train",
                }
            )

        ds = SignDataset(manifest_path=manifest_csv, data_root=self.tmp_dir, split="train")
        with self.assertRaises(FileNotFoundError):
            _ = ds[0]

        # Buat file keypoint dengan isi NaN seluruhnya -> wajib ditolak ValueError
        nan_kp_path = self.tmp_dir / "missing_kp.npz"
        np.savez_compressed(nan_kp_path, kp=np.full((16, 86, 3), np.nan, dtype=np.float32))
        with self.assertRaises(ValueError):
            _ = ds[0]

        # Pastikan extract_rgb_features tidak membuat demo dataset atau token acak
        with self.assertRaises(FileNotFoundError):
            extract_rgb_features.extract_rgb_tokens_for_manifest(
                manifest_path=self.tmp_dir / "nonexistent_manifest.csv",
                out_dir=self.tmp_dir / "rgb_out",
            )

    def test_15_video_unknown_label_and_empty_split_rejected(self) -> None:
        """Video dengan label tidak dikenal dan manifest dengan split kosong wajib ditolak."""
        bad_vid = self.tmp_dir / "KELAS_TIDAK_ADA" / "v1.mp4"
        bad_vid.parent.mkdir(parents=True, exist_ok=True)
        bad_vid.write_bytes(b"1234")
        with self.assertRaises(ValueError):
            extract_keypoints.resolve_video_gloss_and_label(bad_vid, source="bisindo", label_map={})

        # Manifest hanya punya split 'train', saat diminta split='test' wajib lempar ValueError (bukan menyalin train!)
        manifest_only_train = self.tmp_dir / "only_train.csv"
        with manifest_only_train.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["video_id", "source", "gloss", "label", "signer", "kp_path", "rgb_path", "split_sd"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "video_id": "vid_train_1",
                    "source": "bisindo",
                    "gloss": "HALO",
                    "label": 0,
                    "signer": "S01",
                    "kp_path": "kp.npz",
                    "rgb_path": "",
                    "split_sd": "train",
                }
            )
        with self.assertRaises(ValueError) as ctx_empty:
            SignDataset(manifest_path=manifest_only_train, data_root=self.tmp_dir, split="test")
        self.assertIn("Split 'test'", str(ctx_empty.exception))

    def test_16_video_fsl_and_bisindo_separation_enforced(self) -> None:
        """Pastikan FSL-105 dan BISINDO tidak pernah tercampur di extract_keypoints maupun SignDataset."""
        fsl_clips_dir = ROOT / "data" / "raw" / "video" / "fsl_105" / "clips"
        fsl_labels_csv = ROOT / "data" / "raw" / "video" / "fsl_105" / "labels.csv"
        if fsl_clips_dir.exists():
            fsl_label_map = extract_keypoints.load_optional_labels_csv(fsl_clips_dir, fsl_labels_csv)
            sample_fsl_mov = next((fsl_clips_dir / "0").glob("*.MOV"))
            # Jika source='bisindo' diberikan pada video FSL-105, wajib ditolak!
            with self.assertRaises(ValueError) as ctx_mix:
                extract_keypoints.resolve_video_gloss_and_label(
                    sample_fsl_mov, source="bisindo", label_map=fsl_label_map
                )
            self.assertIn("Pencampuran dataset terdeteksi", str(ctx_mix.exception))

            # Verifikasi split resmi train.csv (1.704) dan test.csv (426) pada FSL-105
            split_map = extract_keypoints.load_official_split_map(fsl_clips_dir)
            fsl_videos = extract_keypoints.discover_video_files(fsl_clips_dir)
            train_cnt = sum(
                1 for p in fsl_videos if split_map.get(f"{p.parent.name.lower()}/{p.name.lower()}") == "train"
            )
            test_cnt = sum(
                1 for p in fsl_videos if split_map.get(f"{p.parent.name.lower()}/{p.name.lower()}") == "test"
            )
            self.assertEqual(train_cnt, 1704)
            self.assertEqual(test_cnt, 426)

        # Manifest yang mencampur source='bisindo' dan source='fsl' tanpa source_filter wajib ditolak oleh SignDataset
        mixed_manifest = self.tmp_dir / "mixed_sources.csv"
        with mixed_manifest.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["video_id", "source", "gloss", "label", "signer", "kp_path", "rgb_path", "split_sd"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "video_id": "b1",
                    "source": "bisindo",
                    "gloss": "HALO",
                    "label": 0,
                    "signer": "S01",
                    "kp_path": "b1.npz",
                    "rgb_path": "",
                    "split_sd": "train",
                }
            )
            writer.writerow(
                {
                    "video_id": "f1",
                    "source": "fsl",
                    "gloss": "GOOD MORNING",
                    "label": 0,
                    "signer": "unannotated",
                    "kp_path": "f1.npz",
                    "rgb_path": "",
                    "split_sd": "train",
                }
            )

        with self.assertRaises(ValueError) as ctx_ds_mix:
            SignDataset(manifest_path=mixed_manifest, data_root=self.tmp_dir, split="train")
        self.assertIn("Pencampuran dataset lintas bahasa isyarat", str(ctx_ds_mix.exception))

    def test_17_text_train_test_leakage_both_gloss_and_sentence(self) -> None:
        """Pastikan kebocoran gloss (source) meskipun kalimat berbeda tetap terdeteksi dan ditolak."""
        train_tmp = self.tmp_dir / "train_gloss_leak.tsv"
        val_tmp = self.tmp_dir / "val_clean2.tsv"
        test_tmp = self.tmp_dir / "test_manual2.tsv"

        with test_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["SAYA MAU TANYA GURU", "Saya ingin bertanya kepada guru."])

        with val_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["KAMU BACA BUKU", "Kamu sedang membaca buku."])

        # Gloss sama persis dengan test_tmp meskipun kalimat target berbeda -> wajib ditolak!
        with train_tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["gloss", "kalimat"])
            writer.writerow(["SAYA MAU TANYA GURU", "Kalimat berbeda tetapi gloss bocor."])

        with self.assertRaises(ValueError) as ctx:
            load_and_verify_text_splits(train_path=train_tmp, val_path=val_tmp, test_path=test_tmp)
        self.assertIn("test gloss leakage", str(ctx.exception))

    def test_18_text_vocabulary_fitted_strictly_without_test_set(self) -> None:
        """Pastikan vocabulary dibangun eksklusif dari train_pairs dan kata khusus test dipetakan ke <unk> (3)."""
        train_pairs = [
            ("SAYA BACA BUKU", "Saya sedang membaca buku."),
            ("HALO GURU", "Halo Ibu Guru."),
        ]
        test_pairs = [
            ("KATA_KHUSUS_TEST_GLOSS", "Kalimat eksklusif evaluasi ujian_rahasia."),
        ]

        vocab = build_text_vocabulary(train_pairs, vocab_size=256)
        self.assertNotIn("KATA_KHUSUS_TEST_GLOSS", vocab)
        self.assertNotIn("ujian_rahasia.", vocab)
        self.assertIn("SAYA", vocab)
        self.assertIn("membaca", vocab)

        src_test, tgt_test = encode_pairs_with_vocab(test_pairs, vocab=vocab, max_src_len=4, max_tgt_len=6)
        # Token pertama pada src_test wajib berupa <unk> = 3 karena tidak pernah masuk ke vocab train
        self.assertEqual(int(src_test[0, 0]), vocab["<unk>"])
        self.assertEqual(int(tgt_test[0, 0]), vocab["<bos>"])
        self.assertEqual(int(tgt_test[0, 1]), vocab["<unk>"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

