"""Disabled-by-default Cloudflare R2 artifact storage boundary."""

from __future__ import annotations

from pathlib import Path

from .config import Settings, settings


class R2ConfigurationError(RuntimeError):
    """Raised when R2 is requested without complete configuration."""


class R2ArtifactStore:
    """Future artifact store; it is never used by user image handling."""

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self._client = None

    def _get_client(self):
        if not self.config.r2_enabled:
            raise R2ConfigurationError("R2 is disabled")
        required = (
            self.config.r2_access_key_id,
            self.config.r2_secret_access_key,
            self.config.r2_bucket,
            self.config.r2_endpoint_url,
        )
        if not all(required):
            raise R2ConfigurationError("R2 is enabled but configuration is incomplete")
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                endpoint_url=self.config.r2_endpoint_url,
                aws_access_key_id=self.config.r2_access_key_id,
                aws_secret_access_key=self.config.r2_secret_access_key,
                region_name="auto",
            )
        return self._client

    def upload_artifact(self, path: str | Path, key: str) -> None:
        """Upload an explicitly supplied future artifact, never an uploaded image."""

        client = self._get_client()
        client.upload_file(str(path), self.config.r2_bucket, key)

    def download_artifact(self, key: str, destination: str | Path) -> None:
        client = self._get_client()
        client.download_file(self.config.r2_bucket, key, str(destination))
