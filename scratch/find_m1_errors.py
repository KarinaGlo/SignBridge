import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
import torch
from torch.utils.data import DataLoader
from signbridge.models.stgcn import PoseModel
from signbridge.data.dataset import SignDataset

manifest_path = Path("data/manifest_wl_bisindo.csv")
test_ds = SignDataset(manifest_path, split="test", protocol="sd")
test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

ckpt = torch.load("outputs/experiments/M1_stgcn_baseline/best_model.pt", map_location="cpu")
model = PoseModel(num_classes=32, hidden_dim=256, dropout=0.1, num_blocks=4)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

preds = []
labels = []
with torch.no_grad():
    for b in test_loader:
        logits = model.forward_logits(b["pose"], mask=b["mask"])
        preds.extend(torch.argmax(logits, dim=-1).tolist())
        labels.extend(b["label"].tolist())

class_names = test_ds.classes
print(f"Total test samples: {len(labels)}, Correct: {sum(p == l for p, l in zip(preds, labels))}")
for i, (p, l) in enumerate(zip(preds, labels)):
    if p != l:
        s_info = test_ds.samples[i]["signer"]
        vid_id = test_ds.samples[i]["video_id"]
        print(f"Sample {i} (vid: {vid_id}): True={class_names[l]} (id={l}) -> Pred={class_names[p]} (id={p}) | Signer={s_info}")
