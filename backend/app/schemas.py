"""Stable API response schemas for diagnostic image analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class ExtendedForensics(BaseModel):
    histogram: list[dict[str, Any]] = Field(default_factory=list)
    channel_stats: dict[str, dict[str, float]] = Field(default_factory=dict)
    brightness: float | None = None
    contrast: float | None = None
    frequency_profiles: dict[str, list[dict[str, float]]] = Field(default_factory=dict)
    frequency_energy: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    visualizations: dict[str, str] = Field(default_factory=dict)


class ModelAvailabilityResponse(BaseModel):
    key: str
    name: str
    available: bool
    message: str
    task: str | None = None
    checkpoint_version: str | None = None


class ModelResultResponse(BaseModel):
    key: str
    name: str
    available: bool
    prediction: str | None = None
    real_probability: float | None = None
    fake_probability: float | None = None
    score_type: str | None = None
    model_version: str | None = None
    task: str | None = None
    label_semantics: str | None = None
    processing_time_ms: float | None = None
    reason: str | None = None
    calibrated: bool = False
    calibration_method: str | None = None
    calibration_dataset: str | None = None
    checkpoint_status: str = "unavailable"
    applicable_task: bool = True
    calibration_status: str = "uncalibrated"
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class TaskDetectionResponse(BaseModel):
    task: str
    label_semantics: str
    verdict: str
    available: bool
    model_agreement: str | None = None
    models: list[ModelResultResponse] = Field(default_factory=list)
    warning: str | None = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    inference_available: bool
    prediction: str | None = None
    score: float | None = None
    real_probability: float | None = None
    fake_probability: float | None = None
    score_type: str | None = None
    model_version: str | None = None
    checkpoint_task: str | None = None
    label_semantics: str | None = None
    domain_warning: str | None = None
    processing_time_ms: float | None = None
    message: str
    metadata: DiagnosticMetadata
    visualizations: DiagnosticVisualizations
    spectral_profile: list[dict[str, Any]]
    findings: list[str]
    verdict_state: str = "DIAGNOSTIC ONLY"
    model_agreement: str | None = None
    models: list[ModelResultResponse] = Field(default_factory=list)
    model_availability: list[ModelAvailabilityResponse] = Field(default_factory=list)
    detections: list[TaskDetectionResponse] = Field(default_factory=list)
    extended: ExtendedForensics | None = None
    dwt_levels: dict[str, str] = Field(default_factory=dict)
    # Separate detection results for deepfake vs AI-generated distinction
    separate_detections: dict[str, dict[str, Any]] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    service: str
    mode: str
    version: str
    inference_available: bool


class ErrorResponse(BaseModel):
    detail: str
