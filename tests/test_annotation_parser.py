"""
test_annotation_parser.py — Unit tests dan property-based tests untuk AnnotationParser.

Validates: Requirements 1.5, 15.2, 15.3, 15.4
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from src.data.annotation_parser import AnnotationParser, VALID_SPLITS
from src.data.models import VideoMetadata
from src.exceptions import SchemaValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_jsonl(tmp_path: Path, lines: list[dict | str], filename: str = "ann.jsonl") -> Path:
    """Write a list of dicts (or raw strings) to a .jsonl file."""
    p = tmp_path / filename
    with p.open("w", encoding="utf-8") as fh:
        for line in lines:
            if isinstance(line, dict):
                fh.write(json.dumps(line) + "\n")
            else:
                fh.write(line + "\n")
    return p


def valid_record(**overrides) -> dict:
    base = {
        "path": "videos/MAKAN/signer01_001.mp4",
        "gloss": "MAKAN",
        "signer_id": "signer01",
        "split": "train",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Unit tests — load()
# ---------------------------------------------------------------------------

class TestAnnotationParserLoad:

    def test_load_valid_single_record(self, tmp_path):
        p = write_jsonl(tmp_path, [valid_record()])
        parser = AnnotationParser()
        records = parser.load(p)
        assert len(records) == 1
        r = records[0]
        assert r.path == "videos/MAKAN/signer01_001.mp4"
        assert r.gloss == "MAKAN"
        assert r.signer_id == "signer01"
        assert r.split == "train"

    def test_load_all_valid_splits(self, tmp_path):
        rows = [valid_record(split=s) for s in ["train", "val", "test"]]
        p = write_jsonl(tmp_path, rows)
        parser = AnnotationParser()
        records = parser.load(p)
        assert len(records) == 3
        splits = {r.split for r in records}
        assert splits == {"train", "val", "test"}

    def test_load_optional_fields_present(self, tmp_path):
        row = valid_record()
        row.update({"duration_sec": 2.5, "resolution": "640x480", "fps": 30.0})
        p = write_jsonl(tmp_path, [row])
        parser = AnnotationParser()
        records = parser.load(p)
        r = records[0]
        assert r.duration_sec == pytest.approx(2.5)
        assert r.resolution == "640x480"
        assert r.fps == pytest.approx(30.0)

    def test_load_optional_fields_absent(self, tmp_path):
        p = write_jsonl(tmp_path, [valid_record()])
        parser = AnnotationParser()
        records = parser.load(p)
        r = records[0]
        assert r.duration_sec is None
        assert r.resolution is None
        assert r.fps is None

    def test_load_skips_blank_lines(self, tmp_path):
        content = (
            json.dumps(valid_record(split="train")) + "\n"
            + "\n"
            + json.dumps(valid_record(split="val")) + "\n"
        )
        p = tmp_path / "ann.jsonl"
        p.write_text(content, encoding="utf-8")
        parser = AnnotationParser()
        records = parser.load(p)
        assert len(records) == 2

    def test_load_multiple_records(self, tmp_path):
        rows = [valid_record(signer_id=f"signer{i:02d}", split="train") for i in range(10)]
        p = write_jsonl(tmp_path, rows)
        parser = AnnotationParser()
        records = parser.load(p)
        assert len(records) == 10

    def test_load_integer_duration_converted_to_float(self, tmp_path):
        row = valid_record()
        row["duration_sec"] = 3  # integer, bukan float
        p = write_jsonl(tmp_path, [row])
        parser = AnnotationParser()
        records = parser.load(p)
        assert isinstance(records[0].duration_sec, float)
        assert records[0].duration_sec == pytest.approx(3.0)

    # ------------------------------------------------------------------
    # Error cases — field wajib hilang
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("missing_field", ["path", "gloss", "signer_id", "split"])
    def test_load_raises_when_required_field_missing(self, tmp_path, missing_field):
        row = valid_record()
        del row[missing_field]
        p = write_jsonl(tmp_path, [row])
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.field_name == missing_field
        assert err.line_number == 1
        assert p.name in str(err)

    def test_load_raises_correct_line_number(self, tmp_path):
        """Baris ke-3 yang bermasalah harus melaporkan line_number=3."""
        rows = [
            valid_record(split="train"),
            valid_record(split="val"),
            valid_record(),   # akan dimodifikasi di bawah
        ]
        rows[2] = {k: v for k, v in rows[2].items() if k != "gloss"}
        p = write_jsonl(tmp_path, rows)
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        assert exc_info.value.line_number == 3

    def test_load_raises_when_split_invalid(self, tmp_path):
        row = valid_record(split="unknown")
        p = write_jsonl(tmp_path, [row])
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.field_name == "split"
        assert err.found_value == "unknown"
        assert err.line_number == 1

    def test_load_raises_when_required_field_not_string(self, tmp_path):
        row = valid_record()
        row["path"] = 123  # integer, bukan string
        p = write_jsonl(tmp_path, [row])
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.field_name == "path"
        assert err.found_value == 123

    def test_load_raises_on_invalid_json(self, tmp_path):
        p = write_jsonl(tmp_path, ["not valid json {{{"])
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.field_name == "<json>"
        assert err.line_number == 1

    def test_load_raises_on_json_array_instead_of_object(self, tmp_path):
        p = write_jsonl(tmp_path, ['["train", "MAKAN"]'])
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.field_name == "<root>"

    def test_load_error_contains_filename(self, tmp_path):
        row = valid_record(split="bad_split")
        p = write_jsonl(tmp_path, [row], filename="my_annotations.jsonl")
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        assert "my_annotations.jsonl" in str(exc_info.value)

    def test_load_raises_filenotfounderror_for_missing_file(self, tmp_path):
        parser = AnnotationParser()
        with pytest.raises(FileNotFoundError):
            parser.load(tmp_path / "nonexistent.jsonl")

    # ------------------------------------------------------------------
    # SchemaValidationError attributes
    # ------------------------------------------------------------------

    def test_schema_error_attributes(self, tmp_path):
        row = valid_record(split="invalid_split")
        p = write_jsonl(tmp_path, [row], filename="test_attrs.jsonl")
        parser = AnnotationParser()
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.load(p)
        err = exc_info.value
        assert err.file_path.name == "test_attrs.jsonl"
        assert err.field_name == "split"
        assert err.found_value == "invalid_split"
        assert err.line_number == 1


# ---------------------------------------------------------------------------
# Unit tests — save()
# ---------------------------------------------------------------------------

class TestAnnotationParserSave:

    def test_save_produces_valid_jsonl(self, tmp_path):
        records = [
            VideoMetadata(path="a.mp4", gloss="MAKAN", signer_id="s1", split="train"),
            VideoMetadata(path="b.mp4", gloss="MINUM", signer_id="s2", split="val"),
        ]
        p = tmp_path / "out.jsonl"
        parser = AnnotationParser()
        parser.save(records, p)

        lines = p.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)  # tidak boleh raise
            assert isinstance(obj, dict)

    def test_save_omits_none_optional_fields(self, tmp_path):
        record = VideoMetadata(path="a.mp4", gloss="MAKAN", signer_id="s1", split="train")
        p = tmp_path / "out.jsonl"
        parser = AnnotationParser()
        parser.save([record], p)
        obj = json.loads(p.read_text(encoding="utf-8").strip())
        assert "duration_sec" not in obj
        assert "resolution" not in obj
        assert "fps" not in obj

    def test_save_includes_optional_fields_when_set(self, tmp_path):
        record = VideoMetadata(
            path="a.mp4", gloss="MAKAN", signer_id="s1", split="train",
            duration_sec=3.0, resolution="640x480", fps=30.0,
        )
        p = tmp_path / "out.jsonl"
        parser = AnnotationParser()
        parser.save([record], p)
        obj = json.loads(p.read_text(encoding="utf-8").strip())
        assert obj["duration_sec"] == pytest.approx(3.0)
        assert obj["resolution"] == "640x480"
        assert obj["fps"] == pytest.approx(30.0)

    def test_save_creates_parent_directories(self, tmp_path):
        nested = tmp_path / "a" / "b" / "annotations.jsonl"
        records = [VideoMetadata(path="a.mp4", gloss="MAKAN", signer_id="s1", split="train")]
        parser = AnnotationParser()
        parser.save(records, nested)
        assert nested.exists()

    def test_save_empty_list(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        parser = AnnotationParser()
        parser.save([], p)
        assert p.read_text(encoding="utf-8") == ""

    def test_save_required_fields_present(self, tmp_path):
        record = VideoMetadata(path="x.mp4", gloss="TIDUR", signer_id="s3", split="test")
        p = tmp_path / "out.jsonl"
        parser = AnnotationParser()
        parser.save([record], p)
        obj = json.loads(p.read_text(encoding="utf-8").strip())
        assert obj["path"] == "x.mp4"
        assert obj["gloss"] == "TIDUR"
        assert obj["signer_id"] == "s3"
        assert obj["split"] == "test"


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

class TestAnnotationRoundTrip:

    def test_round_trip_required_fields_identical(self, tmp_path):
        original = [
            VideoMetadata(path="a/b.mp4", gloss="MAKAN", signer_id="s01", split="train"),
            VideoMetadata(path="c/d.mp4", gloss="MINUM", signer_id="s02", split="val"),
            VideoMetadata(path="e/f.mp4", gloss="TIDUR", signer_id="s03", split="test"),
        ]
        p = tmp_path / "roundtrip.jsonl"
        parser = AnnotationParser()
        parser.save(original, p)
        loaded = parser.load(p)

        assert len(loaded) == len(original)
        for orig, loaded_r in zip(original, loaded):
            assert loaded_r.path == orig.path
            assert loaded_r.gloss == orig.gloss
            assert loaded_r.signer_id == orig.signer_id
            assert loaded_r.split == orig.split

    def test_round_trip_with_optional_fields(self, tmp_path):
        record = VideoMetadata(
            path="v.mp4", gloss="DUDUK", signer_id="s04", split="test",
            duration_sec=4.1, resolution="1280x720", fps=25.0,
        )
        p = tmp_path / "with_optional.jsonl"
        parser = AnnotationParser()
        parser.save([record], p)
        loaded = parser.load(p)
        r = loaded[0]
        assert r.duration_sec == pytest.approx(record.duration_sec)
        assert r.resolution == record.resolution
        assert r.fps == pytest.approx(record.fps)


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# Validates: Requirements 1.5, 15.4, 15.5 (Property 3: Annotation Round-Trip)
# ---------------------------------------------------------------------------

# Strategi untuk string path yang sederhana (hindari karakter NUL yang tidak valid di JSON)
_path_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters=("\x00",)),
    min_size=1,
    max_size=200,
)

_gloss_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters=("\x00",)),
    min_size=1,
    max_size=100,
)

_signer_id_strategy = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters=("\x00",)),
    min_size=1,
    max_size=50,
)

_split_strategy = st.sampled_from(sorted(VALID_SPLITS))

_video_metadata_strategy = st.builds(
    VideoMetadata,
    path=_path_strategy,
    gloss=_gloss_strategy,
    signer_id=_signer_id_strategy,
    split=_split_strategy,
    duration_sec=st.one_of(st.none(), st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False)),
    resolution=st.one_of(st.none(), st.from_regex(r"\d{2,4}x\d{2,4}", fullmatch=True)),
    fps=st.one_of(st.none(), st.floats(min_value=1.0, max_value=240.0, allow_nan=False, allow_infinity=False)),
)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(records=st.lists(_video_metadata_strategy, min_size=1, max_size=20))
def test_property_annotation_round_trip(tmp_path_factory, records):
    """
    Property 3: Annotation Round-Trip

    Untuk sembarang VideoMetadata yang valid, serialize → deserialize harus
    menghasilkan objek dengan nilai identik pada semua field wajib.

    Validates: Requirements 1.5, 15.4, 15.5
    """
    tmp_path = tmp_path_factory.mktemp("pbt")
    p = tmp_path / "pbt.jsonl"
    parser = AnnotationParser()
    parser.save(records, p)
    loaded = parser.load(p)

    assert len(loaded) == len(records)
    for orig, result in zip(records, loaded):
        assert result.path == orig.path, f"path mismatch: {result.path!r} != {orig.path!r}"
        assert result.gloss == orig.gloss, f"gloss mismatch: {result.gloss!r} != {orig.gloss!r}"
        assert result.signer_id == orig.signer_id, f"signer_id mismatch: {result.signer_id!r} != {orig.signer_id!r}"
        assert result.split == orig.split, f"split mismatch: {result.split!r} != {orig.split!r}"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    path_val=_path_strategy,
    gloss_val=_gloss_strategy,
    signer_id_val=_signer_id_strategy,
)
def test_property_invalid_split_raises_schema_error(tmp_path_factory, path_val, gloss_val, signer_id_val):
    """
    Property 18 (partial): AnnotationParser harus raise SchemaValidationError
    untuk setiap record dengan split yang bukan "train", "val", atau "test".

    Validates: Requirements 15.2, 15.3
    """
    tmp_path = tmp_path_factory.mktemp("pbt_invalid")
    row = {
        "path": path_val,
        "gloss": gloss_val,
        "signer_id": signer_id_val,
        "split": "invalid_split_xyz",
    }
    p = tmp_path / "invalid.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

    parser = AnnotationParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)

    err = exc_info.value
    assert err.field_name == "split"
    assert err.found_value == "invalid_split_xyz"
    assert err.line_number == 1


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    missing_field=st.sampled_from(sorted(["path", "gloss", "signer_id", "split"])),
    path_val=_path_strategy,
    gloss_val=_gloss_strategy,
    signer_id_val=_signer_id_strategy,
    split_val=_split_strategy,
)
def test_property_missing_required_field_raises_schema_error(
    tmp_path_factory, missing_field, path_val, gloss_val, signer_id_val, split_val
):
    """
    Property 18 (partial): AnnotationParser harus raise SchemaValidationError
    untuk record yang tidak memiliki salah satu field wajib.

    Validates: Requirements 15.2, 15.3
    """
    tmp_path = tmp_path_factory.mktemp("pbt_missing")
    row = {
        "path": path_val,
        "gloss": gloss_val,
        "signer_id": signer_id_val,
        "split": split_val,
    }
    del row[missing_field]

    p = tmp_path / "missing.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

    parser = AnnotationParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)

    err = exc_info.value
    assert err.field_name == missing_field
    assert err.line_number == 1
