import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Set MPLCONFIGDIR to avoid permission error
os.environ['MPLCONFIGDIR'] = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'matplotlib')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
KP_DIR = ROOT / "data" / "keypoints" / "wl_bisindo"
FIG_DIR = ROOT / "docs" / "figures" / "wlbisindo_quality_audit"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# 86-node landmark connections for visualization
# Pose: 0: nose, 1: L_shoulder, 2: R_shoulder, 3: L_elbow, 4: R_elbow, 5: L_wrist, 6: R_wrist, 7: L_hip, 8: R_hip
POSE_CONNECTIONS = [
    (1, 2),  # shoulders
    (1, 3), (3, 5),  # left arm
    (2, 4), (4, 6),  # right arm
    (1, 7), (2, 8), (7, 8),  # torso
    (0, 1), (0, 2)   # neck/head to shoulders
]

# Hand connections (21 nodes, relative 0..20)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # index
    (0, 9), (9, 10), (10, 11), (11, 12),   # middle
    (0, 13), (13, 14), (14, 15), (15, 16), # ring
    (0, 17), (17, 18), (18, 19), (19, 20)  # pinky
]

def plot_distributions(df_samples):
    print("Generating dataset_validity_distribution.png...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Overall valid rate histogram
    axes[0].hist(df_samples['overall_valid_rate'] * 100, bins=25, color='#2563EB', edgecolor='black', alpha=0.8)
    axes[0].set_title('Overall Landmark Validity Rate (%)', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Validity (%)')
    axes[0].set_ylabel('Sample Count')
    axes[0].axvline(df_samples['overall_valid_rate'].mean() * 100, color='red', linestyle='--', label=f"Mean: {df_samples['overall_valid_rate'].mean()*100:.1f}%")
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # 2. Hand valid rates comparison
    axes[1].hist(df_samples['lhand_valid_rate'] * 100, bins=20, color='#F59E0B', alpha=0.7, label=f"Left Hand (Mean: {df_samples['lhand_valid_rate'].mean()*100:.1f}%)", edgecolor='black')
    axes[1].hist(df_samples['rhand_valid_rate'] * 100, bins=20, color='#10B981', alpha=0.7, label=f"Right Hand (Mean: {df_samples['rhand_valid_rate'].mean()*100:.1f}%)", edgecolor='black')
    axes[1].set_title('Left vs Right Hand Validity Rate (%)', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Validity (%)')
    axes[1].set_ylabel('Sample Count')
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    # 3. Frames with hands present
    axes[2].hist(df_samples['frames_either_hand_present'], bins=20, color='#8B5CF6', edgecolor='black', alpha=0.8, label=f"Either Hand (Mean: {df_samples['frames_either_hand_present'].mean():.1f}/64)")
    axes[2].hist(df_samples['frames_both_hands_present'], bins=20, color='#EC4899', edgecolor='black', alpha=0.7, label=f"Both Hands (Mean: {df_samples['frames_both_hands_present'].mean():.1f}/64)")
    axes[2].set_title('Hand-Active Frames (out of 64)', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Frames Detected')
    axes[2].set_ylabel('Sample Count')
    axes[2].legend()
    axes[2].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "dataset_validity_distribution.png", dpi=200)
    plt.close()

def plot_by_signer(df_signers):
    print("Generating validity_by_signer.png...")
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df_signers))
    width = 0.16
    
    ax.bar(x - 2*width, df_signers['mean_pose_valid_rate']*100, width, label='Pose', color='#3B82F6')
    ax.bar(x - width, df_signers['mean_face_valid_rate']*100, width, label='Face', color='#8B5CF6')
    ax.bar(x, df_signers['mean_rhand_valid_rate']*100, width, label='Right Hand', color='#10B981')
    ax.bar(x + width, df_signers['mean_lhand_valid_rate']*100, width, label='Left Hand', color='#F59E0B')
    ax.bar(x + 2*width, df_signers['mean_overall_valid_rate']*100, width, label='Overall', color='#6B7280')
    
    ax.set_ylabel('Mean Validity Rate (%)', fontsize=11, fontweight='bold')
    ax.set_title('Landmark Validity Rate by Signer (WL-BISINDO)', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\n({c} cls, {n} vids)" for s, c, n in zip(df_signers['signer'], df_signers['class_count'], df_signers['sample_count'])])
    ax.set_ylim(0, 110)
    ax.legend(loc='lower right', framealpha=0.9)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "validity_by_signer.png", dpi=200)
    plt.close()

def plot_by_class(df_classes):
    print("Generating validity_by_class.png...")
    fig, ax = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(df_classes))
    width = 0.38
    
    rects1 = ax.bar(x - width/2, df_classes['mean_rhand_valid_rate']*100, width, label='Right Hand (Dominant)', color='#10B981', alpha=0.85)
    rects2 = ax.bar(x + width/2, df_classes['mean_lhand_valid_rate']*100, width, label='Left Hand', color='#F59E0B', alpha=0.85)
    
    ax.set_ylabel('Mean Hand Validity Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Left vs Right Hand Validity Rate Across 32 WL-BISINDO Classes\n(Red labels highlight 4 Two-Handed Symmetric Classes: MOTOR, BAGAIMANA, TEMAN, RUMAH)', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    labels = [f"{g}\n(L{l})" for l, g in zip(df_classes['label'], df_classes['gloss'])]
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    
    # Color tick labels
    for tick_label, gtype in zip(ax.get_xticklabels(), df_classes['gesture_type']):
        if 'TWO_HANDED' in gtype:
            tick_label.set_color('#DC2626')
            tick_label.set_fontweight('bold')
            
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "validity_by_class.png", dpi=200)
    plt.close()

