"""Reproducible, checkpoint-backed evaluation for image classifiers."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
from PIL import Image, ImageFilter
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from backend.app.frequency import preprocess_fft
from backend.app.preprocessing import preprocess_rgb
from backend.training.fft_baseline import build_fft_model
from backend.training.fusion_baseline import RGBFFTFusionModel
from backend.training.rgb_baseline import (
    RGBManifestDataset,
    build_model,
    read_manifest,
)


def _metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    predictions = (scores >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, scores)) if len(set(labels)) == 2 else None,
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def bootstrap_intervals(
    labels: np.ndarray,
    scores: np.ndarray,
    *,
    seed: int = 42,
    iterations: int = 1000,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {name: [] for name in ("accuracy", "precision", "recall", "f1", "roc_auc")}
    for _ in range(iterations):
        indexes = rng.integers(0, len(labels), size=len(labels))
        sample_labels = labels[indexes]
        sample_scores = scores[indexes]
        result = _metrics(sample_labels, sample_scores)
        for name in values:
            if result[name] is not None:
                values[name].append(result[name])
    return {
        name: {
            "lower_95": float(np.percentile(samples, 2.5)) if samples else 0.0,
            "upper_95": float(np.percentile(samples, 97.5)) if samples else 0.0,
        }
        for name, samples in values.items()
    }


def _open_image(path: str) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB").copy()


def _fft_tensor(image: Image.Image, mode: str) -> torch.Tensor:
    if mode == "native":
        native = preprocess_fft(image, target_size=(32, 32))
        padded = np.zeros((3, 224, 224), dtype=np.float32)
        start = (224 - 32) // 2
        padded[:, start:start + 32, start:start + 32] = native
        return torch.from_numpy(padded)
    return torch.from_numpy(preprocess_fft(image))


def _scores(
    model_name: str,
    model: torch.nn.Module,
    rows: list[Any],
    *,
    fft_input: str,
    transform: Callable[[Image.Image], Image.Image] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    labels: list[int] = []
    scores: list[float] = []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            image = _open_image(row.path)
            if transform:
                image = transform(image)
            rgb = torch.from_numpy(preprocess_rgb(image)).unsqueeze(0)
            fft = _fft_tensor(image, fft_input).unsqueeze(0)
            if model_name == "rgb":
                logits = model(rgb)
            elif model_name == "fft":
                logits = model(fft)
            else:
                logits = model(rgb, fft)
            labels.append(row.label)
            scores.append(float(torch.softmax(logits, dim=1)[0, 1]))
    return np.asarray(labels), np.asarray(scores)


def _load_model(model_name: str, checkpoint: Path) -> torch.nn.Module:
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if model_name == "rgb":
        model = build_model(pretrained=False)
    elif model_name == "fft":
        model = build_fft_model(pretrained=False)[0]
    else:
        model = RGBFFTFusionModel(pretrained=False)
    model.load_state_dict(payload["model_state"], strict=True)
    return model


def evaluate(
    model_name: str,
    checkpoint: Path,
    manifest_dir: Path,
    *,
    fft_input: str = "upsampled",
    seed: int = 42,
    bootstrap_iterations: int = 1000,
) -> dict[str, Any]:
    rows = read_manifest(manifest_dir / "test.csv", "test")
    model = _load_model(model_name, checkpoint)
    labels, scores = _scores(model_name, model, rows, fft_input=fft_input)
    result: dict[str, Any] = {
        "model": model_name,
        "checkpoint": str(checkpoint),
        "test_count": len(rows),
        "statistical_warning": len(rows) < 200,
        "metrics": _metrics(labels, scores),
        "bootstrap_95": bootstrap_intervals(
            labels, scores, seed=seed, iterations=bootstrap_iterations
        ),
        "fft_input": fft_input,
        "trivial_baseline": {},
        "robustness": {},
    }

    features = []
    for row in rows:
        array = np.asarray(_open_image(row.path), dtype=np.float32) / 255.0
        features.append([float(array.mean()), float(array.std())])
    baseline = LogisticRegression(random_state=seed).fit(features, labels)
    baseline_scores = baseline.predict_proba(features)[:, 1]
    result["trivial_baseline"] = _metrics(labels, baseline_scores)

    corruptions: dict[str, Callable[[Image.Image], Image.Image]] = {
        "jpeg_q30": lambda image: Image.open(
            io.BytesIO(_encode_jpeg(image, 30))
        ).convert("RGB"),
        "jpeg_q60": lambda image: Image.open(
            io.BytesIO(_encode_jpeg(image, 60))
        ).convert("RGB"),
        "jpeg_q90": lambda image: Image.open(
            io.BytesIO(_encode_jpeg(image, 90))
        ).convert("RGB"),
        "resize": lambda image: image.resize((16, 16)).resize((224, 224)),
        "blur": lambda image: image.filter(ImageFilter.GaussianBlur(1.0)),
        "noise": lambda image: _add_noise(image, seed),
    }
    for name, transform in corruptions.items():
        corrupted_labels, corrupted_scores = _scores(
            model_name, model, rows, fft_input=fft_input, transform=transform
        )
        result["robustness"][name] = _metrics(corrupted_labels, corrupted_scores)
    return result


def _encode_jpeg(image: Image.Image, quality: int) -> bytes:
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality)
    return output.getvalue()


def _add_noise(image: Image.Image, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    array = np.asarray(image, dtype=np.int16)
    noise = rng.normal(0, 8, size=array.shape)
    return Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8), "RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-only", action="store_true", required=True)
    parser.add_argument("--model", choices=("rgb", "fft", "fusion"), required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--fft-input", choices=("native", "upsampled"), default="upsampled")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    args = parser.parse_args()
    report = evaluate(
        args.model,
        args.checkpoint,
        args.manifest_dir,
        fft_input=args.fft_input,
        seed=args.seed,
        bootstrap_iterations=args.bootstrap_iterations,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
