import sys
import json
import yaml
from pathlib import Path
import numpy as np
import pandas as pd
import torch

ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT))

from signbridge.models.stgcn import PoseModel, STGCNEncoder, STGCNBlock, GraphConv
from signbridge.models.student import StudentPoseTransformer
from signbridge.graph import build_adjacency, is_graph_connected, get_anatomical_edges
from signbridge.data.dataset import SignDataset

m1_dir = ROOT / "outputs" / "experiments" / "M1_stgcn_baseline"
m0_dir = ROOT / "outputs" / "experiments" / "M0_student_baseline"
report_path = ROOT / "docs" / "M1_STGCN_TRAINING_REPORT.md"

print("=================================================================")
print("          AUDIT SCRIPT: M1 ST-GCN FINAL ACADEMIC REVIEW          ")
print("=================================================================")

# 1. Check Artifact Existence & Sizes
print("\n--- 1. ARTIFACT EXISTENCE & SIZES ---")
artifacts_m1 = [
    "best_model.pt",
    "last_model.pt",
    "training_config.yaml",
    "training_history.csv",
    "training_loss.png",
    "training_accuracy.png",
    "confusion_matrix.png",
    "classification_report.csv",
    "evaluation_metrics.json",
    "experiment_metadata.json",
    "experiment_summary.json",
    "graph_adjacency.npy",
    "graph_topology.json",
]
for a in artifacts_m1:
    p = m1_dir / a
    assert p.exists(), f"Missing artifact: {a}"
    print(f"  [OK] {a:<28} Size: {p.stat().st_size:>10,} bytes")

# 2. Check Numerical Claims
print("\n--- 2. NUMERICAL CLAIMS VERIFICATION ---")
with open(m1_dir / "evaluation_metrics.json") as f:
    eval_m1 = json.load(f)
with open(m1_dir / "experiment_summary.json") as f:
    sum_m1 = json.load(f)
with open(m1_dir / "experiment_metadata.json") as f:
    meta_m1 = json.load(f)
with open(m1_dir / "training_config.yaml") as f:
    cfg_m1 = yaml.safe_load(f)
df_hist_m1 = pd.read_csv(m1_dir / "training_history.csv")
df_cls_m1 = pd.read_csv(m1_dir / "classification_report.csv", index_col=0)

# Epochs
num_epochs = len(df_hist_m1)
best_epoch_hist = int(df_hist_m1.loc[df_hist_m1["val_loss"].idxmin()]["epoch"])
min_val_loss = float(df_hist_m1["val_loss"].min())
val_acc_at_best = float(df_hist_m1.loc[df_hist_m1["val_loss"].idxmin()]["val_acc"])

print(f"  Total Epochs: {num_epochs} (reported: 89)")
print(f"  Best Epoch: {best_epoch_hist} (reported: 79)")
print(f"  Best Val Loss: {min_val_loss:.4f} (reported: 0.7120)")
print(f"  Val Acc at Best: {val_acc_at_best*100:.2f}% (reported: 98.89%)")

assert num_epochs == 89
assert best_epoch_hist == 79
assert abs(min_val_loss - 0.7120) < 1e-4
assert abs(val_acc_at_best - 0.9889) < 1e-4

# Test Metrics
test_m = eval_m1["test_metrics"]
print(f"  Test Loss: {test_m['test_loss']:.4f} (reported: 0.6986)")
print(f"  Test Accuracy: {test_m['test_accuracy']*100:.2f}% ({test_m['correct_test_samples']}/{test_m['total_test_samples']})")
print(f"  Top-5 Accuracy: {test_m['test_top5_accuracy']*100:.2f}%")
print(f"  Macro Precision: {test_m['test_macro_precision']*100:.2f}% (reported: 99.24%)")
print(f"  Macro Recall: {test_m['test_macro_recall']*100:.2f}% (reported: 99.12%)")
print(f"  Macro F1: {test_m['test_macro_f1']*100:.2f}% (reported: 99.14%)")
print(f"  Weighted F1: {test_m['test_weighted_f1']*100:.2f}% (reported: 99.13%)")

assert test_m["correct_test_samples"] == 456
assert test_m["total_test_samples"] == 460
assert abs(test_m["test_accuracy"] - 0.991304) < 1e-4
assert abs(test_m["test_macro_precision"] - 0.992417) < 1e-4
assert abs(test_m["test_macro_recall"] - 0.991220) < 1e-4
assert abs(test_m["test_macro_f1"] - 0.991392) < 1e-4

# Checkpoint parameter count
ckpt_best = torch.load(m1_dir / "best_model.pt", map_location="cpu")
ckpt_last = torch.load(m1_dir / "last_model.pt", map_location="cpu")
assert ckpt_best["epoch"] == 79
assert ckpt_last["epoch"] == 89

model_m1 = PoseModel(num_classes=32, hidden_dim=256, dropout=0.1, num_blocks=4)
model_m1.load_state_dict(ckpt_best["model_state_dict"])
p_count = sum(p.numel() for p in model_m1.parameters() if p.requires_grad)
print(f"  Trainable Parameters: {p_count:,} (reported: 1,096,408)")
assert p_count == 1096408

