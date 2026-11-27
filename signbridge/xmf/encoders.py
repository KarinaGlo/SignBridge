"""
signbridge/xmf/encoders.py — kebun encoder per modalitas untuk studi perbandingan SignBridge-XMF.

Semua encoder mengeluarkan DERET TOKEN berdimensi d agar bisa dipasangkan dengan fusion apa pun:
    VIDEO (pose [B,T,86,3])        -> [B, P, d]        P = shapes.pose_tokens
    CITRA (frames [B,F,3,112,112]) -> [B, F, d]
    AUDIO (wave [B,40000])         -> [B, 31, d]       log-mel 64 bin dihitung DI DALAM graf
    TEKS  (id karakter [B,64])     -> ([B, 64, d], pad_mask [B, 64])

Pilihan (kunci config `model.encoders.<modal>`):
    pose  : transformer (default) | bigru | tcn
    image : mobilenetv3 (default) | shufflenetv2 | efficientnet_b0 | resnet18
    audio : cnn_transformer (default) | conformer | resnet
    text  : transformer (default) | bilstm | textcnn
Semuanya hanya memakai operator yang didukung ONNX opset 17 / ONNX Runtime Web (WASM).
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from signbridge.xmf.config import AUDIO_SR, IMAGENET_MEAN, IMAGENET_STD, TEXT_VOCAB_SIZE

AUDIO_TOKENS = 31


def tx(d: int, nhead: int, layers: int, dropout: float) -> nn.TransformerEncoder:
    layer = nn.TransformerEncoderLayer(d, nhead, d * 2, dropout, activation="gelu", batch_first=True,
                                       norm_first=True)
    return nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)


# =============================================================================
# VIDEO / pose — front-end bersama (embedding per bagian tubuh + kecepatan), back-end temporal berbeda
# =============================================================================
PARTS = [(0, 9), (9, 30), (30, 51), (51, 86)]   # badan, tangan kiri, tangan kanan, wajah


class _PoseFront(nn.Module):
    def __init__(self, d: int, dropout: float):
        super().__init__()
        q = d // 4
        self.parts = nn.ModuleList([nn.Linear((b - a) * 6, q) for a, b in PARTS])
        self.proj = nn.Sequential(nn.LayerNorm(4 * q), nn.Linear(4 * q, d), nn.GELU(), nn.Dropout(dropout))

    def forward(self, pose: torch.Tensor) -> torch.Tensor:
        B, T, V, C = pose.shape
        vel = torch.cat([torch.zeros_like(pose[:, :1]), pose[:, 1:] - pose[:, :-1]], dim=1)
        x = torch.cat([pose, vel], dim=-1)                                  # [B,T,86,6]
        feats = [lin(x[:, :, a:b].reshape(B, T, (b - a) * 6)) for (a, b), lin in zip(PARTS, self.parts)]
        return self.proj(torch.cat(feats, -1))                              # [B,T,d]


def _pool_tokens(h: torch.Tensor, tokens: int) -> torch.Tensor:
    B, T, D = h.shape
    return h if tokens == T else h.reshape(B, tokens, T // tokens, D).mean(2)


class PoseTransformer(nn.Module):
    """Transformer temporal 2 lapis (self-attention antar frame)."""

    def __init__(self, d, nhead, dropout, frames, tokens):
        super().__init__()
        assert frames % tokens == 0
        self.tokens = tokens
        self.front = _PoseFront(d, dropout)
        self.pos = nn.Parameter(torch.randn(1, frames, d) * 0.02)
        self.enc = tx(d, nhead, 2 if frames > 1 else 1, dropout)

    def forward(self, pose):
        return _pool_tokens(self.enc(self.front(pose) + self.pos), self.tokens)


class PoseBiGRU(nn.Module):
    """BiGRU 2 lapis — baseline rekuren klasik untuk pengenalan isyarat berbasis keypoint."""

    def __init__(self, d, nhead, dropout, frames, tokens):
        super().__init__()
        self.tokens = tokens
        self.front = _PoseFront(d, dropout)
        self.rnn = nn.GRU(d, d // 2, num_layers=2, batch_first=True, bidirectional=True, dropout=dropout)
        self.norm = nn.LayerNorm(d)

    def forward(self, pose):
        h, _ = self.rnn(self.front(pose))
        return _pool_tokens(self.norm(h), self.tokens)


class PoseTCN(nn.Module):
    """Temporal Convolutional Network: Conv1d residual ber-dilatasi 1-2-4 (reseptif ±29 frame)."""

    def __init__(self, d, nhead, dropout, frames, tokens):
        super().__init__()
        self.tokens = tokens
        self.front = _PoseFront(d, dropout)
        self.blocks = nn.ModuleList([
            nn.Sequential(nn.Conv1d(d, d, 5, padding=2 * r, dilation=r), nn.BatchNorm1d(d), nn.GELU(),
                          nn.Dropout(dropout))
            for r in (1, 2, 4)])
        self.norm = nn.LayerNorm(d)

    def forward(self, pose):
        x = self.front(pose).transpose(1, 2)                                # [B,d,T]
        for blk in self.blocks:
            x = x + blk(x)
        return _pool_tokens(self.norm(x.transpose(1, 2)), self.tokens)


POSE_ENCODERS = {"transformer": PoseTransformer, "bigru": PoseBiGRU, "tcn": PoseTCN}


# =============================================================================
# CITRA — CNN ringan pra-latih ImageNet per frame -> 1 token/frame -> Transformer temporal
# =============================================================================
def _image_backbone(name: str, pretrained: bool):
    """Kembalikan (nn.Sequential fitur, jumlah kanal keluaran)."""
    import torchvision.models as tvm

    def load(fn, weights):
        if pretrained:
            try:
                return fn(weights=weights)
            except Exception as e:  # noqa: BLE001  (tanpa internet -> inisialisasi acak)
                print(f"[XMF] bobot ImageNet {name} tidak bisa diunduh ({e}); pakai inisialisasi acak.")
        return fn(weights=None)

    if name == "mobilenetv3":
        net = load(tvm.mobilenet_v3_small, tvm.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        return net.features, 576
    if name == "shufflenetv2":
        net = load(tvm.shufflenet_v2_x1_0, tvm.ShuffleNet_V2_X1_0_Weights.IMAGENET1K_V1)
        return nn.Sequential(net.conv1, net.maxpool, net.stage2, net.stage3, net.stage4, net.conv5), 1024
    if name == "efficientnet_b0":
        net = load(tvm.efficientnet_b0, tvm.EfficientNet_B0_Weights.IMAGENET1K_V1)
        return net.features, 1280
    if name == "resnet18":
        net = load(tvm.resnet18, tvm.ResNet18_Weights.IMAGENET1K_V1)
        return nn.Sequential(nn.Sequential(net.conv1, net.bn1, net.relu, net.maxpool),
                             net.layer1, net.layer2, net.layer3, net.layer4), 512
    raise ValueError(f"backbone citra tidak dikenal: {name}")


IMAGE_BACKBONES = ("mobilenetv3", "shufflenetv2", "efficientnet_b0", "resnet18")


class ImageEncoder(nn.Module):
    def __init__(self, d, nhead, dropout, frames, pretrained=True, freeze_blocks=4, backbone="mobilenetv3"):
        super().__init__()
        self.backbone, ch = _image_backbone(backbone, pretrained)
        # bekukan sebagian awal backbone (proporsional terhadap jumlah blok, acuan MobileNetV3 = 13 blok)
        n_freeze = int(round(freeze_blocks * len(self.backbone) / 13)) if backbone != "mobilenetv3" else freeze_blocks
        for i, blk in enumerate(self.backbone):
            if i < n_freeze:
                for p in blk.parameters():
                    p.requires_grad = False
        self.register_buffer("mean", torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1) * 255.0)
        self.register_buffer("std", torch.tensor(IMAGENET_STD).view(1, 3, 1, 1) * 255.0)
        self.proj = nn.Sequential(nn.Linear(ch, d), nn.LayerNorm(d), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, frames, d) * 0.02)
        self.enc = tx(d, nhead, 1, dropout) if frames > 1 else nn.Identity()

    def forward(self, frames):
        B, Fr, C, H, W = frames.shape
        x = (frames.reshape(B * Fr, C, H, W) - self.mean) / self.std        # normalisasi DI DALAM graf
        x = self.backbone(x).mean(dim=(2, 3))                               # GAP
        return self.enc(self.proj(x).reshape(B, Fr, -1) + self.pos)


# =============================================================================
# AUDIO — log-mel di dalam graf (identik dengan signbridge.multimodal.features.log_mel)
# =============================================================================
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

    def forward(self, wav: torch.Tensor) -> torch.Tensor:                   # [B, N] -> [B, 64, 248]
        if torch.is_autocast_enabled() and wav.is_cuda:   # spektrum daya bisa > 65504 -> overflow di fp16
            with torch.autocast("cuda", enabled=False):
                return self._forward(wav.float())
        return self._forward(wav)

    def _forward(self, wav: torch.Tensor) -> torch.Tensor:
        x = wav.unsqueeze(1)
        re = F.conv1d(x, self.wcos, stride=self.hop)
        im = F.conv1d(x, self.wsin, stride=self.hop)
        feat = torch.log(torch.matmul(self.fb, re * re + im * im) + 1e-6)
        mu = feat.mean(dim=(1, 2), keepdim=True)
        sd = ((feat - mu) ** 2).mean(dim=(1, 2), keepdim=True).sqrt()
        return (feat - mu) / (sd + 1e-5)


def spec_augment(m: torch.Tensor, training: bool) -> torch.Tensor:
    if not training:
        return m
    B, Fq, T = m.shape
    m = m.clone()
    for b in range(B):
        f0 = int(torch.randint(0, Fq - 8, (1,)))
        m[b, f0: f0 + int(torch.randint(0, 8, (1,)))] = 0
        t0 = int(torch.randint(0, T - 25, (1,)))
        m[b, :, t0: t0 + int(torch.randint(0, 25, (1,)))] = 0
    return m


class AudioCNNTransformer(nn.Module):
    """Conv1d x2 (subsampling 4x) + Transformer 1 lapis — model audio awal SignBridge-XMF."""

    def __init__(self, d, nhead, dropout):
        super().__init__()
        self.mel = LogMel()
        self.conv = nn.Sequential(nn.Conv1d(64, d, 3, stride=2, padding=1), nn.GELU(),
                                  nn.Conv1d(d, d, 3, stride=2, padding=1), nn.GELU())
        self.pool = nn.AvgPool1d(2)
        self.pos = nn.Parameter(torch.randn(1, AUDIO_TOKENS, d) * 0.02)
        self.norm = nn.LayerNorm(d)
        self.enc = tx(d, nhead, 1, dropout)

    def forward(self, wav):
        x = self.pool(self.conv(spec_augment(self.mel(wav), self.training))).transpose(1, 2)
        return self.enc(self.norm(x) + self.pos[:, : x.size(1)])


class _ConformerConv(nn.Module):
    def __init__(self, d, kernel, dropout):
        super().__init__()
        self.norm = nn.LayerNorm(d)
        self.pw1 = nn.Conv1d(d, 2 * d, 1)
        self.dw = nn.Conv1d(d, d, kernel, padding=kernel // 2, groups=d)
        self.bn = nn.BatchNorm1d(d)
        self.pw2 = nn.Conv1d(d, d, 1)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):                                                   # [B,T,d]
        y = self.pw1(self.norm(x).transpose(1, 2))
        y = F.glu(y, dim=1)
        y = F.silu(self.bn(self.dw(y)))
        return self.drop(self.pw2(y).transpose(1, 2))


class ConformerBlock(nn.Module):
    """Gulati dkk. (2020): FFN/2 -> MHSA -> modul konvolusi -> FFN/2 -> LayerNorm (macaron)."""

    def __init__(self, d, nhead, dropout, kernel=15):
        super().__init__()

        def ffn():
            return nn.Sequential(nn.LayerNorm(d), nn.Linear(d, 4 * d), nn.SiLU(), nn.Dropout(dropout),
                                 nn.Linear(4 * d, d), nn.Dropout(dropout))

        self.ff1, self.ff2 = ffn(), ffn()
        self.att_norm = nn.LayerNorm(d)
        self.att = nn.MultiheadAttention(d, nhead, dropout=dropout, batch_first=True)
        self.att_drop = nn.Dropout(dropout)
        self.conv = _ConformerConv(d, kernel, dropout)
        self.out_norm = nn.LayerNorm(d)

    def forward(self, x):
        x = x + 0.5 * self.ff1(x)
        a = self.att_norm(x)
        x = x + self.att_drop(self.att(a, a, a, need_weights=False)[0])
        x = x + self.conv(x)
        x = x + 0.5 * self.ff2(x)
        return self.out_norm(x)


class AudioConformer(nn.Module):
    """Conformer: subsampling Conv2d 4x pada log-mel -> 2 blok Conformer -> pooling ke 31 token."""

    def __init__(self, d, nhead, dropout, layers=2, ch=32):
        super().__init__()
        self.mel = LogMel()
        self.sub = nn.Sequential(nn.Conv2d(1, ch, 3, stride=2, padding=1), nn.SiLU(),
                                 nn.Conv2d(ch, ch, 3, stride=2, padding=1), nn.SiLU())   # 64x248 -> 16x62
        self.inp = nn.Sequential(nn.Linear(ch * 16, d), nn.Dropout(dropout))
        self.pos = nn.Parameter(torch.randn(1, 62, d) * 0.02)
        self.blocks = nn.Sequential(*[ConformerBlock(d, nhead, dropout) for _ in range(layers)])
        self.pool = nn.AvgPool1d(2)

    def forward(self, wav):
        m = spec_augment(self.mel(wav), self.training).unsqueeze(1)         # [B,1,64,248]
        x = self.sub(m)                                                     # [B,ch,16,62]
        B, C, Fq, T = x.shape
        x = self.inp(x.permute(0, 3, 1, 2).reshape(B, T, C * Fq)) + self.pos[:, :T]
        x = self.blocks(x)
        return self.pool(x.transpose(1, 2)).transpose(1, 2)                 # [B,31,d]


class _BasicBlock2d(nn.Module):
    def __init__(self, cin, cout, stride):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, stride, 1, bias=False)
        self.b1 = nn.BatchNorm2d(cout)
        self.c2 = nn.Conv2d(cout, cout, 3, 1, 1, bias=False)
        self.b2 = nn.BatchNorm2d(cout)
        self.short = (nn.Sequential(nn.Conv2d(cin, cout, 1, stride, bias=False), nn.BatchNorm2d(cout))
                      if stride != 1 or cin != cout else nn.Identity())

    def forward(self, x):
        return F.relu(self.b2(self.c2(F.relu(self.b1(self.c1(x))))) + self.short(x))


class AudioResNet(nn.Module):
    """ResNet 2D pada spektrogram log-mel (blok residual 32-64-128-128, stride 2 tiga kali) -> 31 token."""

    def __init__(self, d, nhead, dropout):
        super().__init__()
        self.mel = LogMel()
        self.stem = nn.Sequential(nn.Conv2d(1, 32, 3, 1, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU())
        self.layers = nn.Sequential(_BasicBlock2d(32, 32, 1), _BasicBlock2d(32, 64, 2),
                                    _BasicBlock2d(64, 128, 2), _BasicBlock2d(128, 128, 2))   # 64x248 -> 8x31
        self.proj = nn.Sequential(nn.Linear(128, d), nn.LayerNorm(d), nn.Dropout(dropout))

    def forward(self, wav):
        x = self.layers(self.stem(spec_augment(self.mel(wav), self.training).unsqueeze(1)))
        return self.proj(x.mean(2).transpose(1, 2))                         # rata-rata frekuensi -> [B,31,d]


AUDIO_ENCODERS = {"cnn_transformer": AudioCNNTransformer, "conformer": AudioConformer, "resnet": AudioResNet}


# =============================================================================
# TEKS — tingkat karakter (tahan salah ketik, kosakata 58 konsep, cukup kecil untuk browser)
# =============================================================================
def _text_pad(text: torch.Tensor) -> torch.Tensor:
    pad = text.eq(0)
    first = torch.arange(text.size(1), device=text.device).eq(0).unsqueeze(0)
    return pad & ~(pad.all(dim=1, keepdim=True) & first)                   # cegah baris all-pad (NaN)


class TextTransformer(nn.Module):
    """Embedding karakter + posisi -> Transformer encoder 1 lapis (mask padding)."""

    def __init__(self, d, nhead, dropout, max_len):
        super().__init__()
        self.emb = nn.Embedding(TEXT_VOCAB_SIZE, d, padding_idx=0)
        self.pos = nn.Parameter(torch.randn(1, max_len, d) * 0.02)
        self.enc = tx(d, nhead, 1, dropout)

    def forward(self, text):
        pad = _text_pad(text)
        return self.enc(self.emb(text) + self.pos, src_key_padding_mask=pad), pad


class TextBiLSTM(nn.Module):
    """Embedding karakter -> BiLSTM 1 lapis."""

    def __init__(self, d, nhead, dropout, max_len):
        super().__init__()
        self.emb = nn.Embedding(TEXT_VOCAB_SIZE, d, padding_idx=0)
        self.rnn = nn.LSTM(d, d // 2, batch_first=True, bidirectional=True)
        self.norm = nn.LayerNorm(d)
        self.drop = nn.Dropout(dropout)

    def forward(self, text):
        pad = _text_pad(text)
        h, _ = self.rnn(self.drop(self.emb(text)))
        return self.norm(h), pad


class TextCNN(nn.Module):
    """TextCNN (Kim, 2014) tingkat karakter: kernel 2/3/4/5 paralel, keluaran per posisi."""

    def __init__(self, d, nhead, dropout, max_len):
        super().__init__()
        self.emb = nn.Embedding(TEXT_VOCAB_SIZE, d, padding_idx=0)
        self.convs = nn.ModuleList([nn.Conv1d(d, d // 4, k, padding=k // 2) for k in (2, 3, 4, 5)])
        self.proj = nn.Sequential(nn.GELU(), nn.Dropout(dropout), nn.Linear(d, d), nn.LayerNorm(d))

    def forward(self, text):
        pad = _text_pad(text)
        x = self.emb(text).transpose(1, 2)
        L = text.size(1)
        y = torch.cat([c(x)[:, :, :L] for c in self.convs], 1).transpose(1, 2)
        return self.proj(y), pad


TEXT_ENCODERS = {"transformer": TextTransformer, "bilstm": TextBiLSTM, "textcnn": TextCNN}
