"""Runtime registry for the independent RGB, FFT, and fusion checkpoints."""

from __future__ import annotations

import io
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from .frequency import preprocess_fft
from .model_inference import InferenceResult, _CIFAKE_RESOLUTION_THRESHOLD, _is_path_within_project
from .preprocessing import preprocess_rgb

try:
    from backend.training.fft_baseline import build_fft_model
    from backend.training.fusion_baseline import RGBFFTFusionModel
except ModuleNotFoundError:
    from training.fft_baseline import build_fft_model
    from training.fusion_baseline import RGBFFTFusionModel


@dataclass(frozen=True)
class ModelAvailability:
    key: str
    name: str
    available: bool
    message: str
    task: str | None = None
    checkpoint_version: str | None = None


class _CheckpointInference:
    """Shared safe checkpoint loading and metadata handling."""

    architecture = "ResNet-18"

    def __init__(self, key: str, name: str, checkpoint_path: str, model_version: str = "") -> None:
        candidate = Path(checkpoint_path).expanduser() if checkpoint_path else None
        self.key = key
        self.name = name
        self._checkpoint_was_relative = bool(candidate and not candidate.is_absolute())
        self.checkpoint_path = (
            candidate if candidate and candidate.is_absolute()
            else Path(__file__).resolve().parents[2] / candidate if candidate
            else None
        )
        self.model_version = model_version
        self._model: torch.nn.Module | None = None
        self._error: str | None = None
        self._error_at = 0.0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.task = ""
        self.label_semantics = ""
        self.score_type = ""
        self.calibrated = False
        self.calibration_method: str | None = None
        self.calibration_dataset: str | None = None
        self.threshold = 0.5
        self.temperature = 1.0
        self.uncertainty_band = (0.35, 0.65)
        self.training_resolution: int | None = None

    @property
    def available(self) -> bool:
        self._load_if_configured()
        return self._model is not None

    @property
    def status_message(self) -> str:
        self._load_if_configured()
        if self._model is not None:
            return "Loaded; scores are uncalibrated model probabilities."
        return self._error or "No checkpoint is configured."

    def _load_model(self, state: dict[str, Any]) -> torch.nn.Module:
        raise NotImplementedError

    def _load_if_configured(self) -> None:
        if self._model is not None or self.checkpoint_path is None:
            return
        if self._error is not None and time.monotonic() - self._error_at < 10:
            return
        try:
            if not self.checkpoint_path.is_file():
                raise FileNotFoundError("checkpoint file is missing")
            if self._checkpoint_was_relative and not _is_path_within_project(
                self.checkpoint_path, Path(__file__).resolve().parents[2]
            ):
                raise ValueError("checkpoint path is outside project directory")
            payload = torch.load(self.checkpoint_path, map_location="cpu", weights_only=True)
            if not isinstance(payload, dict) or not isinstance(payload.get("model_state"), dict):
                raise ValueError("checkpoint has no model_state")
            config = payload.get("config", {})
            if not isinstance(config, dict):
                raise ValueError("checkpoint config is invalid")
            self.task = str(config.get("task", ""))
            if not self.task:
                raise ValueError("checkpoint is missing task metadata")
            self.label_semantics = str(config.get("label_semantics", "real/fake"))
            self.score_type = str(config.get("score_type", "uncalibrated model probability"))
            self.calibrated = bool(config.get("calibrated", False))
            self.calibration_method = (
                str(config["calibration_method"])
                if config.get("calibration_method")
                else None
            )
            self.calibration_dataset = (
                str(config["calibration_dataset"])
                if config.get("calibration_dataset")
                else None
            )
            self.threshold = float(config.get("threshold", 0.5))
            self.temperature = max(float(config.get("temperature", 1.0)), 1e-6)
            band = config.get("uncertainty_band", [0.35, 0.65])
            if isinstance(band, (list, tuple)) and len(band) == 2:
                self.uncertainty_band = (float(band[0]), float(band[1]))
            self.training_resolution = config.get("training_resolution")
            self._model = self._load_model(payload["model_state"]).to(self.device)
            self._model.eval()
            if not self.model_version:
                self.model_version = f"{self.key}:{self.checkpoint_path.stem}"
            self._error = None
        except (OSError, RuntimeError, ValueError, KeyError, TypeError, EOFError) as exc:
            self._error = str(exc)
            self._error_at = time.monotonic()

    def _result(self, logits: torch.Tensor, started: float, image_bytes: bytes) -> InferenceResult:
        probabilities = torch.softmax(logits / self.temperature, dim=1)[0]
        real_probability = float(probabilities[0].item())
        fake_probability = float(probabilities[1].item())
        prediction = "likely_manipulated" if fake_probability >= self.threshold else "likely_real"
        reason = None
        if self.task == "cifake" and self.training_resolution is not None:
            with Image.open(io.BytesIO(image_bytes)) as source:
                short_side = min(source.size)
            if short_side > _CIFAKE_RESOLUTION_THRESHOLD:
                prediction = "inconclusive"
                reason = (
                    "This CIFAKE checkpoint was trained on 32x32 images; "
                    "the uploaded image is outside that resolution domain."
                )
        low, high = self.uncertainty_band
        if low <= fake_probability <= high:
            prediction = "inconclusive"
            reason = "The model score is inside its configured uncertainty band."
        return InferenceResult(
            prediction=prediction,
            score=fake_probability,
            real_probability=real_probability,
            fake_probability=fake_probability,
            model_version=self.model_version,
            task=self.task,
            label_semantics=self.label_semantics,
            score_type=self.score_type,
            processing_time_ms=round((time.perf_counter() - started) * 1000, 2),
            reason=reason,
            calibrated=self.calibrated,
            calibration_method=self.calibration_method,
            calibration_dataset=self.calibration_dataset,
        )

    def predict(self, image_bytes: bytes) -> InferenceResult:
        raise NotImplementedError


