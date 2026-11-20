"""
multimodal.py — M6: SignBridge Multimodal Fusion Network (4 modalitas dalam SATU model).

Masukan (Kontrak 7, urutan modalitas: video, image, audio, text):
    pose          float32 [B, 64, 86, 3]   keypoint ternormalisasi (video)
    image         float32 [B, 3, 112, 112] crop tangan (citra)
    audio         float32 [B, 64, 248]     log-mel 2,5 dtk (audio)
    text          int64   [B, 64]          id karakter (teks)
    modality_mask float32 [B, 4]           1 = modalitas tersedia, 0 = hilang
Keluaran:
    logits            [B, 32]  skor 32 konsep kelas
    modality_weights  [B, 4]   bobot fusion yang DIPELAJARI per sampel (jumlah = 1, nol untuk yang hilang)

Arsitektur:
  1. Empat encoder khusus modalitas mengubah tiap masukan menjadi deret token berdimensi d (=128):
       video : 516 fitur/frame (posisi + kecepatan) -> Linear -> Transformer 2 lapis -> 16 token
       citra : CNN 4 blok (stride 2) -> peta 7x7 -> 49 token
       audio : Conv1d 2 lapis (stride 2) di atas 64 bin mel -> pooling 2 -> Transformer 1 lapis -> 31 token
       teks  : embedding karakter + posisi -> Transformer 1 lapis -> 64 token (mask padding)
  2. Embedding tipe modalitas ditambahkan, token [CLS] dipasang di depan, lalu SEMUA token
     masuk ke Transformer fusion 2 lapis (self-attention lintas modalitas). Token dari modalitas
     yang hilang di-mask (key_padding_mask) sehingga tidak dapat di-attend.
  3. Gated modality weighting: vektor ringkasan tiap modalitas u_m (rata-rata token hasil fusion)
     diberi skor s_m = v^T tanh(W u_m); bobot alpha = softmax(s) atas modalitas yang tersedia.
         z = sum_m alpha_m * u_m
  4. Representasi akhir h = LayerNorm(CLS + z) -> Linear -> 32 logits.
  5. Head bantu unimodal (satu per modalitas) pada u_m menjaga tiap encoder tetap informatif.

Pelatihan memakai modality dropout (modalitas dihapus acak) agar model tidak bergantung pada
satu modalitas saja dan tetap bekerja saat modalitas tertentu tidak tersedia di kelas.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from signbridge.multimodal.constants import (
    AUDIO_NUM_MELS,
    NUM_MODALITIES,
    TEXT_MAX_LEN,
)
from signbridge.multimodal.features import TEXT_VOCAB_SIZE

NEG_INF = -1e4  # aman untuk fp16/ONNX (bukan -inf)


def _encoder(d_model: int, nhead: int, layers: int, dropout: float) -> nn.TransformerEncoder:
    layer = nn.TransformerEncoderLayer(
        d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
        dropout=dropout, activation="gelu", batch_first=True,
    )
    return nn.TransformerEncoder(layer, num_layers=layers, enable_nested_tensor=False)


class PoseEncoder(nn.Module):
    """[B, 64, 86, 3] -> [B, 16, d]"""

    def __init__(self, d: int, nhead: int, dropout: float):
        super().__init__()
        self.proj = nn.Sequential(nn.Linear(86 * 3 * 2, d), nn.LayerNorm(d), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, 64, d) * 0.02)
        self.enc = _encoder(d, nhead, 2, dropout)
        self.pool = nn.AvgPool1d(4)  # 64 -> 16 token (ukuran tetap, aman untuk ONNX)

    def forward(self, pose: torch.Tensor) -> torch.Tensor:
        B, T, V, C = pose.shape
        vel = torch.cat([torch.zeros_like(pose[:, :1]), pose[:, 1:] - pose[:, :-1]], dim=1)
        x = torch.cat([pose, vel], dim=-1).reshape(B, T, V * C * 2)
        x = self.enc(self.proj(x) + self.pos[:, :T])
        return self.pool(x.transpose(1, 2)).transpose(1, 2)


class ImageEncoder(nn.Module):
    """[B, 3, 112, 112] -> [B, 49, d] (CNN ringan dari nol; bisa diganti MobileNetV3 pretrained)."""

    def __init__(self, d: int, dropout: float):
        super().__init__()
        chans = [3, 32, 64, 96, 128]
        blocks = []
        for cin, cout in zip(chans[:-1], chans[1:]):
            blocks += [nn.Conv2d(cin, cout, 3, stride=2, padding=1, bias=False),
                       nn.BatchNorm2d(cout), nn.GELU()]
        self.cnn = nn.Sequential(*blocks)          # 112 -> 56 -> 28 -> 14 -> 7
        self.proj = nn.Sequential(nn.Linear(chans[-1], d), nn.LayerNorm(d), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, 49, d) * 0.02)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        x = self.cnn(image).flatten(2).transpose(1, 2)  # [B, 49, 128]
        return self.proj(x) + self.pos


class AudioEncoder(nn.Module):
    """[B, 64, 248] log-mel -> [B, 31, d]"""

    def __init__(self, d: int, nhead: int, dropout: float, num_tokens: int = 31):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(AUDIO_NUM_MELS, d, 3, stride=2, padding=1), nn.GELU(),
            nn.Conv1d(d, d, 3, stride=2, padding=1), nn.GELU(),
        )                                            # 248 -> 124 -> 62
        self.pool = nn.AvgPool1d(2)                  # 62 -> 31 token
        self.pos = nn.Parameter(torch.randn(1, num_tokens, d) * 0.02)
        self.norm = nn.LayerNorm(d)
        self.enc = _encoder(d, nhead, 1, dropout)

    def forward(self, audio: torch.Tensor) -> torch.Tensor:
        x = self.pool(self.conv(audio)).transpose(1, 2)  # [B, 31, d]
        return self.enc(self.norm(x) + self.pos)


class TextEncoder(nn.Module):
    """[B, 64] id karakter -> ([B, 64, d], padding_mask [B, 64] True = padding)"""

    def __init__(self, d: int, nhead: int, dropout: float):
        super().__init__()
        self.emb = nn.Embedding(TEXT_VOCAB_SIZE, d, padding_idx=0)
        self.pos = nn.Parameter(torch.randn(1, TEXT_MAX_LEN, d) * 0.02)
        self.enc = _encoder(d, nhead, 1, dropout)

    def forward(self, text: torch.Tensor):
        pad = text.eq(0)
        # baris yang seluruhnya padding: buka token pertama agar attention tidak NaN
        pad = pad & ~(pad.all(dim=1, keepdim=True) & (torch.arange(text.size(1), device=text.device) == 0))
        x = self.emb(text) + self.pos[:, : text.size(1)]
        return self.enc(x, src_key_padding_mask=pad), pad


class SignBridgeMultimodalFusion(nn.Module):
    def __init__(
        self,
        num_classes: int = 32,
        d_model: int = 128,
        nhead: int = 4,
        fusion_layers: int = 2,
        dropout: float = 0.1,
        modality_dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.modality_dropout = modality_dropout
        d = d_model
        self.pose_enc = PoseEncoder(d, nhead, dropout)
        self.image_enc = ImageEncoder(d, dropout)
        self.audio_enc = AudioEncoder(d, nhead, dropout)
        self.text_enc = TextEncoder(d, nhead, dropout)
        self.type_emb = nn.Parameter(torch.randn(NUM_MODALITIES, d) * 0.02)
        self.cls = nn.Parameter(torch.randn(1, 1, d) * 0.02)
        self.fusion = _encoder(d, nhead, fusion_layers, dropout)
        # gated modality weighting
        self.gate_proj = nn.Linear(d, d)
        self.gate_vec = nn.Linear(d, 1, bias=False)
        self.out_norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, num_classes)
        self.aux_heads = nn.ModuleList([nn.Linear(d, num_classes) for _ in range(NUM_MODALITIES)])

    # ------------------------------------------------------------------
    def apply_modality_dropout(self, mask: torch.Tensor) -> torch.Tensor:
        """Saat training: hapus tiap modalitas yang ada dengan peluang p, sisakan minimal satu."""
        if not self.training or self.modality_dropout <= 0:
            return mask
        keep = (torch.rand_like(mask) > self.modality_dropout).float()
        new = mask * keep
        empty = (new.sum(dim=1) == 0) & (mask.sum(dim=1) > 0)
        if empty.any():
            # kembalikan satu modalitas acak di antara yang semula tersedia
            scores = torch.rand_like(mask) * mask + mask * 1e-3
            pick = F.one_hot(scores.argmax(dim=1), NUM_MODALITIES).float()
            new = torch.where(empty[:, None], pick, new)
        return new

    def forward(
        self,
        pose: torch.Tensor,
        image: torch.Tensor,
        audio: torch.Tensor,
        text: torch.Tensor,
        modality_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        mask = self.apply_modality_dropout(modality_mask.float())
        B = pose.size(0)

        tokens = [
            self.pose_enc(pose),
            self.image_enc(image),
            self.audio_enc(audio),
        ]
        text_tok, text_pad = self.text_enc(text)
        tokens.append(text_tok)

        seq, pads, spans = [self.cls.expand(B, -1, -1)], [torch.zeros(B, 1, dtype=torch.bool, device=pose.device)], []
        start = 1
        for m, tok in enumerate(tokens):
            tok = tok + self.type_emb[m]
            missing = mask[:, m] < 0.5                                   # [B]
            pad = missing[:, None].expand(-1, tok.size(1))
            if m == 3:
                pad = pad | text_pad
            seq.append(tok)
            pads.append(pad)
            spans.append((start, start + tok.size(1)))
            start += tok.size(1)
        x = torch.cat(seq, dim=1)
        key_pad = torch.cat(pads, dim=1)
        h = self.fusion(x, src_key_padding_mask=key_pad)

        # ringkasan per modalitas (rata-rata token yang valid)
        summaries = []
        for (a, b) in spans:
            valid = (~key_pad[:, a:b]).float().unsqueeze(-1)
            summaries.append((h[:, a:b] * valid).sum(1) / valid.sum(1).clamp_min(1.0))
        U = torch.stack(summaries, dim=1)                                # [B, 4, d]

        scores = self.gate_vec(torch.tanh(self.gate_proj(U))).squeeze(-1)  # [B, 4]
        scores = scores.masked_fill(mask < 0.5, NEG_INF)
        alpha = torch.softmax(scores, dim=1) * mask
        alpha = alpha / alpha.sum(dim=1, keepdim=True).clamp_min(1e-6)
        z = (alpha.unsqueeze(-1) * U).sum(dim=1)

        fused = self.out_norm(h[:, 0] + z)
        logits = self.head(fused)
        aux = torch.stack([head(U[:, m]) for m, head in enumerate(self.aux_heads)], dim=1)  # [B, 4, C]
        return {
            "logits": logits,
            "modality_weights": alpha,
            "aux_logits": aux,
            "used_mask": mask,
            "features": fused,
        }


class MultimodalOnnxWrapper(nn.Module):
    """Pembungkus ekspor ONNX: 5 masukan -> (logits, modality_weights)."""

    def __init__(self, model: SignBridgeMultimodalFusion):
        super().__init__()
        self.model = model

    def forward(self, pose, image, audio, text, modality_mask):
        out = self.model(pose, image, audio, text, modality_mask)
        return out["logits"], out["modality_weights"]


def multimodal_loss(
    out: Dict[str, torch.Tensor],
    labels: torch.Tensor,
    label_smoothing: float = 0.1,
    lambda_aux: float = 0.3,
) -> Dict[str, torch.Tensor]:
    """L = CE(fusion) + lambda_aux * rata-rata CE(head unimodal) atas modalitas yang dipakai."""
    main = F.cross_entropy(out["logits"], labels, label_smoothing=label_smoothing)
    used = out["used_mask"]                                           # [B, 4]
    aux = out["aux_logits"]                                           # [B, 4, C]
    B, M, C = aux.shape
    ce = F.cross_entropy(aux.reshape(B * M, C), labels.repeat_interleave(M),
                         label_smoothing=label_smoothing, reduction="none").reshape(B, M)
    aux_loss = (ce * used).sum() / used.sum().clamp_min(1.0)
    return {"loss": main + lambda_aux * aux_loss, "main": main.detach(), "aux": aux_loss.detach()}


def count_parameters(model: Optional[nn.Module]) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad) if model is not None else 0
