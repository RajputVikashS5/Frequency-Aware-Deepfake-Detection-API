"""Read-only, paginated inventory of FaceForensics++ and CIFAKE objects in R2."""

from __future__ import annotations

import argparse
import csv
import io
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .config import settings
from .r2 import R2ArtifactStore
from .r2_verify import dataset_prefixes, validate_configuration

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | {".mp4"}
KNOWN_EXTENSIONS = MEDIA_EXTENSIONS | {".csv"}
_TRANSIENT_CODES = {"SlowDown", "RequestTimeout", "InternalError", "503", "500"}


@dataclass(frozen=True)
class ObjectListing:
    keys: tuple[str, ...]
    completed: bool
    truncated_by_limit: bool
    warnings: tuple[str, ...] = ()


@dataclass
class FaceForensicsMetadataReport:
    """Conservative CSV inspection result; unknown columns are never guessed."""

    headers: list[str]
    rows: int
    records: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_faceforensicspp_video_manifest(
    data: bytes,
    name: str,
    *,
    available_keys: Iterable[str] = (),
) -> dict[str, object]:
    """Parse the verified FaceForensics++ ``File Path``/``Label`` CSV shape.

    Other CSV shapes are returned as an inspection-only result and are not
    assigned labels.
    """

    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    headers = reader.fieldnames or []
    normalized = {
        header.strip().lower().replace("-", "_").replace(" ", "_"): header
        for header in headers
    }
    path_column = normalized.get("file_path") or normalized.get("filepath")
    label_column = normalized.get("label") or normalized.get("class")
    if not path_column or not label_column:
        return {
            "metadata_source": name,
            "records": [],
            "unmatched_metadata_entries": [],
            "videos_without_metadata": [],
            "duplicate_entries": [],
            "ambiguous_labels": [],
            "warnings": ["CSV does not have a recognized File Path and Label schema"],
        }

    available = {key.replace("\\", "/") for key in available_keys}
    records: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    ambiguous: list[str] = []
    unmatched: list[str] = []
    for row in reader:
        object_key = (row.get(path_column) or "").replace("\\", "/").strip()
        label = (row.get(label_column) or "").strip().lower()
        if not object_key:
            continue
        if label not in {"real", "fake"}:
            ambiguous.append(object_key)
            continue
        if object_key in seen:
            duplicates.append(object_key)
            if seen[object_key] != label:
                ambiguous.append(object_key)
            continue
        seen[object_key] = label
        if available and object_key not in available and f"faceforensics++/{object_key}" not in available:
            unmatched.append(object_key)
        parts = [part for part in object_key.split("/") if part]
        records.append({
            "dataset": "faceforensicspp",
            "object_key": object_key,
            "media_type": "video",
            "label": label,
            "manipulation_type": "" if parts[0].lower() == "original" else parts[0] if parts else "",
            "partition": "",
            "source_video_id": Path(object_key).stem,
            "metadata_source": name,
        })
    video_keys = {
        key for key in available
        if Path(key).suffix.lower() == ".mp4"
    }
    matched = {record["object_key"] for record in records}
    videos_without_metadata = sorted(
        key for key in video_keys
        if key not in matched and key.removeprefix("faceforensics++/") not in matched
    )
    return {
        "metadata_source": name,
        "records": records,
        "unmatched_metadata_entries": sorted(set(unmatched)),
        "videos_without_metadata": videos_without_metadata,
        "duplicate_entries": sorted(set(duplicates)),
        "ambiguous_labels": sorted(set(ambiguous)),
        "warnings": [],
    }


def _is_transient(exc: Exception) -> bool:
    code = str(getattr(exc, "response", {}).get("Error", {}).get("Code", ""))
    return code in _TRANSIENT_CODES or isinstance(exc, (TimeoutError, ConnectionError))


def _list_objects(
    client: Any,
    bucket: str,
    prefix: str,
    max_objects: int,
    *,
    retries: int = 2,
    sleep: Any = time.sleep,
) -> ObjectListing:
    if max_objects < 1:
        raise ValueError("max_objects must be positive")
    keys: list[str] = []
    warnings: list[str] = []
    request: dict[str, object] = {
        "Bucket": bucket,
        "Prefix": prefix,
        "MaxKeys": min(max_objects, 1000),
    }
    while len(keys) < max_objects:
        response: dict[str, Any] | None = None
        for attempt in range(retries + 1):
            try:
                response = client.list_objects_v2(**request)
                break
            except Exception as exc:
                if not _is_transient(exc) or attempt == retries:
                    warnings.append(f"listing failed after {attempt + 1} attempt(s): {type(exc).__name__}")
                    return ObjectListing(tuple(keys), False, False, tuple(warnings))
                sleep(0.1 * (2**attempt))
        if response is None:
            return ObjectListing(tuple(keys), False, False, tuple(warnings))

        contents = response.get("Contents") or []
        for item in contents:
            key = item.get("Key")
            if key:
                keys.append(str(key))
                if len(keys) == max_objects:
                    break

        is_truncated = bool(response.get("IsTruncated"))
        if len(keys) >= max_objects:
            # A full final page is complete; only a truncated service response
            # means that the configured bound hid additional objects.
            limited = is_truncated
            return ObjectListing(tuple(keys[:max_objects]), not limited, limited, tuple(warnings))
        if not is_truncated:
            return ObjectListing(tuple(keys), True, False, tuple(warnings))
        token = response.get("NextContinuationToken")
        if not token:
            warnings.append("R2 reported a truncated page without a continuation token")
            return ObjectListing(tuple(keys), False, False, tuple(warnings))
        request = {
            "Bucket": bucket,
            "Prefix": prefix,
            "MaxKeys": min(max_objects - len(keys), 1000),
            "ContinuationToken": token,
        }
    return ObjectListing(tuple(keys), True, False, tuple(warnings))


