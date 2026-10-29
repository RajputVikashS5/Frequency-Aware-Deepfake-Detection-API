import csv
from pathlib import Path

import torch
import numpy as np
from PIL import Image

from backend.training.fft_baseline import (
    FFTManifestDataset,
    build_fft_model,
    train,
)
from backend.training.rgb_baseline import TrainingConfig


def _write_manifests(root: Path) -> Path:
    images = root / "images"
    images.mkdir()
    manifest = root / "manifests"
    manifest.mkdir()
    for split in ("train", "val", "test"):
        rows = []
        for label_name, label in (("real", 0), ("fake", 1)):
            path = images / f"{split}-{label_name}.png"
            pixels = np.random.default_rng(hash(split + label_name) & 0xFFFF).integers(
                0, 256, size=(16, 16, 3), dtype=np.uint8
            )
            Image.fromarray(pixels, "RGB").save(path)
            rows.append({
                "path": str(path),
                "label_name": label_name,
                "label": label,
                "group_id": f"{split}-{label_name}",
                "split": split,
            })
        with (manifest / f"{split}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
    external_rows = []
    for label_name, label in (("real", 0), ("fake", 1)):
        path = images / f"external-{label_name}.png"
        pixels = np.random.default_rng(hash("external" + label_name) & 0xFFFF).integers(
            0, 256, size=(16, 16, 3), dtype=np.uint8
        )
        Image.fromarray(pixels, "RGB").save(path)
        external_rows.append({
            "path": str(path),
            "label_name": label_name,
            "label": label,
            "group_id": f"external-{label_name}",
            "split": "external-test",
        })
    with (manifest / "external-test.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=external_rows[0])
        writer.writeheader()
        writer.writerows(external_rows)
    (manifest / "external-test-dataset-card.json").write_text(
        '{"external_evaluation_only": true}', encoding="utf-8"
    )
    return manifest


def test_fft_dataset_and_model_contract(tmp_path):
    manifest = _write_manifests(tmp_path)
    from backend.training.rgb_baseline import read_manifest

    rows = read_manifest(manifest / "train.csv", "train")
    image, label, path, group = FFTManifestDataset(rows, manifest)[0]
    model, pretrained_loaded = build_fft_model(False)
    output = model(image.unsqueeze(0))

    assert tuple(image.shape) == (3, 224, 224)
    assert label in (0, 1)
    assert path and group
    assert pretrained_loaded is False
    assert tuple(output.shape) == (1, 2)
    assert torch.isfinite(output).all()


def test_fft_training_smoke_writes_reloadable_checkpoint(tmp_path):
    manifest = _write_manifests(tmp_path)
    output = tmp_path / "experiment"
    report = train(TrainingConfig(
        task="cifake",
        manifest_dir=manifest,
        output_dir=output,
        epochs=1,
        batch_size=2,
        pretrained=False,
    ))

    checkpoint = Path(report["best_checkpoint"])
    assert checkpoint.is_file()
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model, _ = build_fft_model(False)
    model.load_state_dict(payload["model_state"], strict=True)
    assert report["best_epoch"] == 1
    assert report["test_metrics"]["confusion_matrix"]
