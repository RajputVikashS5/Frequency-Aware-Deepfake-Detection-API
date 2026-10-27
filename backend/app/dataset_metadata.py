"""Validation of provenance and group metadata for local image datasets."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SOURCE_FIELDS = (
    "name",
    "version",
    "source_url",
    "license_or_access_terms",
    "permitted_intended_use",
    "date_obtained",
    "label_definitions",
    "data_type",
    "video_derived",
    "grouping_policy",
    "limitations_bias_notes",
)


@dataclass(frozen=True)
class MetadataValidation:
    metadata: dict[str, object]
    groups: dict[str, str]
    warnings: tuple[str, ...]


def _read_source(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("dataset-source.json is required")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid dataset-source.json: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("dataset-source.json must contain a JSON object")
    missing = [field for field in REQUIRED_SOURCE_FIELDS if not value.get(field)]
    if missing:
        raise ValueError(f"dataset-source.json missing required fields: {', '.join(missing)}")
    if value["data_type"] != "image":
        raise ValueError("dataset-source.json data_type must be 'image'")
    if not isinstance(value["label_definitions"], dict):
        raise ValueError("label_definitions must be an object")
    return value


def _read_groups(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not {"path", "group_id"}.issubset(reader.fieldnames or ()):
            raise ValueError("groups.csv must contain path and group_id columns")
        groups: dict[str, str] = {}
        for row in reader:
            image_path = (row.get("path") or "").replace("\\", "/").strip()
            group_id = (row.get("group_id") or "").strip()
            if not image_path or not group_id:
                raise ValueError("groups.csv cannot contain blank path or group_id")
            if image_path in groups and groups[image_path] != group_id:
                raise ValueError(f"groups.csv maps {image_path} to multiple groups")
            groups[image_path] = group_id
        return groups


def validate_dataset_metadata(
    root: str | Path,
    *,
    dataset_kind: str | None = None,
) -> MetadataValidation:
    dataset_root = Path(root)
    metadata = _read_source(dataset_root / "dataset-source.json")
    groups_path = dataset_root / "groups.csv"
    groups = _read_groups(groups_path)
    warnings: list[str] = []
    if dataset_kind == "forgerynet" or "forgerynet" in str(metadata["name"]).lower():
        if metadata["video_derived"] is not True:
            raise ValueError("ForgeryNet metadata must set video_derived=true")
        if not groups:
            raise ValueError("ForgeryNet requires groups.csv with every image mapped")
    if dataset_kind == "cifake" or "cifake" in str(metadata["name"]).lower():
        if not str(metadata["grouping_policy"]).strip():
            raise ValueError("CIFAKE requires a documented grouping policy")
        if not groups:
            warnings.append("No source identity metadata; each image will use its own group.")
    return MetadataValidation(metadata, groups, tuple(warnings))
