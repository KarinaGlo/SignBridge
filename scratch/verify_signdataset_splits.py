import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.data.dataset import SignDataset, _TORCH_AVAILABLE
from signbridge.constants import NUM_KEYPOINTS, NUM_COORDS, T_MAX

def test_signdataset():
    print("=== TESTING SignDataset END-TO-END ON ALL SPLITS ===")
    print(f"PyTorch available: {_TORCH_AVAILABLE}")
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    
    splits = ["train", "val", "test"]
    expected_counts = {"train": 960, "val": 180, "test": 460}
    
    for split in splits:
        print(f"\n--- Loading split: {split} (protocol='sd') ---")
        ds = SignDataset(
            manifest_path=manifest_path,
            data_root=ROOT,
            split=split,
            protocol="sd",
            allow_mixed_sources=False
        )
        print(f"Dataset length: {len(ds)} (expected {expected_counts[split]})")
        assert len(ds) == expected_counts[split], f"Split count mismatch: {len(ds)} != {expected_counts[split]}"
        
        # Check first, middle, and last item
        sample_indices = [0, len(ds)//2, len(ds)-1]
        for idx in sample_indices:
            sample = ds[idx]
            pose = sample["pose"]
            mask = sample["mask"]
            frame_mask = sample["frame_mask"]
            label = sample["label"]
            signer = sample["signer"]
            video_id = sample["video_id"]
            
            assert pose.shape == (T_MAX, NUM_KEYPOINTS, NUM_COORDS), f"Bad pose shape: {pose.shape}"
            assert mask.shape == (T_MAX, NUM_KEYPOINTS), f"Bad mask shape: {mask.shape}"
            assert frame_mask.shape == (T_MAX,), f"Bad frame_mask shape: {frame_mask.shape}"
            assert not np.isnan(pose).any(), f"NaN found in {video_id}"
            assert not np.isinf(pose).any(), f"Inf found in {video_id}"
            assert 0 <= int(label) < 32, f"Bad label index: {label}"
            
        # Verify all 32 labels in split
        labels_present = set()
        for idx in range(len(ds)):
            labels_present.add(int(ds[idx]["label"]))
            
        print(f"Split {split}: {len(labels_present)}/32 classes represented.")
        assert len(labels_present) == 32, f"Expected 32 classes in {split}, got {len(labels_present)}"
        
    print("\nALL SignDataset SPLIT TESTS PASSED SUCCESSFULLY! Zero synthetic fallbacks.")

if __name__ == "__main__":
    test_signdataset()
