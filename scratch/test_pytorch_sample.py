import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch
import numpy as np
import json
from signbridge.models.student import StudentPoseTransformer

# 1. Load checkpoint
ckpt_path = "outputs/experiments/M0_student_baseline/best_model.pt"
ckpt = torch.load(ckpt_path, map_location="cpu")

# 2. Build model
model = StudentPoseTransformer(
    num_classes=32,
    d_model=160,
    nhead=4,
    num_layers=4,
    dim_feedforward=640,
    dropout=0.0
)
model.load_state_dict(ckpt["model_state_dict"], strict=True)
model.eval()

# 3. Load sample
sample_path = "data/keypoints/wl_bisindo/wl_bisindo_signer0_label0_sample1.npz"
npz = np.load(sample_path)
stored_kp = npz["keypoints"] # [64, 86, 3]
true_label = int(npz["label"])
true_gloss = str(npz["gloss"])

# 4. Forward
input_tensor = torch.from_numpy(stored_kp).unsqueeze(0) # [1, 64, 86, 3]
with torch.no_grad():
    logits = model(input_tensor)
    probs = torch.softmax(logits, dim=-1)[0]

top3_vals, top3_indices = torch.topk(probs, 3)

with open("web/model/labels.json", "r") as f:
    labels = json.load(f)

print(f"Sample: {sample_path}")
print(f"True Label: {true_label} ({true_gloss})")
print(f"Predicted Class Index: {top3_indices[0].item()}")
print(f"Predicted Gloss: {labels[top3_indices[0].item()]}")
print(f"Top-1 Confidence: {top3_vals[0].item():.4f}")
print("Top-3 Predictions:")
for i in range(3):
    idx = top3_indices[i].item()
    print(f"  {i+1}. {labels[idx]} (index {idx}): {top3_vals[i].item():.4f}")
