"""Image forensics processing module: Spatial, 2D FFT, and Haar DWT analysis."""

from __future__ import annotations

import base64
import hashlib
import io
import logging
from typing import Any

import cv2
import numpy as np
from PIL import Image
import pywt

logger = logging.getLogger(__name__)


def decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR numpy image."""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file: could not decode image format.")
    return img


def detect_and_crop_face(bgr_img: np.ndarray) -> tuple[np.ndarray, bool, dict[str, int]]:
    """Detect frontal face and crop with margin. Falls back to center crop."""
    h, w = bgr_img.shape[:2]
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    if face_cascade.empty():
        logger.warning("Face cascade could not be loaded; using centre-crop fallback")
        faces = ()
    else:
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

    if len(faces) > 0:
        # Pick largest face
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, fw, fh = faces[0]
        # 15% margin
        margin_x = int(fw * 0.15)
        margin_y = int(fh * 0.15)
        x1 = max(0, x - margin_x)
        y1 = max(0, y - margin_y)
        x2 = min(w, x + fw + margin_x)
        y2 = min(h, y + fh + margin_y)
        crop = bgr_img[y1:y2, x1:x2]
        crop_resized = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_AREA)
        bbox = {"x": int(x), "y": int(y), "w": int(fw), "h": int(fh)}
        return crop_resized, True, bbox

    # Center crop fallback
    min_dim = min(h, w)
    start_x = (w - min_dim) // 2
    start_y = (h - min_dim) // 2
    crop = bgr_img[start_y : start_y + min_dim, start_x : start_x + min_dim]
    crop_resized = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_AREA)
    bbox = {"x": int(start_x), "y": int(start_y), "w": int(min_dim), "h": int(min_dim)}
    return crop_resized, False, bbox


def compute_fft_spectrum(gray_face: np.ndarray) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Compute centered 2D Fourier log magnitude spectrum and radial profile."""
    h, w = gray_face.shape
    f = np.fft.fft2(gray_face.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude = np.log(np.abs(fshift) + 1e-6)

    # Normalize magnitude for visual map [0, 255]
    norm_mag = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    vis_fft = cv2.applyColorMap(norm_mag, cv2.COLORMAP_MAGMA)

    # Radial profile analysis: concentric rings from center
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(np.int32)
    max_radius = min(cx, cy)

    radial_bins = 20
    radial_profile = []
    bin_size = max_radius / radial_bins
    for i in range(radial_bins):
        r_start = i * bin_size
        r_end = (i + 1) * bin_size
        mask = (r >= r_start) & (r < r_end)
        mean_val = float(np.mean(magnitude[mask])) if np.any(mask) else 0.0
        norm_val = round(min(100.0, max(0.0, (mean_val / (magnitude.max() + 1e-6)) * 100)), 1)
        freq_label = f"{(i / radial_bins):.2f}π"
        radial_profile.append({"frequency": freq_label, "energy": norm_val})
    return vis_fft, radial_profile


def compute_dwt_subbands(gray_face: np.ndarray) -> np.ndarray:
    """Compute 2D Haar Discrete Wavelet Transform and return 2x2 tiled subbands."""
    face_float = gray_face.astype(np.float32) / 255.0
    coeffs2 = pywt.dwt2(face_float, "haar")
    LL, (LH, HL, HH) = coeffs2

    def to_uint8(subband: np.ndarray) -> np.ndarray:
        norm = cv2.normalize(np.abs(subband), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return norm

    ll_u = to_uint8(LL)
    lh_u = to_uint8(LH)
    hl_u = to_uint8(HL)
    hh_u = to_uint8(HH)

    # Add quadrant text labels
    def add_label(img: np.ndarray, text: str) -> np.ndarray:
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.putText(bgr, text, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 1, cv2.LINE_AA)
        return bgr

    top_row = np.hstack([add_label(ll_u, "LL: Approx"), add_label(hl_u, "HL: Vertical")])
    bottom_row = np.hstack([add_label(lh_u, "LH: Horiz"), add_label(hh_u, "HH: Diagonal")])
    grid = np.vstack([top_row, bottom_row])

    return grid


def compute_spatial_analysis(bgr_face: np.ndarray) -> np.ndarray:
    """Compute Error Level Analysis (ELA) and boundary gradient heatmap."""
    # 1. Error Level Analysis (JPEG re-compression error)
    pil_img = Image.fromarray(cv2.cvtColor(bgr_face, cv2.COLOR_BGR2RGB))
    buffer = io.BytesIO()
    pil_img.save(buffer, "JPEG", quality=90)
    buffer.seek(0)
    recompressed = cv2.cvtColor(np.array(Image.open(buffer)), cv2.COLOR_RGB2BGR)

    ela = cv2.absdiff(bgr_face, recompressed)
    ela_gray = cv2.cvtColor(ela, cv2.COLOR_BGR2GRAY)
    ela_enhanced = cv2.multiply(ela_gray, 18)

    # 2. High-pass boundary gradient
    laplacian = cv2.Laplacian(cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY), cv2.CV_32F)
    lap_abs = np.abs(laplacian)
    lap_norm = cv2.normalize(lap_abs, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Combine ELA and boundary map
    combined = cv2.addWeighted(ela_enhanced, 0.6, lap_norm, 0.4, 0)
    colored_map = cv2.applyColorMap(combined, cv2.COLORMAP_TURBO)

    # Blend 60% heatmap with 40% face
    blended = cv2.addWeighted(colored_map, 0.65, bgr_face, 0.35, 0)

    return blended


def image_to_base64_data_uri(img_bgr: np.ndarray, format_ext: str = ".jpg") -> str:
    """Encode BGR image to base64 Data URI."""
    success, buffer = cv2.imencode(format_ext, img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    if not success:
        raise ValueError("Failed to encode image to base64")
    b64_str = base64.b64encode(buffer).decode("utf-8")
    mime = "image/jpeg" if format_ext == ".jpg" else "image/png"
    return f"data:{mime};base64,{b64_str}"


def analyze_image_bytes(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Execute complete multi-modal forensic inspection on an uploaded image."""
    bgr_img = decode_image(file_bytes)
    h, w = bgr_img.shape[:2]
    file_size_kb = round(len(file_bytes) / 1024, 1)
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # Face detection
    bgr_face, face_found, bbox = detect_and_crop_face(bgr_img)
    gray_face = cv2.cvtColor(bgr_face, cv2.COLOR_BGR2GRAY)

    # Streams
    vis_fft, radial_profile = compute_fft_spectrum(gray_face)
    vis_dwt = compute_dwt_subbands(gray_face)
    vis_spatial = compute_spatial_analysis(bgr_face)

    findings = [
        f"Face detected: {'yes' if face_found else 'no'}"
        + (" (centre-crop fallback used)." if not face_found else "."),
        f"Image dimensions: {w} x {h} pixels.",
        "Fourier log-magnitude spectrum, Haar wavelet subbands, and JPEG recompression measurements were generated.",
    ]

    return {
        "metadata": {
            "filename": str(filename),
            "dimensions": f"{int(w)} x {int(h)} px",
            "filesize_kb": float(file_size_kb),
            "sha256": str(sha256_hash),
            "face_detected": bool(face_found),
            "bounding_box": {k: int(v) for k, v in bbox.items()},
        },
        "visualizations": {
            "face_crop": image_to_base64_data_uri(bgr_face),
            "fft_spectrum": image_to_base64_data_uri(vis_fft),
            "dwt_subbands": image_to_base64_data_uri(vis_dwt),
            "spatial_heatmap": image_to_base64_data_uri(vis_spatial),
        },
        "spectral_profile": [
            {"frequency": str(item["frequency"]), "energy": float(item["energy"])}
            for item in radial_profile
        ],
        "findings": findings,
    }