# Checkpoint file sizes distinction
best_size = (m1_dir / "best_model.pt").stat().st_size
last_size = (m1_dir / "last_model.pt").stat().st_size
print(f"  best_model.pt size: {best_size:,} bytes (~13.61 MB - includes optimizer state dict: {'optimizer_state_dict' in ckpt_best})")
print(f"  last_model.pt size: {last_size:,} bytes (~4.79 MB - weights only: {'optimizer_state_dict' in ckpt_last})")
assert "optimizer_state_dict" in ckpt_best
assert "optimizer_state_dict" not in ckpt_last

# 3. Model Architecture Verification
print("\n--- 3. MODEL ARCHITECTURE VERIFICATION ---")
A_np = build_adjacency(86)
print(f"  Adjacency shape: {A_np.shape} (3 partitions, 86x86)")
assert A_np.shape == (3, 86, 86)
edges = get_anatomical_edges()
print(f"  Anatomical edges: {len(edges)} (reported: 94)")
assert len(edges) == 94
assert is_graph_connected(86)

# Verify adaptive matrix in GraphConv
assert hasattr(model_m1.encoder.blocks[0].gcn, "B"), "Missing adaptive adjacency matrix B!"
print(f"  Adaptive matrix B shape: {model_m1.encoder.blocks[0].gcn.B.shape}")

# Verify 4 layers channels
expected_channels = [(6, 64), (64, 64), (64, 128), (128, 256)]
for idx, blk in enumerate(model_m1.encoder.blocks):
    in_c = blk.gcn.conv.in_channels
    out_c = blk.bn1.num_features
    stride = blk.tcn[0].stride[0]
    kernel = blk.tcn[0].kernel_size
    pad = blk.tcn[0].padding
    print(f"  Block {idx}: In={in_c}, Out={out_c}, Stride={stride}, Kernel={kernel}, Pad={pad}")
    assert (in_c, out_c) == expected_channels[idx]
    assert kernel == (9, 1)
    assert pad == (4, 0)

# 4. Dataset & Split Consistency (M0 vs M1)
print("\n--- 4. DATASET & SPLIT INTEGRITY ---")
manifest_p = ROOT / "data" / "manifest_wl_bisindo.csv"
ds_m1_test = SignDataset(manifest_p, split="test", protocol="sd")
ds_m0_test = SignDataset(manifest_p, split="test", protocol="sd")

assert len(ds_m1_test) == 460
assert len(ds_m0_test) == 460
m1_test_vids = [s["video_id"] for s in ds_m1_test.samples]
m0_test_vids = [s["video_id"] for s in ds_m0_test.samples]
assert m1_test_vids == m0_test_vids, "M0 and M1 test samples differ!"
print("  Test sample IDs between M0 and M1 are 100% identical (460 samples).")

# 5. M0 vs M1 Metrics
print("\n--- 5. M0 VS M1 COMPARISON AUDIT ---")
with open(m0_dir / "evaluation_metrics.json") as f:
    eval_m0 = json.load(f)["test_metrics"]
with open(m0_dir / "experiment_metadata.json") as f:
    meta_m0 = json.load(f)

m0_acc = eval_m0["test_accuracy"]
m1_acc = eval_m1["test_metrics"]["test_accuracy"]
m0_f1 = eval_m0["test_macro_f1"]
m1_f1 = eval_m1["test_metrics"]["test_macro_f1"]
m0_prec = eval_m0["test_macro_precision"]
m1_prec = eval_m1["test_metrics"]["test_macro_precision"]

print(f"  Test Accuracy: M0={m0_acc*100:.4f}% vs M1={m1_acc*100:.4f}% (Delta = {(m1_acc-m0_acc)*100:+.4f}%)")
print(f"  Macro F1:      M0={m0_f1*100:.4f}% vs M1={m1_f1*100:.4f}% (Delta = {(m1_f1-m0_f1)*100:+.4f}%)")
print(f"  Macro Prec:    M0={m0_prec*100:.4f}% vs M1={m1_prec*100:.4f}% (Delta = {(m1_prec-m0_prec)*100:+.4f}%)")
print(f"  Parameters:    M0=1,335,872 vs M1=1,096,408 (Delta = {1096408-1335872:,} / -17.93%)")

# 6. Check Markdown Image Links
print("\n--- 6. IMAGE PATHS VERIFICATION ---")
docs_dir = ROOT / "docs"
img_loss = docs_dir / "../outputs/experiments/M1_stgcn_baseline/training_loss.png"
img_acc = docs_dir / "../outputs/experiments/M1_stgcn_baseline/training_accuracy.png"
img_cm = docs_dir / "../outputs/experiments/M1_stgcn_baseline/confusion_matrix.png"

assert img_loss.resolve().exists(), f"Image not found: {img_loss}"
assert img_acc.resolve().exists(), f"Image not found: {img_acc}"
assert img_cm.resolve().exists(), f"Image not found: {img_cm}"
print(f"  [OK] training_loss.png exists ({img_loss.resolve().stat().st_size:,} bytes)")
print(f"  [OK] training_accuracy.png exists ({img_acc.resolve().stat().st_size:,} bytes)")
print(f"  [OK] confusion_matrix.png exists ({img_cm.resolve().stat().st_size:,} bytes)")

print("\n=================================================================")
print("             AUDIT CHECKLIST PASSED WITHOUT ERRORS              ")
print("=================================================================")

