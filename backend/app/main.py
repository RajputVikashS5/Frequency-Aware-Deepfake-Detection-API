from __future__ import annotations

import io
import os
import re
import sys
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
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
import cv2

from .config import settings
from .forensics import analyze_image_bytes
from .model_inference import RGBBaselineInference
from .schemas import AnalysisResponse, ErrorResponse, HealthResponse

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
# Phase 9: Load verified model checkpoint if configured
inference_model = RGBBaselineInference(settings.model_checkpoint_path, settings.model_version) if settings.model_checkpoint_path else RGBBaselineInference("", "")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
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
    prediction = score = model_version = score_type = None
    checkpoint_task = label_semantics = domain_warning = None
    processing_time_ms = None
    inference_available = inference_model.available

    if inference_available:
        result = await run_in_threadpool(inference_model.predict, content)
        checkpoint_task = result.task
        label_semantics = result.label_semantics
        score_type = result.score_type
        prediction = (
            result.prediction
            if result.task != "cifake" or result.prediction == "inconclusive"
            else None
        )
        score = result.score if result.task != "cifake" else None
        model_version = result.model_version
        processing_time_ms = result.processing_time_ms
        status = "inference_complete"
        domain_warning = result.reason
        if result.task == "cifake" and domain_warning is None:
            domain_warning = (
                "This checkpoint was trained on 32x32 CIFAKE images "
                "(AI-generated versus real), so it is not valid for manipulated-image labeling."
            )
        if result.prediction == "inconclusive":
            message = domain_warning or "The model could not make a confident in-domain classification."
        else:
            message = "Model inference completed. The score is not calibrated."
    else:
        checkpoint_task = label_semantics = domain_warning = None
        status = "diagnostic_complete"
        message = (
            "Diagnostic FFT, DWT, ELA, and face-crop outputs are available. "
            f"No trained model is loaded ({inference_model.status_message}). "
            "These diagnostics are not a deepfake classification."
        )

    return AnalysisResponse(
        status=status,
        inference_available=inference_available,
        prediction=prediction,
        score=score,
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
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_image(file: Annotated[UploadFile, File(...)]) -> AnalysisResponse:
    return await _analyze(file)


@app.post(
    "/predict",
    response_model=AnalysisResponse,
    deprecated=True,
)
async def predict_compatibility(file: Annotated[UploadFile, File(...)]) -> AnalysisResponse:
    """Deprecated compatibility alias for /api/v1/analyze."""

    return await _analyze(file)
