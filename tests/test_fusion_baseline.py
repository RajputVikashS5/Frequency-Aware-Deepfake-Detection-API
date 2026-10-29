import csv
from pathlib import Path

import torch
import numpy as np
from PIL import Image

from backend.app.frequency import preprocess_fft
from backend.training.fusion_baseline import FusionManifestDataset, RGBFFTFusionModel, train
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
                "path": str(path), "label_name": label_name, "label": label,
                "group_id": f"{split}-{label_name}", "split": split,
            })
        with (manifest / f"{split}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
    external = []
    for label_name, label in (("real", 0), ("fake", 1)):
        path = images / f"external-{label_name}.png"
        pixels = np.random.default_rng(hash("external" + label_name) & 0xFFFF).integers(
            0, 256, size=(16, 16, 3), dtype=np.uint8
        )
        Image.fromarray(pixels, "RGB").save(path)
        external.append({
            "path": str(path), "label_name": label_name, "label": label,
            "group_id": f"external-{label_name}", "split": "external-test",
        })
    with (manifest / "external-test.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=external[0])
        writer.writeheader()
        writer.writerows(external)
    (manifest / "external-test-dataset-card.json").write_text(
        '{"external_evaluation_only": true}', encoding="utf-8"
    )
    return manifest


def test_fusion_dataset_and_forward_contract(tmp_path):
    manifest = _write_manifests(tmp_path)
    from backend.training.rgb_baseline import read_manifest

    rows = read_manifest(manifest / "train.csv", "train")
    rgb, fft, label, path, group = FusionManifestDataset(rows, manifest)[0]
    model = RGBFFTFusionModel(pretrained=False)
    output = model(rgb.unsqueeze(0), fft.unsqueeze(0))

    assert tuple(rgb.shape) == (3, 224, 224)
    assert tuple(fft.shape) == (3, 224, 224)
    assert label in (0, 1)
    assert path and group
    assert tuple(output.shape) == (1, 2)
    assert torch.isfinite(output).all()


def test_fusion_fft_matches_flipped_rgb_source(tmp_path, monkeypatch):
    manifest = _write_manifests(tmp_path)
    from backend.training.rgb_baseline import read_manifest

    rows = read_manifest(manifest / "train.csv", "train")
    monkeypatch.setattr("backend.training.fusion_baseline.random.random", lambda: 0.1)
    rgb, fft, _, path, _ = FusionManifestDataset(rows, manifest, training=True)[0]

    with Image.open(path) as source:
        flipped = source.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
    flipped = flipped.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    expected_buffer = __import__("io").BytesIO()
    flipped.save(expected_buffer, format="PNG")
    expected = torch.from_numpy(preprocess_fft(expected_buffer.getvalue()))

    assert torch.allclose(fft, expected)
    assert torch.isfinite(rgb).all()


def test_fusion_training_smoke_writes_reloadable_checkpoint(tmp_path):
    manifest = _write_manifests(tmp_path)
    output = tmp_path / "experiment"
    report = train(TrainingConfig(
        task="cifake", manifest_dir=manifest, output_dir=output,
        epochs=1, batch_size=2, pretrained=False,
    ))
    checkpoint = Path(report["best_checkpoint"])
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = RGBFFTFusionModel(pretrained=False)
    model.load_state_dict(payload["model_state"], strict=True)
    assert report["best_epoch"] == 1
    assert report["test_metrics"]["confusion_matrix"]
