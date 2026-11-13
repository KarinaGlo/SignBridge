"""
fusion.py — Modul Fusion: Gated Fusion (E4) dan Cross-Attention Fusion (E5).

Requirements: 9.1–9.5.

Dua implementasi fusion tersedia:
  1. GatedFusionModule (default, E4):
       g = σ(W[p̄; r̄]),  z = g⊙p̄ + (1-g)⊙r̄
       Output z adalah convex combination antara pose dan RGB features.

  2. CrossAttentionFusionModule (E5, Teacher model kompleks):
       A2B: A = Query, B = Key & Value  → out_A2B
       B2A: B = Query, A = Key & Value  → out_B2A
       Combine: fused = LayerNorm(out_A2B + out_B2A + residual_A)   (Post-LN)

Input:  feat_A/feat_pose [B, 512], feat_B/feat_rgb [B, 512]
Output: fused [B, 512]
"""

from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# GatedFusionModule — E4 (default Teacher fusion)
# ---------------------------------------------------------------------------

class GatedFusionModule(nn.Module):
    """
    Gated Fusion: g = σ(W[p̄; r̄]),  z = g⊙p̄ + (1-g)⊙r̄

    Requirement 9.1–9.3:
      - Input: feat_pose p̄ [B, dim], feat_rgb r̄ [B, dim]
      - Gate g ∈ [0, 1] element-wise (sigmoid → convex combination).
      - Output z [B, dim] adalah convex combination dari p̄ dan r̄.
    """

    def __init__(self, dim: int = 512):
        super().__init__()
        self.dim = dim
        # W: maps concat [p̄; r̄] ∈ R^{2*dim} → gate ∈ R^{dim}
        self.gate_fc = nn.Linear(dim * 2, dim)

    def forward(
        self,
        feat_pose: torch.Tensor,   # p̄ [B, dim]
        feat_rgb: torch.Tensor,    # r̄ [B, dim]
    ) -> Tuple[torch.Tensor, None]:
        """
        Returns: (z [B, dim], None)
        None placeholder menjaga antarmuka seragam dengan CrossAttentionFusionModule.
        """
        concat = torch.cat([feat_pose, feat_rgb], dim=-1)  # [B, 2*dim]
        g = torch.sigmoid(self.gate_fc(concat))            # [B, dim], ∈ (0,1)
        z = g * feat_pose + (1.0 - g) * feat_rgb          # [B, dim], convex combination
        return z, None


# ---------------------------------------------------------------------------
# CrossAttentionFusionModule — E5 (alternative Teacher fusion)
# ---------------------------------------------------------------------------

class CrossAttentionFusionModule(nn.Module):
    """
    Bidirectional Cross-Attention Fusion (E5).

    Requirement 9.4–9.5:
      - A2B: A = Query, B = Key & Value
      - B2A: B = Query, A = Key & Value
      - Post-LN setelah residual addition.
      - Attention weights disimpan per arah untuk interpretabilitas.

    Input:  feat_A [B, 512], feat_B [B, 512]
    Output: (fused [B, 512], attn_weights {"A2B": ..., "B2A": ...} | None)
    """

    def __init__(self, dim: int = 512, num_heads: int = 8):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads

        # Cross-attention: A = Q, B = K, V
        self.cross_attn_A2B = nn.MultiheadAttention(dim, num_heads, batch_first=True)
        # Cross-attention: B = Q, A = K, V
        self.cross_attn_B2A = nn.MultiheadAttention(dim, num_heads, batch_first=True)

        # Post-LN (Requirement 9.4)
        self.layer_norm_1 = nn.LayerNorm(dim)
        self.layer_norm_2 = nn.LayerNorm(dim)

    def forward(
        self,
        feat_A: torch.Tensor,
        feat_B: torch.Tensor,
        return_attn_weights: bool = True,
    ) -> Tuple[torch.Tensor, Optional[Dict[str, torch.Tensor]]]:
        """
        feat_A: [B, 512]
        feat_B: [B, 512]
        Returns: (fused [B, 512], {"A2B": attn, "B2A": attn} | None)
        """
        # Unsqueeze → seq_len = 1  for MultiheadAttention
        A = feat_A.unsqueeze(1)  # [B, 1, 512]
        B = feat_B.unsqueeze(1)  # [B, 1, 512]

        # --- A → B cross-attention ---
        out_A2B, attn_A2B = self.cross_attn_A2B(
            query=A, key=B, value=B,
            need_weights=return_attn_weights,
            average_attn_weights=False,
        )

        # --- B → A cross-attention ---
        out_B2A, attn_B2A = self.cross_attn_B2A(
            query=B, key=A, value=A,
            need_weights=return_attn_weights,
            average_attn_weights=False,
        )

        # --- Combine with residual + Post-LN ---
        fused = self.layer_norm_1(out_A2B + out_B2A + A)  # [B, 1, 512]
        fused = self.layer_norm_2(fused)                   # [B, 1, 512]
        fused = fused.squeeze(1)                           # [B, 512]

        attn_weights: Optional[Dict[str, torch.Tensor]] = None
        if return_attn_weights:
            attn_weights = {
                "A2B": attn_A2B,  # [B, num_heads, 1, 1]
                "B2A": attn_B2A,
            }

        return fused, attn_weights


# ---------------------------------------------------------------------------
# FusionModule — alias default (Gated Fusion) untuk kompatibilitas mundur
# ---------------------------------------------------------------------------

class FusionModule(CrossAttentionFusionModule):
    """
    Bidirectional Cross-Attention Fusion (E5) / Backward-compatible FusionModule.

    Untuk Gated Fusion (E4), gunakan GatedFusionModule secara eksplisit atau
    build_fusion(fusion_type="gated").
    """

    def __init__(self, dim: int = 512, num_heads: int = 8):
        super().__init__(dim=dim, num_heads=num_heads)



def build_fusion(
    fusion_type: Literal["gated", "cross_attention"] = "gated",
    dim: int = 512,
    num_heads: int = 8,
) -> nn.Module:
    """
    Factory function untuk membangun modul fusion sesuai tipe.

    Parameters
    ----------
    fusion_type : "gated" (default, E4) | "cross_attention" (E5)
    dim         : dimensi fitur (default 512)
    num_heads   : jumlah attention head — hanya digunakan untuk "cross_attention"

    Returns
    -------
    GatedFusionModule atau CrossAttentionFusionModule
    """
    if fusion_type == "gated":
        return GatedFusionModule(dim=dim)
    elif fusion_type == "cross_attention":
        return CrossAttentionFusionModule(dim=dim, num_heads=num_heads)
    else:
        raise ValueError(
            f"fusion_type tidak dikenal: {fusion_type!r}. "
            "Pilihan valid: 'gated', 'cross_attention'"
        )
