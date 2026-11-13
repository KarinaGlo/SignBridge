import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch

def inspect_checkpoint(path):
    print(f"\n==========================================")
    print(f"CHECKPOINT: {path}")
    print(f"File size: {os.path.getsize(path):,} bytes")
    ckpt = torch.load(path, map_location="cpu")
    print(f"Top-level keys: {list(ckpt.keys())}")
    for k in ckpt.keys():
        if k != "model_state_dict" and k != "optimizer_state_dict":
            print(f"  {k}: {ckpt[k]}")
    
    sd = ckpt.get("model_state_dict", {})
    total_params = 0
    print(f"\nTotal tensors in model_state_dict: {len(sd)}")
    for name, tensor in sd.items():
        n_elem = tensor.numel()
        total_params += n_elem
    print(f"Total parameters (sum of numel): {total_params:,}")
    
    # Check if 'classes' or 'labels' or 'label_map' is stored anywhere
    has_labels = "classes" in ckpt or "labels" in ckpt or "label_to_idx" in ckpt or "idx_to_label" in ckpt
    print(f"Explicit label mapping stored in root: {has_labels}")
    if "config" in ckpt:
        cfg = ckpt["config"]
        print("Dataset config:", cfg.get("dataset"))
        print("Model config:", cfg.get("model"))
        print("Training config:", cfg.get("training"))

inspect_checkpoint("outputs/experiments/M0_student_baseline/best_model.pt")
inspect_checkpoint("outputs/experiments/M0_student_baseline/last_model.pt")

