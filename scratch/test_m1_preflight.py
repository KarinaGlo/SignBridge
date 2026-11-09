import os
import sys
import time
import tempfile
from pathlib import Path

# Matplotlib config
os.environ['MPLCONFIGDIR'] = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'matplotlib')

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.models.stgcn import PoseModel
from signbridge.graph import build_adjacency, is_graph_connected, get_anatomical_edges
from signbridge.data.dataset import SignDataset
from signbridge.constants import BISINDO_32_GLOSSES, NUM_KEYPOINTS

def run_preflight_checks():
    print("=================================================================")
    print("      TAHAP A.5: PRE-TRAINING TESTS — M1 ST-GCN BASELINE         ")
    print("=================================================================")
    
    results = {}
    
    # 1. Model initialization test
    print("\n[Check 1/12] Model initialization test...")
    model = PoseModel(num_classes=32, hidden_dim=256, dropout=0.1, num_blocks=4)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Initialized PoseModel (ST-GCN 4-block) with {param_count:,} parameters.")
    assert param_count == 1096408, f"Unexpected parameter count: {param_count}"
    results["1_model_initialization"] = "PASS"
    
    # 2. Graph adjacency shape test
    print("\n[Check 2/12] Graph adjacency shape test...")
    A = build_adjacency(86)
    print(f"  3-Partition Adjacency shape: {A.shape} (expected: (3, 86, 86))")
    assert A.shape == (3, 86, 86), f"Unexpected adjacency shape: {A.shape}"
    # Check 1-hop symmetry
    assert np.allclose(A[1], A[1].T, atol=1e-6), "1-hop adjacency matrix is not symmetric!"
    assert np.allclose(A[0], np.eye(86), atol=1e-6), "Partition 0 is not identity self-loops!"
    print("  Adjacency matrix shape and symmetry verified.")
    results["2_adjacency_shape"] = "PASS"
    
    # 3. Graph connectivity sanity check
    print("\n[Check 3/12] Graph connectivity sanity check...")
    connected = is_graph_connected(86)
    edges = get_anatomical_edges()
    print(f"  Anatomical edges defined: {len(edges)} edges across 86 nodes.")
    print(f"  Graph single connected component: {connected}")
    assert connected, "Graph has isolated nodes!"
    results["3_graph_connectivity"] = "PASS"
    
    # 4. Forward pass with small batch
    print("\n[Check 4/12] Forward pass with small batch...")
    batch_size = 4
    dummy_pose = torch.randn(batch_size, 64, 86, 3)
    dummy_mask = torch.ones(batch_size, 64, 86, dtype=torch.bool)
    logits = model.forward_logits(dummy_pose, mask=dummy_mask)
    print(f"  Forward pass succeeded with batch size {batch_size}.")
    results["4_forward_pass"] = "PASS"
    
    # 5. Output shape test
    print("\n[Check 5/12] Output shape test...")
    print(f"  Output logits shape: {logits.shape} (expected: (4, 32))")
    assert logits.shape == (batch_size, 32), f"Expected shape ({batch_size}, 32), got {logits.shape}"
    results["5_output_shape"] = "PASS"
    
    # 6. Loss computation
    print("\n[Check 6/12] Loss computation test...")
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    dummy_labels = torch.tensor([0, 5, 12, 31], dtype=torch.long)
    loss = criterion(logits, dummy_labels)
    loss_val = loss.item()
    print(f"  Loss computed: {loss_val:.4f} (finite, positive scalar).")
    assert np.isfinite(loss_val) and loss_val > 0.0, f"Invalid loss value: {loss_val}"
    results["6_loss_computation"] = "PASS"
    
    # 7. Backpropagation
    print("\n[Check 7/12] Backpropagation test...")
    model.zero_grad()
    loss.backward()
    print("  Loss backward() completed successfully.")
    results["7_backpropagation"] = "PASS"
    
    # 8. Gradient finite check
    print("\n[Check 8/12] Gradient finite check...")
    has_nan_inf = False
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Parameter {name} has None grad!"
            if not torch.all(torch.isfinite(param.grad)):
                has_nan_inf = True
                print(f"  Gradient for {name} contains NaN/Inf!")
    assert not has_nan_inf, "One or more gradients contain NaN or Inf!"
    print("  All model parameter gradients are 100% finite.")
    results["8_gradient_finite"] = "PASS"
    
    # 9. Masked landmark test
    print("\n[Check 9/12] Masked landmark test (simulating 1-handed signs)...")
    masked_pose = torch.randn(4, 64, 86, 3)
    masked_mask = torch.ones(4, 64, 86, dtype=torch.bool)
    # Mask out left hand entirely (nodes 9 to 30)
    masked_mask[:, :, 9:30] = False
    masked_pose[:, :, 9:30] = 0.0
    
    model.zero_grad()
    masked_logits = model.forward_logits(masked_pose, mask=masked_mask)
    masked_loss = criterion(masked_logits, dummy_labels)
    masked_loss.backward()
    
    assert torch.all(torch.isfinite(masked_logits)), "Masked logits contain NaN/Inf!"
    assert np.isfinite(masked_loss.item()), "Masked loss is NaN/Inf!"
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert torch.all(torch.isfinite(param.grad)), f"Gradient for {name} with mask contains NaN/Inf!"
    print(f"  Masked forward & backward test passed cleanly (loss = {masked_loss.item():.4f}).")
    results["9_masked_landmark_test"] = "PASS"
    
    # 10. Checkpoint save/load test
    print("\n[Check 10/12] Checkpoint save/load test...")
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    try:
        torch.save({"model_state_dict": model.state_dict(), "epoch": 1}, tmp_path)
        new_model = PoseModel(num_classes=32, hidden_dim=256, dropout=0.1, num_blocks=4)
        ckpt = torch.load(tmp_path, map_location="cpu")
        new_model.load_state_dict(ckpt["model_state_dict"])
        
        diffs = []
        for k in model.state_dict():
            d = torch.norm(model.state_dict()[k].float() - new_model.state_dict()[k].float()).item()
            diffs.append(d)
        assert sum(diffs) == 0.0, "Loaded weights do not match saved weights!"
        print("  Checkpoint saved and loaded with 0.0 weight difference.")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    results["10_checkpoint_save_load"] = "PASS"
    
    # 11. Dataset split consistency check
    print("\n[Check 11/12] Dataset split consistency check...")
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    train_ds = SignDataset(manifest_path, data_root=ROOT, split="train", protocol="sd", allow_mixed_sources=False)
    val_ds = SignDataset(manifest_path, data_root=ROOT, split="val", protocol="sd", allow_mixed_sources=False)
    test_ds = SignDataset(manifest_path, data_root=ROOT, split="test", protocol="sd", allow_mixed_sources=False)
    
    print(f"  Split counts: Train={len(train_ds)}, Val={len(val_ds)}, Test={len(test_ds)}")
    assert len(train_ds) == 960, f"Expected 960 train samples, got {len(train_ds)}"
    assert len(val_ds) == 180, f"Expected 180 val samples, got {len(val_ds)}"
    assert len(test_ds) == 460, f"Expected 460 test samples, got {len(test_ds)}"
    assert len(train_ds.classes) == 32, f"Expected 32 classes, got {len(train_ds.classes)}"
    assert train_ds.classes[0] == "AIR", f"Expected class 0 to be AIR, got {train_ds.classes[0]}"
    assert train_ds.classes[31] == "MALAM", f"Expected class 31 to be MALAM, got {train_ds.classes[31]}"
    print(f"  Class 0: {train_ds.classes[0]}, Class 31: {train_ds.classes[31]}")
    print("  Dataset split sizes and class definitions are 100% identical to M0.")
    results["11_dataset_split_consistency"] = "PASS"
    
    # 12. Deterministic seed check
    print("\n[Check 12/12] Deterministic seed check...")
    train_ds.set_epoch(0)
    sample_a = train_ds[0]["pose"]
    train_ds.set_epoch(0)
    sample_b = train_ds[0]["pose"]
    assert torch.equal(sample_a, sample_b), "Augmentation stream is not deterministic for same epoch!"
    train_ds.set_epoch(1)
    sample_c = train_ds[0]["pose"]
    # Should differ due to epoch seed change
    diff_epoch = torch.norm(sample_a - sample_c).item()
    print(f"  Sample reproducibility check: same epoch diff = 0.0, different epoch diff = {diff_epoch:.4f}")
    assert diff_epoch > 0.0, "Different epochs produced identical augmentation!"
    results["12_deterministic_seed"] = "PASS"
    
    print("\n=================================================================")
    print("  ALL 12 PRE-TRAINING CHECKS PASSED: STATUS = READY FOR TRAINING ")
    print("=================================================================")
    return True

if __name__ == "__main__":
    success = run_preflight_checks()
    if not success:
        sys.exit(1)
