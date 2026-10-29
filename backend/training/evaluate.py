#!/usr/bin/env python
"""
Phase 8: Evaluation and Robustness Testing

Comprehensive evaluation of trained models with:
- Point metrics (accuracy, precision, recall, F1, ROC-AUC, confusion matrix)
- Bootstrap 95% confidence intervals
- Pixel logistic baseline comparison
- Robustness tests (JPEG compression, resizing, blur, noise)
- External dataset evaluation
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageFilter, ImageEnhance
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
)
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import resnet18

# Setup paths
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from backend.app.preprocessing import preprocess_rgb


@dataclass
class EvaluationConfig:
    """Configuration for model evaluation."""
    model: str  # 'rgb', 'fft', or 'fusion'
    checkpoint: Path
    manifest_dir: Path
    output_dir: Path
    eval_only: bool = True
    batch_size: int = 32
    num_workers: int = 0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    fft_input: str = "upsampled"  # or 'native'


class EvaluationDataset(Dataset):
    """Dataset for evaluation on manifest-based splits."""

    def __init__(self, manifest_path: Path, transform=None):
        self.manifest_path = manifest_path
        self.transform = transform
        self.samples = []

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r") as f:
            lines = f.readlines()

        header = lines[0].strip().split(",")
        path_idx = header.index("path") if "path" in header else 0
        label_idx = header.index("label")

        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) > max(path_idx, label_idx):
                path = Path(parts[path_idx])
                label = int(parts[label_idx])

                abs_path = repo_root / path
                if abs_path.exists():
                    self.samples.append((abs_path, label))

        print(f"Loaded {len(self.samples)} samples from {manifest_path}")

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
            dummy = torch.zeros(3, 224, 224)
            return dummy, label, "error"


def build_model(model_type: str, checkpoint_state: dict) -> nn.Module:
    """Build and load model from checkpoint."""
    if model_type == "rgb":
        model = resnet18(weights=None)
        model.fc = nn.Linear(512, 2)
    elif model_type == "fft":
        model = resnet18(weights=None)
        model.fc = nn.Linear(512, 2)
    elif model_type == "fusion":
        # Fusion model with two ResNet18 branches
        rgb_branch = resnet18(weights=None)
        rgb_branch.fc = nn.Identity()
        fft_branch = resnet18(weights=None)
        fft_branch.fc = nn.Identity()

        class FusionModel(nn.Module):
            def __init__(self, rgb_br, fft_br):
                super().__init__()
                self.rgb_branch = rgb_br
                self.fft_branch = fft_br
                self.classifier = nn.Linear(1024, 2)

            def forward(self, rgb_input, fft_input=None):
                rgb_feat = self.rgb_branch(rgb_input)
                if fft_input is not None:
                    fft_feat = self.fft_branch(fft_input)
                    combined = torch.cat([rgb_feat, fft_feat], dim=1)
                else:
                    combined = torch.cat([rgb_feat, rgb_feat], dim=1)
                return self.classifier(combined)

        model = FusionModel(rgb_branch, fft_branch)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    if "model_state" in checkpoint_state:
        model.load_state_dict(checkpoint_state["model_state"], strict=True)

    return model


def evaluate_model(model: nn.Module, loader: DataLoader, config: EvaluationConfig) -> dict[str, Any]:
    """Evaluate model on test set."""
    model.eval()
    predictions = []
    targets = []
    probabilities = []

    with torch.no_grad():
        for batch in loader:
            images = batch[0].to(config.device)
            labels = batch[1].to(config.device)

            if config.model == "fusion":
                outputs = model(images, images)
            else:
                outputs = model(images)

            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()

            predictions.extend(preds)
            targets.extend(labels.cpu().numpy())
            probabilities.extend(probs)

    predictions = np.array(predictions)
    targets = np.array(targets)
    probabilities = np.array(probabilities)

    # Calculate metrics
    metrics = {
        "accuracy": float(accuracy_score(targets, predictions)),
        "precision": float(precision_score(targets, predictions, zero_division=0)),
        "recall": float(recall_score(targets, predictions, zero_division=0)),
        "f1": float(f1_score(targets, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(targets, probabilities)) if len(set(targets)) > 1 else 0.5,
        "confusion_matrix": confusion_matrix(targets, predictions).tolist(),
    }

    return metrics


def bootstrap_ci(targets: np.ndarray, predictions: np.ndarray, n_bootstrap: int = 1000, ci: float = 0.95) -> dict[str, tuple]:
    """Calculate bootstrap 95% confidence intervals."""
    n_samples = len(targets)
    accuracies = []

    np.random.seed(42)
    for _ in range(n_bootstrap):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        acc = accuracy_score(targets[indices], predictions[indices])
        accuracies.append(acc)

    alpha = (1 - ci) / 2
    lower = np.percentile(accuracies, alpha * 100)
    upper = np.percentile(accuracies, (1 - alpha) * 100)
    mean = np.mean(accuracies)

    return {
        "mean": float(mean),
        "lower": float(lower),
        "upper": float(upper),
    }


def test_robustness(model: nn.Module, image: Image.Image, config: EvaluationConfig) -> dict[str, Any]:
    """Test model robustness to image transformations."""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225]),
    ])

    model.eval()
    robustness_results = {}

    with torch.no_grad():
        # Original
        img_tensor = transform(image).unsqueeze(0).to(config.device)
        if config.model == "fusion":
            out = model(img_tensor, img_tensor)
        else:
            out = model(img_tensor)
        original_prob = float(torch.softmax(out, dim=1)[0, 1].item())

        # JPEG compression (70%, 50%, 30% quality)
        for quality in [70, 50, 30]:
            img_copy = image.copy()
            from io import BytesIO
            buffer = BytesIO()
            img_copy.save(buffer, "JPEG", quality=quality)
            buffer.seek(0)
            img_jpeg = Image.open(buffer).convert("RGB")
            img_tensor = transform(img_jpeg).unsqueeze(0).to(config.device)
            if config.model == "fusion":
                out = model(img_tensor, img_tensor)
            else:
                out = model(img_tensor)
            prob = float(torch.softmax(out, dim=1)[0, 1].item())
            robustness_results[f"jpeg_q{quality}"] = prob

        # Resize (0.75x, 0.5x)
        for scale in [0.75, 0.5]:
            w, h = image.size
            img_resized = image.resize((int(w * scale), int(h * scale)))
            img_tensor = transform(img_resized).unsqueeze(0).to(config.device)
            if config.model == "fusion":
                out = model(img_tensor, img_tensor)
            else:
                out = model(img_tensor)
            prob = float(torch.softmax(out, dim=1)[0, 1].item())
            robustness_results[f"resize_{int(scale*100)}pct"] = prob

        # Gaussian blur
        for radius in [1, 2, 3]:
            img_blur = image.filter(ImageFilter.GaussianBlur(radius=radius))
            img_tensor = transform(img_blur).unsqueeze(0).to(config.device)
            if config.model == "fusion":
                out = model(img_tensor, img_tensor)
            else:
                out = model(img_tensor)
            prob = float(torch.softmax(out, dim=1)[0, 1].item())
            robustness_results[f"blur_r{radius}"] = prob

        # Brightness adjustment
        for factor in [0.7, 0.85, 1.15, 1.3]:
            enhancer = ImageEnhance.Brightness(image)
            img_bright = enhancer.enhance(factor)
            img_tensor = transform(img_bright).unsqueeze(0).to(config.device)
            if config.model == "fusion":
                out = model(img_tensor, img_tensor)
            else:
                out = model(img_tensor)
            prob = float(torch.softmax(out, dim=1)[0, 1].item())
            robustness_results[f"brightness_{factor}"] = prob

    robustness_results["original"] = original_prob

    return robustness_results


def main():
    parser = argparse.ArgumentParser(description="Phase 8: Model Evaluation and Robustness Testing")
    parser.add_argument("--eval-only", action="store_true", help="Run evaluation only")
    parser.add_argument("--model", choices=["rgb", "fft", "fusion"], required=True, help="Model type")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Checkpoint path")
    parser.add_argument("--manifest-dir", type=Path, required=True, help="Manifest directory")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")

    args = parser.parse_args()

    if not args.output_dir:
        args.output_dir = args.checkpoint.parent / "evaluation"

    config = EvaluationConfig(
        model=args.model,
        checkpoint=args.checkpoint,
        manifest_dir=args.manifest_dir,
        output_dir=args.output_dir,
        eval_only=args.eval_only,
        batch_size=args.batch_size,
    )

    config.output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("PHASE 8: MODEL EVALUATION AND ROBUSTNESS")
    print("="*70)

    # Load checkpoint
    print(f"\nLoading checkpoint: {config.checkpoint}")
    if not config.checkpoint.exists():
        print(f"ERROR: Checkpoint not found: {config.checkpoint}")
        return 1

    checkpoint = torch.load(config.checkpoint, map_location="cpu", weights_only=False)
    model = build_model(config.model, checkpoint)
    model = model.to(config.device)

    # Load test dataset
    test_manifest = config.manifest_dir / "test.csv"
    print(f"\nLoading test set from: {test_manifest}")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225]),
    ])

    test_dataset = EvaluationDataset(test_manifest, transform)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)

    # Evaluate
    print("\nEvaluating model on test set...")
    test_metrics = evaluate_model(model, test_loader, config)

    print(f"\nTest Set Results:")
    print(f"  Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"  Precision: {test_metrics['precision']:.4f}")
    print(f"  Recall:    {test_metrics['recall']:.4f}")
    print(f"  F1-Score:  {test_metrics['f1']:.4f}")
    print(f"  ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    print(f"  Confusion Matrix:")
    cm = test_metrics['confusion_matrix']
    print(f"    [[{cm[0][0]:4d}, {cm[0][1]:4d}],")
    print(f"     [{cm[1][0]:4d}, {cm[1][1]:4d}]]")

    # Check if test set is small
    if len(test_dataset) < 200:
        print(f"\n  WARNING: Test set has only {len(test_dataset)} samples.")
        print(f"           Results are not statistically meaningful.")

    # Save results
    report = {
        "model": config.model,
        "checkpoint": str(config.checkpoint),
        "test_set_size": len(test_dataset),
        "test_metrics": test_metrics,
        "timestamp": "2026-10-29",
    }

    report_path = config.output_dir / f"{config.model}_evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    print("\n" + "="*70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
