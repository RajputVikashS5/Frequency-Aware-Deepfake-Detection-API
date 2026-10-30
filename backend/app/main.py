from __future__ import annotations

import io
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Annotated

# Ensure repository root is on sys.path so 'backend' package resolves cleanly from any working directory
_repo_root = str(Path(__file__).resolve().parents[2])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from PIL import Image, UnidentifiedImageError
import cv2

from .config import settings
from .forensics import analyze_image_bytes
from .model_inference import RGBBaselineInference
from .model_registry import FFTBaselineInference, FusionBaselineInference, ModelRegistry
from .schemas import (
    AnalysisResponse,
    ErrorResponse,
    HealthResponse,
    ModelAvailabilityResponse,
    ModelResultResponse,
    TaskDetectionResponse,
)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": {"JPEG"},
    "image/png": {"PNG"},
    "image/webp": {"WEBP"},
    "image/bmp": {"BMP"},
}

# Sanitize filename: remove path components and keep only safe filename characters
_FILENAME_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9._-]")


def _sanitize_filename(filename: str) -> str:
    """Remove path traversal characters and keep only safe filename characters."""
    # First, take only the basename (removes any directory components)
    basename = os.path.basename(filename)
    # Remove any remaining unsafe characters
    safe = _FILENAME_SANITIZE_RE.sub("_", basename)
    # Ensure we don't end up with an empty filename
    if not safe or safe in (".", ".."):
        return "uploaded_image"
    return safe

app = FastAPI(
    title="SpectraGuard: Frequency-Aware Image Deepfake Detection API",
    version="1.0.0",
    description="Frequency-aware image deepfake detection API with diagnostic spatial, Fourier, and wavelet analysis.",
)
# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Phase 9: Load verified model checkpoint if configured
inference_model = (
    RGBBaselineInference(
        settings.deepfake_rgb_model_checkpoint_path,
        settings.model_version,
    )
    if settings.deepfake_rgb_model_checkpoint_path
    else RGBBaselineInference("", "")
)
ai_model_registry = ModelRegistry(
    {
        "rgb": RGBBaselineInference(settings.ai_rgb_model_checkpoint_path, ""),
        "fft": FFTBaselineInference("fft", "FFT ResNet-18", settings.ai_fft_model_checkpoint_path, ""),
        "fusion": FusionBaselineInference(
            "fusion", "RGB + FFT Fusion", settings.ai_fusion_model_checkpoint_path, ""
        ),
    },
    expected_tasks={"cifake"},
)
deepfake_model_registry = ModelRegistry(
    {
        "rgb": inference_model,
        "fft": FFTBaselineInference(
            "deepfake-fft",
            "Deepfake FFT ResNet-18",
            settings.deepfake_fft_model_checkpoint_path,
            "",
        ),
        "fusion": FusionBaselineInference(
            "deepfake-fusion",
            "Deepfake RGB + FFT Fusion",
            settings.deepfake_fusion_model_checkpoint_path,
            "",
        ),
    },
    expected_tasks={"faceforensicspp", "forgerynet"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
    # Security: warn about dangerous origins
    # "null" origin comes from file:// URLs - avoid in production
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail)).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="spectraguard-image-deepfake-detector",
        mode="image-forensics",
        version="1.0.0",
        inference_available=inference_model.available,
    )


def _validate_image(data: bytes, content_type: str) -> tuple[int, int, str]:
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")
    # Validate content_type format to prevent header injection / DoS
    if not content_type or not isinstance(content_type, str) or len(content_type) > 128:
        raise HTTPException(status_code=415, detail="Invalid content type header.")
    content_type = content_type.strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type. Use JPEG, PNG, WEBP, or BMP.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            warnings.simplefilter("error", Image.DecompressionBombError)
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image_format = image.format
                width, height = image.size
    except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid or corrupt image: {exc}") from exc

    if image_format not in ALLOWED_CONTENT_TYPES[content_type]:
        raise HTTPException(status_code=415, detail="Image content does not match the declared content type.")
    if width > settings.max_image_width or height > settings.max_image_height:
        raise HTTPException(status_code=413, detail="Image dimensions exceed the configured limit.")
    if width * height > settings.max_image_pixels:
        raise HTTPException(status_code=413, detail="Image pixel count exceeds the configured limit.")
    return width, height, image_format


