from __future__ import annotations

import io
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.forensics import analyze_image_bytes

app = FastAPI(
    title="SpectraGuard: Frequency-Aware Image Deepfake Detection API",
    version="1.0.0",
    description="Multimodal spatial, 2D Fourier (FFT), and discrete wavelet (DWT) forensic inspection for images.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "spectraguard-image-deepfake-detector",
        "mode": "image-forensics",
        "version": "1.0.0",
    }


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)) -> dict:
    """Analyze uploaded facial image for synthetic deepfake artifacts."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    content_type = file.content_type or ""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/bmp", "application/octet-stream"}
    
    # Check extension as well
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    if not file.filename.lower().endswith(valid_extensions) and content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload an image file (JPG, PNG, WEBP, or BMP).",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        results = analyze_image_bytes(file_bytes, file.filename)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image forensic analysis error: {str(e)}")
