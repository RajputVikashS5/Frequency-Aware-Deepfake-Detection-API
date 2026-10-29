"""Stable API response schemas for diagnostic image analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DiagnosticMetadata(BaseModel):
    filename: str
    dimensions: str
    filesize_kb: float
    sha256: str
    face_detected: bool
    bounding_box: dict[str, int]


class DiagnosticVisualizations(BaseModel):
    face_crop: str
    fft_spectrum: str
    dwt_subbands: str
    spatial_heatmap: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    inference_available: bool
    prediction: str | None = None
    score: float | None = None
    score_type: str | None = None
    model_version: str | None = None
    checkpoint_task: str | None = None
    label_semantics: str | None = None
    domain_warning: str | None = None
    message: str
    metadata: DiagnosticMetadata
    visualizations: DiagnosticVisualizations
    spectral_profile: list[dict[str, Any]]
    findings: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    mode: str
    version: str
    inference_available: bool


class ErrorResponse(BaseModel):
    detail: str
