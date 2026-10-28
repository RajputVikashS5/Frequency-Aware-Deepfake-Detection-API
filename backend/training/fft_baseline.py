"""Independent FFT-only ResNet-18 baseline using validated image manifests."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import ResNet18_Weights, resnet18

from backend.app.frequency import preprocess_fft
from backend.training.rgb_baseline import (
    ManifestRow,
    TrainingConfig,
    _metrics,
    read_manifest,
    seed_everything,
    _resolve_path,
    validate_task_manifests,
)


class FFTManifestDataset(Dataset[tuple[torch.Tensor, int, str, str]]):
    """Lazily converts manifest images into the canonical FFT tensor."""

    def __init__(self, rows: list[ManifestRow], manifest_dir: Path):
        self.rows = rows
        self.manifest_dir = manifest_dir

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, str, str]:
        row = self.rows[index]
        path = _resolve_path(row.path, self.manifest_dir)
        try:
            with path.open("rb") as handle:
                tensor = torch.from_numpy(preprocess_fft(handle.read()))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"Unable to load FFT training image {path}: {exc}") from exc
        return tensor, row.label, row.path, row.group_id


def build_fft_model(pretrained: bool) -> tuple[nn.Module, bool]:
    """Build ResNet-18 and report whether pretrained weights loaded successfully."""

    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, 2)
    return model, bool(pretrained)


def train(config: TrainingConfig) -> dict[str, Any]:
    started = time.perf_counter()
    seed_everything(config.seed)
    validation = validate_task_manifests(config)
    rows = validation.pop("rows")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, pretrained_loaded = build_fft_model(config.pretrained)
    model.to(device)
    loaders = {
        name: DataLoader(
            FFTManifestDataset(split_rows, config.manifest_dir),
            batch_size=config.batch_size,
            shuffle=name == "train",
            num_workers=config.num_workers,
        )
        for name, split_rows in rows.items()
    }
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    criterion = nn.CrossEntropyLoss()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    best_accuracy = -1.0
    history: list[dict[str, Any]] = []
    best_path = config.output_dir / f"{config.task}-fft-resnet18-best.pt"
    for epoch in range(1, config.epochs + 1):
        model.train()
        total_loss = 0.0
        for images, labels, _, _ in loaders["train"]:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(images.to(device)), labels.to(device))
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(labels)
        val_metrics = _metrics(model, loaders["val"], device)
        history.append({
            "epoch": epoch,
            "train_loss": total_loss / len(loaders["train"].dataset),
            "val_metrics": val_metrics,
        })
        if val_metrics["accuracy"] > best_accuracy:
            best_accuracy = val_metrics["accuracy"]
            torch.save({
                "model_state": model.state_dict(),
                "config": {**asdict(config), "input_contract": "fft-chw-224-repeat3"},
                "epoch": epoch,
                "val_metrics": val_metrics,
            }, best_path)
    checkpoint = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"], strict=True)
    test_metrics = _metrics(model, loaders["test"], device)
    external_metrics = None
    if config.task == "cifake":
        external_rows = read_manifest(
            config.manifest_dir / "external-test.csv",
            "external-test",
            max_records=config.max_records,
        )
        external_loader = DataLoader(
            FFTManifestDataset(external_rows, config.manifest_dir),
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=config.num_workers,
        )
        external_metrics = _metrics(model, external_loader, device)
    prefix = f"{config.task}-fft-resnet18"
    (config.output_dir / f"{prefix}-history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (config.output_dir / f"{prefix}-config.json").write_text(json.dumps({
        **asdict(config),
        "manifest_dir": str(config.manifest_dir),
        "output_dir": str(config.output_dir),
        "input_contract": {
            "source": "RGB image decoded with Pillow",
            "grayscale": "Pillow L conversion",
            "resize": [224, 224],
            "fft": "fft2, fftshift, log1p(abs(fft))",
            "normalization": "per-image min-max to [0, 1]",
            "model_channels": 3,
            "dtype": "float32",
        },
    }, indent=2, default=str), encoding="utf-8")
    report = {
        **validation,
        "device": str(device),
        "pretrained_weights_requested": config.pretrained,
        "pretrained_weights_loaded": pretrained_loaded,
        "best_checkpoint": str(best_path),
        "best_epoch": checkpoint["epoch"],
        "best_validation_metrics": checkpoint["val_metrics"],
        "test_metrics": test_metrics,
        "external_test_metrics": external_metrics,
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "comparison_protocol": "same manifest directory, seed, optimizer, split policy, and metric definitions as RGB baseline",
    }
    (config.output_dir / f"{prefix}-report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("forgerynet", "cifake"), required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/fft-baseline"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--source-frame-manifest", type=Path)
    args = parser.parse_args()
    config = TrainingConfig(
        task=args.task, manifest_dir=args.manifest_dir, output_dir=args.output_dir,
        epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.learning_rate,
        seed=args.seed, max_records=args.max_records, pretrained=not args.no_pretrained,
        source_frame_manifest=args.source_frame_manifest,
    )
    try:
        if args.preflight_only:
            result = validate_task_manifests(config)
            result.pop("rows")
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(train(config), indent=2, default=str))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"FFT baseline failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