def list_bounded_objects(client: Any, bucket: str, prefix: str, max_objects: int) -> list[str]:
    """Compatibility wrapper returning only keys."""

    return list(_list_objects(client, bucket, prefix, max_objects).keys)


def _relative_key(key: str, prefix: str) -> str:
    return key[len(prefix):].lstrip("/") if key.startswith(prefix) else key


def _cifake_location(relative: str) -> tuple[str | None, str | None]:
    parts = [part for part in relative.split("/") if part]
    partition_index = next(
        (index for index, part in enumerate(parts) if part.lower() in {"train", "test"}),
        None,
    )
    if partition_index is None:
        return None, None
    label = next(
        (part.lower() for part in parts[partition_index + 1:] if part.lower() in {"real", "fake"}),
        None,
    )
    return parts[partition_index].lower(), label


def _cifake_report(keys: Iterable[str], prefix: str) -> dict[str, object]:
    partitions: dict[str, Counter[str]] = {"train": Counter(), "test": Counter()}
    representatives: dict[str, list[str]] = {}
    unknown_objects = 0
    recognized_images = 0
    for key in keys:
        relative = _relative_key(key, prefix)
        extension = Path(key).suffix.lower()
        partition, label = _cifake_location(relative)
        if extension in IMAGE_EXTENSIONS and partition in partitions and label in {"real", "fake"}:
            recognized_images += 1
            partitions[partition][label] += 1
            representative_key = f"{partition}/{label}"
            representatives.setdefault(representative_key, [])
            if len(representatives[representative_key]) < 3:
                representatives[representative_key].append(key)
        else:
            unknown_objects += 1
    recognized_total = sum(sum(values.values()) for values in partitions.values())
    return {
        "partition_label_counts": {
            partition: dict(sorted(counts.items())) for partition, counts in partitions.items()
        },
        "recognized_image_objects": recognized_images,
        "class_totals_reconcile": recognized_total == recognized_images,
        "representative_keys": representatives,
        "unknown_or_unclassified_objects": unknown_objects,
    }


def build_cifake_image_manifest(keys: Iterable[str], prefix: str) -> list[dict[str, str]]:
    """Create stable, deduplicated object-key records for verified CIFAKE images."""

    records: dict[str, dict[str, str]] = {}
    for key in sorted(set(keys)):
        relative = _relative_key(key, prefix)
        partition, label = _cifake_location(relative)
        if Path(key).suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if partition not in {"train", "test"} or label not in {"real", "fake"}:
            continue
        records[key] = {
            "dataset": "cifake",
            "object_key": key,
            "media_type": "image",
            "label": label,
            "manipulation_type": "",
            "partition": partition,
            "source_video_id": "",
            "metadata_source": "verified object-key layout",
        }
    return list(records.values())


def write_object_manifest(path: str | Path, records: Iterable[dict[str, str]]) -> None:
    """Write a deterministic CSV manifest without image/video downloads."""

    fields = [
        "dataset", "object_key", "media_type", "label", "manipulation_type",
        "partition", "source_video_id", "metadata_source",
    ]
    rows = sorted(records, key=lambda row: row.get("object_key", ""))
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def _video_dataset_report(keys: Iterable[str], prefix: str) -> dict[str, object]:
    relative_keys = [_relative_key(key, prefix) for key in keys]
    media = [value for value in relative_keys if Path(value).suffix.lower() in MEDIA_EXTENSIONS]
    original = sum(value.lower().startswith("original/") for value in media)
    csv_count = sum(Path(value).suffix.lower() == ".csv" for value in relative_keys)
    manipulation_counts: Counter[str] = Counter()
    for value in media:
        parts = [part for part in value.split("/") if part]
        if parts and parts[0].lower() not in {"original", "csv"}:
            manipulation_counts[parts[0]] += 1
    return {
        "manipulation_folders": sorted(manipulation_counts),
        "manipulation_type_counts": dict(sorted(manipulation_counts.items())),
        "original_videos": original,
        "manipulated_videos": sum(manipulation_counts.values()),
        "csv_metadata_files": csv_count,
        "media_files": len(media),
    }


