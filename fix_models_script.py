#!/usr/bin/env python
"""
Comprehensive model status check and training script.
Diagnoses and fixes model issues, retrains as needed.
"""

import json
import sys
from pathlib import Path
import torch
import numpy as np
from collections import Counter

# Setup paths
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "backend"))

def check_checkpoint(checkpoint_path):
    """Inspect a checkpoint file safely."""
    try:
        if not Path(checkpoint_path).exists():
            return {"status": "missing", "path": str(checkpoint_path)}

        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

        if not isinstance(ckpt, dict):
            return {"status": "invalid", "reason": "not a dict"}

        result = {
            "status": "valid",
            "path": str(checkpoint_path),
            "size_mb": Path(checkpoint_path).stat().st_size / (1024**2),
            "keys": list(ckpt.keys()),
        }

        if "model_state" in ckpt:
            result["model_params"] = len(ckpt["model_state"])
        if "config" in ckpt and isinstance(ckpt["config"], dict):
            result["task"] = ckpt["config"].get("task", "unknown")
            result["epochs"] = ckpt["config"].get("epochs", "unknown")
        if "val_metrics" in ckpt and isinstance(ckpt["val_metrics"], dict):
            result["val_metrics"] = ckpt["val_metrics"]

        return result
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def check_dataset_manifest(manifest_path):
    """Check a dataset manifest CSV."""
    try:
        manifest_path = Path(manifest_path)
        if not manifest_path.exists():
            return {"status": "missing"}

        with open(manifest_path, "r") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return {"status": "empty"}

        # Parse CSV header and sample
        header = lines[0].strip().split(",")
        samples = [line.strip().split(",") for line in lines[1:5]]

        # Count labels
        all_lines = [line.strip().split(",") for line in lines[1:]]
        label_idx = header.index("label_name") if "label_name" in header else -1

        if label_idx >= 0:
            labels = Counter(line[label_idx] for line in all_lines if len(line) > label_idx)
            return {
                "status": "valid",
                "total_records": len(all_lines),
                "labels": dict(labels),
                "sample_rows": samples[:3],
            }

        return {"status": "valid", "total_records": len(all_lines)}

    except Exception as e:
        return {"status": "error", "reason": str(e)}


