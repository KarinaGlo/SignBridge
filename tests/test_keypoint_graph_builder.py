"""
test_keypoint_graph_builder.py

Unit tests for:
  - KeypointGraphBuilder  (Tasks 3.7)
  - CoordinateNormalizer  (Task 3.8)

Property-based tests:
  - Property 6: Graph Coordinate Normalization  (Task 3.9)
  - Property 7: Graph Topology Validation       (Task 3.10)

Requirements covered: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
import tempfile
import numpy as np
import yaml
from pathlib import Path
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from src.data.keypoint_graph_builder import KeypointGraphBuilder, KeypointGraph
from src.data.coordinate_normalizer import CoordinateNormalizer
from src.exceptions import GraphConfigError

# ---------------------------------------------------------------------------
# Shared fixture — path to the real graph config
# ---------------------------------------------------------------------------

GRAPH_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "graph_config.yaml"


@pytest.fixture(scope="module")
def graph() -> KeypointGraph:
    """Load the real graph config once for all unit tests."""
    builder = KeypointGraphBuilder()
    return builder.build_from_yaml(GRAPH_CONFIG_PATH)


# ===========================================================================
# Unit tests — KeypointGraphBuilder (Task 3.7)
# ===========================================================================

def test_build_valid_graph_from_yaml(graph):
    """Loading configs/graph_config.yaml must succeed without raising."""
    assert isinstance(graph, KeypointGraph)


def test_num_nodes_correct(graph):
    """graph.num_nodes must equal 33 (MediaPipe pose keypoints)."""
    assert graph.num_nodes == 33


def test_node_labels_count(graph):
    """There must be exactly 33 node labels."""
    assert len(graph.node_labels) == 33


def test_spatial_edges_nonempty(graph):
    """The spatial edge list must not be empty."""
    assert len(graph.spatial_edges) > 0


def test_all_nodes_connected(graph):
    """Every node in the loaded config must appear in at least one edge — no isolated nodes."""
    connected: set[int] = set()
    for src, dst in graph.spatial_edges:
        connected.add(src)
        connected.add(dst)
    for src, dst in graph.symmetry_edges:
        connected.add(src)
        connected.add(dst)
    all_nodes = set(range(graph.num_nodes))
    assert all_nodes == connected, f"Isolated nodes: {all_nodes - connected}"


def test_adjacency_matrix_shape(graph):
    """Adjacency matrix must have shape (33, 33)."""
    assert graph.adjacency_matrix.shape == (33, 33)


def test_adjacency_matrix_symmetric(graph):
    """Adjacency matrix must be symmetric: adj[i,j] == adj[j,i] for all i,j."""
    adj = graph.adjacency_matrix
    assert np.allclose(adj, adj.T), "Adjacency matrix is not symmetric"


def test_invalid_node_index_raises(tmp_path):
    """An edge referencing node index 33 (out of range for 33 nodes) must raise GraphConfigError."""
    config = {
        "num_nodes": 33,
        "node_labels": [f"node_{i}" for i in range(33)],
        "edges": {
            "spatial": [[0, 1], [33, 0]],  # 33 is invalid (valid range 0-32)
            "temporal": [],
            "symmetry": [],
        },
    }
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(yaml.dump(config))

    builder = KeypointGraphBuilder()
    with pytest.raises(GraphConfigError):
        builder.build_from_yaml(config_path)


def test_isolated_node_raises(tmp_path):
    """A config where a node has no edges must raise GraphConfigError mentioning the index."""
    # 4 nodes, but node 3 has no edges
    config = {
        "num_nodes": 4,
        "node_labels": ["a", "b", "c", "isolated"],
        "edges": {
            "spatial": [[0, 1], [1, 2]],  # node 3 has no edges
            "temporal": [],
            "symmetry": [],
        },
    }
    config_path = tmp_path / "isolated.yaml"
    config_path.write_text(yaml.dump(config))

    builder = KeypointGraphBuilder()
    with pytest.raises(GraphConfigError) as exc_info:
        builder.build_from_yaml(config_path)
    assert "3" in str(exc_info.value)


def test_temporal_edges_count():
    """build_temporal_edges(33, 10) must return exactly 33 × 9 = 297 edges."""
    builder = KeypointGraphBuilder()
    edges = builder.build_temporal_edges(33, 10)
    assert len(edges) == 33 * 9


def test_symmetry_edges_nonempty(graph):
    """The loaded graph must have at least one symmetry edge."""
    assert len(graph.symmetry_edges) > 0


# ===========================================================================
# Unit tests — CoordinateNormalizer (Task 3.8)
# ===========================================================================

def _make_keypoints(cx: float = 0.5, cy: float = 0.5, spread: float = 0.3) -> np.ndarray:
    """Return [543, 3] float32 keypoints with a non-degenerate pose bbox."""
    kp = np.full((543, 3), 0.5, dtype=np.float32)
    half = spread / 2.0
    # pose keypoints span [cx-half, cx+half]
    kp[42:75, 0] = np.linspace(cx - half, cx + half, 33, dtype=np.float32)
    kp[42:75, 1] = np.linspace(cy - half, cy + half, 33, dtype=np.float32)
    return kp


def test_normalize_frame_output_range():
    """All normalized x and y values must lie within [-1, 1]."""
    kp = _make_keypoints()
    normalizer = CoordinateNormalizer()
    normalized, _ = normalizer.normalize_frame(kp)
    assert normalized[:, 0].max() <= 1.0 + 1e-6
    assert normalized[:, 0].min() >= -1.0 - 1e-6
    assert normalized[:, 1].max() <= 1.0 + 1e-6
    assert normalized[:, 1].min() >= -1.0 - 1e-6


def test_normalize_frame_fallback_prev_bbox():
    """When the pose bbox is degenerate (all pose kp identical), prev_bbox must be used."""
    # Degenerate frame: all pose keypoints at the same point → width=height=0
    kp_degenerate = np.full((543, 3), 0.5, dtype=np.float32)

    # prev_bbox that is non-degenerate
    prev_bbox = (0.2, 0.2, 0.8, 0.8)
    normalizer = CoordinateNormalizer()
    normalized, used_bbox = normalizer.normalize_frame(kp_degenerate, prev_bbox=prev_bbox)

    assert used_bbox == prev_bbox, "Expected prev_bbox to be used for degenerate frame"
    # Normalized values must still be finite and in [-1, 1]
    assert np.all(np.isfinite(normalized[:, :2]))
    assert normalized[:, :2].max() <= 1.0 + 1e-6
    assert normalized[:, :2].min() >= -1.0 - 1e-6


def test_normalize_sequence_shape():
    """Output shape must equal input shape [T, N, 3]."""
    T, N = 10, 543
    seq = np.random.rand(T, N, 3).astype(np.float32)
    # Ensure non-degenerate pose bbox per frame
    for t in range(T):
        seq[t, 42:75, 0] = np.linspace(0.1, 0.9, 33)
        seq[t, 42:75, 1] = np.linspace(0.1, 0.9, 33)

    normalizer = CoordinateNormalizer()
    result = normalizer.normalize_sequence(seq)
    assert result.shape == (T, N, 3)


def test_normalize_sequence_no_nan():
    """Normalized sequence must contain no NaN values."""
    T, N = 8, 543
    seq = np.random.rand(T, N, 3).astype(np.float32)
    for t in range(T):
        seq[t, 42:75, 0] = np.linspace(0.1, 0.9, 33)
        seq[t, 42:75, 1] = np.linspace(0.1, 0.9, 33)

    normalizer = CoordinateNormalizer()
    result = normalizer.normalize_sequence(seq)
    assert not np.any(np.isnan(result))


# ===========================================================================
# Property 6: Graph Coordinate Normalization (Task 3.9)
# **Validates: Requirements 4.4**
# ===========================================================================

@settings(max_examples=100)
@given(
    pose_spread=st.floats(0.05, 0.9),
    cx=st.floats(0.1, 0.9),
    cy=st.floats(0.1, 0.9),
)
def test_property_6_normalized_values_in_range(pose_spread, cx, cy):
    """
    Property 6: For any non-degenerate bounding box, normalized coords ∈ [-1.0, 1.0].
    **Validates: Requirements 4.4**
    """
    # Create [543, 3] keypoints where pose (42:75) spans [cx-spread/2, cx+spread/2]
    keypoints = np.full((543, 3), 0.5, dtype=np.float32)
    half = pose_spread / 2.0
    # Place pose keypoints to define a non-degenerate bbox
    keypoints[42:75, 0] = np.linspace(cx - half, cx + half, 33).astype(np.float32)
    keypoints[42:75, 1] = np.linspace(cy - half, cy + half, 33).astype(np.float32)

    normalizer = CoordinateNormalizer()
    normalized, bbox = normalizer.normalize_frame(keypoints)

    # All values should be in [-1, 1] (with small float tolerance)
    assert normalized.max() <= 1.0 + 1e-5, (
        f"Normalized max {normalized.max()} exceeds 1.0 (pose_spread={pose_spread}, cx={cx}, cy={cy})"
    )
    assert normalized.min() >= -1.0 - 1e-5, (
        f"Normalized min {normalized.min()} is below -1.0 (pose_spread={pose_spread}, cx={cx}, cy={cy})"
    )


# ===========================================================================
# Property 7: Graph Topology Validation (Task 3.10)
# **Validates: Requirements 4.3, 4.5**
# ===========================================================================

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    invalid_idx=st.integers(min_value=33, max_value=1000)
)
def test_property_7_invalid_node_index_rejected(invalid_idx):
    """
    Property 7: Any graph config with an edge referencing node index >= num_nodes
    must be rejected with GraphConfigError identifying the invalid index.
    **Validates: Requirements 4.3, 4.5**
    """
    config = {
        "num_nodes": 33,
        "node_labels": [f"node_{i}" for i in range(33)],
        "edges": {
            "spatial": [[0, 1], [invalid_idx, 0]],  # invalid_idx >= 33
            "temporal": [],
            "symmetry": [],
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "bad_config.yaml"
        config_path.write_text(yaml.dump(config))

        builder = KeypointGraphBuilder()
        with pytest.raises(GraphConfigError) as exc_info:
            builder.build_from_yaml(config_path)
        assert str(invalid_idx) in str(exc_info.value)


def test_property_7_isolated_node_reports_index(tmp_path):
    """
    Property 7: Graph config with isolated node must be rejected and
    the error message must include the isolated node's index.
    **Validates: Requirements 4.3, 4.5**
    """
    # 5 nodes, but node 4 has no edges
    config = {
        "num_nodes": 5,
        "node_labels": ["a", "b", "c", "d", "isolated"],
        "edges": {
            "spatial": [[0, 1], [1, 2], [2, 3]],  # node 4 isolated
            "temporal": [],
            "symmetry": [],
        },
    }
    config_path = tmp_path / "isolated.yaml"
    config_path.write_text(yaml.dump(config))

    builder = KeypointGraphBuilder()
    with pytest.raises(GraphConfigError) as exc_info:
        builder.build_from_yaml(config_path)
    # Must mention isolated node index 4
    assert "4" in str(exc_info.value)
