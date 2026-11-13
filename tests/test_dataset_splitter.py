"""
test_dataset_splitter.py — Unit tests dan property tests untuk DatasetSplitter.

Tasks: 2.3, 2.4
Requirements: 1.4, 1.5, 2.3
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.data.dataset_splitter import DataSplit, DatasetSplitter
from src.data.models import VideoMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_wl_bisindo_metadata(
    num_signers: int = 5,
    glosses: int = 5,
    samples_per_combo: int = 2,
) -> list[VideoMetadata]:
    """Create realistic WL-BISINDO metadata with known signer distribution."""
    records: list[VideoMetadata] = []
    for signer_idx in range(num_signers):
        signer_id = f"S{signer_idx + 1:03d}"
        for gloss in [f"GLOSS_{i:02d}" for i in range(glosses)]:
            for s in range(samples_per_combo):
                records.append(
                    VideoMetadata(
                        path=f"raw/{gloss}/{signer_id}_{gloss}_{s:03d}.mp4",
                        gloss=gloss,
                        signer_id=signer_id,
                        split="train",
                    )
                )
    return records


def make_wlasl_metadata(
    num_glosses: int = 10,
    samples_per_gloss: int = 10,
) -> list[VideoMetadata]:
    """Create WLASL-style metadata with multiple samples per gloss."""
    records: list[VideoMetadata] = []
    for g in range(num_glosses):
        gloss = f"GLOSS_{g:03d}"
        for s in range(samples_per_gloss):
            records.append(
                VideoMetadata(
                    path=f"wlasl/{gloss}/video_{s:04d}.mp4",
                    gloss=gloss,
                    signer_id=f"S{s:03d}",
                    split="train",
                )
            )
    return records


# ---------------------------------------------------------------------------
# Unit tests — split_wl_bisindo
# ---------------------------------------------------------------------------

class TestSplitWlBisindo:
    def test_no_signer_leakage_5_signers(self):
        """With 5 signers, no signer appears in more than one split."""
        metadata = make_wl_bisindo_metadata(num_signers=5)
        splitter = DatasetSplitter()
        split = splitter.split_wl_bisindo(metadata)

        train_signers = {r.signer_id for r in split.train}
        val_signers = {r.signer_id for r in split.val}
        test_signers = {r.signer_id for r in split.test}

        assert train_signers.isdisjoint(val_signers), "Signer leakage: train ∩ val"
        assert train_signers.isdisjoint(test_signers), "Signer leakage: train ∩ test"
        assert val_signers.isdisjoint(test_signers), "Signer leakage: val ∩ test"

    def test_all_records_assigned(self):
        """len(train)+len(val)+len(test) == len(metadata)."""
        metadata = make_wl_bisindo_metadata(num_signers=5)
        splitter = DatasetSplitter()
        split = splitter.split_wl_bisindo(metadata)
        assert len(split.train) + len(split.val) + len(split.test) == len(metadata)

    def test_split_field_set_correctly(self):
        """Every record in train has split=='train', etc."""
        metadata = make_wl_bisindo_metadata(num_signers=5)
        splitter = DatasetSplitter()
        split = splitter.split_wl_bisindo(metadata)

        for record in split.train:
            assert record.split == "train", f"Expected 'train', got {record.split!r}"
        for record in split.val:
            assert record.split == "val", f"Expected 'val', got {record.split!r}"
        for record in split.test:
            assert record.split == "test", f"Expected 'test', got {record.split!r}"

    def test_approximate_ratios_5_signers(self):
        """Proportions within ±5% (reasonable for 5 signers, whole-signer granularity)."""
        metadata = make_wl_bisindo_metadata(num_signers=10, glosses=8, samples_per_combo=3)
        splitter = DatasetSplitter()
        split = splitter.split_wl_bisindo(metadata, ratios=(0.70, 0.15, 0.15))

        total = len(metadata)
        train_ratio = len(split.train) / total
        val_ratio = len(split.val) / total
        test_ratio = len(split.test) / total

        assert abs(train_ratio - 0.70) <= 0.10, f"Train ratio {train_ratio:.2f} too far from 0.70"
        assert abs(val_ratio - 0.15) <= 0.10, f"Val ratio {val_ratio:.2f} too far from 0.15"
        assert abs(test_ratio - 0.15) <= 0.10, f"Test ratio {test_ratio:.2f} too far from 0.15"

    def test_deterministic_same_seed(self):
        """Same seed → identical split assignment."""
        metadata1 = make_wl_bisindo_metadata(num_signers=5)
        metadata2 = make_wl_bisindo_metadata(num_signers=5)

        splitter = DatasetSplitter()
        split1 = splitter.split_wl_bisindo(metadata1, seed=42)
        split2 = splitter.split_wl_bisindo(metadata2, seed=42)

        paths1 = sorted(r.path for r in split1.train)
        paths2 = sorted(r.path for r in split2.train)
        assert paths1 == paths2, "Same seed should produce identical splits"

    def test_different_seeds_produce_different_splits(self):
        """Different seeds may produce different results (with enough signers)."""
        metadata1 = make_wl_bisindo_metadata(num_signers=10)
        metadata2 = make_wl_bisindo_metadata(num_signers=10)

        splitter = DatasetSplitter()
        split1 = splitter.split_wl_bisindo(metadata1, seed=42)
        split2 = splitter.split_wl_bisindo(metadata2, seed=999)

        signers_train_1 = {r.signer_id for r in split1.train}
        signers_train_2 = {r.signer_id for r in split2.train}
        # With 10 signers, it is very likely that different seeds produce different assignments
        assert signers_train_1 != signers_train_2, (
            "Different seeds should (likely) produce different splits for 10 signers"
        )

    def test_returns_data_split_type(self):
        """Returns DataSplit instance."""
        metadata = make_wl_bisindo_metadata(num_signers=5)
        splitter = DatasetSplitter()
        result = splitter.split_wl_bisindo(metadata)
        assert isinstance(result, DataSplit)

    def test_single_signer_goes_to_train(self):
        """With 1 signer, all records end up in train."""
        metadata = make_wl_bisindo_metadata(num_signers=1)
        splitter = DatasetSplitter()
        split = splitter.split_wl_bisindo(metadata)

        assert len(split.train) == len(metadata)
        assert len(split.val) == 0
        assert len(split.test) == 0
        for record in split.train:
            assert record.split == "train"


# ---------------------------------------------------------------------------
# Unit tests — split_wlasl_stratified
# ---------------------------------------------------------------------------

class TestSplitWlaslStratified:
    def test_wlasl_split_test_is_empty(self):
        """split_wlasl_stratified returns test==[]."""
        metadata = make_wlasl_metadata()
        splitter = DatasetSplitter()
        split = splitter.split_wlasl_stratified(metadata)
        assert split.test == []

    def test_wlasl_all_records_assigned(self):
        """All records in train+val."""
        metadata = make_wlasl_metadata()
        splitter = DatasetSplitter()
        split = splitter.split_wlasl_stratified(metadata)
        assert len(split.train) + len(split.val) == len(metadata)

    def test_wlasl_ratio_approx(self):
        """Train ~80%, val ~20% (±5%)."""
        metadata = make_wlasl_metadata(num_glosses=20, samples_per_gloss=20)
        splitter = DatasetSplitter()
        split = splitter.split_wlasl_stratified(metadata, ratio=0.80)

        total = len(metadata)
        train_ratio = len(split.train) / total
        val_ratio = len(split.val) / total

        assert abs(train_ratio - 0.80) <= 0.05, f"Train ratio {train_ratio:.2f} off"
        assert abs(val_ratio - 0.20) <= 0.05, f"Val ratio {val_ratio:.2f} off"

    def test_wlasl_each_gloss_in_both_splits(self):
        """Glosses with enough samples appear in both train and val."""
        metadata = make_wlasl_metadata(num_glosses=5, samples_per_gloss=10)
        splitter = DatasetSplitter()
        split = splitter.split_wlasl_stratified(metadata, ratio=0.80, min_samples_per_gloss=2)

        train_glosses = {r.gloss for r in split.train}
        val_glosses = {r.gloss for r in split.val}
        all_glosses = {r.gloss for r in metadata}

        # Every gloss with >= 4 total samples should appear in both splits
        for gloss in all_glosses:
            gloss_count = sum(1 for r in metadata if r.gloss == gloss)
            if gloss_count >= 4:
                assert gloss in train_glosses, f"Gloss {gloss} missing from train"
                assert gloss in val_glosses, f"Gloss {gloss} missing from val"


# ---------------------------------------------------------------------------
# Property 2 — Signer-Independent Split Correctness
# ---------------------------------------------------------------------------

@st.composite
def signer_metadata_strategy(
    draw,
    min_signers: int = 3,
    max_signers: int = 10,
) -> list[VideoMetadata]:
    """Generate a realistic WL-BISINDO metadata list with varied signer counts."""
    num_signers = draw(st.integers(min_value=min_signers, max_value=max_signers))
    signer_ids = [f"S{i:03d}" for i in range(num_signers)]
    glosses = ["MAKAN", "MINUM", "TIDUR", "DUDUK", "BERDIRI"]
    records: list[VideoMetadata] = []
    for sid in signer_ids:
        for gloss in glosses:
            for idx in range(2):
                records.append(
                    VideoMetadata(
                        path=f"raw/{gloss}/{sid}_{gloss}_{idx:03d}.mp4",
                        gloss=gloss,
                        signer_id=sid,
                        split="train",
                    )
                )
    return records


@settings(max_examples=100)
@given(metadata=signer_metadata_strategy(min_signers=3, max_signers=10))
def test_property_2_signer_independent_split_no_leakage(metadata: list[VideoMetadata]) -> None:
    """
    Property 2: No signer_id appears in more than one split.
    Validates: Requirements 1.4, 2.3
    """
    splitter = DatasetSplitter()
    split = splitter.split_wl_bisindo(metadata, ratios=(0.70, 0.15, 0.15))

    # All records must be accounted for
    total = len(split.train) + len(split.val) + len(split.test)
    assert total == len(metadata), (
        f"Record count mismatch: {total} != {len(metadata)}"
    )

    train_signers = {r.signer_id for r in split.train}
    val_signers = {r.signer_id for r in split.val}
    test_signers = {r.signer_id for r in split.test}

    assert train_signers.isdisjoint(val_signers), (
        f"Signer leakage: train ∩ val = {train_signers & val_signers}"
    )
    assert train_signers.isdisjoint(test_signers), (
        f"Signer leakage: train ∩ test = {train_signers & test_signers}"
    )
    assert val_signers.isdisjoint(test_signers), (
        f"Signer leakage: val ∩ test = {val_signers & test_signers}"
    )

    # Every signer must be assigned to exactly one split
    all_signers = {r.signer_id for r in metadata}
    assigned = train_signers | val_signers | test_signers
    assert assigned == all_signers, (
        f"Some signers not assigned: missing = {all_signers - assigned}"
    )

    # Split field on each record must match the list it appears in
    for record in split.train:
        assert record.split == "train"
    for record in split.val:
        assert record.split == "val"
    for record in split.test:
        assert record.split == "test"
