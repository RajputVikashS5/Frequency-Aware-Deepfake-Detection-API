"""Fetch and recover bounded CIFAKE inspection samples from R2."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, UnidentifiedImageError

from .config import settings
from .inventory_forgerynet import IMAGE_EXTENSIONS, _list_objects
from .r2 import R2ArtifactStore
from .r2_verify import R2VerificationError, dataset_prefixes, validate_configuration

_IMAGE_SUFFIXES = IMAGE_EXTENSIONS | {".bmp", ".tif", ".tiff"}
_MANIFEST_NAME = "sample-manifest.json"


def _label_for_key(key: str, prefix: str) -> str | None:
    relative = key[len(prefix):] if key.startswith(prefix) else key
    parts = [part.lower() for part in relative.replace("\\", "/").split("/") if part]
    return next((part for part in parts if part in {"real", "fake"}), None)


def _partition_for_key(key: str, prefix: str) -> str | None:
    relative = key[len(prefix):] if key.startswith(prefix) else key
    parts = [part.lower() for part in relative.replace("\\", "/").split("/") if part]
    return next((part for part in parts if part in {"train", "test"}), None)


def _read_manifest(root: Path) -> dict[str, Any]:
    path = root / _MANIFEST_NAME
    if not path.is_file():
        return {"dataset": "cifake", "objects": [], "counts": {}, "warnings": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Existing manifest is invalid: {path} ({exc})") from exc
    if not isinstance(value, dict) or not isinstance(value.get("objects", []), list):
        raise ValueError(f"Existing manifest has an unsupported format: {path}")
    return value


def _resolve_local(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path.cwd() / path


def _verified_image(data: bytes) -> tuple[int, int, str]:
    with Image.open(BytesIO(data)) as image:
        image.verify()
    with Image.open(BytesIO(data)) as image:
        return image.width, image.height, image.format or ""


def _write_manifest(root: Path, manifest: dict[str, Any], *, recompute_counts: bool = True) -> None:
    def item_partition(item: dict[str, Any]) -> str:
        return str(item.get("partition") or _partition_for_key(
            str(item.get("key", "")), str(manifest.get("prefix", ""))
        ) or "").lower()

    if recompute_counts:
        manifest["counts"] = {
            label: sum(
                item.get("status") == "downloaded"
                and item.get("label_name") == label
                and item_partition(item) == item.get("partition", item_partition(item))
                for item in manifest.get("objects", [])
            )
            for label in ("real", "fake")
        }
    manifest["objects"] = sorted(
        manifest.get("objects", []),
        key=lambda item: (item.get("partition", ""), item.get("label_name", ""), item.get("key", "")),
    )
    (root / _MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _existing_source_keys(manifest: dict[str, Any], partition: str) -> set[str]:
    def item_partition(item: dict[str, Any]) -> str:
        value = item.get("partition") or _partition_for_key(
            str(item.get("key", "")), str(manifest.get("prefix", ""))
        )
        if value:
            return str(value).lower()
        parts = Path(str(item.get("local_path", ""))).parts
        return next((part.lower() for part in parts if part.lower() in {"train", "test"}), "")

    return {
        str(item["key"])
        for item in manifest.get("objects", [])
        if (
            item_partition(item) == partition
            and item.get("key")
            and item.get("status") == "downloaded"
        )
    }


def _next_local_path(root: Path, partition: str, label: str, suffix: str) -> Path:
    directory = root / partition / label
    directory.mkdir(parents=True, exist_ok=True)
    index = 0
    while True:
        candidate = directory / f"{index:02d}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def fetch_sample(
    dataset: str,
    output: Path,
    *,
    per_label: int = 10,
    partition: str | None = None,
    force: bool = False,
    client: Any | None = None,
    config: Any = settings,
) -> dict[str, object]:
    if dataset != "cifake":
        raise ValueError("This sample command supports CIFAKE only")
    if not 1 <= per_label <= 10:
        raise ValueError("--per-label must be between 1 and 10")
    if partition not in {"train", "test"}:
        raise ValueError("CIFAKE downloads require --partition train or test")
    output.mkdir(parents=True, exist_ok=True)
    manifest = _read_manifest(output)
    if client is None:
        validate_configuration(config)
        client = R2ArtifactStore(config)._get_client()
    prefix = dataset_prefixes(config)["cifake"] + f"{partition}/"
    listing = _list_objects(client, config.r2_bucket, prefix, 1_000_000)
    if listing.warnings:
        raise RuntimeError("; ".join(listing.warnings))
    candidates = {
        label: [
            key for key in listing.keys
            if Path(key).suffix.lower() in _IMAGE_SUFFIXES
            and _label_for_key(key, prefix) == label
        ]
        for label in ("real", "fake")
    }
    existing_keys = _existing_source_keys(manifest, partition)
    counts = {
        label: sum(
            (
                item.get("partition")
                or _partition_for_key(str(item.get("key", "")), str(manifest.get("prefix", "")))
                or next(
                    (
                        part.lower()
                        for part in Path(str(item.get("local_path", ""))).parts
                        if part.lower() in {"train", "test"}
                    ),
                    "",
                )
            ) == partition
            and item.get("label_name") == label
            and item.get("status") == "downloaded"
            for item in manifest.get("objects", [])
        )
        for label in ("real", "fake")
    }
    failures: list[dict[str, str]] = []
    for label in ("real", "fake"):
        if not candidates[label]:
            failures.append({"label": label, "reason": "no eligible image objects found"})
        for key in candidates[label]:
            if counts[label] >= per_label:
                break
            if key in existing_keys:
                continue
            body = BytesIO()
            try:
                client.download_fileobj(config.r2_bucket, key, body)
                data = body.getvalue()
                width, height, image_format = _verified_image(data)
                suffix = Path(key).suffix.lower()
                local = _next_local_path(output, partition, label, suffix)
                if local.exists() and not force:
                    continue
                local.write_bytes(data)
                entry = {
                    "key": key,
                    "partition": partition,
                    "local_path": str(local),
                    "label_name": label,
                    "label": 0 if label == "real" else 1,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data),
                    "width": width,
                    "height": height,
                    "format": image_format,
                    "status": "downloaded",
                }
                manifest.setdefault("objects", []).append(entry)
                existing_keys.add(key)
                counts[label] += 1
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                failures.append({"label": label, "key": key, "reason": str(exc)})
    manifest.update({
        "dataset": "cifake",
        "prefix": dataset_prefixes(config)["cifake"],
        "per_label_limit": per_label,
        "full_dataset_downloaded": False,
        "warnings": failures,
    })
    _write_manifest(output, manifest)
    manifest["counts_by_partition"] = {
        selected_partition: {
            label: sum(
                item.get("status") == "downloaded"
                and item.get("label_name") == label
                and (
                    item.get("partition")
                    or _partition_for_key(str(item.get("key", "")), str(manifest.get("prefix", "")))
                ) == selected_partition
                for item in manifest.get("objects", [])
            )
            for label in ("real", "fake")
        }
        for selected_partition in ("train", "test")
    }
    manifest["counts"] = manifest["counts_by_partition"][partition]
    _write_manifest(output, manifest, recompute_counts=False)
    if any(counts[label] < per_label for label in ("real", "fake")):
        manifest["incomplete"] = True
        manifest["missing_samples"] = {
            label: max(0, per_label - counts[label]) for label in ("real", "fake")
        }
    return manifest


def recover_samples(sources: Iterable[Path], output: Path) -> dict[str, object]:
    """Merge verified files from old sample roots into one canonical root."""

    output.mkdir(parents=True, exist_ok=True)
    destination_manifest = _read_manifest(output)
    known_keys = {item.get("key") for item in destination_manifest.get("objects", [])}
    report: dict[str, Any] = {
        "reused": [], "skipped": [], "invalid": [], "missing": [], "downloaded": [],
    }
    for source in sources:
        manifest = _read_manifest(source)
        for item in manifest.get("objects", []):
            key = item.get("key")
            source_path = _resolve_local(source, item.get("local_path", ""))
            label = str(item.get("label_name", "")).lower()
            partition = str(
                item.get("partition")
                or _partition_for_key(str(key), str(manifest.get("prefix", "")))
                or next(
                    (
                        part.lower()
                        for part in source_path.parts
                        if part.lower() in {"train", "test"}
                    ),
                    "",
                )
            ).lower()
            if label not in {"real", "fake"} or partition not in {"train", "test"} or not key:
                report["skipped"].append({"source": str(source_path), "reason": "ambiguous manifest metadata"})
                continue
            if not source_path.is_file():
                report["invalid"].append({"source": str(source_path), "reason": "missing local image"})
                continue
            try:
                data = source_path.read_bytes()
                width, height, image_format = _verified_image(data)
            except (OSError, UnidentifiedImageError, ValueError) as exc:
                report["invalid"].append({"source": str(source_path), "reason": str(exc)})
                continue
            if key in known_keys:
                report["skipped"].append({"key": key, "reason": "source key already present"})
                continue
            target = _next_local_path(output, partition, label, source_path.suffix.lower())
            shutil.copy2(source_path, target)
            entry = {
                **item, "key": key, "partition": partition, "label_name": label,
                "label": 0 if label == "real" else 1, "local_path": str(target),
                "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
                "width": width, "height": height, "format": image_format, "status": "downloaded",
            }
            destination_manifest.setdefault("objects", []).append(entry)
            known_keys.add(key)
            report["reused"].append({"key": key, "local_path": str(target)})
    destination_manifest.update({"dataset": "cifake", "full_dataset_downloaded": False})
    _write_manifest(output, destination_manifest)
    for partition in ("train", "test"):
        for label in ("real", "fake"):
            count = sum(
                item.get("partition") == partition and item.get("label_name") == label
                and item.get("status") == "downloaded"
                for item in destination_manifest.get("objects", [])
            )
            if count == 0:
                report["missing"].append({"partition": partition, "label": label})
    (output / "recovery-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("cifake",), default="cifake")
    parser.add_argument("--per-label", type=int, default=10)
    parser.add_argument("--partition", choices=("train", "test"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--recover-from", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        if args.recover_from:
            result = recover_samples(args.recover_from, args.output)
        else:
            result = fetch_sample(
                args.dataset, args.output, per_label=args.per_label,
                partition=args.partition, force=args.force,
            )
        print(json.dumps(result, indent=2))
    except (R2VerificationError, OSError, ValueError, RuntimeError) as exc:
        print(f"Sample operation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
