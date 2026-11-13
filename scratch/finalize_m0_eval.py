import os
import sys
import time
import json
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

from signbridge.models.student import StudentPoseTransformer
from signbridge.data.dataset import SignDataset

OUT_DIR = ROOT / "outputs" / "experiments" / "M0_student_baseline"

def evaluate_loader(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for batch in loader:
            pose = batch["pose"].to(device)
            mask = batch["mask"].to(device)
            labels = batch["label"].to(device)
            
            # Mask invalid landmarks
            pose = pose * mask.unsqueeze(-1).float()
            
            logits = model(pose)
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

def main():
    device = torch.device("cpu")
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    
    val_dataset = SignDataset(manifest_path, data_root=ROOT, split="val", protocol="sd", allow_mixed_sources=False)
    test_dataset = SignDataset(manifest_path, data_root=ROOT, split="test", protocol="sd", allow_mixed_sources=False)
    
    # Official 32 classes from dataset
    class_names = test_dataset.classes
    print("Class names (32 classes):", class_names)
    assert len(class_names) == 32
    
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    # Load config and best model
    with open(OUT_DIR / "training_config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    model = StudentPoseTransformer(
        num_classes=32,
        d_model=config["model"]["d_model"],
        nhead=config["model"]["nhead"],
        num_layers=config["model"]["num_layers"],
        dim_feedforward=config["model"]["dim_feedforward"],
        dropout=config["model"]["dropout"],
        max_len=64,
        num_keypoints=86,
    ).to(device)
    
    ckpt_path = OUT_DIR / "best_model.pt"
    ckpt = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    best_epoch = ckpt["epoch"]
    criterion = nn.CrossEntropyLoss(label_smoothing=config["training"]["label_smoothing"])
    
    print(f"\nLoaded Best Checkpoint from Epoch {best_epoch}")
    
    # Validation Evaluation
    val_loss, val_acc, val_preds, val_labels, _ = evaluate_loader(model, val_loader, criterion, device)
    val_macro_f1 = f1_score(val_labels, val_preds, average='macro', zero_division=0)
    val_weighted_f1 = f1_score(val_labels, val_preds, average='weighted', zero_division=0)
    
    # Test Evaluation (Strictly One-Shot)
    test_loss, test_acc, test_preds, test_labels, test_probs = evaluate_loader(model, test_loader, criterion, device)
    test_macro_prec = precision_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_prec = precision_score(test_labels, test_preds, average='weighted', zero_division=0)
    test_macro_rec = recall_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_rec = recall_score(test_labels, test_preds, average='weighted', zero_division=0)
    test_macro_f1 = f1_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_f1 = f1_score(test_labels, test_preds, average='weighted', zero_division=0)
    
    top5_correct = 0
    for prob_vec, true_lbl in zip(test_probs, test_labels):
        top5_indices = np.argsort(prob_vec)[-5:]
        if true_lbl in top5_indices:
            top5_correct += 1
    test_top5_acc = top5_correct / len(test_labels)
    
    print("\n--- EVALUATION RESULTS ---")
    print(f"Val  | Loss: {val_loss:.4f} | Acc: {val_acc*100:.2f}% | Macro F1: {val_macro_f1*100:.2f}%")
    print(f"Test | Loss: {test_loss:.4f} | Acc: {test_acc*100:.2f}% | Top-5 Acc: {test_top5_acc*100:.2f}% | Macro F1: {test_macro_f1*100:.2f}% | Weighted F1: {test_weighted_f1*100:.2f}%")
    
    # Classification Report
    labels_display = [f"{i}_{class_names[i]}" for i in range(32)]
    clf_dict = classification_report(test_labels, test_preds, target_names=labels_display, output_dict=True, zero_division=0)
    df_clf = pd.DataFrame(clf_dict).transpose()
    df_clf.to_csv(OUT_DIR / "classification_report.csv")
    print(f"Saved: {OUT_DIR / 'classification_report.csv'}")
    
    # Best & Worst classes
    class_stats = []
    for i in range(32):
        cname = f"{i}_{class_names[i]}"
        class_stats.append({
            "label": i,
            "gloss": class_names[i],
            "precision": round(clf_dict[cname]["precision"], 4),
            "recall": round(clf_dict[cname]["recall"], 4),
            "f1-score": round(clf_dict[cname]["f1-score"], 4),
            "support": int(clf_dict[cname]["support"])
        })
    df_stats = pd.DataFrame(class_stats)
    top_5 = df_stats.sort_values(by="f1-score", ascending=False).head(5)
    bottom_5 = df_stats.sort_values(by="f1-score", ascending=True).head(5)
    
    print("\nTop 5 Classes:")
    print(top_5.to_string(index=False))
    print("\nBottom 5 Classes:")
    print(bottom_5.to_string(index=False))
    
    # Confusion Matrix
    cm = confusion_matrix(test_labels, test_preds, labels=list(range(32)))
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(32),
        yticks=np.arange(32),
        xticklabels=class_names,
        yticklabels=class_names,
        title=f'M0 Student Baseline Confusion Matrix (WL-BISINDO Test Set, N={len(test_labels)})\nTest Accuracy: {test_acc*100:.2f}%, Macro F1: {test_macro_f1*100:.2f}% (Epoch {best_epoch})',
        ylabel='True Label',
        xlabel='Predicted Label'
    )
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor", fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png", dpi=250)
    plt.close()
    print(f"Saved: {OUT_DIR / 'confusion_matrix.png'}")
    
    # Evaluation Metrics JSON
    df_history = pd.read_csv(OUT_DIR / "training_history.csv")
    total_epochs = len(df_history)
    total_time_sec = float(df_history["duration_sec"].sum())
    
    param_count = sum(p.numel() for p in model.parameters())
    eval_metrics = {
        "model_name": "M0_Student_Baseline",
        "best_epoch": int(best_epoch),
        "total_epochs_trained": int(total_epochs),
        "parameter_count": param_count,
        "total_training_duration_seconds": round(total_time_sec, 2),
        "total_training_duration_minutes": round(total_time_sec / 60, 2),
        "validation_metrics": {
            "val_loss": round(val_loss, 4),
            "val_accuracy": round(val_acc, 4),
            "val_macro_f1": round(val_macro_f1, 4),
            "val_weighted_f1": round(val_weighted_f1, 4)
        },
        "test_metrics": {
            "test_loss": round(test_loss, 4),
            "test_accuracy": round(test_acc, 4),
            "test_top5_accuracy": round(test_top5_acc, 4),
            "test_macro_precision": round(test_macro_prec, 4),
            "test_macro_recall": round(test_macro_rec, 4),
            "test_macro_f1": round(test_macro_f1, 4),
            "test_weighted_f1": round(test_weighted_f1, 4)
        },
        "top_5_classes": top_5.to_dict(orient="records"),
        "bottom_5_classes": bottom_5.to_dict(orient="records"),
        "status": "TRAINING COMPLETED"
    }
    with open(OUT_DIR / "evaluation_metrics.json", "w") as f:
        json.dump(eval_metrics, f, indent=2)
    print(f"Saved: {OUT_DIR / 'evaluation_metrics.json'}")
    
    # Experiment Metadata JSON
    metadata = {
        "experiment_id": "M0_student_baseline",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "TRAINING COMPLETED",
        "environment": {
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__
        },
        "hardware": {
            "device": "CPU",
            "host_gpu": "NVIDIA GeForce RTX 3050 (6GB) - Not used for M0 CPU baseline",
            "cpu_architecture": "AMD64"
        },
        "git": {
            "commit": "b38b4da93b525f68edf4a9cfe6eb9331e13582e2",
            "branch": "feature/dataset-acquisition"
        },
        "dataset": {
            "name": "WL-BISINDO",
            "classes": 32,
            "total_samples": 1600,
            "splits": {"train": 960, "val": 180, "test": 460}
        },
        "artifacts": [
            "best_model.pt",
            "last_model.pt",
            "training_config.yaml",
            "training_history.csv",
            "evaluation_metrics.json",
            "classification_report.csv",
            "confusion_matrix.png",
            "training_loss.png",
            "training_accuracy.png",
            "experiment_metadata.json"
        ]
    }
    with open(OUT_DIR / "experiment_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved: {OUT_DIR / 'experiment_metadata.json'}")
    print("\n>>> ALL M0 FINAL EVALUATION ARTIFACTS SAVED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    main()