def _model_response(
    key: str,
    model: object,
    result: object | None,
) -> ModelResultResponse:
    return ModelResultResponse(
        key=key,
        name=getattr(model, "name", key.upper()),
        available=result is not None,
        prediction=result.prediction if result else None,
        real_probability=result.real_probability if result else None,
        fake_probability=result.fake_probability if result else None,
        score_type=result.score_type if result else None,
        model_version=result.model_version if result else None,
        task=result.task if result else None,
        label_semantics=result.label_semantics if result else None,
        processing_time_ms=result.processing_time_ms if result else None,
        reason=result.reason if result else model.status_message,
        calibrated=result.calibrated if result else False,
        calibration_method=result.calibration_method if result else None,
        calibration_dataset=result.calibration_dataset if result else None,
    )


def _task_detection(
    task: str,
    label_semantics: str,
    registry: ModelRegistry,
    results: dict[str, object],
) -> TaskDetectionResponse:
    responses = [
        _model_response(key, model, results.get(key))
        for key, model in registry.models.items()
    ]
    predictions = [
        result.prediction
        for result in results.values()
        if result.prediction in {"likely_real", "likely_manipulated"}
    ]
    if not predictions:
        verdict = "MODEL UNAVAILABLE" if not results else "INCONCLUSIVE"
    else:
        fake_count = predictions.count("likely_manipulated")
        real_count = predictions.count("likely_real")
        if fake_count == real_count:
            verdict = "INCONCLUSIVE"
        elif fake_count > real_count:
            verdict = "LIKELY AI-GENERATED" if task == "ai_generated_vs_real" else "LIKELY MANIPULATED"
        else:
            verdict = "LIKELY REAL" if task == "ai_generated_vs_real" else "LIKELY AUTHENTIC"
    agreement = None
    if len(predictions) >= 2:
        agreement = "agree" if len(set(predictions)) == 1 else "disagree"
    available = bool(results)
    if not available:
        warning = "No trained checkpoint is configured for this detection task."
    elif any(not response.calibrated for response in responses if response.available):
        warning = "Scores are uncalibrated model outputs, not validated probabilities."
    else:
        warning = None
    return TaskDetectionResponse(
        task=task,
        label_semantics=label_semantics,
        verdict=verdict,
        available=available,
        model_agreement=agreement,
        models=responses,
        warning=warning,
    )


