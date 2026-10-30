"""Environment-backed API and storage configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


def _load_dotenv() -> None:
    """Load simple KEY=VALUE entries without printing or overriding env vars."""

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL_CHECKPOINT = (
    _PROJECT_ROOT
    / "experiments"
    / "rgb-baseline"
    / "faceforensicspp-c23-r2-v1-limited-clean"
    / "faceforensicspp-rgb-resnet18-best.pt"
)
_DEFAULT_CIFAKE_RGB_CHECKPOINT = (
    _PROJECT_ROOT / "experiments" / "rgb-baseline" / "cifake-image-v2"
    / "cifake-rgb-resnet18-best.pt"
)
_DEFAULT_CIFAKE_FFT_CHECKPOINT = (
    _PROJECT_ROOT / "experiments" / "fft-baseline" / "cifake-image-v2"
    / "cifake-fft-resnet18-best.pt"
)
_DEFAULT_CIFAKE_FUSION_CHECKPOINT = (
    _PROJECT_ROOT / "experiments" / "fusion-baseline" / "cifake-image-v2"
    / "cifake-fusion-resnet18-best.pt"
)
_DEFAULT_DEEPFAKE_RGB_CHECKPOINT = _DEFAULT_MODEL_CHECKPOINT


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_origin(origin: str) -> str:
    """Validate that an origin is a properly formatted URL with a scheme and host."""
    origin = origin.strip()
    if not origin:
        return origin
    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid CORS origin: {origin!r} (must have scheme and host)")
    return origin


def _origins() -> list[str]:
    configured = os.getenv("ALLOWED_FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [_validate_origin(origin) for origin in configured.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    max_image_width: int = int(os.getenv("MAX_IMAGE_WIDTH", "8192"))
    max_image_height: int = int(os.getenv("MAX_IMAGE_HEIGHT", "8192"))
    max_image_pixels: int = int(os.getenv("MAX_IMAGE_PIXELS", str(40_000_000)))
    allowed_frontend_origins: list[str] | None = None
    r2_enabled: bool = _bool("R2_ENABLED", False)
    r2_account_id: str = os.getenv("R2_ACCOUNT_ID", "")
    r2_bucket: str = os.getenv("R2_BUCKET", "")
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    r2_endpoint_url: str = os.getenv("R2_ENDPOINT_URL", "")
    r2_faceforensicspp_prefix: str = os.getenv(
        "R2_FACEFORENSICSPP_PREFIX", "faceforensics++"
    )
    r2_cifake_prefix: str = os.getenv("R2_CIFAKE_PREFIX", "CIfake")
    # An empty MODEL_CHECKPOINT_PATH intentionally selects diagnostics-only mode.
    model_checkpoint_path: str = os.getenv("MODEL_CHECKPOINT_PATH", str(_DEFAULT_MODEL_CHECKPOINT))
    model_version: str = os.getenv("MODEL_VERSION", "")
    ai_rgb_model_checkpoint_path: str = os.getenv(
        "RGB_MODEL_CHECKPOINT_PATH", str(_DEFAULT_CIFAKE_RGB_CHECKPOINT)
    )
    ai_fft_model_checkpoint_path: str = os.getenv(
        "FFT_MODEL_CHECKPOINT_PATH", str(_DEFAULT_CIFAKE_FFT_CHECKPOINT)
    )
    ai_fusion_model_checkpoint_path: str = os.getenv(
        "FUSION_MODEL_CHECKPOINT_PATH", str(_DEFAULT_CIFAKE_FUSION_CHECKPOINT)
    )
    deepfake_rgb_model_checkpoint_path: str = os.getenv(
        "DEEPFAKE_RGB_MODEL_CHECKPOINT_PATH",
        os.getenv("MODEL_CHECKPOINT_PATH", str(_DEFAULT_DEEPFAKE_RGB_CHECKPOINT)),
    )
    deepfake_fft_model_checkpoint_path: str = os.getenv(
        "DEEPFAKE_FFT_MODEL_CHECKPOINT_PATH", ""
    )
    deepfake_fusion_model_checkpoint_path: str = os.getenv(
        "DEEPFAKE_FUSION_MODEL_CHECKPOINT_PATH", ""
    )

    def __post_init__(self) -> None:
        if self.allowed_frontend_origins is None:
            object.__setattr__(self, "allowed_frontend_origins", _origins())
        # Validate numeric limits
        if self.max_upload_bytes <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be a positive integer")
        if self.max_image_width <= 0 or self.max_image_height <= 0:
            raise ValueError("MAX_IMAGE_WIDTH and MAX_IMAGE_HEIGHT must be positive integers")
        if self.max_image_pixels <= 0:
            raise ValueError("MAX_IMAGE_PIXELS must be a positive integer")
        # Validate R2 configuration consistency
        if self.r2_enabled:
            if not self.r2_account_id or not self.r2_bucket:
                raise ValueError("R2_ENABLED=true requires R2_ACCOUNT_ID and R2_BUCKET")
            if not self.r2_access_key_id or not self.r2_secret_access_key:
                raise ValueError("R2_ENABLED=true requires R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY")
            if not self.r2_endpoint_url:
                raise ValueError("R2_ENABLED=true requires R2_ENDPOINT_URL")


settings = Settings()