def plot_left_vs_right(df_samples, df_classes):
    print("Generating left_vs_right_hand.png...")
    fig, ax = plt.subplots(figsize=(9, 7))
    
    # Scatter all samples
    colors = {'ONE_HANDED_RIGHT': '#3B82F6', 'TWO_HANDED_SYMMETRIC': '#DC2626'}
    
    # Merge class gesture type to samples
    df_merged = pd.merge(df_samples, df_classes[['label', 'gesture_type']], on='label')
    
    for gtype, grp in df_merged.groupby('gesture_type'):
        ax.scatter(grp['rhand_valid_rate']*100, grp['lhand_valid_rate']*100, 
                   alpha=0.6, s=25, label=f"{gtype} ({len(grp)} samples)", color=colors.get(gtype, '#6B7280'))
        
    ax.set_xlabel('Right Hand Validity Rate (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Left Hand Validity Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Hand Detection Asymmetry: Left vs Right Hand Validity (1,600 samples)\nDemonstrates 2 distinct natural linguistic clusters in WL-BISINDO', fontsize=12, fontweight='bold')
    ax.axhline(50, color='gray', linestyle=':', alpha=0.5)
    ax.axvline(50, color='gray', linestyle=':', alpha=0.5)
    ax.legend(loc='center left', fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "left_vs_right_hand.png", dpi=200)
    plt.close()

