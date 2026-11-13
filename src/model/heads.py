"""
heads.py — Classification heads: GlossHead and FonologisHead.

Task 6.9.
Requirements: 10.1, 10.2, 11.1.
"""

from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# GlossHead (Requirement 10.1)
# ---------------------------------------------------------------------------

class GlossHead(nn.Module):
    """
    Gloss classification head.

    Architecture: FC(512) → LayerNorm → GELU → FC(num_classes)

    Supports dynamic ``num_classes`` so the same code works for
    WLASL (2 006 gloss) and WL-BISINDO (32 gloss).  (Requirement 10.2)
    """

    def __init__(self, in_dim: int = 512, num_classes: int = 32):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, in_dim)
        self.ln = nn.LayerNorm(in_dim)
        self.gelu = nn.GELU()
        self.fc2 = nn.Linear(in_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, 512] → [B, num_classes]."""
        x = self.fc1(x)
        x = self.ln(x)
        x = self.gelu(x)
        x = self.fc2(x)
        return x


# ---------------------------------------------------------------------------
# FonologisHead (Requirement 11.1)
# ---------------------------------------------------------------------------

class FonologisHead(nn.Module):
    """
    Phonological prediction head (multitask).

    Three independent sub-heads:
      - handshape  : 10–50 classes
      - lokasi     : 5–20 classes
      - arah_gerak : 4–12 classes

    Each sub-head has the same architecture as GlossHead.
    """

    def __init__(
        self,
        in_dim: int = 512,
        num_handshape: int = 20,
        num_lokasi: int = 10,
        num_arah_gerak: int = 8,
    ):
        super().__init__()
        self.handshape_head = GlossHead(in_dim, num_handshape)
        self.lokasi_head = GlossHead(in_dim, num_lokasi)
        self.arah_gerak_head = GlossHead(in_dim, num_arah_gerak)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        x: [B, 512]
        Returns: {
            "handshape_logits":  [B, num_handshape],
            "lokasi_logits":     [B, num_lokasi],
            "arah_gerak_logits": [B, num_arah_gerak],
        }
        """
        return {
            "handshape_logits": self.handshape_head(x),
            "lokasi_logits": self.lokasi_head(x),
            "arah_gerak_logits": self.arah_gerak_head(x),
        }
