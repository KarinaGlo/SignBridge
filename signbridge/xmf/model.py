"""
signbridge/xmf/model.py — SignBridge-XMF: Cross-Modal Attention Fusion Transformer.

SATU model menerima 4 modalitas SEKALIGUS (data mentah; preprocessing numerik ada di dalam graf):
    pose          float32 [B, T, 86, 3]        keypoint ternormalisasi (VIDEO)
    frames        float32 [B, F, 3, 112, 112]  piksel 0..255 dari klip yang sama (CITRA)
    audio         float32 [B, 40000]           gelombang 16 kHz, 2,5 dtk (AUDIO)
    text          int64   [B, 64]              id karakter (TEKS)
    modality_mask float32 [B, 4]               1 = modalitas tersedia
Keluaran:
    logits            [B, C]     skor kelas hasil fusion
    modality_weights  [B, 4]     bobot gating yang dipelajari (jumlah 1; 0 utk modalitas hilang)
    modality_logits   [B, 4, C]  skor tiap modalitas di RUANG KONSEP BERSAMA (head prototipe dibagi)

Arsitektur:
  (1) Encoder per modalitas -> deret token berdimensi d
        VIDEO : embedding per-bagian tubuh (badan/tangan kiri/tangan kanan/wajah) + kecepatan
                -> Transformer temporal 2 lapis -> pooling ke P token
        CITRA : MobileNetV3-Small (ImageNet) per frame -> 1 token/frame -> Transformer temporal 1 lapis
        AUDIO : log-mel 64 bin (STFT sebagai Conv1d tetap) -> Conv1d x2 -> Transformer 1 lapis -> 31 token
        TEKS  : embedding karakter + posisi -> Transformer 1 lapis -> 64 token (mask padding)
  (2) CROSS-MODAL ATTENTION FUSION: [CLS] + semua token (+ embedding tipe modalitas) masuk Transformer
      fusion L lapis; setiap token dapat meng-attend token modalitas lain. Token modalitas yang hilang
      di-mask (key_padding_mask).
  (3) GATED MODALITY WEIGHTING: ringkasan u_m tiap modalitas -> skor s_m = v^T tanh(W u_m);
      alpha = softmax(s) atas modalitas tersedia; z = sum alpha_m u_m.
  (4) h = LayerNorm(CLS + z) -> Linear -> logits.
  (5) Head prototipe kosinus BERSAMA untuk semua u_m -> keempat modalitas dipetakan ke ruang konsep
      yang sama (bisa dipakai verifikasi lintas-modal, mis. teks target vs isyarat peraga).
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from signbridge.xmf.config import (
    AUDIO_SR, IMAGENET_MEAN, IMAGENET_STD, NUM_MODALITIES, TEXT_VOCAB_SIZE, TaskShapes,
)

NEG = -1e4


def _tx(d: int, nhead: int, layers: int, dropout: float) -> nn.TransformerEncoder:
    layer = nn.TransformerEncoderLayer(d, nhead, d * 2, dropout, activation="gelu", batch_first=True,
                                       norm_first=True)
    return nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)


# ---------------------------------------------------------------------------
# VIDEO / pose
# ---------------------------------------------------------------------------
PARTS = [(0, 9), (9, 30), (30, 51), (51, 86)]   # badan, tangan kiri, tangan kanan, wajah


class PoseEncoder(nn.Module):
    def __init__(self, d: int, nhead: int, dropout: float, frames: int, tokens: int):
        super().__init__()
        assert frames % tokens == 0
        self.tokens = tokens
        q = d // 4
        self.parts = nn.ModuleList([nn.Linear((b - a) * 3 * 2, q) for a, b in PARTS])
        self.proj = nn.Sequential(nn.LayerNorm(4 * q), nn.Linear(4 * q, d), nn.GELU(), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, frames, d) * 0.02)
        self.enc = _tx(d, nhead, 2 if frames > 1 else 1, dropout)

    def forward(self, pose: torch.Tensor) -> torch.Tensor:
        B, T, V, C = pose.shape
        vel = torch.cat([torch.zeros_like(pose[:, :1]), pose[:, 1:] - pose[:, :-1]], dim=1)
        x = torch.cat([pose, vel], dim=-1)                                  # [B,T,86,6]
        feats = [lin(x[:, :, a:b].reshape(B, T, (b - a) * 6)) for (a, b), lin in zip(PARTS, self.parts)]
        h = self.enc(self.proj(torch.cat(feats, -1)) + self.pos)
        if self.tokens == T:
            return h
        return h.reshape(B, self.tokens, T // self.tokens, -1).mean(2)       # pooling temporal


# ---------------------------------------------------------------------------
# CITRA
# ---------------------------------------------------------------------------
class ImageEncoder(nn.Module):
    def __init__(self, d: int, nhead: int, dropout: float, frames: int, pretrained: bool, freeze_blocks: int):
        super().__init__()
        from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

        weights = None
        if pretrained:
            try:
                weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
                net = mobilenet_v3_small(weights=weights)
            except Exception as e:  # noqa: BLE001  (tanpa internet -> inisialisasi acak)
                print(f"[XMF] bobot ImageNet tidak bisa diunduh ({e}); pakai inisialisasi acak.")
                net = mobilenet_v3_small(weights=None)
        else:
            net = mobilenet_v3_small(weights=None)
        self.backbone = net.features                                        # -> [N, 576, 4, 4] @112
        for i, blk in enumerate(self.backbone):
            if i < freeze_blocks:
                for p in blk.parameters():
                    p.requires_grad = False
        self.register_buffer("mean", torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1) * 255.0)
        self.register_buffer("std", torch.tensor(IMAGENET_STD).view(1, 3, 1, 1) * 255.0)
        self.proj = nn.Sequential(nn.Linear(576, d), nn.LayerNorm(d), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, frames, d) * 0.02)
        self.enc = _tx(d, nhead, 1, dropout) if frames > 1 else nn.Identity()

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        B, Fr, C, H, W = frames.shape
        x = (frames.reshape(B * Fr, C, H, W) - self.mean) / self.std        # normalisasi DI DALAM graf
        x = self.backbone(x).mean(dim=(2, 3))                               # GAP -> [B*F, 576]
        x = self.proj(x).reshape(B, Fr, -1) + self.pos
        return self.enc(x)


# ---------------------------------------------------------------------------
# AUDIO (log-mel di dalam graf — identik dengan signbridge.multimodal.features.log_mel)
# ---------------------------------------------------------------------------
class LogMel(nn.Module):
    def __init__(self, n_fft: int = 400, hop: int = 160, n_mels: int = 64):
        super().__init__()
        from signbridge.multimodal.features import mel_filterbank

        self.hop = hop
        win = np.hanning(n_fft).astype(np.float64)
        k = np.arange(n_fft // 2 + 1)[:, None]
        n = np.arange(n_fft)[None, :]
        ang = 2 * np.pi * k * n / n_fft
        self.register_buffer("wcos", torch.tensor(np.cos(ang) * win, dtype=torch.float32).unsqueeze(1))
        self.register_buffer("wsin", torch.tensor(-np.sin(ang) * win, dtype=torch.float32).unsqueeze(1))
        self.register_buffer("fb", torch.tensor(mel_filterbank(AUDIO_SR, n_fft, n_mels), dtype=torch.float32))

    def forward(self, wav: torch.Tensor) -> torch.Tensor:                   # [B, N] -> [B, 64, frames]
        x = wav.unsqueeze(1)
        re = F.conv1d(x, self.wcos, stride=self.hop)
        im = F.conv1d(x, self.wsin, stride=self.hop)
        feat = torch.log(torch.matmul(self.fb, re * re + im * im) + 1e-6)
        mu = feat.mean(dim=(1, 2), keepdim=True)
        sd = ((feat - mu) ** 2).mean(dim=(1, 2), keepdim=True).sqrt()
        return (feat - mu) / (sd + 1e-5)


class AudioEncoder(nn.Module):
    def __init__(self, d: int, nhead: int, dropout: float, tokens: int = 31):
        super().__init__()
        self.mel = LogMel()
        self.conv = nn.Sequential(
            nn.Conv1d(64, d, 3, stride=2, padding=1), nn.GELU(),
            nn.Conv1d(d, d, 3, stride=2, padding=1), nn.GELU(),
        )
        self.pool = nn.AvgPool1d(2)
        self.pos = nn.Parameter(torch.randn(1, tokens, d) * 0.02)
        self.norm = nn.LayerNorm(d)
        self.enc = _tx(d, nhead, 1, dropout)

    def spec_augment(self, m: torch.Tensor) -> torch.Tensor:
        if not self.training:
            return m
        B, Fq, T = m.shape
        m = m.clone()
        for b in range(B):
            f0 = int(torch.randint(0, Fq - 8, (1,)))
            m[b, f0: f0 + int(torch.randint(0, 8, (1,)))] = 0
            t0 = int(torch.randint(0, T - 25, (1,)))
            m[b, :, t0: t0 + int(torch.randint(0, 25, (1,)))] = 0
        return m

    def forward(self, wav: torch.Tensor) -> torch.Tensor:
        x = self.pool(self.conv(self.spec_augment(self.mel(wav)))).transpose(1, 2)
        return self.enc(self.norm(x) + self.pos[:, : x.size(1)])


# ---------------------------------------------------------------------------
# TEKS
# ---------------------------------------------------------------------------
class TextEncoder(nn.Module):
    def __init__(self, d: int, nhead: int, dropout: float, max_len: int):
        super().__init__()
        self.emb = nn.Embedding(TEXT_VOCAB_SIZE, d, padding_idx=0)
        self.pos = nn.Parameter(torch.randn(1, max_len, d) * 0.02)
        self.enc = _tx(d, nhead, 1, dropout)

    def forward(self, text: torch.Tensor):
        pad = text.eq(0)
        first = torch.arange(text.size(1), device=text.device).eq(0).unsqueeze(0)
        pad = pad & ~(pad.all(dim=1, keepdim=True) & first)                # cegah baris all-pad (NaN)
        return self.enc(self.emb(text) + self.pos, src_key_padding_mask=pad), pad


# ---------------------------------------------------------------------------
# MODEL FUSION
# ---------------------------------------------------------------------------
class SignBridgeXMF(nn.Module):
    def __init__(self, num_classes: int, shapes: TaskShapes, d_model: int = 128, nhead: int = 4,
                 fusion_layers: int = 2, dropout: float = 0.1, pretrained_image: bool = True,
                 freeze_image_blocks: int = 4, proto_scale: float = 16.0):
        super().__init__()
        d = d_model
        self.num_classes = num_classes
        self.shapes = shapes
        self.pose_enc = PoseEncoder(d, nhead, dropout, shapes.pose_frames, shapes.pose_tokens)
        self.image_enc = ImageEncoder(d, nhead, dropout, shapes.image_frames, pretrained_image,
                                      freeze_image_blocks)
        self.audio_enc = AudioEncoder(d, nhead, dropout)
        self.text_enc = TextEncoder(d, nhead, dropout, shapes.text_len)
        self.type_emb = nn.Parameter(torch.randn(NUM_MODALITIES, d) * 0.02)
        self.cls = nn.Parameter(torch.randn(1, 1, d) * 0.02)
        self.fusion = _tx(d, nhead, fusion_layers, dropout)
        self.fusion_norm = nn.LayerNorm(d)
        self.gate_proj = nn.Linear(d, d)
        self.gate_vec = nn.Linear(d, 1, bias=False)
        self.out_norm = nn.LayerNorm(d)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d, num_classes))
        self.proto_proj = nn.Linear(d, d)
        self.prototypes = nn.Parameter(torch.randn(num_classes, d) * 0.02)
        self.proto_scale = proto_scale

    def forward(self, pose, frames, audio, text, modality_mask) -> Dict[str, torch.Tensor]:
        mask = modality_mask.float()
        B = pose.size(0)
        text_tok, text_pad = self.text_enc(text)
        tokens = [self.pose_enc(pose), self.image_enc(frames), self.audio_enc(audio), text_tok]

        seq = [self.cls.expand(B, -1, -1)]
        pads = [torch.zeros(B, 1, dtype=torch.bool, device=pose.device)]
        spans, start = [], 1
        for m, tok in enumerate(tokens):
            missing = (mask[:, m] < 0.5).unsqueeze(1).expand(-1, tok.size(1))
            pads.append(missing | text_pad if m == 3 else missing)
            seq.append(tok + self.type_emb[m])
            n_tok = int(tok.shape[1])       # konstanta statis (aman untuk ekspor ONNX)
            spans.append((start, start + n_tok))
            start += n_tok
        key_pad = torch.cat(pads, 1)
        h = self.fusion_norm(self.fusion(torch.cat(seq, 1), src_key_padding_mask=key_pad))

        keep = 1.0 - key_pad.float()                                        # [B, L] 1 = token valid
        U = []
        for a, b in spans:
            valid = keep[:, a:b].unsqueeze(-1)
            U.append((h[:, a:b] * valid).sum(1) / valid.sum(1).clamp_min(1.0))
        U = torch.stack(U, 1)                                               # [B, 4, d]

        s = self.gate_vec(torch.tanh(self.gate_proj(U))).squeeze(-1).masked_fill(mask < 0.5, NEG)
        alpha = torch.softmax(s, 1) * mask
        alpha = alpha / alpha.sum(1, keepdim=True).clamp_min(1e-6)
        fused = self.out_norm(h[:, 0] + (alpha.unsqueeze(-1) * U).sum(1))
        logits = self.head(fused)

        e = F.normalize(self.proto_proj(U), dim=-1)
        p = F.normalize(self.prototypes, dim=-1)
        mod_logits = self.proto_scale * torch.matmul(e, p.t())              # [B, 4, C]
        return {"logits": logits, "modality_weights": alpha, "modality_logits": mod_logits,
                "embedding": fused, "used_mask": mask}


class XMFOnnx(nn.Module):
    def __init__(self, model: SignBridgeXMF):
        super().__init__()
        self.model = model

    def forward(self, pose, frames, audio, text, modality_mask):
        o = self.model(pose, frames, audio, text, modality_mask)
        return o["logits"], o["modality_weights"], o["modality_logits"]


def xmf_loss(out: Dict[str, torch.Tensor], y: torch.Tensor, label_smoothing: float = 0.1,
             lambda_proto: float = 0.5) -> Dict[str, torch.Tensor]:
    """L = CE(fusion) + lambda * rata-rata CE(prototipe bersama) atas modalitas yang dipakai."""
    main = F.cross_entropy(out["logits"], y, label_smoothing=label_smoothing)
    ml, used = out["modality_logits"], out["used_mask"]
    B, M, C = ml.shape
    ce = F.cross_entropy(ml.reshape(B * M, C), y.repeat_interleave(M), reduction="none").reshape(B, M)
    proto = (ce * used).sum() / used.sum().clamp_min(1.0)
    return {"loss": main + lambda_proto * proto, "main": main.detach(), "proto": proto.detach()}


def build_model(task: str, num_classes: int, cfg: Optional[dict] = None) -> SignBridgeXMF:
    from signbridge.xmf.config import SHAPES

    cfg = dict(cfg or {})
    return SignBridgeXMF(num_classes, SHAPES[task], **cfg)


def count_params(m: nn.Module, trainable: bool = False) -> int:
    return sum(p.numel() for p in m.parameters() if (p.requires_grad or not trainable))
