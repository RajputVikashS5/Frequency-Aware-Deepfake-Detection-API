import io
from dataclasses import replace

import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.config import Settings
from backend.app.r2 import R2ArtifactStore, R2ConfigurationError

client = TestClient(main.app)


def image_bytes(format_name="PNG", size=(16, 16)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (40, 80, 120)).save(buffer, format=format_name)
    return buffer.getvalue()


def upload(data, filename="sample.png", content_type="image/png"):
    return client.post(
        "/api/v1/analyze",
        files={"file": (filename, io.BytesIO(data), content_type)},
    )


def test_corrupt_image_is_rejected():
    response = upload(b"not an image")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_unsupported_content_type_is_rejected():
    response = upload(image_bytes(), "sample.gif", "image/gif")
    assert response.status_code == 415


def test_empty_upload_is_rejected():
    response = upload(b"")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_size_limit_is_enforced(monkeypatch):
    original = main.settings.max_upload_bytes
    object.__setattr__(main.settings, "max_upload_bytes", 10)
    try:
        response = upload(image_bytes())
    finally:
        object.__setattr__(main.settings, "max_upload_bytes", original)
    assert response.status_code == 413


def test_dimension_and_pixel_limits_are_enforced(monkeypatch):
    original_width = main.settings.max_image_width
    original_pixels = main.settings.max_image_pixels
    object.__setattr__(main.settings, "max_image_width", 8)
    object.__setattr__(main.settings, "max_image_pixels", 32)
    try:
        dimension_response = upload(image_bytes(size=(16, 4)))
        pixel_response = upload(image_bytes(size=(8, 8)))
    finally:
        object.__setattr__(main.settings, "max_image_width", original_width)
        object.__setattr__(main.settings, "max_image_pixels", original_pixels)
    assert dimension_response.status_code == 413
    assert pixel_response.status_code == 413


def test_r2_is_disabled_by_default():
    config = Settings(r2_enabled=False)
    store = R2ArtifactStore(config)
    assert config.r2_enabled is False
    try:
        store.download_artifact("unused", "unused")
    except R2ConfigurationError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("Disabled R2 store must not connect")
