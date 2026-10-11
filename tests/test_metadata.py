import csv

import pytest

from src.datasets.metadata import (
    MetadataRecord,
    MetadataValidationError,
    assign_video_splits,
    load_metadata,
    validate_records,
)


def make_record(video_id: str = "video-1", frame_index: int = 0) -> MetadataRecord:
    return MetadataRecord(
        video_id=video_id,
        video_path=f"data/raw/{video_id}.mp4",
        label="fake",
        manipulation_type="face_swap",
        identity_group="identity-1",
        frame_index=frame_index,
        face_path=f"data/faces/{video_id}_{frame_index}.jpg",
        split="train",
        preprocessing_version="v1",
    )


def test_validate_records_rejects_duplicate_frames():
    with pytest.raises(MetadataValidationError, match="Duplicate frame row"):
        validate_records([make_record(), make_record()])


def test_validate_records_rejects_inconsistent_video_attributes():
    second = make_record(frame_index=1)
    second = MetadataRecord(**{**second.__dict__, "split": "test"})

    with pytest.raises(MetadataValidationError, match="inconsistent label or split"):
        validate_records([make_record(), second])


def test_load_metadata_rejects_invalid_label(tmp_path):
    path = tmp_path / "metadata.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "video_id",
                "video_path",
                "label",
                "manipulation_type",
                "identity_group",
                "frame_index",
                "face_path",
                "split",
                "preprocessing_version",
            ),
        )
        writer.writeheader()
        writer.writerow(
            {
                "video_id": "video-1",
                "video_path": "video.mp4",
                "label": "unknown",
                "manipulation_type": "none",
                "identity_group": "identity-1",
                "frame_index": "0",
                "face_path": "face.jpg",
                "split": "train",
                "preprocessing_version": "v1",
            }
        )

    with pytest.raises(MetadataValidationError, match="label must be"):
        load_metadata(path)


def test_assign_video_splits_is_deterministic_and_video_level():
    video_ids = [f"video-{index}" for index in range(20)]
    first = assign_video_splits(video_ids, seed=7)
    second = assign_video_splits(video_ids, seed=7)

    assert first == second
    assert set(first) == set(video_ids)
    assert set(first.values()) == {"train", "val", "test"}


def test_assign_video_splits_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="unique"):
        assign_video_splits(["video-1", "video-1"])
