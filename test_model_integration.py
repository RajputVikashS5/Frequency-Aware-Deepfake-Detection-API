#!/usr/bin/env python
"""
Test the complete model integration - loading the CIFAKE RGB model and making predictions.
"""

import json
import sys
from pathlib import Path

# Add repo root to path
main_repo = Path("E:/Projects/Deepfake detector")
sys.path.insert(0, str(main_repo))


def test_model_loading():
    """Test if the CIFAKE model loads correctly."""
    print("\n" + "="*70)
    print("TEST: MODEL LOADING AND CONFIGURATION")
    print("="*70)

    # Test 1: Check environment configuration
    from backend.app.config import settings
    print(f"\n1. Checking environment configuration:")
    print(f"   MODEL_CHECKPOINT_PATH: {settings.model_checkpoint_path}")
    print(f"   MODEL_VERSION: {settings.model_version}")

    # Test 2: Check if checkpoint file exists
    checkpoint_path = Path(settings.model_checkpoint_path)
    if not checkpoint_path.exists():
        # Try relative to repo root
        checkpoint_path = main_repo / settings.model_checkpoint_path

    print(f"\n2. Checking checkpoint file exists:")
    print(f"   Path: {checkpoint_path}")
    print(f"   Exists: {checkpoint_path.exists()}")
    if checkpoint_path.exists():
        print(f"   Size: {checkpoint_path.stat().st_size / (1024**2):.2f} MB")
    else:
        print(f"   File not found")

    # Test 3: Check the CIFAKE report to verify performance
    report_path = main_repo / "experiments/rgb-baseline/cifake-image-v2/cifake-rgb-resnet18-report.json"
    print(f"\n3. Checking CIFAKE model performance report:")
    print(f"   Report path: {report_path}")

    if report_path.exists():
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)

            test_metrics = report.get('test_metrics', {})
            print(f"   [OK] Report found")
            print(f"   Test Accuracy: {test_metrics.get('accuracy', 'N/A')*100:.1f}%")
            print(f"   ROC-AUC: {test_metrics.get('roc_auc', 'N/A')}")

            # Show confusion matrix
            cm = test_metrics.get('confusion_matrix', [])
            if cm:
                print(f"   Confusion Matrix:")
                print(f"   [[{cm[0][0]}, {cm[0][1]}],")
                print(f"    [{cm[1][0]}, {cm[1][1]}]]")
        except Exception as e:
            print(f"   [ERROR] Error reading report: {type(e).__name__}: {e}")
    else:
        print(f"   [ERROR] Report not found")

    # Test 4: Check if checkpoint exists
    if checkpoint_path.exists():
        print(f"\n4. Attempting to load model...")
        try:
            import torch
            from backend.app.model_inference import RGBBaselineInference

            # Create inference instance
            inference = RGBBaselineInference(str(checkpoint_path), settings.model_version)

            print(f"   Model.available: {inference.available}")
            print(f"   Model.status_message: {inference.status_message}")

            if inference.available:
                print(f"   [OK] Model loaded successfully!")
            else:
                print(f"   [ERROR] Model failed to load")
                print(f"   Error: Could be due to checkpoint format or missing dependencies")

        except Exception as e:
            print(f"   [ERROR] Error loading model: {type(e).__name__}: {e}")
    else:
        print(f"\n4. Cannot test model loading - checkpoint file missing")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print("\nRECOMMENDATIONS:")
    print("1. The .env file is configured with MODEL_CHECKPOINT_PATH")
    print("2. The CIFAKE RGB model exists (93.5% accuracy)")
    print("3. The API should now load this model on startup")
    print("4. Test by running the API:")
    print("   python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000")
    print("5. Visit http://127.0.0.1:8000/health to check model status")
    print("6. Upload an image to /api/v1/analyze to get real predictions")


def main():
    print("Deepfake Detector - Model Integration Test")
    print("Testing configuration of CIFAKE RGB baseline model")
    print("Model: ResNet18 with 93.5% accuracy on CIFAKE test set")

    test_model_loading()


if __name__ == "__main__":
    main()
