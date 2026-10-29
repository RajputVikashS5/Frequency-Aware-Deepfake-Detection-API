from __future__ import annotations

import io
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

app = FastAPI(
    title="SpectraGuard: Frequency-Aware Image Deepfake Detection API",
    version="1.0.0",
    description="Diagnostic spatial, Fourier, and wavelet inspection for images. No trained classifier is loaded.",
)
inference_model = RGBBaselineInference(settings.model_checkpoint_path, settings.model_version)

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
        diagnostic = analyze_image_bytes(content, file.filename)
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise HTTPException(status_code=400, detail=f"Unable to analyze image: {exc}") from exc

    prediction = score = model_version = score_type = None
    inference_available = inference_model.available
    if inference_available:
        result = inference_model.predict(content)
        prediction, score, model_version = result.prediction, result.score, result.model_version
        score_type = "Uncalibrated RGB baseline manipulation probability"
        status = "inference_complete"
        message = (
            "Experimental RGB baseline inference completed. The score is an uncalibrated model probability, "
            "not proof of authenticity or manipulation."
        )
    else:
        status = "diagnostic_complete"
        message = (
            "Diagnostic FFT, DWT, ELA, and face-crop outputs are available. "
            "No trained or calibrated deepfake classifier is loaded; these diagnostics are not a deepfake classification."
        )

    return AnalysisResponse(
        status=status,
        inference_available=inference_available,
        prediction=prediction,
        score=score,
        score_type=score_type,
        model_version=model_version,
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