def inventory_dataset(
    client: Any,
    bucket: str,
    dataset: str,
    prefix: str,
    max_objects: int,
) -> dict[str, object]:
    listing = _list_objects(client, bucket, prefix, max_objects)
    keys = listing.keys
    extensions = Counter(Path(key).suffix.lower() or "<none>" for key in keys)
    report: dict[str, object] = {
        "dataset": dataset,
        "prefix": prefix,
        "objects_scanned": len(keys),
        "completed": listing.completed,
        "truncated_by_limit": listing.truncated_by_limit,
        "extensions": dict(sorted(extensions.items())),
        "unknown_or_unclassified_objects": 0,
        "warnings": list(listing.warnings),
    }
    if dataset.lower() == "cifake":
        report.update(_cifake_report(keys, prefix))
    elif dataset.lower() == "faceforensicspp":
        report.update(_video_dataset_report(keys, prefix))
        report["unknown_or_unclassified_objects"] = sum(
            1 for key in keys
            if Path(key).suffix.lower() not in MEDIA_EXTENSIONS | {".csv"}
        )
    else:
        raise ValueError(f"unsupported dataset: {dataset}")
    if listing.truncated_by_limit:
        report["warnings"].append("Counts are partial because max_objects stopped a truncated listing")
    return report


def inspect_csv(path: Path, preview_rows: int = 5) -> dict[str, object]:
    return inspect_csv_bytes(path.read_bytes(), str(path), preview_rows)


def inspect_csv_bytes(data: bytes, name: str, preview_rows: int = 5) -> dict[str, object]:
    reader = csv.reader(io.StringIO(data.decode("utf-8-sig")))
    headers = next(reader, [])
    rows = [row for _, row in zip(range(preview_rows), reader)]
    if not headers:
        raise ValueError(f"CSV has no header: {name}")
    return {"path": name, "headers": headers, "preview": rows}


def parse_faceforensicspp_csv_bytes(
    data: bytes,
    name: str,
    *,
    preview_rows: int = 5,
) -> FaceForensicsMetadataReport:
    """Parse metadata without assigning semantics to unknown columns."""

    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    headers = reader.fieldnames or []
    if not headers:
        raise ValueError(f"CSV has no header: {name}")
    records = []
    rows = 0
    for row in reader:
        rows += 1
        if len(records) < preview_rows:
            records.append({key: value or "" for key, value in row.items()})
    normalized = {header.strip().lower().replace("-", "_").replace(" ", "_") for header in headers}
    warnings = []
    if not any("video" in header or "filename" in header or "file" in header for header in normalized):
        warnings.append("No obvious video/file column; label mapping was not attempted")
    if not any("label" in header or "class" in header or "manip" in header for header in normalized):
        warnings.append("No obvious label/manipulation column; labels remain unknown")
    return FaceForensicsMetadataReport(headers, rows, records, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("faceforensicspp", "cifake"), required=True)
    parser.add_argument("--max-objects", type=int, default=1000)
    parser.add_argument("--inspect-csv", type=Path, action="append", default=[])
    parser.add_argument("--csv-key", action="append", default=[])
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--preview-rows", type=int, default=5)
    args = parser.parse_args()
    try:
        for path in args.inspect_csv:
            result = inspect_csv(path, args.preview_rows)
            print(f"CSV: {result['path']}")
            print(f"Headers: {', '.join(result['headers'])}")
            for row in result["preview"]:
                print("  " + " | ".join(row))
        validate_configuration(settings)
        client = R2ArtifactStore(settings)._get_client()
        for key in args.csv_key:
            prefix = dataset_prefixes(settings)["faceforensicspp"]
            if not key.startswith(prefix + "csv/") or not key.lower().endswith(".csv"):
                raise ValueError("--csv-key must be a CSV object under faceforensics++/csv/")
            response = client.get_object(Bucket=settings.r2_bucket, Key=key)
            data = response["Body"].read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("CSV preview exceeds the 2 MiB bounded inspection limit")
            result = inspect_csv_bytes(data, key, args.preview_rows)
            print(f"CSV: {result['path']}")
            print(f"Headers: {', '.join(result['headers'])}")
            for row in result["preview"]:
                print("  " + " | ".join(row))
        prefix = dataset_prefixes(settings)[args.dataset]
        report = inventory_dataset(client, settings.r2_bucket, args.dataset, prefix, args.max_objects)
        if args.manifest_output:
            if args.dataset != "cifake":
                raise ValueError("--manifest-output currently supports only cifake")
            listing = _list_objects(client, settings.r2_bucket, prefix, args.max_objects)
            write_object_manifest(
                args.manifest_output,
                build_cifake_image_manifest(listing.keys, prefix),
            )
            report["manifest_output"] = str(args.manifest_output)
        print(report)
    except (OSError, ValueError) as exc:
        print(f"Inventory failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
