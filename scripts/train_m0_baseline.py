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

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.models.student import StudentPoseTransformer
from signbridge.data.dataset import SignDataset
from signbridge.constants import BISINDO_32_GLOSSES, NUM_KEYPOINTS, NUM_COORDS, T_MAX

OUT_DIR = ROOT / "outputs" / "experiments" / "M0_student_baseline"
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
            pose = batch["pose"].to(device)  # [B, 64, 86, 3]
            mask = batch["mask"].to(device)  # [B, 64, 86]
            labels = batch["label"].to(device)  # [B]
            
            # Mask invalid landmarks to (0, 0, 0)
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
    start_time_all = time.time()
    set_seed(42)
    device = torch.device("cpu")
    
    print("=================================================================")
    print("  SIGNBRIDGE TAHAP A.4: M0 STUDENT BASELINE TRAINING (WL-BISINDO)")
    print("=================================================================")
    print(f"Device: {device}")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"NumPy Version: {np.__version__}")
    print(f"Random Seed: 42")
    
    # Configuration dictionary
    config = {
        "experiment_id": "M0_student_baseline",
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
            "type": "StudentPoseTransformer",
            "d_model": 160,
            "nhead": 4,
            "num_layers": 4,
            "dim_feedforward": 640,
            "dropout": 0.10,
            "activation": "gelu"
        },
        "training": {
            "max_epochs": 100,
            "patience": 10,
            "batch_size": 32,
            "optimizer": "AdamW",
            "learning_rate": 0.001,
            "weight_decay": 0.01,
            "label_smoothing": 0.1,
            "scheduler": "ReduceLROnPlateau(factor=0.5, patience=4, min_lr=1e-5)"
        },
        "hardware": {
            "device": "CPU",
            "cpu_architecture": "AMD64",
            "host_gpu": "NVIDIA GeForce RTX 3050 (6GB) - Not used for M0 CPU baseline",
            "python_version": sys.version
        }
    }
    
    with open(OUT_DIR / "training_config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)
        
    # Load Datasets
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    train_dataset = SignDataset(manifest_path, data_root=ROOT, split="train", protocol="sd", allow_mixed_sources=False)
    val_dataset = SignDataset(manifest_path, data_root=ROOT, split="val", protocol="sd", allow_mixed_sources=False)
    test_dataset = SignDataset(manifest_path, data_root=ROOT, split="test", protocol="sd", allow_mixed_sources=False)
    
    print(f"Loaded splits: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")
    assert len(train_dataset) == 960
    assert len(val_dataset) == 180
    assert len(test_dataset) == 460
    
    train_loader = DataLoader(train_dataset, batch_size=config["training"]["batch_size"], shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=config["training"]["batch_size"], shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=config["training"]["batch_size"], shuffle=False, num_workers=0)
    
    # Build Model
    model = StudentPoseTransformer(
        num_classes=config["dataset"]["num_classes"],
        d_model=config["model"]["d_model"],
        nhead=config["model"]["nhead"],
        num_layers=config["model"]["num_layers"],
        dim_feedforward=config["model"]["dim_feedforward"],
        dropout=config["model"]["dropout"],
        max_len=config["dataset"]["seq_len"],
        num_keypoints=config["dataset"]["num_keypoints"],
    ).to(device)
    
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model instantiated: StudentPoseTransformer | Trainable Parameters: {param_count:,}")
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
    
    print("\n--- Starting Training Loop ---")
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
            
            # Mask invalid landmarks
            pose = pose * mask.unsqueeze(-1).float()
            
            optimizer.zero_grad()
            logits = model(pose)
            loss = criterion(logits, labels)
            
            if torch.isnan(loss):
                raise ValueError(f"NaN loss encountered at epoch {epoch}!")
                
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            train_loss += loss.item() * len(labels)
            preds = torch.argmax(logits, dim=-1)
            train_correct += (preds == labels).sum().item()
            train_total += len(labels)
            
        epoch_train_loss = train_loss / train_total
        epoch_train_acc = train_correct / train_total
        
        # Validation
        epoch_val_loss, epoch_val_acc, _, _, _ = evaluate_loader(model, val_loader, criterion, device)
        
        # Step LR Scheduler
        current_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(epoch_val_loss)
        
        epoch_duration = time.time() - epoch_start
        
        record = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_acc": round(epoch_train_acc, 4),
            "val_loss": round(epoch_val_loss, 4),
            "val_acc": round(epoch_val_acc, 4),
            "lr": current_lr,
            "duration_sec": round(epoch_duration, 2)
        }
        history.append(record)
        
        is_best = False
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_val_acc = epoch_val_acc
            best_epoch = epoch
            patience_counter = 0
            is_best = True
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": epoch_val_loss,
                "val_acc": epoch_val_acc,
                "config": config
            }, OUT_DIR / "best_model.pt")
        else:
            patience_counter += 1
            
        print(f"Epoch [{epoch:03d}/{config['training']['max_epochs']}] | "
              f"Train Loss: {epoch_train_loss:.4f} Acc: {epoch_train_acc*100:.2f}% | "
              f"Val Loss: {epoch_val_loss:.4f} Acc: {epoch_val_acc*100:.2f}% | "
              f"LR: {current_lr:.6f} | Time: {epoch_duration:.2f}s "
              f"{'(*BEST*)' if is_best else f'(patience {patience_counter}/{patience})'}")
              
        if patience_counter >= patience:
            print(f"\n[Early Stopping Triggered] No improvement in validation loss for {patience} epochs.")
            break
            
    # Save last model
    torch.save({
        "epoch": len(history),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "val_loss": history[-1]["val_loss"],
        "val_acc": history[-1]["val_acc"],
        "config": config
    }, OUT_DIR / "last_model.pt")
    
    # Save training history
    df_history = pd.DataFrame(history)
    df_history.to_csv(OUT_DIR / "training_history.csv", index=False)
    print(f"Saved: {OUT_DIR / 'training_history.csv'}")
    
    # Plot curves
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df_history['epoch'], df_history['train_loss'], label='Train Loss', color='#2563EB', linewidth=2)
    ax1.plot(df_history['epoch'], df_history['val_loss'], label='Val Loss', color='#DC2626', linewidth=2)
    ax1.axvline(best_epoch, color='gray', linestyle='--', label=f'Best Epoch ({best_epoch})')
    ax1.set_xlabel('Epoch', fontweight='bold')
    ax1.set_ylabel('Cross Entropy Loss', fontweight='bold')
    ax1.set_title('M0 Student Baseline: Training & Validation Loss', fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "training_loss.png", dpi=200)
    plt.close()
    
    fig, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(df_history['epoch'], df_history['train_acc'] * 100, label='Train Acc', color='#2563EB', linewidth=2)
    ax2.plot(df_history['epoch'], df_history['val_acc'] * 100, label='Val Acc', color='#10B981', linewidth=2)
    ax2.axvline(best_epoch, color='gray', linestyle='--', label=f'Best Epoch ({best_epoch})')
    ax2.set_xlabel('Epoch', fontweight='bold')
    ax2.set_ylabel('Accuracy (%)', fontweight='bold')
    ax2.set_title('M0 Student Baseline: Training & Validation Accuracy', fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "training_accuracy.png", dpi=200)
    plt.close()
    print("Saved training curves.")
    
    # Load Best Model for Final Evaluation
    print("\n=================================================================")
    print(f"  EVALUATING BEST MODEL (Epoch {best_epoch}) ON VALIDATION & TEST")
    print("=================================================================")
    best_checkpoint = torch.load(OUT_DIR / "best_model.pt", map_location=device)
    model.load_state_dict(best_checkpoint["model_state_dict"])
    
    val_loss, val_acc, val_preds, val_labels, _ = evaluate_loader(model, val_loader, criterion, device)
    val_macro_f1 = f1_score(val_labels, val_preds, average='macro', zero_division=0)
    val_weighted_f1 = f1_score(val_labels, val_preds, average='weighted', zero_division=0)
    
    # Final One-Shot Evaluation on Test Set
    test_loss, test_acc, test_preds, test_labels, test_probs = evaluate_loader(model, test_loader, criterion, device)
    test_macro_prec = precision_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_prec = precision_score(test_labels, test_preds, average='weighted', zero_division=0)
    test_macro_rec = recall_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_rec = recall_score(test_labels, test_preds, average='weighted', zero_division=0)
    test_macro_f1 = f1_score(test_labels, test_preds, average='macro', zero_division=0)
    test_weighted_f1 = f1_score(test_labels, test_preds, average='weighted', zero_division=0)
    
    # Top-5 accuracy on test set
    top5_correct = 0
    for prob_vec, true_lbl in zip(test_probs, test_labels):
        top5_indices = np.argsort(prob_vec)[-5:]
        if true_lbl in top5_indices:
            top5_correct += 1
    test_top5_acc = top5_correct / len(test_labels)
    
    print(f"\n[Validation Set Performance (Best Epoch {best_epoch})]:")
    print(f"  Loss: {val_loss:.4f} | Accuracy: {val_acc*100:.2f}% | Macro F1: {val_macro_f1*100:.2f}%")
    
    print(f"\n[Final Test Set Performance (Strictly Evaluated Once)]:")
    print(f"  Loss:           {test_loss:.4f}")
    print(f"  Accuracy:       {test_acc*100:.2f}%")
    print(f"  Top-5 Accuracy: {test_top5_acc*100:.2f}%")
    print(f"  Macro Precision:{test_macro_prec*100:.2f}%")
    print(f"  Macro Recall:   {test_macro_rec*100:.2f}%")
    print(f"  Macro F1-Score: {test_macro_f1*100:.2f}%")
    print(f"  Weighted F1:    {test_weighted_f1*100:.2f}%")
    
    # Classification Report
    class_names = [f"{i}_{BISINDO_32_GLOSSES[i]}" for i in range(32)]
    clf_dict = classification_report(test_labels, test_preds, target_names=class_names, output_dict=True, zero_division=0)
    df_clf = pd.DataFrame(clf_dict).transpose()
    df_clf.to_csv(OUT_DIR / "classification_report.csv")
    print(f"Saved: {OUT_DIR / 'classification_report.csv'}")
    
    # Identify Best & Worst Classes
    class_f1s = []
    for i in range(32):
        cname = f"{i}_{BISINDO_32_GLOSSES[i]}"
        class_f1s.append({
            "label": i,
            "gloss": BISINDO_32_GLOSSES[i],
            "precision": clf_dict[cname]["precision"],
            "recall": clf_dict[cname]["recall"],
            "f1-score": clf_dict[cname]["f1-score"],
            "support": clf_dict[cname]["support"]
        })
    df_class_f1s = pd.DataFrame(class_f1s)
    top_classes = df_class_f1s.sort_values(by="f1-score", ascending=False).head(5)
    bottom_classes = df_class_f1s.sort_values(by="f1-score", ascending=True).head(5)
    
    print("\nTop 5 Classes by F1-Score:")
    print(top_classes[["label", "gloss", "f1-score", "support"]].to_string(index=False))
    
    print("\nBottom 5 Classes by F1-Score:")
    print(bottom_classes[["label", "gloss", "f1-score", "support"]].to_string(index=False))
    
    # Confusion Matrix Plot
    cm = confusion_matrix(test_labels, test_preds, labels=list(range(32)))
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(32),
        yticks=np.arange(32),
        xticklabels=BISINDO_32_GLOSSES,
        yticklabels=BISINDO_32_GLOSSES,
        title=f'M0 Student Baseline Confusion Matrix (Test Set, N={len(test_labels)})\nTest Accuracy: {test_acc*100:.2f}%, Macro F1: {test_macro_f1*100:.2f}%',
        ylabel='True Label',
        xlabel='Predicted Label'
    )
    plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor", fontsize=8)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png", dpi=250)
    plt.close()
    print("Saved confusion matrix.")
    
    # Save Evaluation Metrics JSON
    total_training_duration = time.time() - start_time_all
    metrics = {
        "model_name": "M0_Student_Baseline",
        "best_epoch": best_epoch,
        "total_epochs_trained": len(history),
        "parameter_count": param_count,
        "training_time_seconds": round(total_training_duration, 2),
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
        "top_5_classes": top_classes.to_dict(orient="records"),
        "bottom_5_classes": bottom_classes.to_dict(orient="records"),
        "status": "TRAINING COMPLETED"
    }
    
    with open(OUT_DIR / "evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved: {OUT_DIR / 'evaluation_metrics.json'}")
    
    # Save Experiment Metadata
    metadata = {
        "experiment_id": "M0_student_baseline",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": config["hardware"],
        "dependencies": {
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__
        },
        "git_commit": "b38b4da93b525f68edf4a9cfe6eb9331e13582e2",
        "git_branch": "feature/dataset-acquisition",
        "dataset_split_counts": {"train": 960, "val": 180, "test": 460},
        "total_duration_minutes": round(total_training_duration / 60, 2),
        "output_directory": str(OUT_DIR)
    }
    with open(OUT_DIR / "experiment_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved: {OUT_DIR / 'experiment_metadata.json'}")
    
    print("\n=================================================================")
    print("  M0 STUDENT BASELINE TRAINING COMPLETED SUCCESSFULLY!")
    print(f"  Best Epoch: {best_epoch} | Test Acc: {test_acc*100:.2f}% | Test Macro F1: {test_macro_f1*100:.2f}%")
    print(f"  Total Duration: {total_training_duration/60:.2f} minutes")
    print("=================================================================")

if __name__ == "__main__":
    main()
