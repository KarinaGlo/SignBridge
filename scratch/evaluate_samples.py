import sys
import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.models.student import StudentPoseTransformer
from signbridge.features import preprocess_keypoints

def main():
    ckpt_path = ROOT / "outputs" / "experiments" / "M0_student_baseline" / "best_model.pt"
    labels_path = ROOT / "web" / "model" / "labels.json"
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    labels = json.loads(labels_path.read_text("utf-8"))
    df = pd.read_csv(manifest_path)
    
    model = StudentPoseTransformer(
        num_classes=32,
        d_model=160,
        nhead=4,
        num_layers=4,
        dim_feedforward=640,
        dropout=0.0,
        max_len=64,
        num_keypoints=86
    )
    model.load_state_dict(ckpt["model_state_dict"], strict=True)
    model.eval()
    
    # Pick 8 diverse test samples across different classes from 'test' split
    test_df = df[df["split_sd"] == "test"].groupby("label").first().reset_index()
    sample_labels_to_eval = [0, 1, 6, 9, 10, 12, 25, 31] # AIR, BELAJAR, MAAF, SAYA, TERIMA_KASIH, APA, TEMAN, MALAM
    
    print(f"{'True Gloss':<15} | {'Label':<5} | {'Pred Gloss':<15} | {'Pred Idx':<8} | {'Confidence':<12} | {'Logits Range':<18} | {'Match'}")
    print("-" * 92)
    
    for lbl in sample_labels_to_eval:
        row = test_df[test_df["label"] == lbl].iloc[0]
        kp_rel = row["kp_path"]
        true_gloss = row["gloss"]
        sample_path = ROOT / kp_rel
        
        assert sample_path.exists(), f"Sample path not found: {sample_path}"
        data = np.load(str(sample_path))
        raw_kp = data["keypoints"] # [F, 86, 3]
        
        # Preprocessing Contract 3
        kp64, mask = preprocess_keypoints(raw_kp, target_len=64, trim=True)
        inp = torch.from_numpy(kp64).unsqueeze(0).float()
        
        with torch.no_grad():
            logits = model(inp).squeeze(0) # [32]
            probs = torch.softmax(logits, dim=-1)
            
        pred_idx = int(torch.argmax(logits).item())
        confidence = float(probs[pred_idx].item())
        pred_gloss = labels[pred_idx]
        
        logits_min = float(logits.min().item())
        logits_max = float(logits.max().item())
        match = (pred_idx == lbl)
        
        print(f"{true_gloss:<15} | {lbl:<5} | {pred_gloss:<15} | {pred_idx:<8} | {confidence*100:>8.2f}%   | [{logits_min:5.2f}, {logits_max:5.2f}] | {match}")
        
        # Top 3 display
        top3_indices = torch.topk(probs, 3).indices.tolist()
        top3_probs = torch.topk(probs, 3).values.tolist()
        top3_str = ", ".join([f"{labels[i]}: {p*100:.1f}%" for i, p in zip(top3_indices, top3_probs)])
        print(f"   -> Top-3 Softmax: {top3_str}")
        print()

if __name__ == "__main__":
    main()
