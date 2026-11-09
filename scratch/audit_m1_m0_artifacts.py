import json
import yaml
import pandas as pd
import numpy as np
import torch
from pathlib import Path

ROOT = Path(".")
m1_dir = ROOT / "outputs" / "experiments" / "M1_stgcn_baseline"
m0_dir = ROOT / "outputs" / "experiments" / "M0_student_baseline"

print("=== M1 CONFIG ===")
with open(m1_dir / "training_config.yaml") as f:
    cfg = yaml.safe_load(f)
    print(json.dumps(cfg, indent=2))

print("\n=== M1 EVALUATION METRICS ===")
with open(m1_dir / "evaluation_metrics.json") as f:
    m1_eval = json.load(f)
    print(json.dumps(m1_eval, indent=2))

print("\n=== M1 METADATA ===")
with open(m1_dir / "experiment_metadata.json") as f:
    m1_meta = json.load(f)
    print(json.dumps(m1_meta, indent=2))

print("\n=== M1 SUMMARY ===")
with open(m1_dir / "experiment_summary.json") as f:
    m1_sum = json.load(f)
    print(json.dumps(m1_sum, indent=2))

print("\n=== M1 GRAPH TOPOLOGY ===")
with open(m1_dir / "graph_topology.json") as f:
    topo = json.load(f)
    print("Num nodes:", topo["num_nodes"])
    print("Num edges:", topo["num_spatial_edges"])
    print("Is connected:", topo["is_connected"])
    print("Partition definitions:", json.dumps(topo["partition_definitions"], indent=2))
    print("Node groups:", json.dumps(topo["node_groups"], indent=2))

print("\n=== M1 TRAINING HISTORY ===")
df_m1_hist = pd.read_csv(m1_dir / "training_history.csv")
print(f"Total epochs: {len(df_m1_hist)}")
min_val_loss_idx = df_m1_hist["val_loss"].idxmin()
print("Min val loss row:\n", df_m1_hist.loc[min_val_loss_idx])
print("\nFirst 5 epochs:\n", df_m1_hist.head(5))
print("\nLast 15 epochs:\n", df_m1_hist.tail(15))

print("\n=== M1 CLASSIFICATION REPORT (TOP & BOTTOM CLASSES) ===")
df_m1_cls = pd.read_csv(m1_dir / "classification_report.csv", index_col=0)
print(df_m1_cls.to_string())

print("\n=== M0 EVALUATION METRICS ===")
with open(m0_dir / "evaluation_metrics.json") as f:
    m0_eval = json.load(f)
    print(json.dumps(m0_eval, indent=2))

print("\n=== M0 METADATA ===")
with open(m0_dir / "experiment_metadata.json") as f:
    m0_meta = json.load(f)
    print(json.dumps(m0_meta, indent=2))

print("\n=== M0 TRAINING HISTORY ===")
df_m0_hist = pd.read_csv(m0_dir / "training_history.csv")
print(f"M0 total epochs: {len(df_m0_hist)}")
min_val_loss_m0 = df_m0_hist["val_loss"].idxmin()
print("M0 Min val loss row:\n", df_m0_hist.loc[min_val_loss_m0])

print("\n=== M0 CLASSIFICATION REPORT ===")
df_m0_cls = pd.read_csv(m0_dir / "classification_report.csv", index_col=0)
print(df_m0_cls.to_string())

