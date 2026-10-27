"""Numerically stable FFT preprocessing and debugging visualization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


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
