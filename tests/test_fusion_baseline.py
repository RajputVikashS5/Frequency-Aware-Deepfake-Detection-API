import csv
from pathlib import Path

import torch
from PIL import Image

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
            Image.new("RGB", (16, 12), (20 + label * 100, 30, 40)).save(path)
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
        Image.new("RGB", (16, 12), (40 + label * 100, 30, 40)).save(path)
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
