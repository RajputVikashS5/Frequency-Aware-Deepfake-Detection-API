"""Numerically stable FFT preprocessing and debugging visualization."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError


def fft_log_magnitude(
    image: np.ndarray,
    *,
    normalize: bool = True,
) -> np.ndarray:
    """Return a centered 2D FFT log-magnitude map as float32 with shape (H, W)."""

    array = np.asarray(image)
    if array.ndim == 3:
        if array.shape[0] in (1, 3):
            array = np.mean(array, axis=0)
        elif array.shape[-1] in (1, 3):
            array = np.mean(array, axis=-1)
        else:
            raise ValueError("3D input must have one or three channels")
    if array.ndim != 2 or array.size == 0:
        raise ValueError("FFT input must be a non-empty 2D or channel-first/channel-last image")
    values = np.nan_to_num(array.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    spectrum = np.fft.fftshift(np.fft.fft2(values))
    magnitude = np.log1p(np.abs(spectrum)).astype(np.float32)
    if normalize:
        minimum = float(magnitude.min())
        maximum = float(magnitude.max())
        if maximum > minimum:
            magnitude = (magnitude - minimum) / (maximum - minimum)
        else:
            magnitude.fill(0.0)
    return magnitude


def preprocess_fft(
    image: Image.Image | bytes,
    *,
    target_size: tuple[int, int] = (224, 224),
    normalization: str = "minmax",
    global_stats: tuple[float, float] | None = None,
    imagenet_normalize: bool = True,
) -> np.ndarray:
    """Return a normalized FFT image as a repeated three-channel CHW float32 array.

    Images are decoded as RGB, converted to grayscale with Pillow's fixed
    luminance transform, resized before the FFT, and normalized independently
    to [0, 1]. Repeating the single FFT channel preserves the ResNet-18 input
    contract without presenting RGB pixels to the FFT model.
    """

    if len(target_size) != 2 or any(size <= 0 for size in target_size):
        raise ValueError("target_size must contain two positive integers")
    try:
        if isinstance(image, bytes):
            if not image:
                raise ValueError("Image data is empty")
            with Image.open(io.BytesIO(image)) as source:
                source.verify()
            with Image.open(io.BytesIO(image)) as source:
                decoded = source.convert("RGB").copy()
        else:
            decoded = image.convert("RGB")
        resized = decoded.resize((target_size[1], target_size[0]), Image.Resampling.BILINEAR)
        gray = np.asarray(resized.convert("L"), dtype=np.float32) / 255.0
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Unable to decode image for FFT preprocessing: {exc}") from exc
    if normalization not in {"minmax", "global", "none"}:
        raise ValueError("normalization must be minmax, global, or none")
    if normalization == "global" and global_stats is None:
        raise ValueError("global_stats are required for global FFT normalization")
    spectrum = fft_log_magnitude(gray, normalize=normalization == "minmax")
    if normalization == "global":
        mean, std = global_stats
        if std <= 0:
            raise ValueError("global FFT standard deviation must be positive")
        spectrum = (spectrum - mean) / std
    if not np.isfinite(spectrum).all():
        raise ValueError("FFT preprocessing produced non-finite values")
    output = np.repeat(spectrum[np.newaxis, :, :], 3, axis=0).astype(np.float32, copy=False)
    if imagenet_normalize:
        mean = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)[:, None, None]
        std = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)[:, None, None]
        output = (output - mean) / std
    return output.astype(np.float32, copy=False)


def save_fft_visualization(spectrum: np.ndarray, path: str | Path) -> None:
    """Save a normalized FFT map as an 8-bit grayscale image."""

    values = np.asarray(spectrum, dtype=np.float32)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("spectrum must be a finite 2D array")
    minimum, maximum = float(values.min()), float(values.max())
    scaled = np.zeros_like(values) if maximum <= minimum else (values - minimum) / (maximum - minimum)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(scaled * 255.0, 0, 255).astype(np.uint8), mode="L").save(output)
