import csv
from pathlib import Path

import pytest
from PIL import Image

from backend.training.rgb_baseline import (
    RGBManifestDataset,
    TrainingConfig,
    validate_task_manifests,
)


def _write_fixture(root: Path) -> Path:
    source = root / "images"
    source.mkdir()
    rows = {name: [] for name in ("train", "val", "test")}
    for split in rows:
        for label_name, label in (("real", 0), ("fake", 1)):
            path = source / f"{split}-{label_name}.jpg"
            Image.new("RGB", (8, 8), (20 + label * 100, 30, 40)).save(path)
            rows[split].append({
                "path": str(path), "label_name": label_name, "label": label,
                "group_id": f"{split}-{label_name}", "split": split,
            })
    manifest = root / "manifests"
    manifest.mkdir()
    for split, values in rows.items():
        with (manifest / f"{split}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=values[0])
            writer.writeheader()
            writer.writerows(values)
    with (manifest / "external-test.csv").open("w", newline="", encoding="utf-8") as handle:
        external = [{**row, "split": "external-test"} for row in rows["test"]]
        writer = csv.DictWriter(handle, fieldnames=external[0])
        writer.writeheader()
        writer.writerows(external)
    return manifest


def test_rgb_manifest_preflight_and_dataset_output(tmp_path):
    manifest = _write_fixture(tmp_path)
    config = TrainingConfig("cifake", manifest, tmp_path / "out", pretrained=False)
    result = validate_task_manifests(config)
    assert result["records"] == {"train": 2, "val": 2, "test": 2}
    image, label, path, group = RGBManifestDataset(
        result["rows"]["train"], manifest
    )[0]
    assert tuple(image.shape) == (3, 224, 224)
    assert label in (0, 1)
    assert path and group


def test_rgb_manifest_rejects_group_leakage(tmp_path):
    manifest = _write_fixture(tmp_path)
    val = manifest / "val.csv"
    rows = list(csv.DictReader(val.read_text(encoding="utf-8").splitlines()))
    rows[0]["group_id"] = "train-real"
    with val.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="cross splits"):
        validate_task_manifests(TrainingConfig("cifake", manifest, tmp_path / "out", pretrained=False))
