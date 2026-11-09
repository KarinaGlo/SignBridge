import os
import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

# Set MPLCONFIGDIR to avoid permission error
os.environ['MPLCONFIGDIR'] = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'matplotlib')

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "manifest_wl_bisindo.csv"
SIDECAR_PATH = ROOT / "data" / "manifest_wl_bisindo_source_metadata.csv"
KP_DIR = ROOT / "data" / "keypoints" / "wl_bisindo"

# 86-node landmark indices
POSE_SLICE = slice(0, 9)
LHAND_SLICE = slice(9, 30)
RHAND_SLICE = slice(30, 51)
FACE_SLICE = slice(51, 86)
L_SHOULDER_IDX = 1
R_SHOULDER_IDX = 2
L_WRIST_IDX = 5
R_WRIST_IDX = 6

def compute_file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    print("=== STARTING WL-BISINDO COMPREHENSIVE DATASET QUALITY AUDIT ===")
    
    # 1. Load manifests
    df_manifest = pd.read_csv(MANIFEST_PATH)
    df_sidecar = pd.read_csv(SIDECAR_PATH)
    print(f"Loaded manifest: {len(df_manifest)} rows")
    print(f"Loaded sidecar: {len(df_sidecar)} rows")
    
    assert len(df_manifest) == 1600, f"Expected 1600 rows, got {len(df_manifest)}"
    assert len(df_sidecar) == 1600, f"Expected 1600 rows, got {len(df_sidecar)}"
    
    # Merge sidecar video sha256
    merged_df = pd.merge(df_manifest, df_sidecar[["video_id", "sha256", "official_split", "dup_status", "experiment_status"]], on="video_id", how="left")
    
    sample_records = []
    npz_hashes = {}
    feature_hashes = {}
    
    print("Processing 1,600 .npz keypoint files...")
    for idx, row in merged_df.iterrows():
        video_id = row["video_id"]
        signer = row["signer"]
        label = int(row["label"])
        gloss = row["gloss"]
        split = row["split_sd"]
        video_sha256 = row["sha256"]
        
        kp_rel_path = row["kp_path"]
        kp_abs_path = ROOT / kp_rel_path
        
        if not kp_abs_path.exists():
            raise FileNotFoundError(f"Missing keypoint file: {kp_abs_path}")
            
        npz_sha256 = compute_file_sha256(kp_abs_path)
        npz_hashes[video_id] = npz_sha256
        
        data = np.load(kp_abs_path, allow_pickle=True)
        kp = data["keypoints"]  # [64, 86, 3] float32
        valid_mask = data["valid_mask"]  # [64, 86] bool
        raw_kp = data["raw_keypoints"]  # [F_raw, 86, 3]
        raw_frames = raw_kp.shape[0]
        
        # Hash of rounded keypoints for semantic duplicate detection
        kp_rounded = np.round(kp, decimals=3)
        feat_bytes = kp_rounded.tobytes()
        feat_hash = hashlib.sha256(feat_bytes).hexdigest()
        feature_hashes[video_id] = feat_hash
        
        # Structural check
        shape_valid = (kp.shape == (64, 86, 3)) and (valid_mask.shape == (64, 86))
        nan_count = int(np.isnan(kp).sum())
        inf_count = int(np.isinf(kp).sum())
        
        # Valid counts
        total_valid_kps = int(np.sum(valid_mask))
        overall_valid_rate = float(total_valid_kps / (64 * 86))
        
        pose_valid = int(np.sum(valid_mask[:, POSE_SLICE]))
        pose_valid_rate = float(pose_valid / (64 * 9))
        
        lhand_valid = int(np.sum(valid_mask[:, LHAND_SLICE]))
        lhand_valid_rate = float(lhand_valid / (64 * 21))
        
        rhand_valid = int(np.sum(valid_mask[:, RHAND_SLICE]))
        rhand_valid_rate = float(rhand_valid / (64 * 21))
        
        face_valid = int(np.sum(valid_mask[:, FACE_SLICE]))
        face_valid_rate = float(face_valid / (64 * 35))
        
        # Frame-level presence
        f_pose = np.any(valid_mask[:, POSE_SLICE], axis=1)
        f_lhand = np.any(valid_mask[:, LHAND_SLICE], axis=1)
        f_rhand = np.any(valid_mask[:, RHAND_SLICE], axis=1)
        f_face = np.any(valid_mask[:, FACE_SLICE], axis=1)
        f_either_hand = f_lhand | f_rhand
        f_both_hands = f_lhand & f_rhand
        f_empty = ~np.any(valid_mask, axis=1)
        
        frames_pose_present = int(np.sum(f_pose))
        frames_lhand_present = int(np.sum(f_lhand))
        frames_rhand_present = int(np.sum(f_rhand))
        frames_face_present = int(np.sum(f_face))
        frames_either_hand_present = int(np.sum(f_either_hand))
        frames_both_hands_present = int(np.sum(f_both_hands))
        empty_frames_count = int(np.sum(f_empty))
        
        # Coordinate bounds and stats on valid keypoints
        valid_coords = kp[valid_mask]
        if len(valid_coords) > 0:
            x_min, x_max, x_mean, x_std = float(valid_coords[:, 0].min()), float(valid_coords[:, 0].max()), float(valid_coords[:, 0].mean()), float(valid_coords[:, 0].std())
            y_min, y_max, y_mean, y_std = float(valid_coords[:, 1].min()), float(valid_coords[:, 1].max()), float(valid_coords[:, 1].mean()), float(valid_coords[:, 1].std())
            z_min, z_max, z_mean, z_std = float(valid_coords[:, 2].min()), float(valid_coords[:, 2].max()), float(valid_coords[:, 2].mean()), float(valid_coords[:, 2].std())
        else:
            x_min = x_max = x_mean = x_std = 0.0
            y_min = y_max = y_mean = y_std = 0.0
            z_min = z_max = z_mean = z_std = 0.0
            
        # Shoulder normalization sanity
        both_sh_valid = valid_mask[:, L_SHOULDER_IDX] & valid_mask[:, R_SHOULDER_IDX]
        if np.any(both_sh_valid):
            sh_l = kp[both_sh_valid, L_SHOULDER_IDX, :]
            sh_r = kp[both_sh_valid, R_SHOULDER_IDX, :]
            midpoints = 0.5 * (sh_l + sh_r)
            midpoint_dev = float(np.max(np.linalg.norm(midpoints, axis=-1)))
            sh_dists = np.linalg.norm(sh_l - sh_r, axis=-1)
            sh_dist_dev = float(np.max(np.abs(sh_dists - 1.0)))
        else:
            midpoint_dev = -1.0
            sh_dist_dev = -1.0
            
        # Temporal jumps (between consecutive frames for landmarks valid in both)
        interframe_jumps = []
        wrist_jumps = []
        for t in range(63):
            common_valid = valid_mask[t] & valid_mask[t + 1]
            if np.any(common_valid):
                dists = np.linalg.norm(kp[t + 1, common_valid] - kp[t, common_valid], axis=-1)
                interframe_jumps.extend(dists.tolist())
            # Wrist jumps (pose wrists)
            if valid_mask[t, L_WRIST_IDX] and valid_mask[t + 1, L_WRIST_IDX]:
                wrist_jumps.append(float(np.linalg.norm(kp[t + 1, L_WRIST_IDX] - kp[t, L_WRIST_IDX])))
            if valid_mask[t, R_WRIST_IDX] and valid_mask[t + 1, R_WRIST_IDX]:
                wrist_jumps.append(float(np.linalg.norm(kp[t + 1, R_WRIST_IDX] - kp[t, R_WRIST_IDX])))
                
        max_interframe_jump = float(np.max(interframe_jumps)) if interframe_jumps else 0.0
        mean_interframe_jump = float(np.mean(interframe_jumps)) if interframe_jumps else 0.0
        max_wrist_jump = float(np.max(wrist_jumps)) if wrist_jumps else 0.0
        
        # Static freeze detection (temporal std across frames for consistently valid points)
        always_valid = np.all(valid_mask, axis=0)
        if np.any(always_valid):
            temporal_stds = np.std(kp[:, always_valid, :], axis=0)
            is_static_frozen = bool(np.all(temporal_stds < 1e-4))
        else:
            is_static_frozen = False
            
        # Category Assignment
        # INVALID: structural defect, NaN/Inf, or no hand present at all
        if (not shape_valid) or (nan_count > 0) or (inf_count > 0) or (frames_either_hand_present == 0) or (overall_valid_rate < 0.20):
            quality_category = "INVALID"
        # HIGH: >= 70% overall valid, hand present >= 40 frames, low temporal jump, no freeze, empty frames <= 5
        elif (overall_valid_rate >= 0.70) and (frames_either_hand_present >= 40) and (max_interframe_jump < 4.0) and (not is_static_frozen) and (empty_frames_count <= 5):
            quality_category = "HIGH"
        # MEDIUM: >= 45% overall valid, hand present >= 20 frames
        elif (overall_valid_rate >= 0.45) and (frames_either_hand_present >= 20):
            quality_category = "MEDIUM"
        else:
            quality_category = "LOW"
            
        sample_records.append({
            "video_id": video_id,
            "signer": signer,
            "label": label,
            "gloss": gloss,
            "split_sd": split,
            "raw_frames": raw_frames,
            "npz_sha256": npz_sha256,
            "video_sha256": video_sha256,
            "feature_hash": feat_hash,
            "shape_valid": shape_valid,
            "nan_count": nan_count,
            "inf_count": inf_count,
            "total_valid_kps": total_valid_kps,
            "overall_valid_rate": round(overall_valid_rate, 4),
            "pose_valid_rate": round(pose_valid_rate, 4),
            "lhand_valid_rate": round(lhand_valid_rate, 4),
            "rhand_valid_rate": round(rhand_valid_rate, 4),
            "face_valid_rate": round(face_valid_rate, 4),
            "frames_pose_present": frames_pose_present,
            "frames_lhand_present": frames_lhand_present,
            "frames_rhand_present": frames_rhand_present,
            "frames_face_present": frames_face_present,
            "frames_either_hand_present": frames_either_hand_present,
            "frames_both_hands_present": frames_both_hands_present,
            "empty_frames_count": empty_frames_count,
            "x_min": round(x_min, 4),
            "x_max": round(x_max, 4),
            "x_mean": round(x_mean, 4),
            "x_std": round(x_std, 4),
            "y_min": round(y_min, 4),
            "y_max": round(y_max, 4),
            "y_mean": round(y_mean, 4),
            "y_std": round(y_std, 4),
            "z_min": round(z_min, 4),
            "z_max": round(z_max, 4),
            "z_mean": round(z_mean, 4),
            "z_std": round(z_std, 4),
            "shoulder_midpoint_dev": round(midpoint_dev, 6),
            "shoulder_dist_dev": round(sh_dist_dev, 6),
            "max_interframe_jump": round(max_interframe_jump, 4),
            "mean_interframe_jump": round(mean_interframe_jump, 4),
            "max_wrist_jump": round(max_wrist_jump, 4),
            "is_static_frozen": is_static_frozen,
            "quality_category": quality_category,
        })
        
    df_samples = pd.DataFrame(sample_records)
    print("Done processing all samples.")
    
    # 2. Save quality_audit_per_sample.csv
    per_sample_path = KP_DIR / "quality_audit_per_sample.csv"
    df_samples.to_csv(per_sample_path, index=False)
    print(f"Saved: {per_sample_path}")
    
    # 3. Save quality_categories.csv
    categories_path = KP_DIR / "quality_categories.csv"
    df_categories = df_samples[["video_id", "signer", "label", "gloss", "split_sd", "quality_category", "overall_valid_rate", "lhand_valid_rate", "rhand_valid_rate", "frames_either_hand_present"]]
    df_categories.to_csv(categories_path, index=False)
    print(f"Saved: {categories_path}")
    
    # 4. Duplicate Audit
    print("Performing duplicate and leakage audit...")
    video_sha256_counts = df_samples["video_sha256"].value_counts()
    npz_sha256_counts = df_samples["npz_sha256"].value_counts()
    feature_hash_counts = df_samples["feature_hash"].value_counts()
    
    dup_records = []
    # Check for duplicate videos
    dup_videos = video_sha256_counts[video_sha256_counts > 1].index.tolist()
    # Check for duplicate npz
    dup_npz = npz_sha256_counts[npz_sha256_counts > 1].index.tolist()
    # Check for duplicate feature hashes
    dup_feats = feature_hash_counts[feature_hash_counts > 1].index.tolist()
    
    print(f"Duplicate raw video SHA-256 count (>1): {len(dup_videos)}")
    print(f"Duplicate NPZ SHA-256 count (>1): {len(dup_npz)}")
    print(f"Duplicate Feature hash count (>1): {len(dup_feats)}")
    
    for vid, group in df_samples.groupby("video_sha256"):
        is_dup = len(group) > 1
        cross_split = len(group["split_sd"].unique()) > 1 if is_dup else False
        dup_records.append({
            "hash_type": "video_sha256",
            "hash_value": vid,
            "occurrence_count": len(group),
            "video_ids": ";".join(group["video_id"].tolist()),
            "signers": ";".join(group["signer"].unique().tolist()),
            "labels": ";".join(group["label"].astype(str).unique().tolist()),
            "splits": ";".join(group["split_sd"].unique().tolist()),
            "is_duplicate": is_dup,
            "is_cross_split_leakage": cross_split
        })
    
    for f_hash, group in df_samples.groupby("feature_hash"):
        if len(group) > 1:
            cross_split = len(group["split_sd"].unique()) > 1
            dup_records.append({
                "hash_type": "feature_hash",
                "hash_value": f_hash,
                "occurrence_count": len(group),
                "video_ids": ";".join(group["video_id"].tolist()),
                "signers": ";".join(group["signer"].unique().tolist()),
                "labels": ";".join(group["label"].astype(str).unique().tolist()),
                "splits": ";".join(group["split_sd"].unique().tolist()),
                "is_duplicate": True,
                "is_cross_split_leakage": cross_split
            })
            
    df_dups = pd.DataFrame(dup_records)
    dup_csv_path = KP_DIR / "duplicate_audit.csv"
    df_dups.to_csv(dup_csv_path, index=False)
    print(f"Saved: {dup_csv_path}")
    
    # 5. Per-Class Analysis
    print("Computing per-class metrics...")
    class_records = []
    for (label, gloss), grp in df_samples.groupby(["label", "gloss"]):
        n_samples = len(grp)
        mean_overall = float(grp["overall_valid_rate"].mean())
        mean_pose = float(grp["pose_valid_rate"].mean())
        mean_lhand = float(grp["lhand_valid_rate"].mean())
        mean_rhand = float(grp["rhand_valid_rate"].mean())
        mean_face = float(grp["face_valid_rate"].mean())
        mean_f_lhand = float(grp["frames_lhand_present"].mean())
        mean_f_rhand = float(grp["frames_rhand_present"].mean())
        mean_f_both = float(grp["frames_both_hands_present"].mean())
        mean_f_either = float(grp["frames_either_hand_present"].mean())
        
        # Gesture characterization
        if mean_rhand >= 0.60 and mean_lhand < 0.25:
            gesture_type = "ONE_HANDED_RIGHT"
        elif mean_rhand < 0.25 and mean_lhand >= 0.60:
            gesture_type = "ONE_HANDED_LEFT"
        elif mean_rhand >= 0.40 and mean_lhand >= 0.40:
            gesture_type = "TWO_HANDED_SYMMETRIC"
        elif mean_rhand >= 0.60 and mean_lhand >= 0.25:
            gesture_type = "TWO_HANDED_ASYMMETRIC"
        else:
            gesture_type = "LOW_DETECTION"
            
        high_cnt = int((grp["quality_category"] == "HIGH").sum())
        med_cnt = int((grp["quality_category"] == "MEDIUM").sum())
        low_cnt = int((grp["quality_category"] == "LOW").sum())
        inv_cnt = int((grp["quality_category"] == "INVALID").sum())
        
        class_records.append({
            "label": label,
            "gloss": gloss,
            "sample_count": n_samples,
            "gesture_type": gesture_type,
            "mean_overall_valid_rate": round(mean_overall, 4),
            "mean_pose_valid_rate": round(mean_pose, 4),
            "mean_lhand_valid_rate": round(mean_lhand, 4),
            "mean_rhand_valid_rate": round(mean_rhand, 4),
            "mean_face_valid_rate": round(mean_face, 4),
            "mean_frames_lhand": round(mean_f_lhand, 2),
            "mean_frames_rhand": round(mean_f_rhand, 2),
            "mean_frames_both_hands": round(mean_f_both, 2),
            "mean_frames_either_hand": round(mean_f_either, 2),
            "high_quality_count": high_cnt,
            "medium_quality_count": med_cnt,
            "low_quality_count": low_cnt,
            "invalid_quality_count": inv_cnt,
        })
        
    df_classes = pd.DataFrame(class_records).sort_values("label")
    per_class_path = KP_DIR / "quality_audit_per_class.csv"
    df_classes.to_csv(per_class_path, index=False)
    print(f"Saved: {per_class_path}")
    
    # 6. Per-Signer Analysis
    print("Computing per-signer metrics...")
    signer_records = []
    for signer, grp in df_samples.groupby("signer"):
        n_samples = len(grp)
        n_classes = len(grp["label"].unique())
        mean_overall = float(grp["overall_valid_rate"].mean())
        mean_pose = float(grp["pose_valid_rate"].mean())
        mean_lhand = float(grp["lhand_valid_rate"].mean())
        mean_rhand = float(grp["rhand_valid_rate"].mean())
        mean_face = float(grp["face_valid_rate"].mean())
        
        high_cnt = int((grp["quality_category"] == "HIGH").sum())
        med_cnt = int((grp["quality_category"] == "MEDIUM").sum())
        low_cnt = int((grp["quality_category"] == "LOW").sum())
        inv_cnt = int((grp["quality_category"] == "INVALID").sum())
        
        signer_records.append({
            "signer": signer,
            "sample_count": n_samples,
            "class_count": n_classes,
            "mean_overall_valid_rate": round(mean_overall, 4),
            "mean_pose_valid_rate": round(mean_pose, 4),
            "mean_lhand_valid_rate": round(mean_lhand, 4),
            "mean_rhand_valid_rate": round(mean_rhand, 4),
            "mean_face_valid_rate": round(mean_face, 4),
            "high_quality_count": high_cnt,
            "medium_quality_count": med_cnt,
            "low_quality_count": low_cnt,
            "invalid_quality_count": inv_cnt,
        })
        
    df_signers = pd.DataFrame(signer_records).sort_values("signer")
    per_signer_path = KP_DIR / "quality_audit_per_signer.csv"
    df_signers.to_csv(per_signer_path, index=False)
    print(f"Saved: {per_signer_path}")
    
    # 7. Summary Metrics
    print("Generating quality_audit_summary.json...")
    summary = {
        "dataset_name": "WL-BISINDO",
        "total_samples": len(df_samples),
        "total_classes": int(df_samples["label"].nunique()),
        "total_signers": int(df_samples["signer"].nunique()),
        "splits": {
            "train": int((df_samples["split_sd"] == "train").sum()),
            "val": int((df_samples["split_sd"] == "val").sum()),
            "test": int((df_samples["split_sd"] == "test").sum()),
        },
        "quality_distribution": {
            "HIGH": int((df_samples["quality_category"] == "HIGH").sum()),
            "MEDIUM": int((df_samples["quality_category"] == "MEDIUM").sum()),
            "LOW": int((df_samples["quality_category"] == "LOW").sum()),
            "INVALID": int((df_samples["quality_category"] == "INVALID").sum()),
        },
        "quality_percentages": {
            "HIGH": round(float((df_samples["quality_category"] == "HIGH").mean() * 100), 2),
            "MEDIUM": round(float((df_samples["quality_category"] == "MEDIUM").mean() * 100), 2),
            "LOW": round(float((df_samples["quality_category"] == "LOW").mean() * 100), 2),
            "INVALID": round(float((df_samples["quality_category"] == "INVALID").mean() * 100), 2),
        },
        "detection_rates": {
            "overall_valid_rate_mean": round(float(df_samples["overall_valid_rate"].mean()), 4),
            "pose_valid_rate_mean": round(float(df_samples["pose_valid_rate"].mean()), 4),
            "left_hand_valid_rate_mean": round(float(df_samples["lhand_valid_rate"].mean()), 4),
            "right_hand_valid_rate_mean": round(float(df_samples["rhand_valid_rate"].mean()), 4),
            "face_valid_rate_mean": round(float(df_samples["face_valid_rate"].mean()), 4),
        },
        "hand_presence_rates": {
            "mean_frames_left_hand": round(float(df_samples["frames_lhand_present"].mean()), 2),
            "mean_frames_right_hand": round(float(df_samples["frames_rhand_present"].mean()), 2),
            "mean_frames_either_hand": round(float(df_samples["frames_either_hand_present"].mean()), 2),
            "mean_frames_both_hands": round(float(df_samples["frames_both_hands_present"].mean()), 2),
        },
        "gestural_typology": {
            "one_handed_right_classes": int((df_classes["gesture_type"] == "ONE_HANDED_RIGHT").sum()),
            "two_handed_symmetric_classes": int((df_classes["gesture_type"] == "TWO_HANDED_SYMMETRIC").sum()),
            "two_handed_asymmetric_classes": int((df_classes["gesture_type"] == "TWO_HANDED_ASYMMETRIC").sum()),
            "one_handed_left_classes": int((df_classes["gesture_type"] == "ONE_HANDED_LEFT").sum()),
            "low_detection_classes": int((df_classes["gesture_type"] == "LOW_DETECTION").sum()),
        },
        "geometric_normalization_sanity": {
            "max_shoulder_midpoint_deviation": round(float(df_samples["shoulder_midpoint_dev"].max()), 6),
            "max_shoulder_distance_deviation": round(float(df_samples["shoulder_dist_dev"].max()), 6),
            "perfectly_normalized_count": int(((df_samples["shoulder_midpoint_dev"] < 1e-4) & (df_samples["shoulder_dist_dev"] < 1e-4)).sum()),
        },
        "spatial_coordinate_bounds": {
            "x_global_min": round(float(df_samples["x_min"].min()), 4),
            "x_global_max": round(float(df_samples["x_max"].max()), 4),
            "y_global_min": round(float(df_samples["y_min"].min()), 4),
            "y_global_max": round(float(df_samples["y_max"].max()), 4),
            "z_global_min": round(float(df_samples["z_min"].min()), 4),
            "z_global_max": round(float(df_samples["z_max"].max()), 4),
            "total_nan_count": int(df_samples["nan_count"].sum()),
            "total_inf_count": int(df_samples["inf_count"].sum()),
        },
        "temporal_anomalies": {
            "max_interframe_jump": round(float(df_samples["max_interframe_jump"].max()), 4),
            "mean_interframe_jump": round(float(df_samples["mean_interframe_jump"].mean()), 4),
            "max_wrist_jump": round(float(df_samples["max_wrist_jump"].max()), 4),
            "static_frozen_samples": int(df_samples["is_static_frozen"].sum()),
        },
        "duplicate_and_leakage": {
            "duplicate_raw_videos": len(dup_videos),
            "duplicate_npz_files": len(dup_npz),
            "duplicate_feature_hashes": len(dup_feats),
            "cross_split_leakage_count": int(df_dups["is_cross_split_leakage"].sum()),
        },
        "readiness_status": "READY FOR BASELINE TRAINING" if int((df_samples['quality_category'] == 'INVALID').sum()) == 0 and ((df_samples['quality_category'] == 'HIGH').sum() + (df_samples['quality_category'] == 'MEDIUM').sum()) >= 1500 else "READY WITH DATA QUALITY LIMITATIONS"
    }
    
    summary_path = KP_DIR / "quality_audit_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {summary_path}")
    
    print("=== AUDIT SUMMARY ===")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Quality: HIGH={summary['quality_distribution']['HIGH']} ({summary['quality_percentages']['HIGH']}%), MEDIUM={summary['quality_distribution']['MEDIUM']} ({summary['quality_percentages']['MEDIUM']}%), LOW={summary['quality_distribution']['LOW']} ({summary['quality_percentages']['LOW']}%), INVALID={summary['quality_distribution']['INVALID']} ({summary['quality_percentages']['INVALID']}%)")
    print(f"Detection rates: Pose={summary['detection_rates']['pose_valid_rate_mean']}, LHand={summary['detection_rates']['left_hand_valid_rate_mean']}, RHand={summary['detection_rates']['right_hand_valid_rate_mean']}, Face={summary['detection_rates']['face_valid_rate_mean']}, Overall={summary['detection_rates']['overall_valid_rate_mean']}")
    print(f"Readiness: {summary['readiness_status']}")

if __name__ == "__main__":
    main()

