"""
signbridge_model.py — Full Teacher_Model and Student_Model assembly.

Task 6.11.
Requirements: 11.5, 14.1.

Kontrak antarmuka ONNX (tidak boleh berubah):
  StudentModel input:  float32 [1, 64, 86, 3]
  StudentModel output: float32 [1, 32]
  Labels:              labels.json (32 gloss BISINDO)

SignBridgeModel (Teacher):
    Stream_A + Stream_B + GatedFusion/CrossAttention + GlossHead + FonologiHead
    Loss teacher: ℒ = CE_ls(y) + 0.3*(CE_pose + CE_rgb)
                       + 0.5 * (1/|F|) * Σ_f CE(fonologi_f)

StudentModel:
    Pose-only (Stream_A + GlossHead), dirancang untuk ONNX export ≤ 10 MB.
    Loss distilasi: ℒ = α*CE(y,s) + (1-α)*T²*KL(σ(t/T) ‖ σ(s/T))
    Kontrak: α=0.5, T=4 (tidak boleh berubah).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import torch
import torch.nn as nn

from src.model.stream_a import StreamA
from src.model.stream_b import StreamB
from src.model.fusion import build_fusion, GatedFusionModule, CrossAttentionFusionModule
from src.model.heads import GlossHead, FonologisHead


# ---------------------------------------------------------------------------
# Config dataclasses (mirror configs/train_bisindo.yaml → model section)
# ---------------------------------------------------------------------------

@dataclass
class StreamAConfig:
    arch: str = "stgcn"
    num_blocks: int = 10
    hidden_dim: int = 256
    num_heads: int = 8
    num_keypoints: int = 86    # kontrak: 86 node (tidak boleh berubah)
    num_coords: int = 3


@dataclass
class StreamBConfig:
    arch: str = "videomae"
    pretrained_url: str = ""
    frozen_layers: List[str] = field(default_factory=list)
    output_dim: int = 512
    num_frames: int = 16


@dataclass
class FusionConfig:
    type: str = "cross_attention"  # "gated" (E4) | "cross_attention" (E5)
    dim: int = 512
    num_heads: int = 8         # hanya digunakan oleh cross_attention


@dataclass
class GlossHeadConfig:
    in_dim: int = 512
    label_smoothing: float = 0.1


@dataclass
class FonologiHeadConfig:
    in_dim: int = 512
    num_handshape: int = 20
    num_lokasi: int = 10
    num_arah_gerak: int = 8
    lambda_handshape: float = 0.3
    lambda_lokasi: float = 0.3
    lambda_arah_gerak: float = 0.3


PhonologicalHeadConfig = FonologiHeadConfig


class ModelConfig:
    """Top-level model configuration (maps to the ``model:`` section of train YAML)."""

    def __init__(
        self,
        num_classes: int = 32,
        use_fonologi_head: Optional[bool] = None,
        use_phonological_head: Optional[bool] = None,
        t_max: int = 64,
        stream_a: Optional[StreamAConfig] = None,
        stream_b: Optional[StreamBConfig] = None,
        fusion: Optional[FusionConfig] = None,
        gloss_head: Optional[GlossHeadConfig] = None,
        fonologi_head: Optional[FonologiHeadConfig] = None,
        phonological_head: Optional[FonologiHeadConfig] = None,
    ):
        self.num_classes = num_classes
        if use_phonological_head is not None:
            self.use_fonologi_head = bool(use_phonological_head)
        elif use_fonologi_head is not None:
            self.use_fonologi_head = bool(use_fonologi_head)
        else:
            self.use_fonologi_head = True
        self.t_max = t_max
        self.stream_a = stream_a if stream_a is not None else StreamAConfig()
        self.stream_b = stream_b if stream_b is not None else StreamBConfig()
        self.fusion = fusion if fusion is not None else FusionConfig()
        self.gloss_head = gloss_head if gloss_head is not None else GlossHeadConfig()
        if phonological_head is not None:
            self.fonologi_head = phonological_head
        elif fonologi_head is not None:
            self.fonologi_head = fonologi_head
        else:
            self.fonologi_head = FonologiHeadConfig()

    @property
    def use_phonological_head(self) -> bool:
        return self.use_fonologi_head

    @property
    def phonological_head(self) -> FonologiHeadConfig:
        return self.fonologi_head



# ---------------------------------------------------------------------------
# Output containers
# ---------------------------------------------------------------------------

@dataclass
class ModelOutput:
    """Output dari SignBridgeModel.forward()."""
    gloss_logits: torch.Tensor                             # [B, num_classes]
    pose_logits: Optional[torch.Tensor] = None             # [B, num_classes] — dari Stream_A saja
    rgb_logits: Optional[torch.Tensor] = None              # [B, num_classes] — dari Stream_B saja
    phono: Optional[Dict[str, torch.Tensor]] = None        # fonologi logits dict | None
    attn: Optional[Dict[str, torch.Tensor]] = None         # attention weights (E5) | None


# ---------------------------------------------------------------------------
# SignBridgeModel (Teacher) — Task 6.11
# ---------------------------------------------------------------------------

class SignBridgeModel(nn.Module):
    """
    Teacher_Model: Stream_A + Stream_B + Fusion + GlossHead + FonologiHead.

    Mendukung dua tipe fusion (dikonfigurasi via ModelConfig.fusion.type):
      - "gated"           : GatedFusionModule (E4, default)
      - "cross_attention" : CrossAttentionFusionModule (E5)

    Forward:
        keypoints:     [B, T_max=64, 86, 3]  (kontrak ONNX)
        frames:        [B, 16, 3, H, W]
        padding_mask:  [B, T_max]  (True = valid)
    Returns:
        ModelOutput(gloss_logits, pose_logits, rgb_logits, phono, attn)

    Loss teacher (Requirements 11.3):
        ℒ = CE_ls(y) + 0.3*(CE_pose + CE_rgb)
            + 0.5 * (1/|F|) * Σ_f CE(fonologi_f)
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.use_fonologi_head = config.use_fonologi_head

        # Stream_A — input [B, 64, 86, 3]
        sa_cfg = config.stream_a
        self.stream_a = StreamA(
            num_blocks=sa_cfg.num_blocks,
            hidden_dim=sa_cfg.hidden_dim,
            num_heads=sa_cfg.num_heads,
            num_keypoints=sa_cfg.num_keypoints,  # 86
            num_coords=sa_cfg.num_coords,
            arch=sa_cfg.arch,
        )

        # Stream_B — input [B, 16, 3, H, W]
        sb_cfg = config.stream_b
        self.stream_b = StreamB(
            arch=sb_cfg.arch,
            pretrained_url=sb_cfg.pretrained_url,
            frozen_layers=sb_cfg.frozen_layers,
            output_dim=sb_cfg.output_dim,
            num_frames=sb_cfg.num_frames,
        )

        # Auxiliary GlossHead per stream (untuk komponen loss teacher)
        self.pose_head = GlossHead(in_dim=512, num_classes=config.num_classes)
        self.rgb_head = GlossHead(in_dim=sb_cfg.output_dim,
                                  num_classes=config.num_classes)

        # Fusion: gated (E4) atau cross_attention (E5)
        fus_cfg = config.fusion
        self.fusion = build_fusion(
            fusion_type=fus_cfg.type,
            dim=fus_cfg.dim,
            num_heads=fus_cfg.num_heads,
        )
        self.fusion_type = fus_cfg.type

        # Gloss head utama
        self.gloss_head = GlossHead(
            in_dim=config.gloss_head.in_dim,
            num_classes=config.num_classes,
        )

        # Fonologi head (hanya jika diaktifkan)
        if self.use_fonologi_head:
            ph_cfg = config.fonologi_head
            self.fonologi_head = FonologisHead(
                in_dim=ph_cfg.in_dim,
                num_handshape=ph_cfg.num_handshape,
                num_lokasi=ph_cfg.num_lokasi,
                num_arah_gerak=ph_cfg.num_arah_gerak,
            )
        else:
            self.fonologi_head = None

    @property
    def fonologis_head(self):
        return self.fonologi_head

    @property
    def use_phonological_head(self) -> bool:
        return self.use_fonologi_head

    # ------------------------------------------------------------------

    def forward(
        self,
        keypoints: torch.Tensor,    # [B, T_max=64, 86, 3]
        frames: torch.Tensor,       # [B, 16, 3, H, W]
        padding_mask: torch.Tensor, # [B, T_max]  True = valid
    ) -> ModelOutput:
        # Stream A → p̄ [B, 512]
        feat_a = self.stream_a(keypoints, padding_mask)

        # Stream B → r̄ [B, 512]
        feat_b = self.stream_b(frames)

        # Auxiliary logits per-stream (untuk loss teacher)
        pose_logits = self.pose_head(feat_a)   # [B, num_classes]
        rgb_logits  = self.rgb_head(feat_b)    # [B, num_classes]

        # Fusion → z [B, 512]
        fused, attn = self.fusion(feat_a, feat_b)

        # Gloss head utama → [B, num_classes]
        gloss_logits = self.gloss_head(fused)

        # Fonologi head → dict | None
        phono = None
        if self.use_fonologi_head and self.fonologi_head is not None:
            phono = self.fonologi_head(fused)

        return ModelOutput(
            gloss_logits=gloss_logits,
            pose_logits=pose_logits,
            rgb_logits=rgb_logits,
            phono=phono,
            attn=attn,
        )


