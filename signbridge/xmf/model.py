"""
signbridge/xmf/model.py — SignBridge-XMF: kerangka model multimodal yang bisa dikonfigurasi.

SATU model menerima 4 modalitas SEKALIGUS (data mentah; preprocessing numerik ada di dalam graf):
    pose          float32 [B, T, 86, 3]        keypoint ternormalisasi (VIDEO)
    frames        float32 [B, F, 3, 112, 112]  piksel 0..255 dari klip yang sama (CITRA)
    audio         float32 [B, 40000]           gelombang 16 kHz, 2,5 dtk (AUDIO)
    text          int64   [B, 64]              id karakter (TEKS)
    modality_mask float32 [B, 4]               1 = modalitas tersedia
Keluaran (sama untuk SEMUA varian -> aplikasi web tidak perlu diubah):
    logits            [B, C]     skor kelas hasil fusion
    modality_weights  [B, 4]     kontribusi tiap modalitas (jumlah 1; 0 utk modalitas hilang)
    modality_logits   [B, 4, C]  skor tiap modalitas di RUANG KONSEP BERSAMA (head prototipe dibagi)

Komponen yang bisa ditukar (studi perbandingan, lihat docs/XMF_COMPARISON.md):
    encoder video : transformer | bigru | tcn                                  (encoders.py)
    encoder citra : mobilenetv3 | shufflenetv2 | efficientnet_b0 | resnet18
    encoder audio : cnn_transformer | conformer | resnet
    encoder teks  : transformer | bilstm | textcnn
    fusion        : early | weighted | gated | late | refusion | attention     (fusion.py)
Default = Cross-Modal Attention Fusion Transformer + transformer / mobilenetv3 / cnn_transformer / transformer.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from signbridge.xmf.config import TaskShapes
from signbridge.xmf.encoders import (  # noqa: F401  (LogMel diekspor ulang untuk kompatibilitas)
    AUDIO_ENCODERS, IMAGE_BACKBONES, POSE_ENCODERS, TEXT_ENCODERS, ImageEncoder, LogMel,
)
from signbridge.xmf.fusion import FUSION_NAMES, FUSIONS, build_fusion

DEFAULT_ENCODERS = {"pose": "transformer", "image": "mobilenetv3", "audio": "cnn_transformer", "text": "transformer"}


class SignBridgeXMF(nn.Module):
    def __init__(self, num_classes: int, shapes: TaskShapes, d_model: int = 128, nhead: int = 4,
                 fusion_layers: int = 2, dropout: float = 0.1, pretrained_image: bool = True,
                 freeze_image_blocks: int = 4, proto_scale: float = 16.0, fusion: str = "attention",
                 encoders: Optional[Dict[str, str]] = None):
        super().__init__()
        d = d_model
        enc = dict(DEFAULT_ENCODERS, **(encoders or {}))
        for k, reg in (("pose", POSE_ENCODERS), ("audio", AUDIO_ENCODERS), ("text", TEXT_ENCODERS)):
            if enc[k] not in reg:
                raise ValueError(f"encoder {k} tidak dikenal: {enc[k]} (pilihan: {', '.join(reg)})")
        if enc["image"] not in IMAGE_BACKBONES:
            raise ValueError(f"encoder image tidak dikenal: {enc['image']} (pilihan: {', '.join(IMAGE_BACKBONES)})")
        self.num_classes, self.shapes, self.encoders, self.fusion_name = num_classes, shapes, enc, fusion
        self.pose_enc = POSE_ENCODERS[enc["pose"]](d, nhead, dropout, shapes.pose_frames, shapes.pose_tokens)
        self.image_enc = ImageEncoder(d, nhead, dropout, shapes.image_frames, pretrained_image,
                                      freeze_image_blocks, enc["image"])
        self.audio_enc = AUDIO_ENCODERS[enc["audio"]](d, nhead, dropout)
        self.text_enc = TEXT_ENCODERS[enc["text"]](d, nhead, dropout, shapes.text_len)
        self.fuse = build_fusion(fusion, d, nhead, dropout, fusion_layers, num_classes)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d, num_classes))
        self.proto_proj = nn.Linear(d, d)
        self.prototypes = nn.Parameter(torch.randn(num_classes, d) * 0.02)
        self.proto_scale = proto_scale

    def describe(self) -> str:
        e = self.encoders
        return (f"{FUSION_NAMES[self.fusion_name]} | video={e['pose']} citra={e['image']} "
                f"audio={e['audio']} teks={e['text']}")

    def forward(self, pose, frames, audio, text, modality_mask) -> Dict[str, torch.Tensor]:
        mask = modality_mask.float()
        text_tok, text_pad = self.text_enc(text)
        tokens = [self.pose_enc(pose), self.image_enc(frames), self.audio_enc(audio), text_tok]
        pads = []
        for m, tok in enumerate(tokens):
            missing = (mask[:, m] < 0.5).unsqueeze(1).expand(-1, tok.size(1))
            pads.append(missing | text_pad if m == 3 else missing)
        f = self.fuse(tokens, pads, mask)
        logits = f["logits"] if "logits" in f else self.head(f["fused"])
        e = F.normalize(self.proto_proj(f["U"]), dim=-1)
        p = F.normalize(self.prototypes, dim=-1)
        mod_logits = self.proto_scale * torch.matmul(e, p.t())              # [B, 4, C]
        return {"logits": logits, "modality_weights": f["alpha"], "modality_logits": mod_logits,
                "embedding": f["fused"], "used_mask": mask}


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

    return SignBridgeXMF(num_classes, SHAPES[task], **dict(cfg or {}))


def count_params(m: nn.Module, trainable: bool = False) -> int:
    return sum(p.numel() for p in m.parameters() if (p.requires_grad or not trainable))
