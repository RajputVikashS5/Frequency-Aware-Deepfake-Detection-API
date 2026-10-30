"""External evaluation utilities for the independent SpectraGuard tasks.

This module deliberately keeps dataset manifests and metrics task-scoped. It
reuses the production preprocessing and model builders instead of introducing
an evaluation-only input contract.
"""

from __future__ import annotations

import io
import json
import logging
import math
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageFile, ImageFilter, UnidentifiedImageError
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from backend.app.frequency import preprocess_fft
from backend.app.preprocessing import preprocess_rgb
from backend.training.fft_baseline import build_fft_model
from backend.training.fusion_baseline import RGBFFTFusionModel
from backend.training.rgb_baseline import build_model

logger = logging.getLogger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
CLASS_NAMES = {0: "Real / Human", 1: "Fake / AI"}


@dataclass(frozen=True)
class ModelSpec:
    task: str
    model_type: str
    checkpoint: Path
    expected_task: str
    input_contract: str


@dataclass
class LoadedModel:
    spec: ModelSpec
    model: torch.nn.Module | None
    status: str
    reason: str | None = None
    config: dict[str, Any] | None = None


def _safe_load_checkpoint(path: Path) -> Any:
    """Load only restricted tensor/state-dict checkpoint objects."""

    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint does not exist: {path}")
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise ValueError(
            f"Checkpoint is not compatible with safe weights-only loading: {path}. "
            "Re-export it as a state-dict checkpoint offline."
        ) from exc