# ---------------------------------------------------------------------------
# StudentModel — pose-only, dirancang untuk ONNX export ≤ 10 MB
# ---------------------------------------------------------------------------

class StudentModel(nn.Module):
    """
    Student_Model (pose-only): Stream_A + GlossHead.

    Tanpa Stream_B, tanpa Fusion — dirancang untuk ONNX export ≤ 10 MB.

    Kontrak ONNX (tidak boleh berubah — Requirement 14.5):
        Input:  float32 [1, 64, 86, 3]
        Output: float32 [1, 32]
        Labels: labels.json

    Loss distilasi (Requirement 14.2, kontrak α=0.5, T=4):
        ℒ = α·CE(y,s) + (1-α)·T²·KL(σ(t/T) ‖ σ(s/T))

    Forward:
        keypoints:     [B, T_max=64, 86, 3]
        padding_mask:  [B, T_max]  (True = valid)
    Returns:
        gloss_logits:  [B, num_classes]
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # Stream_A only (pose-only)
        sa_cfg = config.stream_a
        self.stream_a = StreamA(
            num_blocks=sa_cfg.num_blocks,
            hidden_dim=sa_cfg.hidden_dim,
            num_heads=sa_cfg.num_heads,
            num_keypoints=sa_cfg.num_keypoints,  # 86
            num_coords=sa_cfg.num_coords,
            arch=sa_cfg.arch,
        )

        # Gloss head only
        self.gloss_head = GlossHead(
            in_dim=config.gloss_head.in_dim,
            num_classes=config.num_classes,
        )

    # ------------------------------------------------------------------

    def forward(
        self,
        keypoints: torch.Tensor,    # [B, T_max=64, 86, 3]  — kontrak ONNX
        padding_mask: torch.Tensor, # [B, T_max]  True = valid
    ) -> torch.Tensor:              # [B, num_classes]
        feat_a = self.stream_a(keypoints, padding_mask)  # [B, 512]
        gloss_logits = self.gloss_head(feat_a)           # [B, num_classes]
        return gloss_logits
