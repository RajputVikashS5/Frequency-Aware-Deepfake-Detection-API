#!/usr/bin/env python
"""
Retrain FaceForensics++ RGB baseline with proper class balancing.
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18

# Setup paths
repo_root = Path(__file__).resolve().parent.parent.parent.parent  # Back to main repo
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "backend"))


@dataclass
class RetrainConfig:
    """Configuration for retraining with class balancing."""
    task: str = "faceforensicspp"
    manifest_dir: Path = repo_root / "data/metadata/faceforensicspp-c23-r2-v1-limited"
    output_dir: Path = repo_root / "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-fixed"

    # Training parameters
    epochs: int = 20
    batch_size: int = 16
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    seed: int = 42

    # Class balancing
    use_class_weights: bool = True
    use_sampler: bool = True

    # Early stopping
    patience: int = 5
    min_delta: float = 0.001

    # Model
    pretrained: bool = True
    num_workers: int = 0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class FaceForensicsDataset(Dataset):
    """Dataset for FaceForensics++ images with proper class balancing."""

    def __init__(self, manifest_path: Path, transform=None):
        self.manifest_path = manifest_path
        self.transform = transform
        self.samples = []

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        # Read CSV
        with open(manifest_path, "r") as f:
            lines = f.readlines()

        # Parse header
        header = lines[0].strip().split(",")
        path_idx = header.index("path")
        label_idx = header.index("label_name") if "label_name" in header else header.index("label")

        # Read samples
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) > max(path_idx, label_idx):
                path = Path(parts[path_idx])
                label_str = parts[label_idx]

                # Convert label to 0/1
                if label_str.lower() in ["real", "0"]:
                    label = 0
                elif label_str.lower() in ["fake", "1"]:
                    label = 1
                else:
                    continue

                # Resolve path relative to repo root
                abs_path = repo_root / path
                if abs_path.exists():
                    self.samples.append((abs_path, label))

        print(f"Loaded {len(self.samples)} samples from {manifest_path}")

        # Count class distribution
        self.class_counts = {0: 0, 1: 0}
        for _, label in self.samples:
            self.class_counts[label] += 1

        print(f"Class distribution: Real={self.class_counts[0]}, Fake={self.class_counts[1]}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]

        try:
            image = Image.open(path).convert("RGB")
            if self.transform:
                image = self.transform(image)

            return image, label, str(path)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            # Return a dummy image
            dummy = torch.zeros(3, 224, 224)
            return dummy, label, "error"


def create_transforms():
    """Create standard transforms for training."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225]),
    ])


def create_class_weights(labels):
    """Calculate class weights for imbalance."""
    class_counts = np.bincount(labels)
    total_samples = len(labels)
    n_classes = len(class_counts)

    weights = total_samples / (n_classes * class_counts)
    weights_tensor = torch.tensor(weights, dtype=torch.float32)

    print(f"Class counts: {class_counts}")
    print(f"Class weights: {weights}")

    return weights_tensor