def _state_and_config(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("model_state", "model_state_dict", "state_dict"):
            if isinstance(payload.get(key), dict):
                config = payload.get("config", {})
                return payload[key], config if isinstance(config, dict) else {}
        if payload and all(isinstance(value, torch.Tensor) for value in payload.values()):
            return payload, {}
    raise ValueError("Checkpoint does not contain a supported state dictionary.")


def _class_mapping(config: dict[str, Any]) -> dict[int, int]:
    mapping = config.get("class_mapping", config.get("classes"))
    if isinstance(mapping, dict):
        normalized: dict[int, int] = {}
        for key, value in mapping.items():
            name = str(key).strip().lower()
            index = int(value)
            if name in {"real", "human", "authentic"}:
                normalized[index] = 0
            elif name in {"fake", "ai", "generated", "manipulated"}:
                normalized[index] = 1
        if len(normalized) == 2:
            return normalized
    label_semantics = str(config.get("label_semantics", "")).lower()
    if label_semantics in {"real/fake", "manipulated_vs_real", "ai_generated_vs_real"}:
        return {0: 0, 1: 1}
    raise ValueError("Checkpoint class mapping cannot be verified from metadata.")


def load_evaluation_model(spec: ModelSpec, device: torch.device) -> LoadedModel:
    try:
        payload = _safe_load_checkpoint(spec.checkpoint)
        state, config = _state_and_config(payload)
        class_mapping = _class_mapping(config)
        if class_mapping != {0: 0, 1: 1}:
            return LoadedModel(spec, None, "skipped", "Class order is not real=0/fake=1.", config)
        if spec.model_type == "rgb":
            model = build_model(pretrained=False)
        elif spec.model_type == "fft":
            model = build_fft_model(pretrained=False)[0]
        elif spec.model_type == "fusion":
            model = RGBFFTFusionModel(pretrained=False)
        else:
            raise ValueError(f"Unsupported model type: {spec.model_type}")
        model.load_state_dict(state, strict=True)
        model.to(device).eval()
        with torch.inference_mode():
            rgb = torch.zeros((1, 3, 224, 224), device=device)
            fft = torch.zeros((1, 3, 224, 224), device=device)
            logits = model(rgb) if spec.model_type == "rgb" else (
                model(fft) if spec.model_type == "fft" else model(rgb, fft)
            )
        if tuple(logits.shape) != (1, 2):
            raise ValueError(f"Expected output shape (1, 2), received {tuple(logits.shape)}")
        return LoadedModel(spec, model, "loaded", config=config)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Skipping %s: %s", spec.checkpoint, exc)
        return LoadedModel(spec, None, "skipped", str(exc))


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        root = destination.resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        archive.extractall(destination)


def download_kaggle_dataset(dataset_id: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    archives = sorted(destination.glob("*.zip"))
    if archives:
        return archives[0]
    command = ["kaggle", "datasets", "download", "-d", dataset_id, "-p", str(destination)]
    result = subprocess.run(command, capture_output=True, text=False, check=False)
    if result.returncode:
        error = result.stderr.decode(errors="replace")
        raise RuntimeError(f"Kaggle download failed for {dataset_id}: {error[-1000:]}")
    archives = sorted(destination.glob("*.zip"))
    if not archives:
        raise FileNotFoundError(f"Kaggle returned no archive in {destination}")
    return archives[0]


def inspect_dataset(root: Path) -> dict[str, Any]:
    files = [path for path in root.rglob("*") if path.is_file()]
    csv_files = sorted(path for path in files if path.suffix.lower() == ".csv")
    image_files = sorted(path for path in files if path.suffix.lower() in IMAGE_EXTENSIONS)
    csv_info = []
    for path in csv_files:
        frame = pd.read_csv(path, nrows=5)
        csv_info.append({"path": path, "columns": list(frame.columns), "sample": frame})
    return {"files": files, "csv_files": csv_files, "image_files": image_files, "csv_info": csv_info}


def _resolve_path(raw: Any, csv_path: Path, root: Path) -> Path | None:
    value = str(raw).strip()
    if not value or value.lower() in {"nan", "none"}:
        return None
    candidate = Path(value)
    candidates = [candidate] if candidate.is_absolute() else [csv_path.parent / candidate, root / candidate]
    for item in candidates:
        resolved = item.resolve()
        if resolved.is_file() and root.resolve() in resolved.parents:
            return resolved
    return None


def build_ai_manifest(root: Path, sample_per_class: int | None = None, seed: int = 42) -> pd.DataFrame:
    csv_path = next((path for path in root.rglob("train.csv") if path.is_file()), None)
    if csv_path is None:
        raise FileNotFoundError("AI dataset train.csv was not found.")
    frame = pd.read_csv(csv_path)
    required = {"file_name", "label"}
    if not required.issubset(frame.columns):
        raise ValueError(f"AI dataset schema changed; expected {required}, got {set(frame.columns)}")
    rows = []
    for _, row in frame.iterrows():
        path = _resolve_path(row["file_name"], csv_path, root)
        if path is None or int(row["label"]) not in {0, 1}:
            continue
        rows.append({
            "path": str(path),
            "label": int(row["label"]),
            "label_name": CLASS_NAMES[int(row["label"])],
            "dataset": "ai_generated",
            "image_id": path.stem,
            "source": "train.csv",
        })
    manifest = pd.DataFrame(rows).drop_duplicates("path")
    return balanced_sample(manifest, sample_per_class, seed)


def _validate_image(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, UnidentifiedImageError):
        return False


def build_face_manifest(
    csv_path: Path,
    cache: Path,
    sample_per_class: int = 100,
    seed: int = 42,
    session: Any = None,
) -> pd.DataFrame:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    frame = pd.read_csv(csv_path)
    required = {"image_id", "image_url", "label"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Face dataset schema changed; expected {required}")
    frame["label"] = frame["label"].astype(str).str.strip().str.upper()
    frame = frame[frame["label"].isin({"REAL", "FAKE"})].copy()
    cache.mkdir(parents=True, exist_ok=True)
    if session is None:
        retry = Retry(total=3, connect=3, read=3, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))
    rows = []
    for label_name in ("REAL", "FAKE"):
        candidates = frame[frame["label"] == label_name].sample(frac=1, random_state=seed)
        valid = 0
        for _, item in candidates.iterrows():
            if valid >= sample_per_class:
                break
            destination = cache / f"{label_name.lower()}_{item['image_id']}.jpg"
            try:
                if not _validate_image(destination):
                    response = session.get(str(item["image_url"]), timeout=(10, 25))
                    response.raise_for_status()
                    with Image.open(io.BytesIO(response.content)) as image:
                        image.convert("RGB").save(destination, "JPEG", quality=95)
                if _validate_image(destination):
                    rows.append({
                        "path": str(destination.resolve()), "label": 0 if label_name == "REAL" else 1,
                        "label_name": CLASS_NAMES[0 if label_name == "REAL" else 1],
                        "dataset": "face_dataset_external_test", "image_id": str(item["image_id"]),
                        "source": str(item.get("source", "")),
                    })
                    valid += 1
            except (OSError, ValueError, requests.RequestException) as exc:
                logger.info("Skipping face image %s: %s", item["image_id"], exc)
    manifest = pd.DataFrame(rows).drop_duplicates("path").reset_index(drop=True)
    return balanced_sample(manifest, sample_per_class, seed)


def balanced_sample(manifest: pd.DataFrame, sample_per_class: int | None, seed: int) -> pd.DataFrame:
    if manifest.empty:
        raise ValueError("Manifest contains no valid images.")
    if not {0, 1}.issubset(set(manifest["label"].unique())):
        raise ValueError("Balanced evaluation requires both real=0 and fake=1 classes.")
    count = min(int(manifest["label"].value_counts().min()), sample_per_class or math.inf)
    parts = [
        manifest[manifest["label"] == label].sample(n=int(count), random_state=seed)
        for label in (0, 1)
    ]
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


class EvaluationDataset(torch.utils.data.Dataset):
    def __init__(self, manifest: pd.DataFrame):
        self.manifest = manifest.reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.manifest)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.manifest.iloc[index]
        with Image.open(row["path"]) as source:
            image = source.convert("RGB")
        rgb = torch.from_numpy(preprocess_rgb(image))
        fft = torch.from_numpy(preprocess_fft(image))
        if not torch.isfinite(rgb).all() or not torch.isfinite(fft).all():
            raise ValueError(f"Non-finite preprocessing result: {row['path']}")
        return {"rgb": rgb, "fft": fft, "label": int(row["label"]), "path": row["path"]}


def predict_model(loaded: LoadedModel, manifest: pd.DataFrame, device: torch.device, batch_size: int = 8) -> dict[str, Any]:
    if loaded.model is None:
        raise ValueError(loaded.reason or "Model is unavailable.")
    loader = torch.utils.data.DataLoader(EvaluationDataset(manifest), batch_size=batch_size, shuffle=False, num_workers=0)
    labels, scores, paths = [], [], []
    with torch.inference_mode():
        for batch in loader:
            rgb, fft = batch["rgb"].to(device), batch["fft"].to(device)
            logits = loaded.model(rgb) if loaded.spec.model_type == "rgb" else (
                loaded.model(fft) if loaded.spec.model_type == "fft" else loaded.model(rgb, fft)
            )
            if tuple(logits.shape[1:]) != (2,) or not torch.isfinite(logits).all():
                raise ValueError("Model produced invalid logits.")
            labels.extend(batch["label"].tolist())
            scores.extend(torch.softmax(logits, dim=1)[:, 1].cpu().tolist())
            paths.extend(batch["path"])
    result = {"labels": np.asarray(labels, dtype=int), "scores": np.asarray(scores, dtype=float), "paths": paths}
    result["predictions"] = (result["scores"] >= 0.5).astype(int)
    return result


def calculate_model_metrics(result: dict[str, Any]) -> dict[str, Any]:
    labels, predictions, scores = result["labels"], result["predictions"], result["scores"]
    cm = confusion_matrix(labels, predictions, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    specificity = tn / (tn + fp) if tn + fp else None
    fpr = fp / (fp + tn) if fp + tn else None
    fnr = fn / (fn + tp) if fn + tp else None
    both = len(np.unique(labels)) == 2
    return {
        "total_images": int(len(labels)), "real_images": int((labels == 0).sum()),
        "fake_images": int((labels == 1).sum()), "accuracy": float(accuracy_score(labels, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "specificity": specificity, "false_positive_rate": fpr, "false_negative_rate": fnr,
        "roc_auc": float(roc_auc_score(labels, scores)) if both else None,
        "average_precision": float(average_precision_score(labels, scores)) if both else None,
        "confusion_matrix": cm.tolist(),
    }


def classification_report_dict(result: dict[str, Any]) -> dict[str, Any]:
    return classification_report(result["labels"], result["predictions"], labels=[0, 1],
                                 target_names=[CLASS_NAMES[0], CLASS_NAMES[1]], zero_division=0, output_dict=True)


def bootstrap_intervals(result: dict[str, Any], seed: int = 42, iterations: int = 1000) -> dict[str, dict[str, float | None]]:
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {}
    for _ in range(iterations):
        indexes = rng.integers(0, len(result["labels"]), len(result["labels"]))
        sample = {key: value[indexes] for key, value in result.items() if isinstance(value, np.ndarray)}
        metrics = calculate_model_metrics(sample)
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and value is not None:
                values.setdefault(key, []).append(float(value))
    return {key: {"lower_95": float(np.percentile(value, 2.5)), "upper_95": float(np.percentile(value, 97.5))}
            for key, value in values.items() if value}


def export_results(task: str, model_name: str, result: dict[str, Any], output_root: Path, seed: int = 42) -> dict[str, Path]:
    output = output_root / task
    output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({
        "image_path": result["paths"], "actual_label": result["labels"],
        "predicted_label": result["predictions"], "fake_score": result["scores"],
    })
    frame["actual_name"] = frame["actual_label"].map(CLASS_NAMES)
    frame["predicted_name"] = frame["predicted_label"].map(CLASS_NAMES)
    frame["correct"] = frame["actual_label"] == frame["predicted_label"]
    prediction_path = output / f"{model_name}_predictions.csv"
    frame.to_csv(prediction_path, index=False)
    metrics = calculate_model_metrics(result)
    metrics_path = output / "external_evaluation_metrics.csv"
    summary = pd.DataFrame([{"task": task, "model": model_name, **metrics}])
    summary.to_csv(metrics_path, mode="a", header=not metrics_path.exists(), index=False)
    report_path = output / f"{model_name}_classification_report.json"
    report_path.write_text(json.dumps(classification_report_dict(result), indent=2), encoding="utf-8")
    (output / f"{model_name}_confusion_matrix.csv").write_text(
        pd.DataFrame(metrics["confusion_matrix"], index=["actual_real", "actual_fake"],
                     columns=["predicted_real", "predicted_fake"]).to_csv()
    )
    return {"predictions": prediction_path, "metrics": metrics_path, "report": report_path}


def plot_curves(task: str, results: dict[str, dict[str, Any]], output_root: Path) -> None:
    import matplotlib.pyplot as plt
    output = output_root / task
    output.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 6))
    for name, result in results.items():
        if len(np.unique(result["labels"])) == 2:
            fpr, tpr, _ = roc_curve(result["labels"], result["scores"])
            plt.plot(fpr, tpr, label=f"{name} AUC={roc_auc_score(result['labels'], result['scores']):.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate"); plt.title(f"{task} ROC")
    plt.legend(); plt.tight_layout(); plt.savefig(output / "roc_comparison.png", dpi=160); plt.close()
    plt.figure(figsize=(8, 6))
    for name, result in results.items():
        if len(np.unique(result["labels"])) == 2:
            precision, recall, _ = precision_recall_curve(result["labels"], result["scores"])
            plt.plot(recall, precision, label=f"{name} AP={average_precision_score(result['labels'], result['scores']):.3f}")
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title(f"{task} precision-recall")
    plt.legend(); plt.tight_layout(); plt.savefig(output / "precision_recall_comparison.png", dpi=160); plt.close()
