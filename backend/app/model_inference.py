"""Safe loading and single-image inference for a trained RGB baseline."""

from __future__ import annotations

import io
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image

# Ensure repository root and backend directory are on sys.path
_repo_root = str(Path(__file__).resolve().parents[2])
_backend_dir = str(Path(__file__).resolve().parents[1])
for _p in (_repo_root, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from backend.app.preprocessing import preprocess_rgb
    from backend.training.rgb_baseline import build_model
except ModuleNotFoundError:
    try:
        from app.preprocessing import preprocess_rgb
        from training.rgb_baseline import build_model
    except (ImportError, ValueError):
        from .preprocessing import preprocess_rgb
        from ..training.rgb_baseline import build_model


@dataclass(frozen=True)
class InferenceResult:
    prediction: str
    score: float
    model_version: str
    task: str
    label_semantics: str
    score_type: str
    reason: str | None = None


class RGBBaselineInference:
    """Loads only an explicit, validated checkpoint; never fabricates a result."""

    def __init__(self, checkpoint_path: str, model_version: str = "") -> None:
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.model_version = model_version
        self._model: torch.nn.Module | None = None
        self._error: str | None = None
        self._error_at = 0.0
        self.task = ""
        self.label_semantics = ""
        self.score_type = ""
        self._error_retry_seconds = 10.0
        self.threshold = 0.5
        self.temperature = 1.0
        self.uncertainty_band = (0.35, 0.65)
        self.training_resolution = None

    @property
    def available(self) -> bool:
        self._load_if_configured()
        return self._model is not None

    @property
    def status_message(self) -> str:
        self._load_if_configured()
        if self._model is not None:
            return "A trained RGB baseline checkpoint is loaded. Scores are uncalibrated model probabilities."
        if not self.checkpoint_path:
            return "No trained RGB baseline checkpoint is configured."
        return "The configured model checkpoint could not be loaded." if self._error else "No trained RGB baseline checkpoint is available."

    def _load_if_configured(self) -> None:
        if self._model is not None or self.checkpoint_path is None:
            return
        if self._error is not None and time.monotonic() - self._error_at < self._error_retry_seconds:
            return
        self._error = None
        if not self.checkpoint_path.is_file():
            self._error = "checkpoint file is missing"
            self._error_at = time.monotonic()
            return
        try:
            payload = torch.load(self.checkpoint_path, map_location="cpu", weights_only=True)
            state = payload.get("model_state") if isinstance(payload, dict) else None
            if not isinstance(state, dict):
                raise ValueError("checkpoint has no model_state")
            checkpoint_config = payload.get("config", {})
            if not isinstance(checkpoint_config, dict):
                raise ValueError("checkpoint config is invalid")
            self.task = str(checkpoint_config.get("task", ""))
            self.label_semantics = str(checkpoint_config.get("label_semantics", ""))
            self.score_type = str(
                checkpoint_config.get("score_type", "uncalibrated model probability")
            )
            self.threshold = float(checkpoint_config.get("threshold", 0.5))
            self.temperature = max(float(checkpoint_config.get("temperature", 1.0)), 1e-6)
            band = checkpoint_config.get("uncertainty_band", [0.35, 0.65])
            if not isinstance(band, (list, tuple)) or len(band) != 2:
                raise ValueError("checkpoint uncertainty_band is invalid")
            self.uncertainty_band = (float(band[0]), float(band[1]))
            self.training_resolution = checkpoint_config.get("training_resolution")
            if not self.task or not self.label_semantics:
                raise ValueError("checkpoint is missing task or label_semantics metadata")
            model = build_model(pretrained=False)
            model.load_state_dict(state, strict=True)
            model.eval()
            self._model = model
            if not self.model_version:
                self.model_version = f"rgb-resnet18:{self.checkpoint_path.stem}"
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            self._error = str(exc)
            self._error_at = time.monotonic()

    def reload(self) -> None:
        """Clear cached model/error state and retry loading on the next access."""
        self._model = None
        self._error = None
        self._error_at = 0.0

    def predict(self, image_bytes: bytes) -> InferenceResult:
        if not self.available or self._model is None:
            raise RuntimeError("No trained model is available for inference")
        array = preprocess_rgb(image_bytes)
        image = torch.from_numpy(np.ascontiguousarray(array)).unsqueeze(0)
        with torch.no_grad():
            logits = self._model(image) / self.temperature
            probability = float(torch.softmax(logits, dim=1)[0, 1].item())
        reason = None
        prediction = "likely_manipulated" if probability >= self.threshold else "likely_real"
        if self.task == "cifake":
            with Image.open(io.BytesIO(image_bytes)) as source:
                short_side = min(source.size)
            if short_side > 64:
                prediction = "inconclusive"
                reason = (
                    "This CIFAKE-only checkpoint was trained on 32x32 images; "
                    "the uploaded image is outside that resolution domain."
                )
        low, high = self.uncertainty_band
        if low <= probability <= high:
            prediction = "inconclusive"
            reason = "The calibrated model score is inside its configured uncertainty band."
        return InferenceResult(
            prediction=prediction,
            score=probability,
            model_version=self.model_version,
            task=self.task,
            label_semantics=self.label_semantics,
            score_type=self.score_type,
            reason=reason,
        )