def plot_quality_categories(df_samples):
    print("Generating quality_category_distribution.png...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    cat_counts = df_samples['quality_category'].value_counts()
    categories = ['HIGH', 'MEDIUM', 'LOW', 'INVALID']
    counts = [cat_counts.get(c, 0) for c in categories]
    colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444']
    
    # Donut chart
    wedges, texts, autotexts = ax1.pie(
        counts, 
        labels=[f"{c}\n({cnt})" for c, cnt in zip(categories, counts)],
        autopct=lambda pct: f"{pct:.1f}%" if pct > 0.05 else "",
        colors=colors,
        startangle=140,
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
        pctdistance=0.75,
        textprops=dict(fontsize=10, fontweight='bold')
    )
    ax1.set_title('Dataset Quality Category Distribution\n(1,600 Extracted Samples)', fontsize=12, fontweight='bold')
    
    # Quality by Signer
    signer_cats = pd.crosstab(df_samples['signer'], df_samples['quality_category'], normalize='index') * 100
    for c in ['HIGH', 'MEDIUM', 'LOW', 'INVALID']:
        if c not in signer_cats.columns:
            signer_cats[c] = 0.0
    signer_cats = signer_cats[['HIGH', 'MEDIUM', 'LOW', 'INVALID']]
    
    signer_cats.plot(kind='bar', stacked=True, color=colors, ax=ax2, edgecolor='black', alpha=0.85)
    ax2.set_title('Quality Breakdown by Signer (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Signer', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, 105)
    ax2.legend(loc='lower left')
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(FIG_DIR / "quality_category_distribution.png", dpi=200)
    plt.close()

def plot_split_distribution(df_samples):
    print("Generating split_distribution.png...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    split_counts = df_samples['split_sd'].value_counts()
    splits = ['train', 'val', 'test']
    counts = [split_counts.get(s, 0) for s in splits]
    pcts = [c / len(df_samples) * 100 for c in counts]
    
    bars = ax.bar(splits, counts, color=['#2563EB', '#F59E0B', '#10B981'], edgecolor='black', alpha=0.85, width=0.5)
    ax.set_title('Dataset Split Distribution (Signer-Dependent / SD)\nTrain (60%) / Val (11.25%) / Test (28.75%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Samples', fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1100)
    
    for bar, c, p in zip(bars, counts, pcts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 20,
                f'{c} samples\n({p:.2f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "split_distribution.png", dpi=200)
    plt.close()

def render_sample_skeleton(video_id: str, out_filename: str, title: str):
    npz_path = KP_DIR / f"{video_id}.npz"
    if not npz_path.exists():
        print(f"Skipping {video_id}: file not found")
        return
        
    data = np.load(npz_path)
    kp = data['keypoints']  # [64, 86, 3]
    mask = data['valid_mask']  # [64, 86]
    
    # Pick 4 frames evenly spaced
    frames_to_plot = [8, 24, 40, 56]
    
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    fig.suptitle(f"{title}\nVideo: {video_id} (Gloss: {data['gloss']}, Signer: {data['signer']})", fontsize=12, fontweight='bold')
    
    for ax_idx, f in enumerate(frames_to_plot):
        ax = axes[ax_idx]
        f_kp = kp[f]
        f_mask = mask[f]
        
        # Invert Y so up is up (in image coords y grows down)
        x_vals = f_kp[:, 0]
        y_vals = -f_kp[:, 1]
        
        # Plot Pose (0:9)
        pose_valid = f_mask[0:9]
        if np.any(pose_valid):
            ax.scatter(x_vals[0:9][pose_valid], y_vals[0:9][pose_valid], color='#2563EB', s=35, zorder=4, label='Pose' if ax_idx==0 else "")
            for p1, p2 in POSE_CONNECTIONS:
                if f_mask[p1] and f_mask[p2]:
                    ax.plot([x_vals[p1], x_vals[p2]], [y_vals[p1], y_vals[p2]], color='#2563EB', linewidth=2.5, zorder=3)
                    
        # Plot Left Hand (9:30)
        lhand_valid = f_mask[9:30]
        if np.any(lhand_valid):
            ax.scatter(x_vals[9:30][lhand_valid], y_vals[9:30][lhand_valid], color='#F59E0B', s=20, zorder=4, label='Left Hand' if ax_idx==0 else "")
            for h1, h2 in HAND_CONNECTIONS:
                idx1 = 9 + h1
                idx2 = 9 + h2
                if f_mask[idx1] and f_mask[idx2]:
                    ax.plot([x_vals[idx1], x_vals[idx2]], [y_vals[idx1], y_vals[idx2]], color='#F59E0B', linewidth=1.5, zorder=3)
                    
        # Plot Right Hand (30:51)
        rhand_valid = f_mask[30:51]
        if np.any(rhand_valid):
            ax.scatter(x_vals[30:51][rhand_valid], y_vals[30:51][rhand_valid], color='#10B981', s=20, zorder=4, label='Right Hand' if ax_idx==0 else "")
            for h1, h2 in HAND_CONNECTIONS:
                idx1 = 30 + h1
                idx2 = 30 + h2
                if f_mask[idx1] and f_mask[idx2]:
                    ax.plot([x_vals[idx1], x_vals[idx2]], [y_vals[idx1], y_vals[idx2]], color='#10B981', linewidth=1.5, zorder=3)
                    
        # Plot Face (51:86)
        face_valid = f_mask[51:86]
        if np.any(face_valid):
            ax.scatter(x_vals[51:86][face_valid], y_vals[51:86][face_valid], color='#8B5CF6', s=8, alpha=0.6, zorder=2, label='Face' if ax_idx==0 else "")
            
        ax.set_title(f"Frame {f+1}/64", fontsize=10, fontweight='bold')
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.8, 1.2)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':', alpha=0.5)
        if ax_idx == 0:
            ax.legend(loc='lower left', fontsize=8)
            
    plt.tight_layout()
    fig.savefig(FIG_DIR / out_filename, dpi=200)
    plt.close()
    print(f"Rendered: {out_filename}")

def main():
    df_samples = pd.read_csv(KP_DIR / "quality_audit_per_sample.csv")
    df_classes = pd.read_csv(KP_DIR / "quality_audit_per_class.csv")
    df_signers = pd.read_csv(KP_DIR / "quality_audit_per_signer.csv")
    
    # 1. Statistical Charts
    plot_distributions(df_samples)
    plot_by_signer(df_signers)
    plot_by_class(df_classes)
    plot_left_vs_right(df_samples, df_classes)
    plot_quality_categories(df_samples)
    plot_split_distribution(df_samples)
    
    # 2. Visual Skeleton Inspections
    # High quality sample
    render_sample_skeleton("wl_bisindo_signer1_label0_sample1", "skeleton_high_sample.png", "High Quality Sample (AIR - 1-handed)")
    # Two-handed sample
    render_sample_skeleton("wl_bisindo_signer1_label25_sample1", "skeleton_two_handed.png", "Two-Handed Symmetric Sample (TEMAN)")
    # One-handed sample
    render_sample_skeleton("wl_bisindo_signer2_label1_sample3", "skeleton_one_handed.png", "One-Handed Sample (BELAJAR)")
    # Medium quality sample
    # Find a medium sample
    med_sample = df_samples[df_samples['quality_category'] == 'MEDIUM'].iloc[0]['video_id']
    render_sample_skeleton(med_sample, "skeleton_medium_sample.png", "Medium Quality Sample (Partial Hand Frames)")
    # Low quality sample
    low_sample = df_samples[df_samples['quality_category'] == 'LOW'].iloc[0]['video_id']
    render_sample_skeleton(low_sample, "skeleton_low_sample.png", "Low Quality Sample (Brief Hand Detection)")
    
    print("All figures successfully generated in docs/figures/wlbisindo_quality_audit/")

if __name__ == "__main__":
    main()
