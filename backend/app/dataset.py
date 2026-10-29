"""Image dataset discovery, validation, deduplication, and splitting."""

from __future__ import annotations

import csv
import hashlib
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from PIL import Image, UnidentifiedImageError
import numpy as np

SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"})
LABELS = {"real": 0, "fake": 1}


@dataclass(frozen=True)
class ImageRecord:
    path: str
    label_name: str
    label: int
    group_id: str
    sha256: str
    width: int
    height: int
    format: str


@dataclass(frozen=True)
class ExcludedImage:
    path: str
    reason: str


@dataclass
class DatasetReport:
    records: list[ImageRecord]
    exclusions: list[ExcludedImage]
    duplicate_paths: list[str]
    content_duplicate_paths: list[str]
    cross_label_duplicate_paths: list[str]

    @property
    def statistics(self) -> dict[str, object]:
        return {
            "valid_images": len(self.records),
            "excluded_images": len(self.exclusions),
            "class_counts": dict(Counter(record.label_name for record in self.records)),
            "group_count": len({record.group_id for record in self.records}),
            "duplicate_files": len(self.duplicate_paths),
            "content_duplicates": len(self.content_duplicate_paths),
            "cross_label_duplicates": len(self.cross_label_duplicate_paths),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pixel_sha256(path: Path) -> str:
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB"))
    return hashlib.sha256(pixels.tobytes()).hexdigest()


def _group_for(path: Path, root: Path, groups: Mapping[str, str] | None) -> str:
    relative = path.relative_to(root).as_posix()
    if groups and relative in groups:
        return groups[relative]
    return relative.rsplit(".", 1)[0]


def scan_dataset(
    root: str | Path,
    *,
    groups: Mapping[str, str] | None = None,
) -> DatasetReport:
    """Scan ``root/real`` and ``root/fake`` without changing labels."""

    dataset_root = Path(root)
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_root}")

    records: list[ImageRecord] = []
    exclusions: list[ExcludedImage] = []
    seen_paths: set[Path] = set()
    seen_hashes: dict[str, str] = {}
    seen_pixel_hashes: dict[str, str] = {}
    duplicate_paths: list[str] = []
    content_duplicate_paths: list[str] = []
    cross_label_duplicate_paths: list[str] = []

    for label_name, label in LABELS.items():
        label_dir = next(
            (candidate for candidate in dataset_root.iterdir()
             if candidate.is_dir() and candidate.name.lower() == label_name),
            dataset_root / label_name,
        )
        if not label_dir.is_dir():
            exclusions.append(ExcludedImage(str(label_dir), f"missing label directory: {label_name}"))
            continue
        for path in sorted(label_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                exclusions.append(ExcludedImage(str(path), "unsupported image format"))
                continue
            resolved = path.resolve()
            if resolved in seen_paths:
                duplicate_paths.append(str(path))
                continue
            seen_paths.add(resolved)
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    image_format = image.format or path.suffix.lstrip(".").upper()
                digest = _sha256(path)
                pixel_digest = _pixel_sha256(path)
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                exclusions.append(ExcludedImage(str(path), f"unreadable or corrupt image: {exc}"))
                continue

            duplicate_of = seen_hashes.get(digest) or seen_pixel_hashes.get(pixel_digest)
            if duplicate_of:
                content_duplicate_paths.append(str(path))
                previous = next(
                    (record for record in records if record.path == duplicate_of),
                    None,
                )
                if previous and previous.label != label:
                    cross_label_duplicate_paths.append(str(path))
                continue
            seen_hashes[digest] = str(path)
            seen_pixel_hashes[pixel_digest] = str(path)
            records.append(
                ImageRecord(
                    path=str(path),
                    label_name=label_name,
                    label=label,
                    group_id=_group_for(path, dataset_root, groups),
                    sha256=digest,
                    width=width,
                    height=height,
                    format=image_format,
                )
            )

    return DatasetReport(
        records,
        exclusions,
        duplicate_paths,
        content_duplicate_paths,
        cross_label_duplicate_paths,
    )


def split_records(
    records: Iterable[ImageRecord],
    *,
    seed: int = 42,
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
) -> dict[str, list[ImageRecord]]:
    """Create deterministic class-aware splits without crossing group IDs."""

    items = list(records)
    if not items:
        raise ValueError("At least one valid image is required")
    if len(ratios) != 3 or any(value <= 0 for value in ratios):
        raise ValueError("ratios must contain three positive values")
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("ratios must sum to 1.0")
    present_labels = {record.label for record in items}
    if present_labels != set(LABELS.values()):
        raise ValueError("both real and fake classes are required for stratified splitting")

    groups: dict[str, list[ImageRecord]] = {}
    for record in items:
        groups.setdefault(record.group_id, []).append(record)
    if len(groups) < 3:
        raise ValueError("at least three groups are required for train, val, and test splits")

    by_label: dict[int, list[list[ImageRecord]]] = {}
    for group_records in groups.values():
        labels = {record.label for record in group_records}
        if len(labels) != 1:
            raise ValueError(f"Group {group_records[0].group_id!r} contains multiple labels")
        by_label.setdefault(next(iter(labels)), []).append(group_records)

    rng = random.Random(seed)
    result = {"train": [], "val": [], "test": []}
    for label_groups in by_label.values():
        rng.shuffle(label_groups)
        count = len(label_groups)
        if count < 3:
            raise ValueError("Each class must have at least three groups for a class-aware split")
        if count == 3:
            train_end, val_end = 1, 2
        else:
            train_end = min(count - 2, max(1, round(count * ratios[0])))
            val_end = min(count - 1, train_end + max(1, round(count * ratios[1])))
            if val_end <= train_end:
                val_end = train_end + 1
        for split, selected in (
            ("train", label_groups[:train_end]),
            ("val", label_groups[train_end:val_end]),
            ("test", label_groups[val_end:]),
        ):
            for group in selected:
                result[split].extend(group)

    if any(not result[split] for split in result):
        raise ValueError("The dataset is insufficient for non-empty train, val, and test splits")
    return result


def write_manifest(path: str | Path, records: Iterable[ImageRecord]) -> None:
    """Write a stable CSV manifest for a split."""

    rows = [asdict(record) for record in records]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ImageRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(rows)
