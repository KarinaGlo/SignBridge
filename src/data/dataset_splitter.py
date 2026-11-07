"""
dataset_splitter.py — Splitting dataset WL-BISINDO dan WLASL.
Requirements: 1.4, 1.5, 2.3
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.data.models import VideoMetadata


@dataclass
class DataSplit:
    train: list[VideoMetadata]
    val: list[VideoMetadata]
    test: list[VideoMetadata] = field(default_factory=list)


class DatasetSplitter:
    """Split dataset dengan stratifikasi signer-independent (WL-BISINDO) atau per-gloss (WLASL)."""

    # ------------------------------------------------------------------
    # WL-BISINDO — signer-independent split
    # ------------------------------------------------------------------

    def split_wl_bisindo(
        self,
        metadata: list[VideoMetadata],
        ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
        seed: int = 42,
    ) -> DataSplit:
        """
        Signer-independent split for WL-BISINDO.

        Algorithm:
        1. Group videos by signer_id.
        2. Sort signer IDs, then shuffle deterministically with `seed`.
        3. Walk through shuffled signers; once cumulative record count >= target
           for a bucket, move to next bucket.
        4. Mutate each VideoMetadata.split field to "train"/"val"/"test".
        5. Return DataSplit.

        Requirements 1.4: Each signer_id appears in EXACTLY ONE split.

        Edge cases:
        - 0 records  → empty DataSplit
        - 1 signer   → all records go to train; val and test are empty
        - 2 signers  → first signer → train, second → val; test is empty
        """
        if not metadata:
            return DataSplit(train=[], val=[], test=[])

        # --- Normalise ratios so they sum to exactly 1.0 -----------------
        total_ratio = sum(ratios)
        r_train, r_val, r_test = (r / total_ratio for r in ratios)

        # --- Group by signer_id ------------------------------------------
        signer_to_records: dict[str, list[VideoMetadata]] = defaultdict(list)
        for record in metadata:
            signer_to_records[record.signer_id].append(record)

        # --- Sort + shuffle -----------------------------------------------
        signer_ids: list[str] = sorted(signer_to_records.keys())
        rng = random.Random(seed)
        rng.shuffle(signer_ids)

        # --- Edge cases: very few signers ---------------------------------
        n_signers = len(signer_ids)
        if n_signers == 1:
            # All records in train
            for record in metadata:
                record.split = "train"
            return DataSplit(
                train=list(metadata),
                val=[],
                test=[],
            )
        if n_signers == 2:
            # First signer → train, second → val
            train_records: list[VideoMetadata] = []
            val_records: list[VideoMetadata] = []
            for record in signer_to_records[signer_ids[0]]:
                record.split = "train"
                train_records.append(record)
            for record in signer_to_records[signer_ids[1]]:
                record.split = "val"
                val_records.append(record)
            return DataSplit(train=train_records, val=val_records, test=[])

        # --- General case: >= 3 signers -----------------------------------
        total_records = len(metadata)
        target_train = r_train * total_records
        target_val   = (r_train + r_val) * total_records  # cumulative threshold

        buckets: list[str] = ["train", "val", "test"]
        split_map: dict[str, str] = {}  # signer_id → split name
        cumulative = 0.0

        for sid in signer_ids:
            n = len(signer_to_records[sid])
            # Decide bucket based on cumulative BEFORE adding current signer
            if cumulative < target_train:
                split_name = "train"
            elif cumulative < target_val:
                split_name = "val"
            else:
                split_name = "test"
            split_map[sid] = split_name
            cumulative += n

        # --- Assign split field and build result lists --------------------
        train_list: list[VideoMetadata] = []
        val_list: list[VideoMetadata] = []
        test_list: list[VideoMetadata] = []

        for sid, records in signer_to_records.items():
            split_name = split_map[sid]
            for record in records:
                record.split = split_name
            if split_name == "train":
                train_list.extend(records)
            elif split_name == "val":
                val_list.extend(records)
            else:
                test_list.extend(records)

        return DataSplit(train=train_list, val=val_list, test=test_list)

    # ------------------------------------------------------------------
    # WLASL — stratified split per gloss
    # ------------------------------------------------------------------

    def split_wlasl_stratified(
        self,
        metadata: list[VideoMetadata],
        ratio: float = 0.80,
        min_samples_per_gloss: int = 2,
        seed: int = 42,
    ) -> DataSplit:
        """
        Stratified split for WLASL, per-gloss.

        Algorithm:
        1. Group videos by gloss.
        2. For each gloss: shuffle videos with seed, assign first floor(n*ratio) to train,
           remainder to val.
        3. If a gloss has fewer than 2*min_samples_per_gloss total, put all in train.
        4. Return DataSplit(train=..., val=..., test=[]).

        Requirements 2.3: Each gloss has >= min_samples_per_gloss in each split
        (when gloss has enough samples).
        """
        gloss_to_records: dict[str, list[VideoMetadata]] = defaultdict(list)
        for record in metadata:
            gloss_to_records[record.gloss].append(record)

        rng = random.Random(seed)
        train_list: list[VideoMetadata] = []
        val_list: list[VideoMetadata] = []

        for gloss, records in sorted(gloss_to_records.items()):
            # Shuffle within each gloss using the shared rng for determinism
            shuffled = list(records)
            rng.shuffle(shuffled)

            n = len(shuffled)
            threshold = 2 * min_samples_per_gloss  # need at least 2 samples per split

            if n < threshold:
                # Too few samples — all go to train
                for record in shuffled:
                    record.split = "train"
                    train_list.append(record)
            else:
                n_train = math.floor(n * ratio)
                # Guarantee at least min_samples_per_gloss in each split
                n_train = max(n_train, min_samples_per_gloss)
                n_train = min(n_train, n - min_samples_per_gloss)

                for record in shuffled[:n_train]:
                    record.split = "train"
                    train_list.append(record)
                for record in shuffled[n_train:]:
                    record.split = "val"
                    val_list.append(record)

        return DataSplit(train=train_list, val=val_list, test=[])
