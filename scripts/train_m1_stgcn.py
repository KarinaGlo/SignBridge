import os
import sys
import time
import json
import random
from pathlib import Path

# Set MPLCONFIGDIR
os.environ['MPLCONFIGDIR'] = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'matplotlib')

import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sklearn
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.models.stgcn import PoseModel
from signbridge.graph import build_adjacency, is_graph_connected, get_anatomical_edges
from signbridge.data.dataset import SignDataset
from signbridge.constants import (
    NUM_KEYPOINTS,
    NUM_COORDS,
    T_MAX,
    POSE_START, POSE_END,
    LEFT_HAND_START, LEFT_HAND_END,
    RIGHT_HAND_START, RIGHT_HAND_END,
    FACE_START, FACE_END
)

OUT_DIR = ROOT / "outputs" / "experiments" / "M1_stgcn_baseline"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def evaluate_loader(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for batch in loader:
            pose = batch["pose"].to(device)    # [B, 64, 86, 3]
            mask = batch["mask"].to(device)    # [B, 64, 86]
            labels = batch["label"].to(device) # [B]
            
            logits = model.forward_logits(pose, mask=mask)
            loss = criterion(logits, labels)
            total_loss += loss.item() * len(labels)
            
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(logits, dim=-1)
            
            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())
            all_probs.extend(probs.cpu().numpy().tolist())
            
    avg_loss = total_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, acc, np.array(all_preds), np.array(all_labels), np.array(all_probs)

def save_graph_artifacts(out_dir: Path):
    A = build_adjacency(NUM_KEYPOINTS)
    np.save(out_dir / "graph_adjacency.npy", A)
    
    edges = get_anatomical_edges()
    topology_info = {
        "num_nodes": NUM_KEYPOINTS,
        "partitions": 3,
        "partition_definitions": {
            "0": "Identity self-loops (A_1 = I_86)",
            "1": "1-hop symmetric normalized adjacency (A_2 = D^{-1/2} A D^{-1/2})",
            "2": "2-hop symmetric normalized adjacency (A_3 = D_2^{-1/2} A_{2-hop} D_2^{-1/2})"
        },
        "node_groups": {
            "pose": {"range": [POSE_START, POSE_END], "count": 9, "description": "Nose, L/R shoulder, elbow, wrist, hip"},
            "left_hand": {"range": [LEFT_HAND_START, LEFT_HAND_END], "count": 21, "description": "Left hand skeleton"},
            "right_hand": {"range": [RIGHT_HAND_START, RIGHT_HAND_END], "count": 21, "description": "Right hand skeleton"},
            "face": {"range": [FACE_START, FACE_END], "count": 35, "description": "Facial contour (lips, eyebrows, eyes, nose)"}
        },
        "num_spatial_edges": len(edges),
        "spatial_edges": [[int(u), int(v)] for u, v in edges],
        "is_connected": is_graph_connected(NUM_KEYPOINTS),
        "temporal_edges": "Implicitly connected across frames via 9x1 Temporal Convolution",
        "self_loops": True
    }
    with open(out_dir / "graph_topology.json", "w") as f:
        json.dump(topology_info, f, indent=2)
    print(f"Graph artifacts saved to {out_dir}")

