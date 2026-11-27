"""
signbridge/xmf/fusion.py — strategi fusion yang dibandingkan pada SignBridge-XMF.

Masukan semua fusion sama: deret token tiap modalitas (dari encoders.py), mask padding token, dan
modality_mask [B,4]. Keluaran: vektor gabungan `fused` [B,d], ringkasan per modalitas `U` [B,4,d],
bobot kontribusi modalitas `alpha` [B,4] (jumlah 1, 0 untuk modalitas hilang), dan opsional `logits`.

    early     Early / feature-level fusion: ringkasan tiap modalitas digabung (concat) -> MLP.
    weighted  Weighted-sum fusion: bobot skalar per modalitas yang dipelajari (statis, sama utk semua input).
    gated     Gated Multimodal Unit (Arevalo dkk., 2017): gerbang per dimensi bergantung input -> jumlah terbobot.
    late      Late / decision-level fusion: classifier per modalitas, skor digabung dengan bobot dipelajari.
    refusion  Re-fusion / progressive fusion (mirip Shankar dkk., 2022): hasil fusion diumpan balik ke
              representasi tiap modalitas lalu di-fusion ulang (2 putaran).
    attention Cross-Modal Attention Fusion Transformer (default SignBridge-XMF): [CLS] + semua token masuk
              Transformer bersama sehingga token satu modalitas meng-attend modalitas lain, + gating.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import torch
import torch.nn as nn

from signbridge.xmf.config import NUM_MODALITIES
from signbridge.xmf.encoders import tx

NEG = -1e4
M = NUM_MODALITIES


def masked_mean(tok: torch.Tensor, pad: torch.Tensor) -> torch.Tensor:
    keep = (~pad).float().unsqueeze(-1)
    return (tok * keep).sum(1) / keep.sum(1).clamp_min(1.0)


def masked_softmax(score: torch.Tensor, mask: torch.Tensor, dim: int = 1) -> torch.Tensor:
    """softmax atas modalitas yang tersedia; modalitas hilang -> 0 persis."""
    m = mask if score.dim() == mask.dim() else mask.unsqueeze(-1)
    a = torch.softmax(score.masked_fill(m < 0.5, NEG), dim) * m
    return a / a.sum(dim, keepdim=True).clamp_min(1e-6)


def summaries(tokens: List[torch.Tensor], pads: List[torch.Tensor], mask: torch.Tensor) -> torch.Tensor:
    return torch.stack([masked_mean(t, p) for t, p in zip(tokens, pads)], 1) * mask.unsqueeze(-1)


class EarlyFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes):
        super().__init__()
        self.mlp = nn.Sequential(nn.Linear(M * d + M, 2 * d), nn.GELU(), nn.Dropout(dropout),
                                 nn.Linear(2 * d, d), nn.LayerNorm(d))

    def forward(self, tokens, pads, mask):
        U = summaries(tokens, pads, mask)
        fused = self.mlp(torch.cat([U.flatten(1), mask], 1))
        alpha = mask / mask.sum(1, keepdim=True).clamp_min(1e-6)
        return {"fused": fused, "U": U, "alpha": alpha}


class WeightedFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes):
        super().__init__()
        self.w = nn.Parameter(torch.zeros(M))
        self.norm = nn.LayerNorm(d)

    def forward(self, tokens, pads, mask):
        U = summaries(tokens, pads, mask)
        alpha = masked_softmax(self.w.unsqueeze(0).expand_as(mask), mask)
        return {"fused": self.norm((alpha.unsqueeze(-1) * U).sum(1)), "U": U, "alpha": alpha}


class _GMU(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.h = nn.ModuleList([nn.Linear(d, d) for _ in range(M)])
        self.z = nn.Linear(M * d, M * d)
        self.norm = nn.LayerNorm(d)

    def forward(self, U, mask):
        B, _, D = U.shape
        H = torch.stack([torch.tanh(lin(U[:, m])) for m, lin in enumerate(self.h)], 1)   # [B,4,d]
        Z = masked_softmax(self.z(U.flatten(1)).reshape(B, M, D), mask)                  # gerbang per dimensi
        return self.norm((Z * H).sum(1)), Z.mean(-1)


class GatedFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes):
        super().__init__()
        self.gmu = _GMU(d)

    def forward(self, tokens, pads, mask):
        U = summaries(tokens, pads, mask)
        fused, a = self.gmu(U, mask)
        return {"fused": fused, "U": U, "alpha": a / a.sum(1, keepdim=True).clamp_min(1e-6)}


class LateFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes):
        super().__init__()
        self.heads = nn.ModuleList([nn.Sequential(nn.LayerNorm(d), nn.Dropout(dropout), nn.Linear(d, num_classes))
                                    for _ in range(M)])
        self.w = nn.Parameter(torch.zeros(M))

    def forward(self, tokens, pads, mask):
        U = summaries(tokens, pads, mask)
        alpha = masked_softmax(self.w.unsqueeze(0).expand_as(mask), mask)
        per = torch.stack([h(U[:, m]) for m, h in enumerate(self.heads)], 1)            # [B,4,C]
        logits = (alpha.unsqueeze(-1) * per).sum(1)
        return {"fused": (alpha.unsqueeze(-1) * U).sum(1), "U": U, "alpha": alpha, "logits": logits}


class ReFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes, rounds: int = 2):
        super().__init__()
        self.gmus = nn.ModuleList([_GMU(d) for _ in range(rounds)])
        self.fb = nn.ModuleList([nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Dropout(dropout))
                                 for _ in range(rounds - 1)])
        self.norm = nn.LayerNorm(d)

    def forward(self, tokens, pads, mask):
        U = U0 = summaries(tokens, pads, mask)
        fused, a = None, None
        for r, gmu in enumerate(self.gmus):
            fused, a = gmu(U, mask)
            if r < len(self.fb):                                            # umpan balik: konteks gabungan
                ctx = fused.unsqueeze(1).expand_as(U)
                U = self.norm(U + self.fb[r](torch.cat([U, ctx], -1))) * mask.unsqueeze(-1)
        return {"fused": fused, "U": U0, "alpha": a / a.sum(1, keepdim=True).clamp_min(1e-6)}


class AttentionFusion(nn.Module):
    def __init__(self, d, nhead, dropout, layers, num_classes):
        super().__init__()
        self.type_emb = nn.Parameter(torch.randn(M, d) * 0.02)
        self.cls = nn.Parameter(torch.randn(1, 1, d) * 0.02)
        self.fusion = tx(d, nhead, layers, dropout)
        self.fusion_norm = nn.LayerNorm(d)
        self.gate_proj = nn.Linear(d, d)
        self.gate_vec = nn.Linear(d, 1, bias=False)
        self.out_norm = nn.LayerNorm(d)

    def forward(self, tokens, pads, mask):
        B = mask.size(0)
        seq = [self.cls.expand(B, -1, -1)]
        key = [torch.zeros(B, 1, dtype=torch.bool, device=mask.device)]
        spans, start = [], 1
        for m, (tok, pad) in enumerate(zip(tokens, pads)):
            seq.append(tok + self.type_emb[m])
            key.append(pad)
            n_tok = int(tok.shape[1])       # konstanta statis (aman untuk ekspor ONNX)
            spans.append((start, start + n_tok))
            start += n_tok
        key_pad = torch.cat(key, 1)
        h = self.fusion_norm(self.fusion(torch.cat(seq, 1), src_key_padding_mask=key_pad))
        U = torch.stack([masked_mean(h[:, a:b], key_pad[:, a:b]) for a, b in spans], 1)
        s = self.gate_vec(torch.tanh(self.gate_proj(U))).squeeze(-1)
        alpha = masked_softmax(s, mask)
        fused = self.out_norm(h[:, 0] + (alpha.unsqueeze(-1) * U).sum(1))
        return {"fused": fused, "U": U * mask.unsqueeze(-1), "alpha": alpha}


FUSIONS = {"early": EarlyFusion, "weighted": WeightedFusion, "gated": GatedFusion, "late": LateFusion,
           "refusion": ReFusion, "attention": AttentionFusion}

FUSION_NAMES = {
    "early": "Early Fusion (concat + MLP)",
    "weighted": "Weighted-Sum Fusion",
    "gated": "Gated Multimodal Unit (GMU)",
    "late": "Late Fusion (decision-level)",
    "refusion": "Re-Fusion (progressive, umpan balik 2 putaran)",
    "attention": "Cross-Modal Attention Fusion Transformer",
}


def build_fusion(name: str, d: int, nhead: int, dropout: float, layers: int, num_classes: int,
                 extra: Optional[Dict] = None) -> nn.Module:
    if name not in FUSIONS:
        raise ValueError(f"fusion tidak dikenal: {name} (pilihan: {', '.join(FUSIONS)})")
    return FUSIONS[name](d, nhead, dropout, layers, num_classes, **(extra or {}))