def train_epoch(model, loader, optimizer, criterion, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    predictions = []
    targets = []

    for images, labels, _ in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        preds = torch.argmax(outputs, dim=1)
        predictions.extend(preds.cpu().numpy())
        targets.extend(labels.cpu().numpy())

    epoch_loss = total_loss / len(loader)
    epoch_acc = accuracy_score(targets, predictions)

    return epoch_loss, epoch_acc


def validate_epoch(model, loader, criterion, device):
    """Validate for one epoch."""
    model.eval()
    total_loss = 0
    predictions = []
    targets = []
    probs = []

    with torch.no_grad():
        for images, labels, _ in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()

            preds = torch.argmax(outputs, dim=1)
            predictions.extend(preds.cpu().numpy())
            targets.extend(labels.cpu().numpy())

            # Store probabilities for ROC-AUC
            probs.extend(torch.softmax(outputs, dim=1)[:, 1].cpu().numpy())

    epoch_loss = total_loss / len(loader)
    epoch_acc = accuracy_score(targets, predictions)

    # Calculate metrics
    metrics = {
        "loss": epoch_loss,
        "accuracy": epoch_acc,
        "precision": precision_score(targets, predictions, zero_division=0),
        "recall": recall_score(targets, predictions, zero_division=0),
        "f1": f1_score(targets, predictions, zero_division=0),
        "roc_auc": roc_auc_score(targets, probs) if len(set(targets)) > 1 else 0.5,
        "confusion_matrix": confusion_matrix(targets, predictions).tolist(),
    }

    return metrics


def build_model(config: RetrainConfig):
    """Build ResNet18 model for binary classification."""
    weights = ResNet18_Weights.IMAGENET1K_V1 if config.pretrained else None
    model = resnet18(weights=weights)

    # Replace final layer for binary classification
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    return model.to(config.device)


def retrain_faceforensics(config: RetrainConfig):
    """Main retraining function."""

    print("\n" + "="*70)
    print("RETRAINING FACEFORENSICS++ WITH CLASS BALANCING")
    print("="*70)

    # Create output directory
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Seed everything
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if config.device == "cuda":
        torch.cuda.manual_seed_all(config.seed)

    # Load datasets
    print(f"\nLoading datasets from {config.manifest_dir}")

    train_path = config.manifest_dir / "train.csv"
    val_path = config.manifest_dir / "val.csv"
    test_path = config.manifest_dir / "test.csv"

    if not all(p.exists() for p in [train_path, val_path, test_path]):
        print("ERROR: Missing manifest files!")
        return False

    transform = create_transforms()

    train_dataset = FaceForensicsDataset(train_path, transform)
    val_dataset = FaceForensicsDataset(val_path, transform)
    test_dataset = FaceForensicsDataset(test_path, transform)

    # Create class weights for imbalance
    if config.use_class_weights:
        train_labels = [label for _, label, _ in train_dataset]
        class_weights = create_class_weights(train_labels)
        criterion = nn.CrossEntropyLoss(weight=class_weights.to(config.device))
    else:
        criterion = nn.CrossEntropyLoss()

    # Create samplers for imbalance
    train_loader_kwargs = {}
    if config.use_sampler:
        train_labels = [label for _, label, _ in train_dataset]
        class_counts = np.bincount(train_labels)
        sample_weights = [1.0 / class_counts[label] for label in train_labels]
        sampler = WeightedRandomSampler(sample_weights, len(train_labels))
        train_loader_kwargs = {"sampler": sampler, "shuffle": False}

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size,
                             num_workers=config.num_workers,
                             **train_loader_kwargs)

    val_loader = DataLoader(val_dataset, batch_size=config.batch_size,
                           shuffle=False, num_workers=config.num_workers)

    test_loader = DataLoader(test_dataset, batch_size=config.batch_size,
                            shuffle=False, num_workers=config.num_workers)

    # Build model
    print("\nBuilding model...")
    model = build_model(config)

    # Create optimizer
    optimizer = optim.AdamW(model.parameters(), lr=config.learning_rate,
                           weight_decay=config.weight_decay)

    # Training loop
    print(f"\nStarting training for {config.epochs} epochs...")
    print(f"Device: {config.device}")
    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Test samples: {len(test_dataset)}")

    history = []
    best_val_accuracy = 0
    patience_counter = 0
    best_model_state = None
    best_epoch = 0

    for epoch in range(config.epochs):
        print(f"\nEpoch {epoch + 1}/{config.epochs}")

        # Train
        train_loss, train_acc = train_epoch(model, train_loader, optimizer,
                                           criterion, config.device)

        # Validate
        val_metrics = validate_epoch(model, val_loader, criterion, config.device)

        # Store history
        history.append({
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "val_f1": val_metrics["f1"],
            "val_roc_auc": val_metrics["roc_auc"],
            "val_confusion_matrix": val_metrics["confusion_matrix"],
        })

        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"  Val Loss: {val_metrics['loss']:.4f}, Val Acc: {val_metrics['accuracy']:.4f}")
        print(f"  Val ROC-AUC: {val_metrics['roc_auc']:.4f}")

        # Early stopping check
        if val_metrics["accuracy"] > best_val_accuracy + config.min_delta:
            best_val_accuracy = val_metrics["accuracy"]
            patience_counter = 0
            best_epoch = epoch + 1
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1

        if patience_counter >= config.patience:
            print(f"\nEarly stopping at epoch {epoch + 1}")
            break

    # Save best model
    if best_model_state is not None:
        checkpoint_path = config.output_dir / "faceforensicspp-rgb-resnet18-best.pt"

        checkpoint = {
            "model_state": best_model_state,
            "config": {
                "task": config.task,
                "manifest_dir": str(config.manifest_dir),
                "output_dir": str(config.output_dir),
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "learning_rate": config.learning_rate,
                "weight_decay": config.weight_decay,
                "seed": config.seed,
                "use_class_weights": config.use_class_weights,
                "use_sampler": config.use_sampler,
            },
            "epoch": best_epoch,
            "val_metrics": history[best_epoch - 1] if best_epoch > 0 else {},
        }

        torch.save(checkpoint, checkpoint_path)
        print(f"\nBest model saved to: {checkpoint_path}")

    # Evaluate on test set
    print("\n" + "-"*70)
    print("EVALUATING ON TEST SET")
    print("-"*70)

    test_metrics = validate_epoch(model, test_loader, criterion, config.device)

    # Create report
    report = {
        "task": config.task,
        "records": {
            "train": len(train_dataset),
            "val": len(val_dataset),
            "test": len(test_dataset),
        },
        "class_counts": {
            "train": train_dataset.class_counts,
            "val": val_dataset.class_counts,
            "test": test_dataset.class_counts,
        },
        "config": vars(config),
        "best_epoch": best_epoch,
        "best_validation_metrics": history[best_epoch - 1] if best_epoch > 0 else {},
        "test_metrics": test_metrics,
        "training_history": history,
    }

    # Save report
    report_path = config.output_dir / "faceforensicspp-rgb-resnet18-report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Save config
    config_path = config.output_dir / "faceforensicspp-rgb-resnet18-config.json"
    with open(config_path, "w") as f:
        json.dump(vars(config), f, indent=2, default=str)

    # Save history
    history_path = config.output_dir / "faceforensicspp-rgb-resnet18-history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nTest Results:")
    print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  Precision: {test_metrics['precision']:.4f}")
    print(f"  Recall: {test_metrics['recall']:.4f}")
    print(f"  F1: {test_metrics['f1']:.4f}")
    print(f"  ROC-AUC: {test_metrics['roc_auc']:.4f}")
    print(f"  Confusion Matrix: {test_metrics['confusion_matrix']}")

    print(f"\nAll artifacts saved to: {config.output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Retrain FaceForensics++ with class balancing")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    config = RetrainConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )

    success = retrain_faceforensics(config)

    if success:
        print("\n✓ Retraining completed successfully!")
    else:
        print("\n✗ Retraining failed!")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
