import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Set MPLCONFIGDIR
os.environ['MPLCONFIGDIR'] = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'matplotlib')

def main():
    print("=== VALIDATING M0 ISOLATED ENVIRONMENT (.venv_m0) ===")
    
    # 1 & 3. Import NumPy & Check Version
    import numpy as np
    print(f"[CHECK 1 & 3] NumPy imported successfully: version = {np.__version__}")
    assert np.__version__ == "1.26.4", f"Expected numpy 1.26.4, got {np.__version__}"
    
    # 2 & 4. Import PyTorch & Check Version
    import torch
    print(f"[CHECK 2 & 4] PyTorch imported successfully: version = {torch.__version__}, CUDA = {torch.cuda.is_available()}")
    assert torch.__version__.startswith("2.2.2"), f"Expected torch 2.2.2, got {torch.__version__}"
    assert not torch.cuda.is_available(), "PyTorch CPU build expected for M0 baseline"
    
    # 5. Uji torch.from_numpy() menggunakan array float32
    arr_np = np.ones((64, 86, 3), dtype=np.float32) * 1.5
    tensor_from_np = torch.from_numpy(arr_np)
    print(f"[CHECK 5] torch.from_numpy() test passed: shape = {tensor_from_np.shape}, dtype = {tensor_from_np.dtype}")
    assert tensor_from_np.shape == (64, 86, 3)
    assert tensor_from_np[0, 0, 0].item() == 1.5
    
    # 6. Uji operasi tensor dasar
    tensor_add = tensor_from_np + 2.0
    tensor_mean = tensor_add.mean()
    tensor_back_np = tensor_add.numpy()
    print(f"[CHECK 6] Basic tensor operations passed: mean = {tensor_mean.item():.2f}, tensor.numpy() shape = {tensor_back_np.shape}")
    assert abs(tensor_mean.item() - 3.5) < 1e-5
    
    # 7. Uji import seluruh modul training M0
    from signbridge.models.student import StudentPoseTransformer
    from signbridge.data.dataset import SignDataset
    from signbridge.constants import NUM_KEYPOINTS, NUM_COORDS, T_MAX
    import yaml
    import sklearn
    from sklearn.metrics import f1_score, confusion_matrix, classification_report
    print(f"[CHECK 7] M0 modules imported: StudentPoseTransformer, SignDataset, scikit-learn {sklearn.__version__}")
    
    model = StudentPoseTransformer(num_classes=32, d_model=160, nhead=4, num_layers=4, dropout=0.1)
    dummy_input = torch.randn(2, 64, 86, 3)
    dummy_out = model(dummy_input)
    print(f"[CHECK 7b] StudentPoseTransformer forward test: output shape = {dummy_out.shape}")
    assert dummy_out.shape == (2, 32)
    
    # 8, 9, 10. Jalankan SignDataset pada train, validation, dan test
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    expected_counts = {"train": 960, "val": 180, "test": 460}
    
    for split in ["train", "val", "test"]:
        ds = SignDataset(
            manifest_path=manifest_path,
            data_root=ROOT,
            split=split,
            protocol="sd",
            allow_mixed_sources=False
        )
        print(f"[CHECK 8 & 9] Split '{split}' loaded: count = {len(ds)} (expected {expected_counts[split]})")
        assert len(ds) == expected_counts[split], f"Count mismatch for {split}"
        
        # Test first sample
        sample = ds[0]
        pose = sample["pose"]
        mask = sample["mask"]
        label = sample["label"]
        signer = sample["signer"]
        video_id = sample["video_id"]
        
        # Check tensor types
        assert isinstance(pose, torch.Tensor), f"Expected torch.Tensor for pose, got {type(pose)}"
        assert isinstance(mask, torch.Tensor), f"Expected torch.Tensor for mask, got {type(mask)}"
        assert isinstance(label, torch.Tensor), f"Expected torch.Tensor for label, got {type(label)}"
        
        # Check shapes & valid_mask
        assert pose.shape == (64, 86, 3), f"Bad pose shape: {pose.shape}"
        assert mask.shape == (64, 86), f"Bad mask shape: {mask.shape}"
        assert mask.dtype == torch.bool, f"Expected bool mask, got {mask.dtype}"
        assert not torch.isnan(pose).any(), f"NaN in {video_id}"
        
        # Check that valid mask has True values
        assert mask.sum() > 0, f"Valid mask is all False in {video_id}"
        
    print("[CHECK 10] valid_mask reading and tensor conversion verified across all splits!")
    print("\n>>> ALL 10 PRE-TRAINING VALIDATION CHECKS PASSED PERFECTLY IN .venv_m0! <<<")

if __name__ == "__main__":
    main()

