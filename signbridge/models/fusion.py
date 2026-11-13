"""
fusion.py — Two-Stream Teacher Model (M4 Cross-Attention & M3 Concat/Gate Ablation)
and RGBOnlyModel (M2 VideoMAE Token Classifier).

Follows Bab 1.4, 1.5, & Bab 5.6, 5.10:
  - Stream A (Pose): ST-GCN -> 16 temporal tokens x 256-d
  - Stream B (RGB):  8 VideoMAE tokens [B, 8, 768] -> Linear(256) + 2-layer Transformer -> 8 tokens x 256-d
  - Bidirectional Cross-Attention (fusion_layers=2 for M4; fusion_layers=0 for M3 ablation):
      * Q=pose, K/V=RGB: softmax(Q_p K_r^T / sqrt(d_k)) V_r
      * Q=RGB, K/V=pose: softmax(Q_r K_p^T / sqrt(d_k)) V_p
  - Gated Fusion:
      * g = sigma(W [p_bar; r_bar])
      * z = g * p_bar + (1 - g) * r_bar
  - Heads:
      * Main 32-gloss head on z
      * Auxiliary pose head on p_bar & auxiliary RGB head on r_bar (weight 0.3)
      * Multitask phonology head on z (weight 0.5)
  - Modality dropout (rgb_drop_p=0.1) during training so teacher does not over-rely on RGB
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn

from signbridge.constants import RGB_NUM_TOKENS, RGB_TOKEN_DIM
from signbridge.models.stgcn import STGCNEncoder, PhonologyMultitaskHead
from signbridge.models.student import StudentPoseTransformer
from signbridge.models.stgcn import PoseModel


class RGBStreamEncoder(nn.Module):
    """
    Stream B encoder over frozen VideoMAE tokens [B, 8, 768] -> [B, 8, d_model=256].
    """

    def __init__(
        self,
        in_dim: int = RGB_TOKEN_DIM,
        d_model: int = 256,
        nhead: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        max_tokens: int = RGB_NUM_TOKENS,
    ) -> None:
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(in_dim, d_model),
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
        )
        self.pos_embed = nn.Parameter(torch.randn(1, max_tokens, d_model) * 0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, rgb_tokens: torch.Tensor) -> torch.Tensor:
        """rgb_tokens: [B, 8, 768] -> [B, 8, d_model]"""
        T = rgb_tokens.shape[1]
        x = self.proj(rgb_tokens) + self.pos_embed[:, :T, :]
        x = self.transformer(x)
        return self.norm(x)


class RGBOnlyModel(nn.Module):
    """
    M2 (E7): VideoMAE RGB-Only Classifier (Bab 5.10):
      8 VideoMAE tokens [B, 8, 768] -> Linear(256) -> 2-layer Transformer -> mean pool -> Linear(num_classes)
    """

    def __init__(
        self,
        num_classes: int = 32,
        d_model: int = 256,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.rgb_encoder = RGBStreamEncoder(d_model=d_model, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(
        self,
        pose: Optional[torch.Tensor] = None,
        rgb: Optional[torch.Tensor] = None,
    ) -> Dict[str, Optional[torch.Tensor]]:
        if rgb is None:
            raise ValueError("RGBOnlyModel requires `rgb` token tensor [B, 8, 768].")
        tokens = self.rgb_encoder(rgb)
        pooled = self.dropout(tokens.mean(dim=1))
        logits = self.classifier(pooled)
        return {
            "logits": logits,
            "pose_logits": None,
            "rgb_logits": logits,
            "phonology_logits": None,
            "gate": None,
            "features": pooled,
        }


class CrossAttentionLayer(nn.Module):
    """
    Bidirectional Cross-Attention Layer between Pose tokens [B, T_p, D] and RGB tokens [B, T_r, D]:
      - Pose attends to RGB (Q=pose, K=RGB, V=RGB)
      - RGB attends to Pose (Q=RGB, K=pose, V=pose)
    """

    def __init__(self, d_model: int = 256, nhead: int = 4, dropout: float = 0.1) -> None:
        super().__init__()
        self.p2r_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.r2p_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)

        self.norm_p1 = nn.LayerNorm(d_model)
        self.norm_r1 = nn.LayerNorm(d_model)

        self.ffn_p = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model),
        )
        self.ffn_r = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model),
        )
        self.norm_p2 = nn.LayerNorm(d_model)
        self.norm_r2 = nn.LayerNorm(d_model)

    def forward(
        self,
        pose_tokens: torch.Tensor,
        rgb_tokens: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        # Pose queries RGB
        p_attn, w_p2r = self.p2r_attn(
            query=pose_tokens,
            key=rgb_tokens,
            value=rgb_tokens,
            need_weights=True,
        )
        # RGB queries Pose
        r_attn, w_r2p = self.r2p_attn(
            query=rgb_tokens,
            key=pose_tokens,
            value=pose_tokens,
            need_weights=True,
        )

        p_out = self.norm_p1(pose_tokens + p_attn)
        p_out = self.norm_p2(p_out + self.ffn_p(p_out))

        r_out = self.norm_r1(rgb_tokens + r_attn)
        r_out = self.norm_r2(r_out + self.ffn_r(r_out))

        return p_out, r_out, {"p2r": w_p2r, "r2p": w_r2p}


class GatedFusion(nn.Module):
    """
    Gated Fusion (Bab 1.5 Rumus Inti):
        g = sigma(W [p_bar; r_bar])
        z = g * p_bar + (1 - g) * r_bar
    """

    def __init__(self, d_model: int = 256) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(d_model * 2, d_model)

    def forward(
        self,
        p_bar: torch.Tensor,
        r_bar: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        concat = torch.cat([p_bar, r_bar], dim=-1)
        g = torch.sigmoid(self.gate_proj(concat))
        z = g * p_bar + (1.0 - g) * r_bar
        return z, g


class TwoStreamFusionModel(nn.Module):
    """
    Teacher Two-Stream Model:
      - M4 (E5): fusion_layers=2 (Bidirectional Cross-Attention + Gated Fusion)
      - M3 (E4): fusion_layers=0 (Gated Concatenation without Cross-Attention for ablation)
    """

    def __init__(
        self,
        num_classes: int = 32,
        d_model: int = 256,
        nhead: int = 4,
        fusion_layers: int = 2,
        dropout: float = 0.2,
        rgb_drop_p: float = 0.1,
        use_phonology: bool = True,
        phono_num_classes: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.d_model = d_model
        self.fusion_layers_count = int(fusion_layers)
        self.rgb_drop_p = float(rgb_drop_p)
        self.use_phonology = bool(use_phonology)

        # Stream A (ST-GCN) & Stream B (VideoMAE Token Transformer)
        self.stream_a = STGCNEncoder(hidden_dim=d_model, dropout=dropout)
        self.stream_b = RGBStreamEncoder(d_model=d_model, nhead=nhead, dropout=dropout)

        # Auxiliary per-stream heads (weight 0.3 in teacher loss)
        self.pose_aux_head = nn.Linear(d_model, num_classes)
        self.rgb_aux_head = nn.Linear(d_model, num_classes)

        # Cross-Attention stack (empty when fusion_layers == 0 for M3 ablation)
        self.cross_layers = nn.ModuleList(
            [CrossAttentionLayer(d_model=d_model, nhead=nhead, dropout=dropout) for _ in range(self.fusion_layers_count)]
        )

        # Gated fusion
        self.gated_fusion = GatedFusion(d_model=d_model)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(d_model, num_classes)

        self.phono_head = (
            PhonologyMultitaskHead(in_dim=d_model, attr_num_classes=phono_num_classes)
            if self.use_phonology
            else None
        )

    def forward(
        self,
        pose: torch.Tensor,
        rgb: torch.Tensor,
    ) -> Dict[str, Any]:
        """
        pose: [B, 64, 86, 3]
        rgb:  [B, 8, 768]
        """
        if self.training and self.rgb_drop_p > 0.0:
            # Modality dropout on RGB tokens per sample in batch
            B = rgb.shape[0]
            keep = (torch.rand(B, 1, 1, device=rgb.device) >= self.rgb_drop_p).float()
            rgb = rgb * keep

        p_tokens = self.stream_a.forward_tokens(pose)  # [B, 16, D]
        r_tokens = self.stream_b(rgb)                  # [B, 8, D]

        # Auxiliary stream predictions before fusion
        pose_logits = self.pose_aux_head(p_tokens.mean(dim=1))
        rgb_logits = self.rgb_aux_head(r_tokens.mean(dim=1))

        last_attn = None
        for layer in self.cross_layers:
            p_tokens, r_tokens, last_attn = layer(p_tokens, r_tokens)

        p_bar = p_tokens.mean(dim=1)
        r_bar = r_tokens.mean(dim=1)

        z, gate = self.gated_fusion(p_bar, r_bar)
        z_drop = self.dropout(z)
        logits = self.classifier(z_drop)
        phono_logits = self.phono_head(z_drop) if self.phono_head is not None else None

        return {
            "logits": logits,
            "pose_logits": pose_logits,
            "rgb_logits": rgb_logits,
            "phonology_logits": phono_logits,
            "gate": gate,  # [B, D] gate values in (0, 1)
            "attn": last_attn,
            "features": z,
        }


def build_video_model(
    cfg: Dict[str, Any],
    num_classes: int = 32,
    phono_num_classes: Optional[Dict[str, int]] = None,
) -> nn.Module:
    """
    Factory function constructing M0, M1, M2, M3, M4, M5, or X1-X4 from YAML config dict.
    """
    model_cfg = cfg.get("model", cfg)
    arch = str(model_cfg.get("type", model_cfg.get("arch", "student"))).lower()
    d_model = int(model_cfg.get("d_model", model_cfg.get("hidden_dim", 256)))
    dropout = float(model_cfg.get("dropout", 0.2))
    use_phono = bool(model_cfg.get("phonology", model_cfg.get("use_fonologi_head", False)))

    if arch in ("student", "pose_transformer", "m0", "m5"):
        student_d = int(model_cfg.get("d_model", 160))
        nhead = int(model_cfg.get("nhead", 4))
        layers = int(model_cfg.get("num_layers", 4))
        return StudentPoseTransformer(
            num_classes=num_classes,
            d_model=student_d,
            nhead=nhead,
            num_layers=layers,
            dim_feedforward=student_d * 4,
            dropout=dropout,
        )
    elif arch in ("pose", "stgcn", "m1"):
        return PoseModel(
            num_classes=num_classes,
            hidden_dim=d_model,
            dropout=dropout,
            use_phonology=use_phono,
            phono_num_classes=phono_num_classes,
        )
    elif arch in ("rgb_only", "rgb", "m2"):
        return RGBOnlyModel(
            num_classes=num_classes,
            d_model=d_model,
            dropout=dropout,
        )
    elif arch in ("fusion", "two_stream", "m3", "m4"):
        fusion_layers = int(model_cfg.get("fusion_layers", 2))
        nhead = int(model_cfg.get("nhead", 4))
        rgb_drop_p = float(model_cfg.get("rgb_drop_p", 0.1))
        return TwoStreamFusionModel(
            num_classes=num_classes,
            d_model=d_model,
            nhead=nhead,
            fusion_layers=fusion_layers,
            dropout=dropout,
            rgb_drop_p=rgb_drop_p,
            use_phonology=use_phono,
            phono_num_classes=phono_num_classes,
        )
    else:
        raise ValueError(f"Unknown video model type: {arch!r}")

