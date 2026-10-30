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

# Register safe globals for weights_only=True checkpoint loading
import torch.serialization
import pathlib
import numpy

try:
    torch.serialization.add_safe_globals([
        pathlib.WindowsPath,
        pathlib.PosixPath,
        numpy.core.multiarray.scalar,
        numpy._core.multiarray.scalar,
    ])
except Exception:
    pass  # May fail on some configurations, safe fallback will work

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
    real_probability: float
    fake_probability: float
    model_version: str
    task: str
    label_semantics: str
    score_type: str
    processing_time_ms: float
    reason: str | None = None
    calibrated: bool = False
    calibration_method: str | None = None
    calibration_dataset: str | None = None


# Constant for CIFAKE resolution domain check
_CIFAKE_RESOLUTION_THRESHOLD = 64


def _is_path_within_project(checkpoint_path: Path, project_root: Path) -> bool:
    """Verify checkpoint is within the project directory to prevent path traversal."""
    try:
        checkpoint_path.resolve().relative_to(project_root.resolve())
        return True
    except ValueError:
        return False


class RGBBaselineInference:
    """Loads only an explicit, validated checkpoint; never fabricates a result."""

    def __init__(self, checkpoint_path: str, model_version: str = "") -> None:
        if checkpoint_path:
            candidate = Path(checkpoint_path).expanduser()
            self._checkpoint_was_relative = not candidate.is_absolute()
            self.checkpoint_path = (
                candidate
                if candidate.is_absolute()
                else Path(__file__).resolve().parents[2] / candidate
            )
        else:
            self._checkpoint_was_relative = False
            self.checkpoint_path = None
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
        self.calibrated = False
        self.calibration_method: str | None = None
        self.calibration_dataset: str | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        # Relative configuration must stay inside the project; absolute paths are
        # supported for externally managed checkpoints and test fixtures.
        if self._checkpoint_was_relative and not _is_path_within_project(
            self.checkpoint_path, Path(__file__).resolve().parents[2]
        ):
            self._error = "checkpoint path is outside project directory"
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
            self.label_semantics = str(
                checkpoint_config.get(
                    "label_semantics",
                    {
                        "faceforensicspp": "manipulated_vs_real",
                        "forgerynet": "manipulated_vs_real",
                        "cifake": "ai_generated_vs_real",
                    }.get(self.task, "real/fake"),
                )
            )
            self.score_type = str(
                checkpoint_config.get("score_type", "uncalibrated model probability")
            )
            self.threshold = float(checkpoint_config.get("threshold", 0.5))
            self.temperature = max(float(checkpoint_config.get("temperature", 1.0)), 1e-6)
            band = checkpoint_config.get("uncertainty_band", [0.35, 0.65])
            if isinstance(band, (list, tuple)) and len(band) == 2:
                self.uncertainty_band = (float(band[0]), float(band[1]))
            else:
                self.uncertainty_band = (0.35, 0.65)
            self.training_resolution = checkpoint_config.get("training_resolution", 32)
            self.calibrated = bool(checkpoint_config.get("calibrated", False))
            self.calibration_method = str(checkpoint_config.get("calibration_method", "")) or None
            self.calibration_dataset = str(checkpoint_config.get("calibration_dataset", "")) or None
            if not self.task:
                raise ValueError("checkpoint is missing task metadata")
            model = build_model(pretrained=False)
            model.load_state_dict(state, strict=True)
            model.eval()
            model = model.to(self.device)
            self._model = model
            if not self.model_version:
                self.model_version = f"rgb-resnet18:{self.checkpoint_path.stem}"
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            self._error = str(exc)
            self._error_at = time.monotonic()
        # NOTE: weights_only=False fallback removed for security.
        # Use only checkpoints saved with PyTorch >=1.13 format. If you have
        # older checkpoints, re-export them using torch.save with weights_only=True.

    def reload(self) -> None:
        """Clear cached model/error state and retry loading on the next access."""
        self._model = None
        self._error = None
        self._error_at = 0.0

    def predict(self, image_bytes: bytes) -> InferenceResult:
        if not self.available or self._model is None:
            raise RuntimeError("No trained model is available for inference")
        start_time = time.perf_counter()
        array = preprocess_rgb(image_bytes)
        image = torch.from_numpy(np.ascontiguousarray(array)).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            logits = self._model(image) / self.temperature
            probabilities = torch.softmax(logits, dim=1)[0]
            real_probability = float(probabilities[0].item())
            fake_probability = float(probabilities[1].item())
            probability = fake_probability
        reason = None
        # Task-specific prediction labels
        if self.task == "cifake":
            prediction = "likely_ai_generated" if probability >= self.threshold else "likely_real"
        else:
            # faceforensicspp, forgerynet
            prediction = "likely_manipulated" if probability >= self.threshold else "likely_real"
        if self.task == "cifake" and self.training_resolution is not None:
            with Image.open(io.BytesIO(image_bytes)) as source:
                short_side = min(source.size)
            if short_side > _CIFAKE_RESOLUTION_THRESHOLD:
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
            real_probability=real_probability,
            fake_probability=fake_probability,
            model_version=self.model_version,
            task=self.task,
            label_semantics=self.label_semantics,
            score_type=self.score_type,
            processing_time_ms=float(round((time.perf_counter() - start_time) * 1000, 2)),
            reason=reason,
            calibrated=self.calibrated,
            calibration_method=self.calibration_method,
            calibration_dataset=self.calibration_dataset,
        )
