"""Environment-backed API and storage configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _origins() -> list[str]:
    configured = os.getenv("ALLOWED_FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


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
    r2_forgerynet_prefix: str = os.getenv("R2_FORGERYNET_PREFIX", "forgerynet")
    r2_cifake_prefix: str = os.getenv("R2_CIFAKE_PREFIX", "CIfake")
    model_checkpoint_path: str = os.getenv("MODEL_CHECKPOINT_PATH", "")
    model_version: str = os.getenv("MODEL_VERSION", "")

    def __post_init__(self) -> None:
        if self.allowed_frontend_origins is None:
            object.__setattr__(self, "allowed_frontend_origins", _origins())


settings = Settings()