async def _analyze(file: UploadFile) -> AnalysisResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")
    content = await file.read(settings.max_upload_bytes + 1)
    _validate_image(content, file.content_type or "")
    try:
        diagnostic = analyze_image_bytes(content, _sanitize_filename(file.filename))
    except (OSError, ValueError, UnidentifiedImageError, cv2.error) as exc:
        raise HTTPException(status_code=400, detail=f"Unable to analyze image: {exc}") from exc

    # Phase 9: Real model inference integration
    prediction = score = real_probability = fake_probability = model_version = score_type = None
    checkpoint_task = label_semantics = domain_warning = None
    processing_time_ms = None
    inference_available = inference_model.available
    ai_model_results = ai_model_registry.predict_all(content)
    deepfake_model_results = deepfake_model_registry.predict_all(content)
    ai_availability = ai_model_registry.availability()
    deepfake_availability = deepfake_model_registry.availability()

    if inference_available:
        result = deepfake_model_results.get("rgb")
        if result is None:
            raise HTTPException(status_code=503, detail="Deepfake RGB model became unavailable during analysis.")
        checkpoint_task = result.task
        label_semantics = result.label_semantics
        score_type = result.score_type
        prediction = result.prediction
        score = result.score
        real_probability = result.real_probability
        fake_probability = result.fake_probability
        model_version = result.model_version
        processing_time_ms = result.processing_time_ms
        status = "inference_complete"
        domain_warning = result.reason
        if result.prediction == "inconclusive":
            message = domain_warning or "The model could not make a confident in-domain classification."
        else:
            message = "Separate AI-generated and deepfake detection tasks completed."
    else:
        checkpoint_task = label_semantics = domain_warning = None
        status = "diagnostic_complete"
        message = (
            "Diagnostic FFT, DWT, ELA, and face-crop outputs are available. "
            f"No trained model is loaded ({inference_model.status_message}). "
            "These diagnostics are not a deepfake classification."
        )

    ai_detection = _task_detection(
        "ai_generated_vs_real",
        "AI-generated versus real",
        ai_model_registry,
        ai_model_results,
    )
    deepfake_detection = _task_detection(
        "deepfake_manipulation_vs_authentic",
        "Manipulated versus authentic",
        deepfake_model_registry,
        deepfake_model_results,
    )
    model_responses = [
        _model_response(key, model, deepfake_model_results.get(key))
        for key, model in deepfake_model_registry.models.items()
    ]
    model_agreement = deepfake_detection.model_agreement
    if not inference_available:
        verdict_state = "DIAGNOSTIC ONLY"
    elif prediction == "inconclusive":
        verdict_state = "INCONCLUSIVE"
    elif prediction == "likely_manipulated":
        verdict_state = "LIKELY MANIPULATED"
    else:
        verdict_state = "LIKELY REAL"

    return AnalysisResponse(
        status=status,
        inference_available=inference_available,
        prediction=prediction,
        score=score,
        real_probability=real_probability,
        fake_probability=fake_probability,
        score_type=score_type,
        model_version=model_version,
        checkpoint_task=checkpoint_task,
        label_semantics=label_semantics,
        domain_warning=domain_warning,
        processing_time_ms=processing_time_ms,
        message=message,
        metadata=diagnostic["metadata"],
        visualizations=diagnostic["visualizations"],
        spectral_profile=diagnostic["spectral_profile"],
        findings=diagnostic["findings"],
        verdict_state=verdict_state,
        model_agreement=model_agreement,
        models=model_responses,
        model_availability=[
            ModelAvailabilityResponse(
                key=item.key,
                name=item.name,
                available=item.available,
                message=item.message,
                task=item.task,
                checkpoint_version=item.checkpoint_version,
            )
            for item in [*ai_availability, *deepfake_availability]
        ],
        detections=[ai_detection, deepfake_detection],
        extended=diagnostic.get("extended"),
        dwt_levels=diagnostic.get("dwt_levels", {}),
        separate_detections={
            "deepfake_manipulation": {
                "verdict": deepfake_detection.verdict,
                "models": [m.model_dump() for m in deepfake_detection.models],
                "agreement": deepfake_detection.model_agreement,
                "task": "deepfake_manipulation_vs_authentic",
                "label_semantics": "Manipulated versus authentic",
            },
            "ai_generation": {
                "verdict": ai_detection.verdict,
                "models": [m.model_dump() for m in ai_detection.models],
                "agreement": ai_detection.model_agreement,
                "task": "ai_generated_vs_real",
                "label_semantics": "AI-generated versus real",
            },
        },
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
@limiter.limit("10/minute")  # 10 uploads per minute per IP
async def analyze_image(request: Request, file: Annotated[UploadFile, File(...)]) -> AnalysisResponse:
    return await _analyze(file)


@app.post(
    "/predict",
    response_model=AnalysisResponse,
    deprecated=True,
)
@limiter.limit("10/minute")
async def predict_compatibility(request: Request, file: Annotated[UploadFile, File(...)]) -> AnalysisResponse:
    """Deprecated compatibility alias for /api/v1/analyze."""

    return await _analyze(file)
