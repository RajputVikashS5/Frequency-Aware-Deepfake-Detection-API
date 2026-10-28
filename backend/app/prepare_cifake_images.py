"""Prepare separate CIFAKE train/validation and immutable external-test manifests."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .dataset import scan_dataset, split_records

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _find_partition(root: Path, name: str) -> Path | None:
    return next(
        (path for path in root.iterdir() if path.is_dir() and path.name.lower() == name),
        None,
    )


def _manifest_entries(root: Path) -> list[dict[str, Any]]:
    path = root / "sample-manifest.json"
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid sample-manifest.json: {exc}") from exc
    return value.get("objects", []) if isinstance(value, dict) else []


def validate_cifake(input_root: Path) -> dict[str, object]:
    """Validate a canonical CIFAKE root without copying or downloading files."""

    report: dict[str, Any] = {
        "dataset": "cifake", "root": str(input_root), "sample": True,
        "total_image_files": 0, "partition_counts": {}, "class_counts": {},
        "invalid_files": [], "missing_combinations": [], "duplicate_files": [],
        "manifest_entries_missing_files": [], "files_missing_manifest_entries": [],
        "warnings": [],
    }
    if not input_root.is_dir():
        report["errors"] = [f"Dataset root does not exist: {input_root}"]
        return report
    manifest_entries = _manifest_entries(input_root)
    manifest_paths: set[str] = set()
    for entry in manifest_entries:
        local = Path(str(entry.get("local_path", "")))
        manifest_paths.add(str(local.resolve()))
        if not local.is_absolute():
            local = Path.cwd() / local
        if not local.is_file():
            report["manifest_entries_missing_files"].append(str(local))
    for partition_name in ("train", "test"):
        partition = _find_partition(input_root, partition_name)
        report["partition_counts"][partition_name] = {"real": 0, "fake": 0}
        if partition is None:
            report["missing_combinations"].extend(
                f"{partition_name}/{label}" for label in ("real", "fake")
            )
            continue
        for label in ("real", "fake"):
            label_dir = next(
                (path for path in partition.iterdir()
                 if path.is_dir() and path.name.lower() == label),
                None,
            )
            if label_dir is None:
                report["missing_combinations"].append(f"{partition_name}/{label}")
                continue
            seen_hashes: dict[str, str] = {}
            for path in sorted(label_dir.rglob("*")):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                report["total_image_files"] += 1
                report["partition_counts"][partition_name][label] += 1
                resolved = str(path.resolve())
                if resolved not in manifest_paths:
                    report["files_missing_manifest_entries"].append(str(path))
                try:
                    with Image.open(path) as image:
                        image.verify()
                    digest_builder = hashlib.sha256()
                    with path.open("rb") as handle:
                        for block in iter(lambda: handle.read(1024 * 1024), b""):
                            digest_builder.update(block)
                    digest = digest_builder.hexdigest()
                    if digest in seen_hashes:
                        report["duplicate_files"].append(
                            {"path": str(path), "duplicate_of": seen_hashes[digest]}
                        )
                    seen_hashes[digest] = str(path)
                except (OSError, UnidentifiedImageError, ValueError) as exc:
                    report["invalid_files"].append({"path": str(path), "reason": str(exc)})
    for partition, counts in report["partition_counts"].items():
        report["class_counts"][partition] = counts
    sample_manifest = input_root / "sample-manifest.json"
    if sample_manifest.is_file():
        try:
            report["sample"] = not bool(json.loads(sample_manifest.read_text()).get("full_dataset_downloaded"))
        except (OSError, json.JSONDecodeError):
            report["warnings"].append("sample-manifest.json could not establish completeness")
    report["valid"] = not report["missing_combinations"] and not report["invalid_files"]
    return report


def _copy_partition(source: Path, destination: Path, limit: int) -> int:
    count = 0
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
            relative = path.relative_to(source)
            label = relative.parts[0].lower() if relative.parts else ""
            if label not in {"real", "fake"}:
                continue
            target = destination / label / Path(*relative.parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            count += 1
            if count >= limit:
                break
    return count


def _write_records(
    path: Path,
    records: list,
    *,
    split: str,
    external: bool = False,
) -> None:
    fields = ["path", "label_name", "label", "group_id", "sha256", "width", "height", "format", "split"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {field: getattr(record, field, "") for field in fields}
            row["split"] = "external-test" if external else split
            writer.writerow(row)


def reject_external_evaluation_manifest(path: Path) -> None:
    """Reject an external-test card wherever a training command is requested."""

    card_path = path if path.name.endswith(".json") else path.parent / "external-test-dataset-card.json"
    if card_path.is_file():
        card = json.loads(card_path.read_text(encoding="utf-8"))
        if card.get("external_evaluation_only") is True:
            raise ValueError("external_evaluation_only manifests are evaluation-only and cannot train")


def prepare_cifake(
    input_root: Path,
    output: Path,
    *,
    seed: int = 42,
    max_test_images: int | None = None,
    source_metadata: Path | None = None,
) -> dict[str, object]:
    if not input_root.is_dir():
        raise ValueError(f"CIFAKE input directory does not exist: {input_root}")
    train = _find_partition(input_root, "train")
    test = _find_partition(input_root, "test")
    if train is None or test is None:
        missing = [name for name, value in (("train", train), ("test", test)) if value is None]
        raise ValueError(
            "CIFAKE input must contain both train and test directories; "
            f"missing: {', '.join(missing)}. Recover or fetch the missing partition first."
        )
    validation = validate_cifake(input_root)
    if not validation["valid"]:
        raise ValueError(
            "CIFAKE input validation failed: "
            f"missing={validation['missing_combinations']}, "
            f"invalid={len(validation['invalid_files'])}. "
            "Run the validation command for details."
        )
    output.mkdir(parents=True, exist_ok=True)
    train_root, test_root = output / "training-source", output / "external-test-source"
    _copy_partition(train, train_root, 10**12)
    _copy_partition(test, test_root, max_test_images or 10**12)
    train_report = scan_dataset(train_root)
    test_report = scan_dataset(test_root)
    splits = split_records(train_report.records, seed=seed)
    for name, records in splits.items():
        _write_records(output / f"{name}.csv", records, split=name)
    _write_records(output / "external-test.csv", test_report.records, split="external-test", external=True)
    if source_metadata is not None:
        metadata = json.loads(source_metadata.read_text(encoding="utf-8"))
        required = ("name", "version", "source_url", "license_or_access_terms", "permitted_intended_use", "date_obtained")
        if any(not metadata.get(field) for field in required):
            raise ValueError("dataset-source.json has incomplete provenance")
        (output / "dataset-source.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (output / "training-source" / "dataset-source.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
    card = {
        "name": "CIFAKE", "version": "image-v1", "dataset": "cifake",
        "external_evaluation_only": False, "grouping_strategy": "one group per image",
        "known_limitations": ["No source/identity metadata was provided; each image is its own group."],
        "split_seed": seed, "external_test_manifest": "external-test.csv",
        "external_test_count": len(test_report.records),
    }
    (output / "dataset-card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    external_card = {**card, "external_evaluation_only": True}
    (output / "external-test-dataset-card.json").write_text(json.dumps(external_card, indent=2), encoding="utf-8")
    (output / "external-test-source" / "dataset-card.json").parent.mkdir(parents=True, exist_ok=True)
    (output / "external-test-source" / "dataset-card.json").write_text(
        json.dumps(external_card, indent=2), encoding="utf-8"
    )
    (output / "report.json").write_text(json.dumps({
        "dataset": "CIFAKE", "version": "image-v1", "split_seed": seed,
        "training_counts": {name: len(records) for name, records in splits.items()},
        "external_test_count": len(test_report.records),
        "external_evaluation_only": True,
    }, indent=2), encoding="utf-8")
    return {"train": len(splits["train"]), "val": len(splits["val"]), "test": len(splits["test"]), "external_test": len(test_report.records)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/metadata/cifake-image-v1"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-test-images", type=int)
    parser.add_argument("--source-metadata", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate_only:
            result = validate_cifake(args.input)
            print(json.dumps(result, indent=2))
            return 0 if result.get("valid") else 1
        if args.source_metadata is None:
            raise ValueError("--source-metadata is required unless --validate-only is used")
        print(prepare_cifake(
            args.input, args.output, seed=args.seed,
            max_test_images=args.max_test_images, source_metadata=args.source_metadata
        ))
    except (OSError, ValueError) as exc:
        print(f"CIFAKE preparation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
