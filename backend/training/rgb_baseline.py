"""Independent RGB ResNet-18 baselines for FaceForensics++ images and CIFAKE."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, UnidentifiedImageError
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader, Dataset
import sys
from torchvision.models import ResNet18_Weights, resnet18

# Ensure repository root and backend directory are on sys.path
_repo_root = str(Path(__file__).resolve().parents[2])
_backend_dir = str(Path(__file__).resolve().parents[1])
for _p in (_repo_root, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from backend.app.preprocessing import Normalization
except ModuleNotFoundError:
    from app.preprocessing import Normalization


@dataclass(frozen=True)
class TrainingConfig:
    task: str
    manifest_dir: Path
    output_dir: Path
    epochs: int = 5
    batch_size: int = 16
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    seed: int = 42
    num_workers: int = 0
    max_records: int | None = None
    pretrained: bool = True
    source_frame_manifest: Path | None = None


@dataclass(frozen=True)
class ManifestRow:
    path: str
    label: int
    label_name: str
    group_id: str
    split: str


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _resolve_path(value: str, manifest_dir: Path) -> Path:
    candidate = Path(value)
    if candidate.is_file():
        return candidate
    root = Path.cwd()
    candidates = (root / candidate, manifest_dir / candidate, manifest_dir.parent / candidate)
    for path in candidates:
        if path.is_file():
            return path
    return candidate


def read_manifest(path: Path, expected_split: str, *, max_records: int | None = None) -> list[ManifestRow]:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest does not exist: {path}")
    rows: list[ManifestRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            try:
                label = int(raw["label"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path} contains an invalid label") from exc
            if label not in {0, 1} or raw.get("label_name") not in {"real", "fake"}:
                raise ValueError(f"{path} contains unsupported label mapping")
            split = raw.get("split", "")
            if split != expected_split:
                raise ValueError(f"{path} has split={split!r}; expected {expected_split!r}")
            if not raw.get("path") or not raw.get("group_id"):
                raise ValueError(f"{path} requires path and group_id for every record")
            rows.append(ManifestRow(raw["path"], label, raw["label_name"], raw["group_id"], split))
    if max_records is not None:
        if max_records < 2:
            raise ValueError("max_records must be at least 2 so both labels can be represented")
        # CSVs are commonly label-sorted. Keep a deterministic balanced subset for
        # smoke tests instead of accidentally training on one class only.
        per_label = max_records // 2
        selected: dict[int, list[ManifestRow]] = {0: [], 1: []}
        for row in rows:
            if len(selected[row.label]) < per_label:
                selected[row.label].append(row)
        rows = selected[0] + selected[1]
    if not rows:
        raise ValueError(f"{path} contains no records")
    return rows


def validate_task_manifests(config: TrainingConfig) -> dict[str, Any]:
    if config.task not in {"faceforensicspp", "cifake"}:
        raise ValueError("task must be faceforensicspp or cifake")
    external_card = config.manifest_dir / "external-test-dataset-card.json"
    if config.task == "cifake" and external_card.is_file():
        card = json.loads(external_card.read_text(encoding="utf-8"))
        if card.get("external_evaluation_only") is not True:
            raise ValueError("CIFAKE external-test card must be evaluation-only")
    if config.task == "faceforensicspp":
        source_manifest = config.source_frame_manifest
        if source_manifest is None:
            raise ValueError(
                "FaceForensics++ training requires --source-frame-manifest "
                "pointing to the official frame-manifest.csv"
            )
        if not source_manifest.is_file():
            raise ValueError(
                "FaceForensics++ training requires frame-manifest.csv with "
                "source_video_key and manipulation_type fields"
            )
        with source_manifest.open(newline="", encoding="utf-8") as handle:
            fields = set(csv.DictReader(handle).fieldnames or ())
        required = {"path", "label_name", "label", "group_id", "source_video_key", "manipulation_type"}
        if not required.issubset(fields):
            raise ValueError(
                "FaceForensics++ frame-manifest.csv lacks validated source/manipulation fields"
            )
    splits = {
        name: read_manifest(config.manifest_dir / f"{name}.csv", name, max_records=config.max_records)
        for name in ("train", "val", "test")
    }
    for split_name, split_rows in splits.items():
        if {row.label for row in split_rows} != {0, 1}:
            raise ValueError(f"{split_name}.csv must contain both real and fake samples")
    external_rows: list[ManifestRow] = []
    if config.task == "cifake":
        external_rows = read_manifest(
            config.manifest_dir / "external-test.csv",
            "external-test",
            max_records=config.max_records,
        )
    all_rows = [row for rows in splits.values() for row in rows] + external_rows
    locations: dict[str, set[str]] = {}
    missing: list[str] = []
    duplicates: list[str] = []
    seen: set[str] = set()
    for row in all_rows:
        path = _resolve_path(row.path, config.manifest_dir)
        key = str(path.resolve())
        if row.split != "external-test":
            locations.setdefault(row.group_id, set()).add(row.split)
        if not path.is_file():
            missing.append(row.path)
        if row.split != "external-test" and key in seen:
            duplicates.append(row.path)
        if row.split != "external-test":
            seen.add(key)
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError(f"Unreadable image {row.path}: {exc}") from exc
    leakage = sorted(group for group, split_names in locations.items() if len(split_names) > 1)
    if missing:
        raise ValueError(f"{config.task} manifest has {len(missing)} missing image files")
    if duplicates:
        raise ValueError(f"{config.task} manifest has duplicate image records")
    if leakage:
        raise ValueError(f"{config.task} source groups cross splits: {leakage[:5]}")
    return {
        "task": config.task,
        "records": {name: len(rows) for name, rows in splits.items()},
        "class_counts": {
            name: {label: sum(row.label_name == label for row in rows) for label in ("real", "fake")}
            for name, rows in splits.items()
        },
        "group_counts": {name: len({row.group_id for row in rows}) for name, rows in splits.items()},
        "duplicate_records": 0,
        "source_group_leakage": [],
        "image_files_validated": len(all_rows),
        "rows": splits,
    }


class RGBManifestDataset(Dataset[tuple[torch.Tensor, int, str, str]]):
    def __init__(self, rows: list[ManifestRow], manifest_dir: Path, *, training: bool = False):
        self.rows = rows
        self.manifest_dir = manifest_dir
        self.training = training
        self.normalization = Normalization()

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, str, str]:
        row = self.rows[index]
        path = _resolve_path(row.path, self.manifest_dir)
        try:
            with Image.open(path) as source:
                image = source.convert("RGB")
            image = image.resize((224, 224), Image.Resampling.BILINEAR)
            if self.training and random.random() < 0.5:
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            array = np.asarray(image, dtype=np.float32) / 255.0
            array = (array - np.asarray(self.normalization.mean)) / np.asarray(self.normalization.std)
            tensor = torch.from_numpy(np.transpose(array, (2, 0, 1)).copy()).float()
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            raise RuntimeError(f"Unable to load training image {path}: {exc}") from exc
        return tensor, row.label, row.path, row.group_id


def build_model(pretrained: bool) -> nn.Module:
    weights = ResNet18_Weights.DEFAULT if pretrained else None
    model = resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, 2)
    return model


def _metrics(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, Any]:
    model.eval()
    total = correct = 0
    loss_sum = 0.0
    labels_all: list[int] = []
    scores_all: list[float] = []
    criterion = nn.CrossEntropyLoss()
    with torch.no_grad():
        for images, labels, _, _ in loader:
            logits = model(images.to(device))
            labels = labels.to(device)
            loss_sum += float(criterion(logits, labels).item()) * len(labels)
            predictions = logits.argmax(dim=1)
            correct += int((predictions == labels).sum().item())
            labels_all.extend(labels.cpu().tolist())
            scores_all.extend(torch.softmax(logits, dim=1)[:, 1].cpu().tolist())
            total += len(labels)
    binary_predictions = [int(value >= 0.5) for value in scores_all]
    roc_auc = roc_auc_score(labels_all, scores_all) if len(set(labels_all)) == 2 else None
    return {
        "loss": loss_sum / total,
        "accuracy": accuracy_score(labels_all, binary_predictions),
        "precision": precision_score(labels_all, binary_predictions, zero_division=0),
        "recall": recall_score(labels_all, binary_predictions, zero_division=0),
        "f1": f1_score(labels_all, binary_predictions, zero_division=0),
        "roc_auc": roc_auc,
        "confusion_matrix": confusion_matrix(labels_all, binary_predictions, labels=[0, 1]).tolist(),
    }


def train(config: TrainingConfig) -> dict[str, Any]:
    seed_everything(config.seed)
    validation = validate_task_manifests(config)
    rows = validation.pop("rows")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config.pretrained).to(device)
    train_loader = DataLoader(
        RGBManifestDataset(rows["train"], config.manifest_dir, training=True),
        batch_size=config.batch_size, shuffle=True, num_workers=config.num_workers,
    )
    val_loader = DataLoader(
        RGBManifestDataset(rows["val"], config.manifest_dir),
        batch_size=config.batch_size, shuffle=False, num_workers=config.num_workers,
    )
    test_loader = DataLoader(
        RGBManifestDataset(rows["test"], config.manifest_dir),
        batch_size=config.batch_size, shuffle=False, num_workers=config.num_workers,
    )
    external_loader = None
    if config.task == "cifake":
        external_rows = read_manifest(
            config.manifest_dir / "external-test.csv",
            "external-test",
            max_records=config.max_records,
        )
        external_loader = DataLoader(
            RGBManifestDataset(external_rows, config.manifest_dir),
            batch_size=config.batch_size, shuffle=False, num_workers=config.num_workers,
        )
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    criterion = nn.CrossEntropyLoss()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    best_accuracy = -1.0
    history: list[dict[str, float | int]] = []
    best_path = config.output_dir / f"{config.task}-rgb-resnet18-best.pt"
    for epoch in range(1, config.epochs + 1):
        model.train()
        total_loss = 0.0
        for images, labels, _, _ in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(images.to(device))
            loss = criterion(logits, labels.to(device))
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(labels)
        val_metrics = _metrics(model, val_loader, device)
        item = {"epoch": epoch, "train_loss": total_loss / len(train_loader.dataset), **{f"val_{k}": v for k, v in val_metrics.items()}}
        history.append(item)
        if val_metrics["accuracy"] > best_accuracy:
            best_accuracy = val_metrics["accuracy"]
            torch.save({"model_state": model.state_dict(), "config": asdict(config), "epoch": epoch, "val_metrics": val_metrics}, best_path)
    checkpoint = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    test_metrics = _metrics(model, test_loader, device)
    (config.output_dir / f"{config.task}-rgb-resnet18-history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (config.output_dir / f"{config.task}-rgb-resnet18-config.json").write_text(
        json.dumps({**asdict(config), "manifest_dir": str(config.manifest_dir), "output_dir": str(config.output_dir)}, indent=2),
        encoding="utf-8",
    )
    report = {
        **validation, "device": str(device), "pretrained_weights_requested": config.pretrained,
        "pretrained_weights_loaded": bool(config.pretrained),
        "pretrained_weights_source": str(ResNet18_Weights.DEFAULT) if config.pretrained else None,
        "best_checkpoint": str(best_path), "best_epoch": checkpoint["epoch"],
        "best_validation_metrics": checkpoint["val_metrics"], "test_metrics": test_metrics,
        "external_test_metrics": _metrics(model, external_loader, device) if external_loader else None,
    }
    (config.output_dir / f"{config.task}-rgb-resnet18-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("faceforensicspp", "cifake"), required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/rgb-baseline"))
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
            print(json.dumps({key: value for key, value in validate_task_manifests(config).items() if key != "rows"}, indent=2))
            return 0
        print(json.dumps(train(config), indent=2))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"RGB baseline failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
