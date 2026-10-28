"""Validate a local dataset and write reproducible leakage-safe manifests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .dataset import ImageRecord, scan_dataset, split_records
from .dataset_metadata import validate_dataset_metadata
from .r2 import R2ArtifactStore, R2ConfigurationError


def load_groups(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not {"path", "group_id"}.issubset(reader.fieldnames or ()):
            raise ValueError("Groups CSV must contain path and group_id columns")
        return {
            row["path"].replace("\\", "/"): row["group_id"]
            for row in reader
            if row.get("path") and row.get("group_id")
        }


def _write_split(path: Path, records: list[ImageRecord], split: str) -> str:
    fields = [
        "path", "label_name", "label", "group_id", "sha256", "width", "height",
        "format", "split",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {field: getattr(record, field) for field in fields if field != "split"}
            row["split"] = split
            writer.writerow(row)
    return _sha256(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _upload_artifacts(output: Path, dataset_version: str, *, force: bool) -> None:
    store = R2ArtifactStore()
    prefix = f"manifests/{dataset_version}/"
    client = store._get_client()
    for path in sorted(output.iterdir()):
        if path.suffix not in {".csv", ".json"}:
            continue
        key = prefix + path.name
        exists = True
        try:
            client.head_object(Bucket=store.config.r2_bucket, Key=key)
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}:
                exists = False
            else:
                raise
        if exists and not force:
            raise FileExistsError(f"R2 artifact already exists: {key}; use --force to overwrite")
        store.upload_artifact(path, key)
        client.head_object(Bucket=store.config.r2_bucket, Key=key)


def prepare_dataset(
    input_path: Path,
    output: Path,
    *,
    seed: int = 42,
    dataset_kind: str | None = None,
    groups_file: Path | None = None,
    upload_r2: bool = False,
    force: bool = False,
) -> dict[str, object]:
    external_marker = input_path / "external_evaluation_only"
    external_metadata = input_path / "dataset-card.json"
    if external_marker.exists():
        raise ValueError("external_evaluation_only datasets cannot be used for training or splits")
    if external_metadata.is_file():
        try:
            card = json.loads(external_metadata.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid dataset-card.json: {exc}") from exc
        if card.get("external_evaluation_only") is True:
            raise ValueError("external_evaluation_only datasets cannot be used for training or splits")
    kind = dataset_kind or (
        "faceforensicspp" if "faceforensics" in input_path.name.lower() else
        "cifake" if "cifake" in input_path.name.lower() else None
    )
    metadata = validate_dataset_metadata(input_path, dataset_kind=kind)
    groups = metadata.groups or load_groups(groups_file)
    report = scan_dataset(input_path, groups=groups)
    if kind == "faceforensicspp":
        missing = [
            record.path for record in report.records
            if             str(Path(record.path).relative_to(input_path)).replace("\\", "/")
            not in groups
        ]
        if missing:
            raise ValueError(
                f"FaceForensics++ is missing group IDs for {len(missing)} images"
            )
    if report.cross_label_duplicate_paths:
        raise ValueError("Exact duplicate image content occurs across labels")
    splits = split_records(report.records, seed=seed)
    output.mkdir(parents=True, exist_ok=True)
    manifest_hashes = {
        split: _write_split(output / f"{split}.csv", records, split)
        for split, records in splits.items()
    }
    exclusions_path = output / "exclusions.csv"
    with exclusions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "reason"])
        writer.writeheader()
        writer.writerows({"path": item.path, "reason": item.reason} for item in report.exclusions)
    report_data = {
        **report.statistics,
        "dataset": metadata.metadata["name"],
        "version": metadata.metadata["version"],
        "seed": seed,
        "ratios": [0.70, 0.15, 0.15],
        "warnings": list(metadata.warnings),
        "split_counts": {name: len(records) for name, records in splits.items()},
    }
    (output / "report.json").write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    card = {
        **metadata.metadata,
        "local_source": str(input_path),
        "r2_prefix": metadata.metadata.get("r2_prefix"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "split_seed": seed,
        "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
        "class_counts_per_split": {
            split: {label: sum(item.label_name == label for item in records)
                     for label in ("real", "fake")}
            for split, records in splits.items()
        },
        "group_counts_per_split": {
            split: len({item.group_id for item in records}) for split, records in splits.items()
        },
        "excluded_file_count": len(report.exclusions),
        "duplicate_findings": report.statistics,
        "manifest_sha256": manifest_hashes,
        "preprocessing_version": "rgb-224-v1",
        "grouping_strategy": metadata.metadata["grouping_policy"],
        "known_limitations": metadata.metadata["limitations_bias_notes"],
        "model_training_occurred": False,
    }
    (output / "dataset-card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    if upload_r2:
        try:
            _upload_artifacts(output, input_path.name, force=force)
        except R2ConfigurationError as exc:
            raise ValueError(f"--upload-r2 requested but R2 is unavailable: {exc}") from exc
    return report_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/metadata"))
    parser.add_argument("--groups-file", type=Path)
    parser.add_argument("--dataset", choices=("faceforensicspp", "cifake"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--upload-r2", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        result = prepare_dataset(
            args.input, args.output, seed=args.seed, dataset_kind=args.dataset,
            groups_file=args.groups_file, upload_r2=args.upload_r2, force=args.force,
        )
    except (OSError, ValueError, FileExistsError) as exc:
        print(f"Dataset preparation failed: {exc}")
        return 1
    for key, value in result.items():
        if key == "warnings":
            for warning in value:
                print(f"WARNING: {warning}")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
