"""Metadata contracts and leakage-safe video-level split utilities."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REQUIRED_COLUMNS = (
    "video_id",
    "video_path",
    "label",
    "manipulation_type",
    "identity_group",
    "frame_index",
    "face_path",
    "split",
    "preprocessing_version",
)
VALID_LABELS = frozenset({"real", "fake"})
VALID_SPLITS = frozenset({"train", "val", "test"})


class MetadataValidationError(ValueError):
    """Raised when metadata violates the project data contract."""


@dataclass(frozen=True)
class MetadataRecord:
    video_id: str
    video_path: str
    label: str
    manipulation_type: str
    identity_group: str
    frame_index: int
    face_path: str
    split: str
    preprocessing_version: str

    @classmethod
    def from_row(cls, row: dict[str, str], row_number: int) -> "MetadataRecord":
        missing = [column for column in REQUIRED_COLUMNS if not row.get(column, "").strip()]
        if missing:
            raise MetadataValidationError(
                f"Row {row_number}: missing required values: {', '.join(missing)}"
            )

        try:
            frame_index = int(row["frame_index"])
        except ValueError as exc:
            raise MetadataValidationError(
                f"Row {row_number}: frame_index must be an integer"
            ) from exc

        if frame_index < 0:
            raise MetadataValidationError(
                f"Row {row_number}: frame_index must be non-negative"
            )

        label = row["label"].strip().lower()
        if label not in VALID_LABELS:
            raise MetadataValidationError(
                f"Row {row_number}: label must be one of {sorted(VALID_LABELS)}"
            )

        split = row["split"].strip().lower()
        if split not in VALID_SPLITS:
            raise MetadataValidationError(
                f"Row {row_number}: split must be one of {sorted(VALID_SPLITS)}"
            )

        return cls(
            video_id=row["video_id"].strip(),
            video_path=row["video_path"].strip(),
            label=label,
            manipulation_type=row["manipulation_type"].strip(),
            identity_group=row["identity_group"].strip(),
            frame_index=frame_index,
            face_path=row["face_path"].strip(),
            split=split,
            preprocessing_version=row["preprocessing_version"].strip(),
        )


def validate_records(records: Iterable[MetadataRecord]) -> list[MetadataRecord]:
    """Validate uniqueness and consistency constraints across metadata rows."""

    validated = list(records)
    seen_frames: set[tuple[str, int]] = set()
    video_attributes: dict[str, tuple[str, str]] = {}

    for record in validated:
        frame_key = (record.video_id, record.frame_index)
        if frame_key in seen_frames:
            raise MetadataValidationError(
                f"Duplicate frame row for video_id={record.video_id!r}, "
                f"frame_index={record.frame_index}"
            )
        seen_frames.add(frame_key)

        attributes = (record.label, record.split)
        previous = video_attributes.setdefault(record.video_id, attributes)
        if previous != attributes:
            raise MetadataValidationError(
                f"Video {record.video_id!r} has inconsistent label or split"
            )

    return validated


def load_metadata(path: str | Path) -> list[MetadataRecord]:
    """Load and validate a CSV metadata file."""

    metadata_path = Path(path)
    with metadata_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_columns = tuple(reader.fieldnames or ())
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in actual_columns
        ]
        if missing_columns:
            raise MetadataValidationError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

        records = [
            MetadataRecord.from_row(row, row_number=index)
            for index, row in enumerate(reader, start=2)
        ]

    return validate_records(records)


def assign_video_splits(
    video_ids: Sequence[str],
    *,
    seed: int = 42,
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> dict[str, str]:
    """Assign each source video to exactly one deterministic split."""

    if not video_ids:
        raise ValueError("video_ids must contain at least one value")
    if len(set(video_ids)) != len(video_ids):
        raise ValueError("video_ids must be unique")
    if any(ratio < 0 for ratio in ratios) or sum(ratios) <= 0:
        raise ValueError("ratios must be non-negative and have a positive sum")

    unique_ids = list(video_ids)
    random.Random(seed).shuffle(unique_ids)
    total = sum(ratios)
    train_end = round(len(unique_ids) * ratios[0] / total)
    val_end = train_end + round(len(unique_ids) * ratios[1] / total)

    return {
        video_id: split
        for index, video_id in enumerate(unique_ids)
        for split in (
            "train"
            if index < train_end
            else "val"
            if index < val_end
            else "test",
        )
    }
