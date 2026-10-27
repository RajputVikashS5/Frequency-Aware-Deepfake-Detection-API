"""Extract deterministic, evenly spaced frames from local ForgeryNet videos."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def extract_frames(
    video: Path,
    output: Path,
    *,
    samples: int = 8,
    margin: float = 0.05,
    jpeg_quality: int = 95,
) -> list[dict[str, object]]:
    if samples < 1 or not 0 <= margin < 0.5:
        raise ValueError("samples must be positive and margin must be in [0, 0.5)")
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError(f"unable to open local video: {video}")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    if frame_count < 1:
        capture.release()
        raise ValueError(f"video has no readable frames: {video}")
    start = int(frame_count * margin)
    end = max(start, frame_count - 1 - int(frame_count * margin))
    positions = [round(start + (end - start) * index / max(samples - 1, 1)) for index in range(samples)]
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for index, position in enumerate(dict.fromkeys(positions)):
        capture.set(cv2.CAP_PROP_POS_FRAMES, position)
        ok, frame = capture.read()
        if not ok:
            continue
        source_name = "__".join(video.with_suffix("").parts[-2:])
        name = f"{source_name}__frame-{position:08d}__sample-{index:03d}.jpg"
        destination = output / name
        written = cv2.imwrite(str(destination), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        if not written:
            raise OSError(f"unable to write extracted frame: {destination}")
        records.append({
            "path": str(destination),
            "frame_index": position,
            "timestamp_seconds": round(position / fps, 6) if fps > 0 else "",
            "extraction_settings": f"samples={samples};margin={margin};jpeg_quality={jpeg_quality}",
        })
    capture.release()
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--margin", type=float, default=0.05)
    args = parser.parse_args()
    try:
        for record in extract_frames(args.input, args.output, samples=args.samples, margin=args.margin):
            print(record)
    except (OSError, ValueError) as exc:
        print(f"Frame extraction failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