class FFTBaselineInference(_CheckpointInference):
    """Inference adapter for the independently trained FFT ResNet-18."""

    def _load_model(self, state: dict[str, Any]) -> torch.nn.Module:
        model, _ = build_fft_model(pretrained=False)
        model.load_state_dict(state, strict=True)
        return model

    def predict(self, image_bytes: bytes) -> InferenceResult:
        if not self.available or self._model is None:
            raise RuntimeError(self.status_message)
        started = time.perf_counter()
        tensor = torch.from_numpy(np.ascontiguousarray(preprocess_fft(image_bytes))).unsqueeze(0)
        with torch.inference_mode():
            return self._result(self._model(tensor.to(self.device)), started, image_bytes)


class FusionBaselineInference(_CheckpointInference):
    """Inference adapter for the trained two-branch RGB+FFT fusion model."""

    architecture = "Two-branch ResNet-18 fusion"

    def _load_model(self, state: dict[str, Any]) -> torch.nn.Module:
        model = RGBFFTFusionModel(pretrained=False)
        model.load_state_dict(state, strict=True)
        return model

    def predict(self, image_bytes: bytes) -> InferenceResult:
        if not self.available or self._model is None:
            raise RuntimeError(self.status_message)
        started = time.perf_counter()
        rgb = torch.from_numpy(np.ascontiguousarray(preprocess_rgb(image_bytes))).unsqueeze(0)
        fft = torch.from_numpy(np.ascontiguousarray(preprocess_fft(image_bytes))).unsqueeze(0)
        with torch.inference_mode():
            return self._result(self._model(rgb.to(self.device), fft.to(self.device)), started, image_bytes)


class ModelRegistry:
    """Loads each configured model independently and never fabricates results."""

    def __init__(
        self,
        models: dict[str, _CheckpointInference],
        *,
        expected_tasks: set[str] | None = None,
    ) -> None:
        self.models = models
        self.expected_tasks = expected_tasks

    def availability(self) -> list[ModelAvailability]:
        available_models = []
        for key, model in self.models.items():
            is_available = model.available
            message = model.status_message
            if is_available and self.expected_tasks and model.task not in self.expected_tasks:
                is_available = False
                message = (
                    f"Checkpoint task {model.task!r} is incompatible with "
                    f"this registry ({', '.join(sorted(self.expected_tasks))})."
                )
            available_models.append(
                ModelAvailability(
                    key=key,
                    name=getattr(model, "name", key.upper()),
                    available=is_available,
                    message=message,
                    task=model.task or None,
                    checkpoint_version=model.model_version or None,
                )
            )
        return available_models

    def predict_all(self, image_bytes: bytes) -> dict[str, InferenceResult]:
        results: dict[str, InferenceResult] = {}
        for key, model in self.models.items():
            if model.available and (
                not self.expected_tasks or model.task in self.expected_tasks
            ):
                results[key] = model.predict(image_bytes)
        return results
