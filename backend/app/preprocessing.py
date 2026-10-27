"""Safe, shared RGB image preprocessing for training and inference."""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class Normalization:
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)


def decode_rgb(data: bytes) -> Image.Image:
    """Decode bytes into an independent RGB PIL image."""

    if not data:
        raise ValueError("Image data is empty")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            return image.convert("RGB").copy()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Unable to decode image: {exc}") from exc


def preprocess_rgb(
    image: Image.Image | bytes,
    *,
    target_size: tuple[int, int] = (224, 224),
    normalization: Normalization | None = Normalization(),
) -> np.ndarray:
    """Return a float32 CHW array, scaled to [0, 1] then optionally normalized."""

    if len(target_size) != 2 or any(size <= 0 for size in target_size):
        raise ValueError("target_size must contain two positive integers")
    decoded = decode_rgb(image) if isinstance(image, bytes) else image.convert("RGB")
    resized = decoded.resize((target_size[1], target_size[0]), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32) / 255.0
    if normalization is not None:
        mean = np.asarray(normalization.mean, dtype=np.float32).reshape(1, 1, 3)
        std = np.asarray(normalization.std, dtype=np.float32).reshape(1, 1, 3)
        if np.any(std <= 0):
            raise ValueError("normalization standard deviations must be positive")
        array = (array - mean) / std
    return np.transpose(array, (2, 0, 1)).astype(np.float32, copy=False)
