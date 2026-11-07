"""
keypoint_graph_builder.py — Construct and validate Keypoint_Graph from YAML config.
Requirements: 4.1, 4.2, 4.3, 4.5
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np
import yaml
from src.exceptions import GraphConfigError


@dataclass
class KeypointGraph:
    num_nodes: int
    node_labels: list[str]
    spatial_edges: list[tuple[int, int]]    # anatomical edges
    symmetry_edges: list[tuple[int, int]]   # left↔right symmetry pairs
    adjacency_matrix: np.ndarray            # [num_nodes, num_nodes] float32, symmetric


class KeypointGraphBuilder:
    """Construct and validate a KeypointGraph from a YAML configuration file."""

    def build_from_yaml(self, config_path: Path) -> KeypointGraph:
        """
        Load configs/graph_config.yaml, validate, build and return KeypointGraph.

        Validation:
        1. All node indices in spatial_edges and symmetry_edges must be in [0, num_nodes-1]
           → raise GraphConfigError("Node index {idx} out of range [0, {num_nodes-1}] in edge {edge}")
        2. Every node must appear in at least one edge (spatial OR symmetry)
           → raise GraphConfigError("Isolated nodes detected: {sorted(isolated_set)}")
        """
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        num_nodes: int = config["num_nodes"]
        node_labels: list[str] = config.get("node_labels", [f"node_{i}" for i in range(num_nodes)])

        edges_section = config.get("edges", {})

        # --- Load spatial edges ---
        raw_spatial = edges_section.get("spatial") or []
        spatial_edges: list[tuple[int, int]] = []
        for edge in raw_spatial:
            src, dst = int(edge[0]), int(edge[1])
            spatial_edges.append((src, dst))

        # --- Load symmetry edges ---
        raw_symmetry = edges_section.get("symmetry") or []
        symmetry_edges: list[tuple[int, int]] = []
        for edge in raw_symmetry:
            src, dst = int(edge[0]), int(edge[1])
            symmetry_edges.append((src, dst))

        # --- Validate node indices (spatial + symmetry) ---
        all_edges = [("spatial", e) for e in spatial_edges] + [("symmetry", e) for e in symmetry_edges]
        for edge_type, edge in all_edges:
            for idx in edge:
                if idx < 0 or idx > num_nodes - 1:
                    raise GraphConfigError(
                        f"Node index {idx} out of range [0, {num_nodes - 1}] in edge {list(edge)}"
                    )

        # --- Validate no isolated nodes ---
        connected_nodes: set[int] = set()
        for src, dst in spatial_edges:
            connected_nodes.add(src)
            connected_nodes.add(dst)
        for src, dst in symmetry_edges:
            connected_nodes.add(src)
            connected_nodes.add(dst)

        all_nodes = set(range(num_nodes))
        isolated = all_nodes - connected_nodes
        if isolated:
            raise GraphConfigError(f"Isolated nodes detected: {sorted(isolated)}")

        # --- Build adjacency matrix ---
        adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        for src, dst in spatial_edges:
            adj[src, dst] = 1.0
            adj[dst, src] = 1.0

        return KeypointGraph(
            num_nodes=num_nodes,
            node_labels=node_labels,
            spatial_edges=spatial_edges,
            symmetry_edges=symmetry_edges,
            adjacency_matrix=adj,
        )

    def build_temporal_edges(
        self, num_nodes: int, num_frames: int
    ) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """
        Generate temporal edges: each (node_i, t) → (node_i, t+1) for t in [0, num_frames-2].
        Returns list of ((node_i, t), (node_i, t+1)).
        Total = num_nodes × (num_frames - 1).
        """
        edges = []
        for t in range(num_frames - 1):
            for node_i in range(num_nodes):
                edges.append(((node_i, t), (node_i, t + 1)))
        return edges
