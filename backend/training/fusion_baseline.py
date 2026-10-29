"""RGB + FFT fusion ResNet-18 baseline using validated image manifests."""

from __future__ import annotations

import argparse
import io
import json
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, UnidentifiedImageError
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import ResNet18_Weights, resnet18

from backend.app.frequency import preprocess_fft
from backend.app.preprocessing import Normalization
from backend.training.rgb_baseline import (
    ManifestRow,
    TrainingConfig,
    _resolve_path,
    read_manifest,
    seed_everything,
    validate_task_manifests,
    _metrics,
    json_safe_config,
    make_loader,
    json_safe_value,
)


class FusionManifestDataset(Dataset[tuple[torch.Tensor, torch.Tensor, int, str, str]]):
    """Create aligned RGB and FFT views from the same source image."""

    def __init__(self, rows: list[ManifestRow], manifest_dir: Path, *, training: bool = False):
        self.rows = rows
        self.manifest_dir = manifest_dir
        self.training = training
        self.normalization = Normalization()

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, int, str, str]:
        row = self.rows[index]
        path = _resolve_path(row.path, self.manifest_dir)
        try:
            with Image.open(path) as source:
                image = source.convert("RGB")
            image = image.resize((224, 224), Image.Resampling.BILINEAR)
            if self.training and random.random() < 0.5:
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            rgb_array = np.asarray(image, dtype=np.float32) / 255.0
            mean = np.asarray(self.normalization.mean, dtype=np.float32)
            std = np.asarray(self.normalization.std, dtype=np.float32)
            rgb_array = (rgb_array - mean) / std
            rgb = torch.from_numpy(np.transpose(rgb_array, (2, 0, 1)).copy()).float()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            fft = torch.from_numpy(preprocess_fft(buffer.getvalue()))
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            raise RuntimeError(f"Unable to load fusion image {path}: {exc}") from exc
        return rgb, fft, row.label, row.path, row.group_id


class RGBFFTFusionModel(nn.Module):
    """Two ResNet-18 feature branches followed by a two-class fusion head."""

    def __init__(self, pretrained: bool):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        try:
            self.rgb_branch = resnet18(weights=weights)
            rgb_loaded = pretrained
        except (OSError, RuntimeError):
            self.rgb_branch = resnet18(weights=None)
            rgb_loaded = False
        try:
            self.fft_branch = resnet18(weights=weights)
            fft_loaded = pretrained
        except (OSError, RuntimeError):
            self.fft_branch = resnet18(weights=None)
            fft_loaded = False
        self.rgb_branch._pretrained_weights_loaded = rgb_loaded
        self.fft_branch._pretrained_weights_loaded = fft_loaded
        rgb_features = self.rgb_branch.fc.in_features
        fft_features = self.fft_branch.fc.in_features
        self.rgb_branch.fc = nn.Identity()
        self.fft_branch.fc = nn.Identity()
        self.classifier = nn.Linear(rgb_features + fft_features, 2)

    def forward(self, rgb: torch.Tensor, fft: torch.Tensor) -> torch.Tensor:
        return self.classifier(torch.cat((self.rgb_branch(rgb), self.fft_branch(fft)), dim=1))


def train(config: TrainingConfig) -> dict[str, Any]:
    started = time.perf_counter()
    seed_everything(config.seed)
    validation = validate_task_manifests(config)
    rows = validation.pop("rows")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = RGBFFTFusionModel(config.pretrained).to(device)
    loaders = {
        name:         make_loader(
            FusionManifestDataset(split_rows, config.manifest_dir, training=name == "train"),
            config,
            shuffle=name == "train",
        )
        for name, split_rows in rows.items()
    }
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    criterion = nn.CrossEntropyLoss()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    best_accuracy = -1.0
    history: list[dict[str, Any]] = []
    best_path = config.output_dir / f"{config.task}-fusion-resnet18-best.pt"
    for epoch in range(1, config.epochs + 1):
        model.train()
        total_loss = 0.0
        for rgb, fft, labels, _, _ in loaders["train"]:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(rgb.to(device), fft.to(device)), labels.to(device))
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(labels)
        val_metrics = _metrics(model, loaders["val"], device)
        history.append({
            "epoch": epoch,
            "train_loss": total_loss / len(loaders["train"].dataset),
            "val_metrics": json_safe_value(val_metrics),
        })
        if val_metrics["accuracy"] > best_accuracy:
            best_accuracy = val_metrics["accuracy"]
            torch.save({
                "model_state": model.state_dict(),
                "config": json_safe_config(config, input_contract="aligned-rgb-and-fft-chw-224"),
                "epoch": epoch,
                "val_metrics": json_safe_value(val_metrics),
            }, best_path)
    checkpoint = torch.load(best_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"], strict=True)
    test_metrics = _metrics(model, loaders["test"], device)
    external_metrics = None
    if config.task == "cifake":
        external_rows = read_manifest(
            config.manifest_dir / "external-test.csv",
            "external-test",
            max_records=config.max_records,
        )
        external_loader = make_loader(FusionManifestDataset(external_rows, config.manifest_dir), config, shuffle=False)
        external_metrics = _metrics(model, external_loader, device)
    prefix = f"{config.task}-fusion-resnet18"
    (config.output_dir / f"{prefix}-history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (config.output_dir / f"{prefix}-config.json").write_text(json.dumps({
        **asdict(config),
        "manifest_dir": str(config.manifest_dir),
        "output_dir": str(config.output_dir),
        "architecture": "two ResNet-18 branches; concatenate 512-d features; Linear(1024, 2)",
        "input_contract": {
            "rgb": "RGB resize 224x224 with ImageNet normalization",
            "fft": "same augmented RGB source -> grayscale -> fft2 -> fftshift -> log1p magnitude -> per-image min-max",
            "augmentation_alignment": "same horizontal flip decision for RGB and FFT views",
        },
    }, indent=2, default=str), encoding="utf-8")
    report = {
        **validation,
        "device": str(device),
        "pretrained_weights_requested": config.pretrained,
        "pretrained_weights_loaded": bool(
            getattr(model.rgb_branch, "_pretrained_weights_loaded", False)
            and getattr(model.fft_branch, "_pretrained_weights_loaded", False)
        ),
        "pretrained_weights_source": str(ResNet18_Weights.DEFAULT) if config.pretrained else None,
        "best_checkpoint": str(best_path),
        "best_epoch": checkpoint["epoch"],
        "best_validation_metrics": checkpoint["val_metrics"],
        "test_metrics": test_metrics,
        "external_test_metrics": external_metrics,
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "comparison_protocol": "same manifests, seed, optimizer, split policy, and metric definitions as RGB and FFT baselines",
    }
    (config.output_dir / f"{prefix}-report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("faceforensicspp", "forgerynet", "cifake"), required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/fusion-baseline"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--source-frame-manifest", type=Path)
    args = parser.parse_args()
    config = TrainingConfig(
        task=args.task, manifest_dir=args.manifest_dir, output_dir=args.output_dir,
        epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.learning_rate,
        weight_decay=args.weight_decay, num_workers=args.num_workers,
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
        print(f"Fusion baseline failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
