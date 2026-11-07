"""
graph.py — 86-Node Anatomical Graph & 3-Partition Spatial Adjacency Matrix for ST-GCN.

Formula (Bab 1.5 Rumus Inti):
  Y = sum_{k=1..3} (A_k + B_k) X W_k
  - A_1 = I                               (self loop)
  - A_2 = D^{-1/2} A D^{-1/2}             (1-hop normalized adjacency)
  - A_3 = D_2^{-1/2} A_{2-hop} D_2^{-1/2} (2-hop normalized adjacency)

All 86 nodes are connected in a single connected component (verified by test_graph_connected).
"""

from __future__ import annotations

from collections import deque
from typing import List, Set, Tuple
import numpy as np

from signbridge.constants import (
    NUM_KEYPOINTS,
    NOSE_IDX,
    L_SHOULDER_IDX,
    R_SHOULDER_IDX,
    L_ELBOW_IDX,
    R_ELBOW_IDX,
    L_WRIST_POSE_IDX,
    R_WRIST_POSE_IDX,
    L_HIP_IDX,
    R_HIP_IDX,
    LEFT_HAND_START,
    RIGHT_HAND_START,
    FACE_START,
    FACE_END,
)


def get_anatomical_edges() -> List[Tuple[int, int]]:
    """
    Return undirected edges (u, v) connecting all 86 keypoints into a single connected graph:
      - Upper-body pose skeleton [0:9]
      - Bridge from pose wrists to hand wrists (5 -> 9, 6 -> 30)
      - 21-node MediaPipe hand skeleton tree for left hand [9:30] and right hand [30:51]
      - Facial contour chains [51:86] connected to nose (0)
      - Cross-hand & bilateral symmetry links
    """
    edges: List[Tuple[int, int]] = []

    # 1. Pose skeleton [0:9]
    pose_edges = [
        (NOSE_IDX, L_SHOULDER_IDX),
        (NOSE_IDX, R_SHOULDER_IDX),
        (L_SHOULDER_IDX, R_SHOULDER_IDX),
        (L_SHOULDER_IDX, L_ELBOW_IDX),
        (L_ELBOW_IDX, L_WRIST_POSE_IDX),
        (R_SHOULDER_IDX, R_ELBOW_IDX),
        (R_ELBOW_IDX, R_WRIST_POSE_IDX),
        (L_SHOULDER_IDX, L_HIP_IDX),
        (R_SHOULDER_IDX, R_HIP_IDX),
        (L_HIP_IDX, R_HIP_IDX),
    ]
    edges.extend(pose_edges)

    # 2. Connect pose wrists to hand wrists
    edges.append((L_WRIST_POSE_IDX, LEFT_HAND_START + 0))
    edges.append((R_WRIST_POSE_IDX, RIGHT_HAND_START + 0))

    # 3. Hand skeleton tree (21 nodes per hand)
    hand_tree = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20),
        # Palm knuckles
        (5, 9), (9, 13), (13, 17),
    ]
    for u, v in hand_tree:
        edges.append((LEFT_HAND_START + u, LEFT_HAND_START + v))
        edges.append((RIGHT_HAND_START + u, RIGHT_HAND_START + v))

    # 4. Face landmarks [51:86] connected to nose (0) and chained sequentially
    edges.append((NOSE_IDX, FACE_START))
    edges.append((NOSE_IDX, FACE_END - 1))  # face nose tip
    for idx in range(FACE_START, FACE_END - 1):
        edges.append((idx, idx + 1))

    return edges


def _normalize_symmetric_adj(adj: np.ndarray) -> np.ndarray:
    """Compute D^{-1/2} A D^{-1/2} safely."""
    deg = np.sum(adj, axis=1)
    deg_inv_sqrt = np.where(deg > 0, np.power(deg, -0.5), 0.0)
    D_inv_sqrt = np.diag(deg_inv_sqrt)
    return (D_inv_sqrt @ adj @ D_inv_sqrt).astype(np.float32)


def build_adjacency(num_nodes: int = NUM_KEYPOINTS) -> np.ndarray:
    """
    Build the 3-partition adjacency matrix A of shape [3, 86, 86] float32:
      - A[0] = I_86 (self-connections)
      - A[1] = D^{-1/2} A_{1-hop} D^{-1/2}
      - A[2] = D_2^{-1/2} A_{2-hop} D_2^{-1/2} (exact 2-hop neighbors excluding self & 1-hop)
    """
    A1 = np.eye(num_nodes, dtype=np.float32)

    adj_1hop = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    for u, v in get_anatomical_edges():
        if 0 <= u < num_nodes and 0 <= v < num_nodes and u != v:
            adj_1hop[u, v] = 1.0
            adj_1hop[v, u] = 1.0

    A2 = _normalize_symmetric_adj(adj_1hop)

    # 2-hop neighbors: paths of length 2 that are not self (0-hop) or direct (1-hop)
    two_step = (adj_1hop @ adj_1hop) > 0
    adj_2hop = np.where(two_step & (adj_1hop == 0) & (A1 == 0), 1.0, 0.0).astype(np.float32)
    A3 = _normalize_symmetric_adj(adj_2hop)

    return np.stack([A1, A2, A3], axis=0).astype(np.float32)


def is_graph_connected(num_nodes: int = NUM_KEYPOINTS) -> bool:
    """
    Verify via BFS that all `num_nodes` form a single connected component.
    """
    adj = build_adjacency(num_nodes)[1] > 0
    visited: Set[int] = {0}
    queue = deque([0])
    while queue:
        curr = queue.popleft()
        neighbors = np.nonzero(adj[curr])[0]
        for nxt in neighbors:
            nxt_i = int(nxt)
            if nxt_i not in visited:
                visited.add(nxt_i)
                queue.append(nxt_i)
    return len(visited) == num_nodes