def main():
    start_time_all = time.time()
    set_seed(42)
    device = torch.device("cpu")
    
    print("=================================================================")
    print("  SIGNBRIDGE TAHAP A.5: M1 ST-GCN BASELINE TRAINING (WL-BISINDO)")
    print("=================================================================")
    print(f"Device: {device}")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"NumPy Version: {np.__version__}")
    print(f"Random Seed: 42")
    
    # Save graph artifacts first
    save_graph_artifacts(OUT_DIR)
    
    config = {
        "experiment_id": "M1_stgcn_baseline",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": 42,
        "protocol": "SD",
        "dataset": {
            "name": "WL-BISINDO",
            "manifest": "data/manifest_wl_bisindo.csv",
            "sidecar": "data/manifest_wl_bisindo_source_metadata.csv",
            "total_samples": 1600,
            "num_classes": 32,
            "seq_len": 64,
            "num_keypoints": 86,
            "splits": {"train": 960, "val": 180, "test": 460}
        },
        "model": {
            "type": "ST-GCN (PoseModel)",
            "num_blocks": 4,
            "hidden_dim": 256,
            "channel_progression": [64, 64, 128, 256],
            "temporal_kernel": 9,
            "dropout": 0.10,
            "residual": True,
            "spatial_adjacency": "3-partition normalized (self, 1-hop, 2-hop)",
            "valid_mask_handling": "Masked input, velocity gating, BN bias suppression, masked spatial pooling"
        },
        "training": {
            "max_epochs": 100,
            "patience": 10,
            "batch_size": 32,
            "optimizer": "AdamW",
            "learning_rate": 0.001,
            "weight_decay": 0.01,
            "label_smoothing": 0.1,
            "scheduler": "ReduceLROnPlateau(factor=0.5, patience=4, min_lr=1e-5)",
            "augmentation": {
                "mirror_p": 0.0,
                "rot_deg": 12.0,
                "scale_range": [0.9, 1.1],
                "shift_range": 0.03,
                "noise_std": 0.003,
                "speed_range": [0.85, 1.15],
                "hand_dropout_p": 0.10
            }
        },
        "hardware": {
            "device": "CPU",
            "cpu_threads": torch.get_num_threads(),
            "cpu_architecture": "AMD64",
            "host_gpu": "NVIDIA GeForce RTX 3050 (6GB) - Evaluated, CPU selected per project spec",
            "python_version": sys.version
        }
    }
    
    with open(OUT_DIR / "training_config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)
        
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    train_dataset = SignDataset(manifest_path, data_root=ROOT, split="train", protocol="sd", allow_mixed_sources=False)
    val_dataset = SignDataset(manifest_path, data_root=ROOT, split="val", protocol="sd", allow_mixed_sources=False)
    test_dataset = SignDataset(manifest_path, data_root=ROOT, split="test", protocol="sd", allow_mixed_sources=False)
    
    print(f"Loaded splits: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")
    assert len(train_dataset) == 960
    assert len(val_dataset) == 180
    assert len(test_dataset) == 460
    
    class_names = train_dataset.classes
    assert len(class_names) == 32
    
    train_loader = DataLoader(train_dataset, batch_size=config["training"]["batch_size"], shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=config["training"]["batch_size"], shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=config["training"]["batch_size"], shuffle=False, num_workers=0)
    
    model = PoseModel(
        num_classes=config["dataset"]["num_classes"],
        hidden_dim=config["model"]["hidden_dim"],
        dropout=config["model"]["dropout"],
        num_blocks=config["model"]["num_blocks"]
    ).to(device)
    
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model instantiated: ST-GCN PoseModel | Trainable Parameters: {param_count:,}")
    config["model"]["parameter_count"] = param_count
    
    criterion = nn.CrossEntropyLoss(label_smoothing=config["training"]["label_smoothing"])
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"]
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=4, min_lr=1e-5
    )
    
    best_val_loss = float('inf')
    best_val_acc = 0.0
    best_epoch = 0
    patience = config["training"]["patience"]
    patience_counter = 0
    
    history = []
    
    print("\n--- STARTING TRAINING LOOP (MAX 100 EPOCHS, PATIENCE 10) ---")
    for epoch in range(1, config["training"]["max_epochs"] + 1):
        epoch_start = time.time()
        train_dataset.set_epoch(epoch)
        
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch in train_loader:
            pose = batch["pose"].to(device)
            mask = batch["mask"].to(device)
            labels = batch["label"].to(device)
            
            optimizer.zero_grad()
            logits = model.forward_logits(pose, mask=mask)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * len(labels)
            preds = torch.argmax(logits, dim=-1)
            train_correct += (preds == labels).sum().item()
            train_total += len(labels)
            
        epoch_train_loss = train_loss / train_total
        epoch_train_acc = train_correct / train_total
        
        epoch_val_loss, epoch_val_acc, _, _, _ = evaluate_loader(model, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(epoch_val_loss)
        
        epoch_dur = time.time() - epoch_start
        
        history_entry = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_acc": round(epoch_train_acc, 4),
            "val_loss": round(epoch_val_loss, 4),
            "val_acc": round(epoch_val_acc, 4),
            "lr": current_lr,
            "duration_sec": round(epoch_dur, 2)
        }
        history.append(history_entry)
        
        is_best = epoch_val_loss < best_val_loss
        if is_best:
            best_val_loss = epoch_val_loss
            best_val_acc = epoch_val_acc
            best_epoch = epoch
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": best_val_loss,
                "val_acc": best_val_acc,
                "config": config,
                "class_names": class_names
            }, OUT_DIR / "best_model.pt")
            saved_tag = "[BEST CHECKPOINT SAVED]"
        else:
            patience_counter += 1
            saved_tag = f"[Patience {patience_counter}/{patience}]"
            
        torch.save({
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "val_loss": epoch_val_loss,
            "val_acc": epoch_val_acc,
            "config": config,
            "class_names": class_names
        }, OUT_DIR / "last_model.pt")
        
        print(f"Epoch [{epoch:03d}/{config['training']['max_epochs']:03d}] | "
              f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc*100:6.2f}% | "
              f"Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc*100:6.2f}% | "
              f"LR: {current_lr:.6f} | Time: {epoch_dur:5.1f}s {saved_tag}")
              
        if patience_counter >= patience:
            print(f"\n-> EARLY STOPPING TRIGGERED AT EPOCH {epoch}. Best epoch was {best_epoch}.")
            break
            
    # Save training history CSV
    df_history = pd.DataFrame(history)
    df_history.to_csv(OUT_DIR / "training_history.csv", index=False)
    
    # Plot Training Curves
    plt.figure(figsize=(9, 5))
    plt.plot(df_history["epoch"], df_history["train_loss"], label="Train Loss", color="royalblue", lw=2)
    plt.plot(df_history["epoch"], df_history["val_loss"], label="Val Loss", color="coral", lw=2)
    plt.axvline(best_epoch, color="forestgreen", linestyle="--", label=f"Best Checkpoint (Epoch {best_epoch})")
    plt.title("M1 ST-GCN Baseline: Training & Validation Loss", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Cross-Entropy Loss (Label Smoothing 0.1)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "training_loss.png", dpi=300)
    plt.close()
    
    plt.figure(figsize=(9, 5))
    plt.plot(df_history["epoch"], df_history["train_acc"] * 100, label="Train Acc", color="royalblue", lw=2)
    plt.plot(df_history["epoch"], df_history["val_acc"] * 100, label="Val Acc", color="coral", lw=2)
    plt.axvline(best_epoch, color="forestgreen", linestyle="--", label=f"Best Checkpoint (Epoch {best_epoch})")
    plt.title("M1 ST-GCN Baseline: Training & Validation Accuracy (%)", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "training_accuracy.png", dpi=300)
    plt.close()
    
    # Evaluate Best Model
    print(f"\n=================================================================")
    print(f"  EVALUATING BEST MODEL (Epoch {best_epoch}) ON VALIDATION & TEST")
    print(f"=================================================================")
    best_ckpt = torch.load(OUT_DIR / "best_model.pt", map_location=device)
    model.load_state_dict(best_ckpt["model_state_dict"])
    
    val_loss, val_acc, val_preds, val_labels, _ = evaluate_loader(model, val_loader, criterion, device)
    test_loss, test_acc, test_preds, test_labels, test_probs = evaluate_loader(model, test_loader, criterion, device)
    
    macro_prec = precision_score(test_labels, test_preds, average='macro', zero_division=0)
    macro_rec = recall_score(test_labels, test_preds, average='macro', zero_division=0)
    macro_f1 = f1_score(test_labels, test_preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(test_labels, test_preds, average='weighted', zero_division=0)
    
    top5_correct = 0
    for prob_vec, true_lbl in zip(test_probs, test_labels):
        top5_indices = np.argsort(prob_vec)[-5:]
        if true_lbl in top5_indices:
            top5_correct += 1
    top5_acc = top5_correct / len(test_labels)
    
    print(f"\nFinal Test Results (Single Evaluation on Held-Out Test Set, N={len(test_labels)}):")
    print(f"  Test Loss:           {test_loss:.4f}")
    print(f"  Test Accuracy:       {test_acc*100:.2f}% ({np.sum(test_preds == test_labels)}/{len(test_labels)})")
    print(f"  Test Top-5 Accuracy: {top5_acc*100:.2f}%")
    print(f"  Macro Precision:     {macro_prec*100:.2f}%")
    print(f"  Macro Recall:        {macro_rec*100:.2f}%")
    print(f"  Macro F1-Score:      {macro_f1*100:.2f}%")
    print(f"  Weighted F1-Score:   {weighted_f1*100:.2f}%")
    
    metrics_summary = {
        "best_epoch": int(best_epoch),
        "validation_metrics": {
            "val_loss": round(val_loss, 4),
            "val_accuracy": round(val_acc, 4)
        },
        "test_metrics": {
            "test_loss": round(test_loss, 4),
            "test_accuracy": round(test_acc, 4),
            "test_top5_accuracy": round(top5_acc, 4),
            "test_macro_precision": round(macro_prec, 4),
            "test_macro_recall": round(macro_rec, 4),
            "test_macro_f1": round(macro_f1, 4),
            "test_weighted_f1": round(weighted_f1, 4),
            "total_test_samples": int(len(test_labels)),
            "correct_test_samples": int(np.sum(test_preds == test_labels))
        }
    }
    with open(OUT_DIR / "evaluation_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    # Classification Report
    cls_report_dict = classification_report(
        test_labels, test_preds, target_names=class_names, output_dict=True, zero_division=0
    )
    df_cls = pd.DataFrame(cls_report_dict).transpose()
    df_cls.to_csv(OUT_DIR / "classification_report.csv", index=True)
    
    # Confusion Matrix
    cm = confusion_matrix(test_labels, test_preds)
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        title=f'M1 ST-GCN Baseline Confusion Matrix (Test Set, N={len(test_labels)})\nTest Accuracy: {test_acc*100:.2f}%, Macro F1: {macro_f1*100:.2f}%',
        ylabel='True Label',
        xlabel='Predicted Label'
    )
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor", fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            if cm[i, j] > 0:
                ax.text(j, i, format(cm[i, j], 'd'),
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black",
                        fontsize=7)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png", dpi=250)
    plt.close()
    
    total_training_time_min = (time.time() - start_time_all) / 60.0
    
    # Metadata
    metadata = {
        "model_architecture": "ST-GCN (Spatial-Temporal Graph Convolutional Network)",
        "num_layers": 4,
        "channel_progression": [64, 64, 128, 256],
        "parameter_count": int(param_count),
        "hidden_dim": 256,
        "dataset": "WL-BISINDO",
        "num_classes": 32,
        "input_tensor_shape": "[B, 64, 86, 3]",
        "valid_mask_shape": "[B, 64, 86]",
        "num_epochs_trained": int(len(history)),
        "best_epoch": int(best_epoch),
        "total_training_time_minutes": round(total_training_time_min, 2),
        "protocol": "Signer-Dependent (SD)",
        "framework_versions": {
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__
        }
    }
    with open(OUT_DIR / "experiment_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
        
    summary_exp = {
        "experiment": "M1_stgcn_baseline",
        "status": "COMPLETED",
        "protocol": "Signer-Dependent (SD)",
        "test_accuracy": round(test_acc, 4),
        "test_macro_f1": round(macro_f1, 4),
        "test_top5_accuracy": round(top5_acc, 4),
        "parameter_count": int(param_count),
        "training_time_minutes": round(total_training_time_min, 2),
        "epochs_trained": int(len(history)),
        "best_epoch": int(best_epoch)
    }
    with open(OUT_DIR / "experiment_summary.json", "w") as f:
        json.dump(summary_exp, f, indent=2)
        
    print(f"\nTRAINING COMPLETED IN {total_training_time_min:.2f} MINUTES.")
    print(f"Artifacts successfully written to: {OUT_DIR}")

if __name__ == "__main__":
    main()