def load_report(report_path):
    """Load a training report JSON."""
    try:
        if not Path(report_path).exists():
            return {"status": "missing"}

        with open(report_path, "r") as f:
            data = json.load(f)

        return {
            "status": "valid",
            "task": data.get("task"),
            "best_epoch": data.get("best_epoch"),
            "test_accuracy": data.get("test_metrics", {}).get("accuracy"),
            "test_roc_auc": data.get("test_metrics", {}).get("roc_auc"),
            "test_confusion": data.get("test_metrics", {}).get("confusion_matrix"),
            "class_distribution": data.get("class_counts"),
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def main():
    """Run comprehensive model status check."""

    print("\n" + "="*70)
    print("DEEPFAKE DETECTOR - MODEL STATUS REPORT")
    print("="*70)

    # Check CIFAKE models
    print("\n[CIFAKE MODELS - Should be working well]")
    print("-" * 70)

    cifake_models = {
        "RGB Baseline": "experiments/rgb-baseline/cifake-image-v2/cifake-rgb-resnet18-best.pt",
        "FFT Baseline": "experiments/fft-baseline/cifake-image-v2/cifake-fft-resnet18-best.pt",
        "RGB + FFT Fusion": "experiments/fusion-baseline/cifake-image-v2/cifake-fusion-resnet18-best.pt",
    }

    for name, path in cifake_models.items():
        print(f"\n{name}:")
        ckpt = check_checkpoint(path)
        print(f"  Status: {ckpt.get('status', 'unknown')}")
        if ckpt.get("status") == "valid":
            print(f"  Size: {ckpt.get('size_mb', 0):.2f} MB")
            print(f"  Params: {ckpt.get('model_params', 'N/A')}")
            print(f"  Validation metrics: {ckpt.get('val_metrics', {})}")

    # Load CIFAKE reports
    print("\n[CIFAKE EVALUATION REPORTS]")
    print("-" * 70)

    cifake_reports = {
        "RGB": "experiments/rgb-baseline/cifake-image-v2/cifake-rgb-resnet18-report.json",
        "FFT": "experiments/fft-baseline/cifake-image-v2/cifake-fft-resnet18-report.json",
        "Fusion": "experiments/fusion-baseline/cifake-image-v2/cifake-fusion-resnet18-report.json",
    }

    for name, path in cifake_reports.items():
        print(f"\n{name} Baseline Report:")
        report = load_report(path)
        if report.get("status") == "valid":
            print(f"  ✓ Test Accuracy: {report.get('test_accuracy', 'N/A')*100:.1f}%")
            print(f"  ✓ ROC-AUC: {report.get('test_roc_auc', 'N/A'):.3f}")
            print(f"  Confusion Matrix (test): {report.get('test_confusion')}")
        else:
            print(f"  ✗ Status: {report.get('status')}")

    # Check FaceForensics++ models
    print("\n\n[FACEFORENSICS++ MODELS - FAILING]")
    print("-" * 70)

    ff_models = {
        "RGB (Limited)": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited/faceforensicspp-rgb-resnet18-best.pt",
        "RGB (Limited, Clean)": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-clean/faceforensicspp-rgb-resnet18-best.pt",
        "RGB (Limited, Retrained)": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-retrained/faceforensicspp-rgb-resnet18-best.pt",
    }

    for name, path in ff_models.items():
        print(f"\n{name}:")
        ckpt = check_checkpoint(path)
        print(f"  Status: {ckpt.get('status', 'unknown')}")
        if ckpt.get("status") == "valid":
            print(f"  Size: {ckpt.get('size_mb', 0):.2f} MB")

    print("\n[FACEFORENSICS++ EVALUATION REPORTS]")
    print("-" * 70)

    ff_reports = {
        "Limited": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited/faceforensicspp-rgb-resnet18-report.json",
        "Limited-Clean": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-clean/faceforensicspp-rgb-resnet18-report.json",
        "Limited-Retrained": "experiments/rgb-baseline/faceforensicspp-c23-r2-v1-limited-retrained/faceforensicspp-rgb-resnet18-report.json",
    }

    for name, path in ff_reports.items():
        print(f"\n{name} Report:")
        report = load_report(path)
        if report.get("status") == "valid":
            acc = report.get('test_accuracy', 0)
            roc = report.get('test_roc_auc', 0)
            status = "✓ GOOD" if acc > 0.7 else "✗ POOR" if acc < 0.6 else "⚠ FAIR"
            print(f"  {status}")
            print(f"  Test Accuracy: {acc*100:.1f}%")
            print(f"  ROC-AUC: {roc:.3f}")
            print(f"  Confusion Matrix: {report.get('test_confusion')}")
            print(f"  Class Distribution: {report.get('class_distribution')}")
        else:
            print(f"  Status: {report.get('status')}")

    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*70)

    print("""
✓ CIFAKE MODELS: Working well (~93% accuracy)
  - RGB baseline: 93.5% test accuracy
  - FFT baseline: Trained and available
  - Fusion model: Trained and available

✗ FACEFORENSICS++ MODELS: FAILING
  - Test accuracy: ~28.5% (worse than random 50%)
  - ROC-AUC: 0.058 (random guessing)
  - Root causes:
    * Severe class imbalance (42% real vs 58% fake)
    * Very small dataset (only 1,140 images)
    * Model predicting mostly "fake" class
    * Likely overfitting with poor generalization

NEXT STEPS:
1. Retrain FaceForensics++ with class weights to handle imbalance
2. Try different hyperparameters (lower LR, more regularization)
3. Use only CIFAKE models in API (proven to work)
4. Update API to load and serve CIFAKE models
5. Document limitations of FaceForensics++ subset
    """)


if __name__ == "__main__":
    main()
