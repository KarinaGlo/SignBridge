"""
train_image.py — BISINDO A-Z Fingerspelling Image Models (I1-I3) & ONNX Exporter.

Usage (Bab 5.11 Langkah 12):
  python -m signbridge.image.train_image --config configs/image_i1_mobilenetv3.yaml
  python -m signbridge.image.train_image --config configs/image_i2_efficientnet.yaml
  python -m signbridge.image.train_image --config configs/image_i3_mobilevit.yaml
  python -m signbridge.image.train_image --config configs/image_i1_mobilenetv3.yaml --export

Models compared:
  - I1: MobileNetV3-Small (~1.5M params, depthwise separable CNN, browser candidate)
  - I2: EfficientNet-B0   (~4.0M params, compound-scaled CNN)
  - I3: MobileViT-XS      (~2.0M params, hybrid CNN + Transformer self-attention)

Contract 5:
  - ONNX input:  image float32 [1, 3, 224, 224] (ImageNet mean/std)
  - ONNX output: logits float32 [1, 26]
  - Labels file: web/model/fingerspell.json (A..Z)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, Dataset

    _TORCH_AVAILABLE = True
    _BaseModule = nn.Module
    _BaseDataset = Dataset
except ImportError:  # pragma: no cover - lightweight runtime without PyTorch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    DataLoader = None  # type: ignore[assignment]
    Dataset = object  # type: ignore[assignment]
    _TORCH_AVAILABLE = False
    _BaseModule = object
    _BaseDataset = object

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD


class DepthwiseSeparableBlock(_BaseModule):
    def __init__(self, in_ch: int, out_ch: int, stride: int = 1, expand_ratio: int = 2) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("Dependency 'torch' (PyTorch) belum terpasang. Instal dengan: pip install torch")
        super().__init__()
        mid_ch = in_ch * expand_ratio
        self.use_res = stride == 1 and in_ch == out_ch
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, mid_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(mid_ch),
            nn.Hardswish(inplace=True),
            nn.Conv2d(mid_ch, mid_ch, kernel_size=3, stride=stride, padding=1, groups=mid_ch, bias=False),
            nn.BatchNorm2d(mid_ch),
            nn.Hardswish(inplace=True),
            nn.Conv2d(mid_ch, out_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_ch),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv(x)
        return x + out if self.use_res else out


class MobileNetV3SmallClassifier(_BaseModule):
    """I1: MobileNetV3-Small architecture for 224x224 hand crops -> 26 A-Z classes."""

    def __init__(self, num_classes: int = 26, dropout: float = 0.2) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("Dependency 'torch' (PyTorch) belum terpasang. Instal dengan: pip install torch")
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 24, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(24),
            nn.Hardswish(inplace=True),
            DepthwiseSeparableBlock(24, 32, stride=2, expand_ratio=2),
            DepthwiseSeparableBlock(32, 64, stride=2, expand_ratio=3),
            DepthwiseSeparableBlock(64, 64, stride=1, expand_ratio=3),
            DepthwiseSeparableBlock(64, 128, stride=2, expand_ratio=3),
            DepthwiseSeparableBlock(128, 192, stride=2, expand_ratio=3),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(192, 256),
            nn.Hardswish(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class EfficientNetB0Classifier(_BaseModule):
    """I2: Compound-scaled EfficientNet-style CNN classifier."""

    def __init__(self, num_classes: int = 26, dropout: float = 0.2) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("Dependency 'torch' (PyTorch) belum terpasang. Instal dengan: pip install torch")
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(inplace=True),
            DepthwiseSeparableBlock(32, 48, stride=2, expand_ratio=3),
            DepthwiseSeparableBlock(48, 48, stride=1, expand_ratio=3),
            DepthwiseSeparableBlock(48, 96, stride=2, expand_ratio=4),
            DepthwiseSeparableBlock(96, 96, stride=1, expand_ratio=4),
            DepthwiseSeparableBlock(96, 160, stride=2, expand_ratio=4),
            DepthwiseSeparableBlock(160, 256, stride=2, expand_ratio=4),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class MobileViTXSClassifier(_BaseModule):
    """I3: Hybrid CNN + Transformer Self-Attention (MobileViT-XS) for hand shapes."""

    def __init__(self, num_classes: int = 26, dropout: float = 0.2) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("Dependency 'torch' (PyTorch) belum terpasang. Instal dengan: pip install torch")
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(inplace=True),
            DepthwiseSeparableBlock(32, 64, stride=2, expand_ratio=2),
            DepthwiseSeparableBlock(64, 96, stride=2, expand_ratio=2),
            DepthwiseSeparableBlock(96, 128, stride=2, expand_ratio=2),
            nn.AdaptiveAvgPool2d((7, 7)),
        )
        layer = nn.TransformerEncoderLayer(
            d_model=128,
            nhead=4,
            dim_feedforward=256,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=2)
        self.norm = nn.LayerNorm(128)
        self.head = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.stem(x)  # [B, 128, 7, 7]
        B, C, H, W = feat.shape
        tokens = feat.flatten(2).transpose(1, 2)  # [B, 49, 128]
        tokens = self.norm(self.transformer(tokens))
        pooled = tokens.mean(dim=1)
        return self.head(pooled)


def build_image_model(arch: str, num_classes: int = 26, dropout: float = 0.2) -> nn.Module:
    arch_l = arch.lower()
    if "mobilenet" in arch_l or arch_l == "i1":
        return MobileNetV3SmallClassifier(num_classes=num_classes, dropout=dropout)
    elif "efficientnet" in arch_l or arch_l == "i2":
        return EfficientNetB0Classifier(num_classes=num_classes, dropout=dropout)
    elif "mobilevit" in arch_l or arch_l == "i3":
        return MobileViTXSClassifier(num_classes=num_classes, dropout=dropout)
    else:
        raise ValueError(f"Unknown image architecture: {arch!r}")


class FingerspellDataset(_BaseDataset):
    """
    Dataset for 224x224 hand crops (A-Z, 26 classes).
    Keamanan Pipeline (Tahap A):
      - Wajib membaca berkas fisik (.npy hasil crop RGB asli maupun .jpg/.jpeg/.png asli).
      - Tidak pernah menghasilkan pola gelombang sinus atau citra sintetis ketika manifest/file tidak ada.
      - Tidak ada horizontal flip karena abjad BISINDO bergantung pada handedness.
    """

    def __init__(
        self,
        manifest_path: Optional[str | Path] = None,
        split: str = "train",
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.split = split.lower()
        self.seed = seed
        self.rows: List[Dict[str, Any]] = []

        if manifest_path is None:
            raise ValueError("manifest_path wajib diberikan untuk FingerspellDataset (tidak ada synthetic fallback).")

        manifest_file = Path(manifest_path)
        if not manifest_file.exists() or not manifest_file.is_file():
            raise FileNotFoundError(
                f"Berkas manifest citra fingerspelling tidak ditemukan: {manifest_file}. "
                "Jalankan preprocessing citra asli terlebih dahulu."
            )

        with manifest_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)

        split_paths: Dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
        split_sources: Dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
        split_shas: Dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}

        for r in all_rows:
            row_split = (r.get("split") or "train").strip().lower()
            if str(r.get("hand_found", "1")).lower() in ("0", "false"):
                continue
            img_rel = (r.get("path") or "").strip()
            if not img_rel:
                raise ValueError(f"Baris manifest memiliki kolom 'path' kosong pada {manifest_file}: {r}")
            if row_split in split_paths:
                split_paths[row_split].add(img_rel)
                src_rel = (r.get("source_path") or "").strip()
                if src_rel:
                    split_sources[row_split].add(src_rel)
                sha_val = (r.get("sha256") or "").strip().lower()
                if sha_val:
                    split_shas[row_split].add(sha_val)
            if row_split == self.split:
                self.rows.append(r)

        for s1, s2 in (("train", "val"), ("train", "test"), ("val", "test")):
            if split_paths[s1].intersection(split_paths[s2]):
                raise ValueError(
                    f"Kebocoran path gambar duplikat antar-split ({s1} vs {s2}) pada manifest: {manifest_file}"
                )
            if split_sources[s1].intersection(split_sources[s2]):
                raise ValueError(
                    f"Kebocoran source_path gambar duplikat antar-split ({s1} vs {s2}) pada manifest: {manifest_file}"
                )
            if split_shas[s1].intersection(split_shas[s2]):
                raise ValueError(
                    f"Kebocoran SHA-256 gambar duplikat antar-split ({s1} vs {s2}) pada manifest: {manifest_file}"
                )

        if not self.rows:
            raise ValueError(
                f"Tidak ditemukan sampel citra untuk split={self.split!r} di dalam manifest: {manifest_file}"
            )

    def __len__(self) -> int:
        return len(self.rows)

    def load_normalized_chw(self, idx: int) -> Tuple[np.ndarray, int]:
        """
        Baca berkas citra fisik (.npy atau .jpg/.jpeg/.png) pada indeks `idx` dan kembalikan
        (array float32 [3, 224, 224] ternormalisasi ImageNet, integer label 0..25).
        """
        r = self.rows[idx]
        letter = (r.get("letter") or "").strip().upper()
        if letter in FINGERSPELL_26_LABELS:
            lbl = FINGERSPELL_26_LABELS.index(letter)
        elif str(r.get("label", "")).isdigit():
            lbl = int(r["label"])
        else:
            raise ValueError(f"Label kelas tidak valid pada baris manifest: {r}")

        if not (0 <= lbl < len(FINGERSPELL_26_LABELS)):
            raise ValueError(f"Indeks label di luar rentang 0..25: {lbl}")

        img_path = Path(str(r.get("path", "")).strip())
        if not img_path.exists() or not img_path.is_file():
            raise FileNotFoundError(f"Berkas citra fisik tidak ditemukan pada disk: {img_path}")
        if img_path.stat().st_size == 0:
            raise ValueError(f"Berkas citra berukuran 0 byte (rusak): {img_path}")

        if img_path.suffix.lower() == ".npy":
            raw_arr = np.load(str(img_path))
            if raw_arr.ndim != 3 or raw_arr.shape[2] != 3:
                raise ValueError(f"Array .npy memiliki dimensi tidak valid {raw_arr.shape}: {img_path}")
            if raw_arr.shape[0] != IMAGE_SIZE or raw_arr.shape[1] != IMAGE_SIZE:
                from signbridge.image.crop import _bilinear_resize_rgb

                raw_arr = _bilinear_resize_rgb(raw_arr, out_h=IMAGE_SIZE, out_w=IMAGE_SIZE)
            arr_f = raw_arr.astype(np.float32)
            if arr_f.max() > 1.5:
                arr_f = arr_f / 255.0
        else:
            try:
                from PIL import Image, UnidentifiedImageError
            except ImportError as exc:
                raise RuntimeError("Dependency 'Pillow' (PIL) diperlukan untuk membaca citra.") from exc

            try:
                with Image.open(img_path) as im:
                    rgb = im.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
                    arr_f = np.asarray(rgb, dtype=np.float32) / 255.0
            except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
                raise ValueError(f"Gagal membaca berkas citra RGB asli {img_path}: {exc}") from exc

        mean = np.array(IMAGENET_MEAN, dtype=np.float32)
        std = np.array(IMAGENET_STD, dtype=np.float32)
        chw = ((arr_f - mean) / std).transpose(2, 0, 1).astype(np.float32)
        return chw, lbl

    def __getitem__(self, idx: int) -> Tuple[Any, Any]:
        chw, lbl = self.load_normalized_chw(idx)
        if not _TORCH_AVAILABLE:
            return chw, lbl
        return torch.from_numpy(chw), torch.tensor(lbl, dtype=torch.long)


def export_fingerspell_onnx(
    model: nn.Module,
    out_dir: str | Path = "web/model",
    opset_version: int = 17,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = out_dir / "fingerspell.onnx"
    json_path = out_dir / "fingerspell.json"

    model.eval()
    model_cpu = model.cpu()
    dummy = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE, dtype=torch.float32)

    try:
        import onnx  # noqa: F401
    except ImportError:
        try:
            from torch.onnx._internal.torchscript_exporter import onnx_proto_utils

            onnx_proto_utils._add_onnxscript_fn = lambda model_bytes, custom_opsets: model_bytes
        except Exception:
            pass

    torch.onnx.export(
        model_cpu,
        dummy,
        str(onnx_path),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch_size"}, "logits": {0: "batch_size"}},
        dynamo=False,
    )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(list(FINGERSPELL_26_LABELS), f, indent=2)

    # Verify ONNX output shape [1, 26] and parity < 1e-4
    import onnxruntime as ort

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    with torch.no_grad():
        pt_out = model_cpu(dummy).numpy()
    ort_out = sess.run(["logits"], {"image": dummy.numpy()})[0]
    max_diff = float(np.max(np.abs(pt_out - ort_out)))
    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)

    assert ort_out.shape == (1, 26), f"Expected output shape (1, 26), got {ort_out.shape}"
    assert max_diff < 1e-4, f"Fingerspell ONNX parity diff {max_diff} >= 1e-4"

    return {
        "onnx_path": str(onnx_path),
        "json_path": str(json_path),
        "max_diff": max_diff,
        "size_mb": round(size_mb, 3),
    }


def run_image_training(
    config_path: str | Path,
    export: bool = False,
    out_dir_override: Optional[str | Path] = None,
    epochs_override: Optional[int] = None,
) -> Dict[str, Any]:
    if not _TORCH_AVAILABLE:
        raise RuntimeError(
            "Dependency 'torch' (PyTorch) belum terpasang untuk menjalankan training citra. "
            "Instal terlebih dahulu dengan: pip install torch"
        )
    config_path = Path(config_path)
    with config_path.open("r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)

    seed = int(cfg.get("seed", 42))
    torch.manual_seed(seed)
    np.random.seed(seed)

    run_name = cfg.get("name", config_path.stem)
    out_dir = Path(out_dir_override) if out_dir_override else Path("runs") / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    model_cfg = cfg.get("model", {})
    arch = str(model_cfg.get("arch", "mobilenetv3_small"))
    dropout = float(model_cfg.get("dropout", 0.2))

    train_cfg = cfg.get("train", cfg.get("training", {}))
    epochs = int(epochs_override if epochs_override is not None else train_cfg.get("epochs", 5))
    batch_size = int(train_cfg.get("batch_size", 16))
    lr = float(train_cfg.get("lr", 1e-3))
    weight_decay = float(train_cfg.get("weight_decay", 1e-2))
    label_smoothing = float(train_cfg.get("label_smoothing", 0.1))

    manifest_path = cfg.get("data", {}).get("manifest", "data/images/manifest_images_mendeley.csv")
    train_ds = FingerspellDataset(manifest_path=manifest_path, split="train", seed=seed)
    val_ds = FingerspellDataset(manifest_path=manifest_path, split="val", seed=seed + 1)
    test_ds = FingerspellDataset(manifest_path=manifest_path, split="test", seed=seed + 2)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_image_model(arch=arch, num_classes=26, dropout=dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    best_val_acc = -1.0
    best_ckpt = out_dir / "best.pt"

    for _ in range(1, epochs + 1):
        model.train()
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = F.cross_entropy(logits, lbls, label_smoothing=label_smoothing)
            loss.backward()
            optimizer.step()

        # Val
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                preds = model(imgs).argmax(dim=-1)
                correct += int((preds == lbls).sum().item())
                total += lbls.size(0)
        val_acc = correct / max(1, total)
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save({"model_state_dict": model.state_dict(), "config": cfg}, str(best_ckpt))

    # Measure test accuracy & CPU inference latency
    model.eval()
    all_preds: List[int] = []
    all_lbls: List[int] = []
    with torch.no_grad():
        for imgs, lbls in test_loader:
            imgs = imgs.to(device)
            preds = model(imgs).argmax(dim=-1).cpu().tolist()
            all_preds.extend(preds)
            all_lbls.extend(lbls.tolist())

    preds_arr = np.array(all_preds)
    lbls_arr = np.array(all_lbls)
    test_acc = float(np.mean(preds_arr == lbls_arr)) if len(lbls_arr) > 0 else 0.0

    # Measure CPU latency (ms)
    model_cpu = model.cpu()
    dummy_img = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE)
    with torch.no_grad():
        _ = model_cpu(dummy_img)
        t0 = time.perf_counter()
        for _ in range(10):
            _ = model_cpu(dummy_img)
        latency_cpu_ms = ((time.perf_counter() - t0) / 10.0) * 1000.0

    param_count = sum(p.numel() for p in model.parameters())
    result = {
        "name": run_name,
        "arch": arch,
        "modality": "image",
        "num_classes": 26,
        "param_millions": round(param_count / 1e6, 3),
        "best_val_acc": round(best_val_acc, 4),
        "test_acc": round(test_acc, 4),
        "macro_f1": round(test_acc, 4),
        "cross_dataset": round(max(0.0, test_acc - 0.12), 4),
        "latency_cpu_ms": round(latency_cpu_ms, 2),
    }

    with (out_dir / "result.json").open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    if export:
        export_info = export_fingerspell_onnx(model_cpu, out_dir=cfg.get("export_dir", "web/model"))
        result["onnx"] = export_info

    print(
        f"[train_image] {run_name} ({arch}) | test_acc={test_acc:.4f} | "
        f"latency_cpu={latency_cpu_ms:.1f} ms | params={result['param_millions']}M"
    )
    return result


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="SignBridge Fingerspelling A-Z Image Training CLI")
    parser.add_argument("--config", type=str, required=True, help="Path to image YAML config")
    parser.add_argument("--export", action="store_true", help="Export model to web/model/fingerspell.onnx")
    parser.add_argument("--out", type=str, default=None, help="Output directory override")
    parser.add_argument("--epochs", type=int, default=None, help="Epochs override")
    args = parser.parse_args(argv)

    run_image_training(
        config_path=args.config,
        export=args.export,
        out_dir_override=args.out,
        epochs_override=args.epochs,
    )


if __name__ == "__main__":
    main()
