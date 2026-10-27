"""Explicit, bounded downloader for ForgeryNet videos; never used by FastAPI."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import settings
from .r2 import R2ArtifactStore
from .r2_verify import dataset_prefixes, validate_configuration


def download_videos(keys: list[str], output: Path, *, max_videos: int = 10) -> list[str]:
    if not 1 <= max_videos <= 100:
        raise ValueError("max_videos must be between 1 and 100")
    prefix = dataset_prefixes(settings)["forgerynet"]
    selected = [key for key in keys if key.startswith(prefix) and key.lower().endswith(".mp4")][:max_videos]
    if not selected:
        raise ValueError("no ForgeryNet MP4 keys selected")
    client = R2ArtifactStore(settings)._get_client()
    output.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for key in selected:
        relative = key[len(prefix):].lstrip("/")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            client.download_fileobj(settings.r2_bucket, key, handle)
        saved.append(str(destination))
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", action="append", required=True, help="R2 object key; repeat for each selected video")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-videos", type=int, default=10)
    args = parser.parse_args()
    try:
        validate_configuration(settings)
        for path in download_videos(args.key, args.output, max_videos=args.max_videos):
            print(path)
    except (OSError, ValueError) as exc:
        print(f"ForgeryNet download failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
