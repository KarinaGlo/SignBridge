"""
server/database.py — Operational & Telemetry Database (PostgreSQL 16 + SQLAlchemy 2.0)
untuk SignBridge ID-PH (BISINDO <-> FSL).

Menyimpan:
  1. sign_concepts       : 32 Konsep Kelas BISINDO <-> FSL (data/bridge/concepts.csv & phonology.csv) + 26 Abjad A-Z
  2. model_versions      : Registri model M0-M5, I1-I3, A1-A3, B0/T1-T3, X1-X4
  3. evaluation_runs     : Hasil evaluasi nyata (ONNX parity, B0 pada test_manual.tsv 105 kalimat, Bridge ID-PH, dll.)
  4. inference_logs      : Log operasional non-blocking dari /predict, /asr, /sentence, /translate
  5. dataset_recordings  : Metadata rekaman mandiri SignBridge-Kelas (tanpa menyimpan blob video/tensor)

Mendukung Graceful Fallback:
  - Membaca DATABASE_URL (PostgreSQL 16).
  - Jika server PostgreSQL tidak tersedia/mati, otomatis beralih ke SQLite fallback
    tanpa menghentikan aplikasi web, model ONNX, maupun endpoint FastAPI.
"""

from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

ROOT = Path(__file__).resolve().parents[1]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SignConcept(Base):
    __tablename__ = "sign_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    gloss: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    bisindo_label: Mapped[str] = mapped_column(String(128), nullable=False)
    fsl_label: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phonology_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    recordings: Mapped[List["DatasetRecording"]] = relationship(
        "DatasetRecording", back_populates="concept", cascade="all, delete-orphan"
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    modality: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    architecture: Mapped[str] = mapped_column(String(128), nullable=False)
    model_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    dataset_source: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    evaluations: Mapped[List["EvaluationRun"]] = relationship(
        "EvaluationRun", back_populates="model_version", cascade="all, delete-orphan"
    )
    inference_logs: Mapped[List["InferenceLog"]] = relationship(
        "InferenceLog", back_populates="model_version"
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_name: Mapped[str] = mapped_column(String(128), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    protocol: Mapped[str] = mapped_column(String(64), nullable=False)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macro_f1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bleu: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chrf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rtf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", back_populates="evaluations")


class InferenceLog(Base):
    __tablename__ = "inference_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    modality: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    model_version_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    room_code: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    input_summary: Mapped[str] = mapped_column(String(256), nullable=False)
    output_summary: Mapped[str] = mapped_column(String(256), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="inference_logs"
    )


class DatasetRecording(Base):
    __tablename__ = "dataset_recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recording_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    concept_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sign_concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    signer_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    gloss: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=2.6, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    keypoint_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    consent_status: Mapped[str] = mapped_column(String(32), default="approved", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="valid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    concept: Mapped[Optional["SignConcept"]] = relationship("SignConcept", back_populates="recordings")


Index("ix_inference_logs_created_at", InferenceLog.created_at)
Index("ix_eval_runs_model_type", EvaluationRun.model_version_id, EvaluationRun.evaluation_type)


class DatabaseManager:
    """
    Pengelola koneksi database operasional SignBridge dengan dukungan:
    - PostgreSQL 16 utama melalui DATABASE_URL
    - Fallback aman ke SQLite jika PostgreSQL sedang luring/tidak aktif
    - Mode kegagalan terisolasi (simulate_failure) untuk pengujian ketahanan
    """

    def __init__(self, database_url: Optional[str] = None, fallback_url: Optional[str] = None) -> None:
        self.configured_url = (
            database_url
            or os.environ.get("DATABASE_URL")
            or "postgresql+psycopg2://signbridge:signbridge_pass@localhost:5432/signbridge_db"
        )
        default_sqlite = f"sqlite:///{(ROOT / 'data' / 'signbridge_operational.db').as_posix()}"
        self.fallback_url = fallback_url or os.environ.get("SIGNBRIDGE_FALLBACK_DB_URL") or default_sqlite
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker[Session]] = None
        self.active_backend: str = "disconnected"
        self.active_url_masked: str = ""
        self.simulate_failure: bool = False
        self.last_error: Optional[str] = None

    @staticmethod
    def _mask_url(url: str) -> str:
        if "@" in url and "://" in url:
            prefix, rest = url.split("://", 1)
            if "@" in rest and ":" in rest.split("@", 1)[0]:
                creds, hostpart = rest.split("@", 1)
                user = creds.split(":", 1)[0]
                return f"{prefix}://{user}:***@{hostpart}"
        return url

    def _build_engine(self, url: str) -> Engine:
        if url.startswith("postgresql"):
            return create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=1800,
                connect_args={"connect_timeout": 2},
            )
        if url.startswith("sqlite"):
            return create_engine(
                url,
                connect_args={"check_same_thread": False},
            )
        return create_engine(url, pool_pre_ping=True)

    def init_db(self, seed: bool = True) -> bool:
        """
        Inisialisasi skema tabel pada PostgreSQL (atau fallback SQLite jika PostgreSQL belum hidup).
        """
        if self.simulate_failure:
            self.last_error = "Simulated database failure active"
            return False

        # 1. Coba koneksi utama (PostgreSQL atau URL yang dikonfigurasi)
        try:
            eng = self._build_engine(self.configured_url)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=eng)
            self.engine = eng
            self.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False)
            self.active_backend = "postgresql" if self.configured_url.startswith("postgresql") else "sqlite"
            self.active_url_masked = self._mask_url(self.configured_url)
            self.last_error = None
            if seed:
                self.seed_initial_data()
            return True
        except Exception as pg_err:
            self.last_error = str(pg_err)

        # 2. Graceful Fallback ke SQLite agar aplikasi & pengujian tetap berjalan
        try:
            if self.fallback_url.startswith("sqlite:///") and ":memory:" not in self.fallback_url:
                db_file = Path(self.fallback_url.replace("sqlite:///", ""))
                db_file.parent.mkdir(parents=True, exist_ok=True)
            eng = self._build_engine(self.fallback_url)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=eng)
            self.engine = eng
            self.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False)
            self.active_backend = "sqlite-fallback"
            self.active_url_masked = self._mask_url(self.fallback_url)
            if seed:
                self.seed_initial_data()
            return True
        except Exception as fb_err:
            self.last_error = f"Primary & fallback failed: {fb_err}"
            self.engine = None
            self.SessionLocal = None
            self.active_backend = "disconnected"
            return False

    def is_connected(self) -> bool:
        if self.simulate_failure or self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def seed_initial_data(self) -> None:
        """
        Seed data faktual dari berkas repositori (data/bridge/concepts.csv, data/phonology.csv,
        web/model/fingerspell.json, configs/*.yaml, dan evaluasi nyata yang terverifikasi).
        """
        if self.SessionLocal is None or self.simulate_failure:
            return

        with self.SessionLocal() as session:
            # A. Seed sign_concepts jika kosong
            existing_concepts = session.scalar(select(func.count(SignConcept.id))) or 0
            if existing_concepts == 0:
                phono_map: Dict[str, Dict[str, Any]] = {}
                phono_csv = ROOT / "data" / "phonology.csv"
                if phono_csv.exists():
                    with phono_csv.open("r", encoding="utf-8") as f:
                        for row in csv.DictReader(f):
                            g = (row.get("gloss") or "").strip().upper()
                            if g:
                                phono_map[g] = {
                                    "handshape": int(row.get("handshape", 0)),
                                    "location": int(row.get("location", 0)),
                                    "movement": int(row.get("movement", 0)),
                                    "two_handed": int(row.get("two_handed", 0)),
                                }

                concepts_csv = ROOT / "data" / "bridge" / "concepts.csv"
                if concepts_csv.exists():
                    with concepts_csv.open("r", encoding="utf-8") as f:
                        for row in csv.DictReader(f):
                            cid = (row.get("concept_id") or "").strip()
                            bisindo = (row.get("bisindo_gloss") or "").strip().upper()
                            fsl = (row.get("fsl_gloss") or "").strip().upper()
                            cat = (row.get("category") or "Umum").strip()
                            id_txt = (row.get("id") or row.get("id_text") or "").strip()
                            fil_txt = (row.get("fil") or row.get("fil_text") or "").strip()
                            en_txt = (row.get("en") or row.get("en_text") or "").strip()
                            if cid and bisindo:
                                session.add(
                                    SignConcept(
                                        concept_code=cid,
                                        gloss=bisindo,
                                        bisindo_label=id_txt or bisindo,
                                        fsl_label=f"{fsl} ({fil_txt})" if fil_txt else fsl,
                                        category=cat,
                                        description=f"ID: {id_txt} | PH: {fil_txt} | EN: {en_txt}",
                                        phonology_json=phono_map.get(bisindo, {}),
                                    )
                                )

                # Tambahkan 26 Abjad Ejaan Jari (A-Z) dari web/model/fingerspell.json
                fs_json = ROOT / "web" / "model" / "fingerspell.json"
                letters: List[str] = [chr(65 + i) for i in range(26)]
                if fs_json.exists():
                    try:
                        loaded = json.loads(fs_json.read_text(encoding="utf-8"))
                        if isinstance(loaded, list) and len(loaded) == 26:
                            letters = [str(x).upper() for x in loaded]
                    except Exception:
                        pass
                for idx, letter in enumerate(letters, start=1):
                    session.add(
                        SignConcept(
                            concept_code=f"A{idx:02d}",
                            gloss=f"ABJAD_{letter}",
                            bisindo_label=letter,
                            fsl_label=letter,
                            category="Abjad Ejaan Jari",
                            description=f"Huruf Ejaan Jari Statis {letter} (BISINDO & FSL)",
                            phonology_json={"type": "fingerspelling", "letter": letter},
                        )
                    )
                session.commit()

            # B. Seed model_versions sesuai arsitektur aktual di repositori
            existing_models = session.scalar(select(func.count(ModelVersion.id))) or 0
            if existing_models == 0:
                models_seed = [
                    ModelVersion(
                        model_code="M0",
                        model_name="Student BiGRU/Transformer Scratch Baseline",
                        modality="video",
                        version="1.0.0",
                        architecture="StudentPoseTransformer (BiGRU + Temporal Attention)",
                        model_path="configs/m0_student_scratch.yaml",
                        dataset_source="WL-BISINDO + SignBridge-Kelas (86-node keypoints)",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="M1",
                        model_name="ST-GCN Pose-Only Teacher",
                        modality="video",
                        version="1.0.0",
                        architecture="Adaptive ST-GCN 86-Node + Multitask Phonology Heads",
                        model_path="configs/m1_pose.yaml",
                        dataset_source="WL-BISINDO + SignBridge-Kelas (86-node + phonology.csv)",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="M2",
                        model_name="VideoMAE RGB-Only Teacher",
                        modality="video",
                        version="1.0.0",
                        architecture="RGBOnlyModel (VideoMAE 768-d Token Transformer)",
                        model_path="configs/m2_rgb.yaml",
                        dataset_source="WL-BISINDO RGB Tokens [8, 768]",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="M3",
                        model_name="Two-Stream Late Concat Fusion",
                        modality="video",
                        version="1.0.0",
                        architecture="TwoStreamFusionModel (ST-GCN + VideoMAE Concat)",
                        model_path="configs/m3_late_fusion.yaml",
                        dataset_source="WL-BISINDO Pose + RGB",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="M4",
                        model_name="Two-Stream Cross-Modal Attention Teacher",
                        modality="video",
                        version="1.0.0",
                        architecture="TwoStreamFusionModel (Bidirectional Cross-Attention)",
                        model_path="configs/m4_cross_attn.yaml",
                        dataset_source="WL-BISINDO + WLASL-300 Pretrain + Phonology",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="M5",
                        model_name="Distilled Student Pose Transformer (ONNX Web)",
                        modality="video",
                        version="2.0.0",
                        architecture="StudentPoseTransformer (KD from M4 Teacher, INT8 ONNX)",
                        model_path="web/model/student.onnx",
                        dataset_source="WL-BISINDO + SignBridge-Kelas (32 Glosses)",
                        is_active=True,
                    ),
                    ModelVersion(
                        model_code="I1",
                        model_name="MobileNetV3-Small Fingerspelling A-Z (ONNX Web)",
                        modality="image",
                        version="1.0.0",
                        architecture="MobileNetV3-Small (224x224 Hand Crop +25% Margin)",
                        model_path="web/model/fingerspell.onnx",
                        dataset_source="BISINDO Alphabet Image Data + Hand Crop Tim",
                        is_active=True,
                    ),
                    ModelVersion(
                        model_code="I2",
                        model_name="EfficientNet-B0 Fingerspelling A-Z",
                        modality="image",
                        version="1.0.0",
                        architecture="EfficientNet-B0 (224x224 RGB)",
                        model_path="configs/i2_efficientnet_b0.yaml",
                        dataset_source="BISINDO Alphabet Image Data",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="I3",
                        model_name="MobileViT-XS Fingerspelling A-Z",
                        modality="image",
                        version="1.0.0",
                        architecture="MobileViT-XS Hybrid CNN-ViT (224x224 RGB)",
                        model_path="configs/i3_mobilevit_xs.yaml",
                        dataset_source="BISINDO Alphabet Image Data",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="A1",
                        model_name="Whisper-Tiny Zero-Shot ASR",
                        modality="audio",
                        version="1.0.0",
                        architecture="openai/whisper-tiny (Zero-Shot id & tl)",
                        model_path="configs/a1_whisper_tiny_zeroshot.yaml",
                        dataset_source="FLEURS id_id & Rekaman Suara Kelas",
                        is_active=True,
                    ),
                    ModelVersion(
                        model_code="A2",
                        model_name="Whisper-Tiny Fine-Tuned Classroom ASR",
                        modality="audio",
                        version="1.0.0",
                        architecture="openai/whisper-tiny (Fine-Tuned Domain Kelas)",
                        model_path="configs/a2_whisper_tiny_ft.yaml",
                        dataset_source="FLEURS id_id + data/audio/metadata.csv",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="A3",
                        model_name="Whisper-Small Zero-Shot / FT ASR",
                        modality="audio",
                        version="1.0.0",
                        architecture="openai/whisper-small",
                        model_path="configs/a3_whisper_small_zeroshot.yaml",
                        dataset_source="FLEURS id_id + data/audio/metadata.csv",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="B0",
                        model_name="Rule-Based Indonesian & Filipino Grammar Engine",
                        modality="text",
                        version="2.0.0",
                        architecture="Deterministic Affix & Phrase Table (pseudo_gloss.py & sentence.js)",
                        model_path="signbridge/text/pseudo_gloss.py",
                        dataset_source="data/text/test_manual.tsv (105 Kalimat Manusia)",
                        is_active=True,
                    ),
                    ModelVersion(
                        model_code="T1",
                        model_name="BiGRU Seq2Seq + Bahdanau Attention",
                        modality="text",
                        version="1.0.0",
                        architecture="GRUAttentionSeq2Seq",
                        model_path="configs/t1_gru_seq2seq.yaml",
                        dataset_source="Tatoeba Indonesian + data/text/train.tsv (170 pairs)",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="T2",
                        model_name="IndoT5-Small Gloss-to-Sentence",
                        modality="text",
                        version="1.0.0",
                        architecture="LazarusNLP/IndoT5-base-small",
                        model_path="configs/t2_indot5_small.yaml",
                        dataset_source="Tatoeba Indonesian + data/text/train.tsv",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="T3",
                        model_name="mT5-Small Multilingual Gloss-to-Sentence",
                        modality="text",
                        version="1.0.0",
                        architecture="google/mt5-small (ID & FIL)",
                        model_path="configs/t3_mt5_small.yaml",
                        dataset_source="data/text/train.tsv + data/bridge/concepts.csv",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="X1",
                        model_name="ST-GCN WLASL Pretrain",
                        modality="fsl_video",
                        version="1.0.0",
                        architecture="ST-GCN 86-Node (WLASL-300 Init)",
                        model_path="configs/x1_wlasl_pretrain.yaml",
                        dataset_source="WLASL-300",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="X2",
                        model_name="FSL-105 Scratch ST-GCN",
                        modality="fsl_video",
                        version="1.0.0",
                        architecture="ST-GCN 86-Node (No Transfer)",
                        model_path="configs/x2_fsl_scratch.yaml",
                        dataset_source="FSL-105 (Mendeley)",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="X3",
                        model_name="FSL-105 Transfer from BISINDO",
                        modality="fsl_video",
                        version="1.0.0",
                        architecture="ST-GCN 86-Node (BISINDO M1 Init -> FSL)",
                        model_path="configs/x3_fsl_from_bisindo.yaml",
                        dataset_source="WL-BISINDO -> FSL-105",
                        is_active=False,
                    ),
                    ModelVersion(
                        model_code="X4",
                        model_name="FSL-105 Transfer from WLASL+BISINDO",
                        modality="fsl_video",
                        version="1.0.0",
                        architecture="ST-GCN 86-Node (WLASL -> BISINDO -> FSL)",
                        model_path="configs/x4_fsl_from_wlasl_bisindo.yaml",
                        dataset_source="WLASL-300 -> WL-BISINDO -> FSL-105",
                        is_active=False,
                    ),
                ]
                session.add_all(models_seed)
                session.commit()

            # C. Seed evaluation_runs HANYA dengan hasil pengukuran faktual yang dijalankan secara nyata
            existing_evals = session.scalar(select(func.count(EvaluationRun.id))) or 0
            if existing_evals == 0:
                self._run_and_record_verified_evaluations(session)

    def _run_and_record_verified_evaluations(self, session: Session) -> None:
        """
        Jalankan evaluasi nyata pada artefak yang tersedia di repositori (data/text/test_manual.tsv,
        web/model/student.onnx, dan web/model/fingerspell.onnx) lalu simpan angka faktualnya.
        """
        from signbridge.audio.train_asr import compute_wer
        from signbridge.text.pseudo_gloss import gloss_to_sentence_rules
        from signbridge.text.train_text import compute_bleu, compute_chrf

        # 1. Evaluasi nyata B0 pada 105 kalimat manusia di data/text/test_manual.tsv
        b0_model = session.scalar(select(ModelVersion).where(ModelVersion.model_code == "B0"))
        test_tsv = ROOT / "data" / "text" / "test_manual.tsv"
        if b0_model and test_tsv.exists():
            t0 = time.perf_counter()
            with test_tsv.open("r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f, delimiter="\t"))
            preds: List[str] = []
            refs: List[str] = []
            wers: List[float] = []
            exact = 0
            for r in rows:
                g = (r.get("gloss") or "").strip()
                ref = (r.get("kalimat") or "").strip()
                if not g or not ref:
                    continue
                pred = gloss_to_sentence_rules(g, lang="id")
                preds.append(pred)
                refs.append(ref)
                wers.append(compute_wer(ref.lower(), pred.lower()))
                if pred.strip().lower() == ref.strip().lower():
                    exact += 1
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            n_samples = max(1, len(refs))
            real_bleu = float(compute_bleu(preds, refs))
            real_chrf = float(compute_chrf(preds, refs))
            real_wer = float(np.mean(wers)) if wers else 0.0
            real_acc = float(exact) / n_samples

            session.add(
                EvaluationRun(
                    model_version_id=b0_model.id,
                    dataset_name="data/text/test_manual.tsv (Disjoint Human Test Set)",
                    evaluation_type="text_gloss_to_sentence",
                    protocol="disjoint_human_105",
                    accuracy=round(real_acc, 4),
                    wer=round(real_wer, 4),
                    bleu=round(real_bleu, 2),
                    chrf=round(real_chrf, 2),
                    latency_ms=round(elapsed_ms / n_samples, 4),
                    test_count=len(refs),
                    result_path="data/text/test_manual.tsv",
                    details_json={
                        "exact_match_count": exact,
                        "total_sentences": len(refs),
                        "verified_by": "SignBridge Automated Suite",
                    },
                )
            )

        # 2. Validasi nyata latensi & struktur ONNX Student Model (M5)
        m5_model = session.scalar(select(ModelVersion).where(ModelVersion.model_code == "M5"))
        student_onnx = ROOT / "web" / "model" / "student.onnx"
        if m5_model and student_onnx.exists():
            try:
                import onnxruntime as ort

                sess = ort.InferenceSession(str(student_onnx), providers=["CPUExecutionProvider"])
                dummy = np.zeros((1, 64, 86, 3), dtype=np.float32)
                t0 = time.perf_counter()
                out = sess.run(["logits"], {"keypoints": dummy})[0]
                lat_ms = (time.perf_counter() - t0) * 1000.0
                size_mb = student_onnx.stat().st_size / (1024 * 1024)
                session.add(
                    EvaluationRun(
                        model_version_id=m5_model.id,
                        dataset_name="ONNX Contract-2 Verification ([1,64,86,3] -> [1,32])",
                        evaluation_type="onnx_validation",
                        protocol="contract_2_parity",
                        latency_ms=round(lat_ms, 3),
                        test_count=1,
                        result_path="web/model/student.onnx",
                        details_json={
                            "output_shape": list(out.shape),
                            "size_mb": round(size_mb, 3),
                            "size_under_10mb": size_mb < 10.0,
                        },
                    )
                )
            except Exception:
                pass

        # 3. Validasi nyata latensi & struktur ONNX Fingerspelling Model (I1)
        i1_model = session.scalar(select(ModelVersion).where(ModelVersion.model_code == "I1"))
        fs_onnx = ROOT / "web" / "model" / "fingerspell.onnx"
        if i1_model and fs_onnx.exists():
            try:
                import onnxruntime as ort

                sess = ort.InferenceSession(str(fs_onnx), providers=["CPUExecutionProvider"])
                dummy_img = np.zeros((1, 3, 224, 224), dtype=np.float32)
                t0 = time.perf_counter()
                out = sess.run(["logits"], {"image": dummy_img})[0]
                lat_ms = (time.perf_counter() - t0) * 1000.0
                size_mb = fs_onnx.stat().st_size / (1024 * 1024)
                session.add(
                    EvaluationRun(
                        model_version_id=i1_model.id,
                        dataset_name="ONNX Contract-5 Verification ([1,3,224,224] -> [1,26])",
                        evaluation_type="onnx_validation",
                        protocol="contract_5_parity",
                        latency_ms=round(lat_ms, 3),
                        test_count=1,
                        result_path="web/model/fingerspell.onnx",
                        details_json={
                            "output_shape": list(out.shape),
                            "size_mb": round(size_mb, 3),
                        },
                    )
                )
            except Exception:
                pass

        session.commit()

    def log_inference_safe(
        self,
        endpoint: str,
        modality: str,
        input_summary: str,
        output_summary: str,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        room_code: Optional[str] = None,
        model_code: Optional[str] = None,
        status: str = "success",
    ) -> Optional[int]:
        """
        Catat aktivitas inferensi ke tabel inference_logs secara aman (non-throwing).
        Jika database sedang bermasalah atau disimulasikan gagal, tidak pernah melempar exception.
        """
        if self.simulate_failure or self.SessionLocal is None:
            return None
        try:
            with self.SessionLocal() as session:
                model_id = None
                if model_code:
                    model_id = session.scalar(
                        select(ModelVersion.id).where(ModelVersion.model_code == model_code)
                    )
                entry = InferenceLog(
                    endpoint=endpoint[:64],
                    modality=modality[:32],
                    model_version_id=model_id,
                    room_code=(room_code or "")[:32] or None,
                    input_summary=str(input_summary)[:256],
                    output_summary=str(output_summary)[:256],
                    confidence=float(confidence) if confidence is not None else None,
                    latency_ms=float(latency_ms) if latency_ms is not None else None,
                    status=status[:32],
                )
                session.add(entry)
                session.commit()
                return entry.id
        except Exception as e:
            self.last_error = str(e)
            return None

    def get_status_summary(self) -> Dict[str, Any]:
        connected = self.is_connected()
        counts = {
            "sign_concepts": 0,
            "model_versions": 0,
            "evaluation_runs": 0,
            "inference_logs": 0,
            "dataset_recordings": 0,
        }
        if connected and self.SessionLocal is not None:
            try:
                with self.SessionLocal() as session:
                    counts["sign_concepts"] = session.scalar(select(func.count(SignConcept.id))) or 0
                    counts["model_versions"] = session.scalar(select(func.count(ModelVersion.id))) or 0
                    counts["evaluation_runs"] = session.scalar(select(func.count(EvaluationRun.id))) or 0
                    counts["inference_logs"] = session.scalar(select(func.count(InferenceLog.id))) or 0
                    counts["dataset_recordings"] = session.scalar(select(func.count(DatasetRecording.id))) or 0
            except Exception as e:
                self.last_error = str(e)
                connected = False

        return {
            "db_connected": connected,
            "active_backend": self.active_backend if connected else "disconnected",
            "database_url": self.active_url_masked,
            "tables": list(counts.keys()),
            "counts": counts,
            "last_error": self.last_error if not connected else None,
        }

