"""Build an image-only FaceForensics++-derived dataset from local videos and CSV mappings."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from .extract_faceforensicspp_frames import extract_frames

FIELD_ALIASES = {
    "manipulated_key": {"manipulated_key", "manipulated_video", "manipulated_video_key", "fake_video", "fake_video_path"},
    "source_id": {"source_id", "original_id", "original_video_id", "source_video_id", "source_video"},
    "manipulation_type": {"manipulation_type", "manipulation", "method", "technique"},
}


def _column(headers: Iterable[str], name: str) -> str | None:
    normalized = {header.strip().lower().replace("-", "_").replace(" ", "_"): header for header in headers}
    for alias in FIELD_ALIASES[name]:
        if alias in normalized:
            return normalized[alias]
    return None


def load_official_mapping(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        columns = {name: _column(headers, name) for name in FIELD_ALIASES}
        missing = [name for name, value in columns.items() if value is None]
        if missing:
            raise ValueError(
                f"{path} lacks required official mapping columns: {', '.join(missing)}; "
                "source relationships cannot be inferred from filenames"
            )
        mapping: dict[str, dict[str, str]] = {}
        for row in reader:
            key = (row.get(columns["manipulated_key"] or "") or "").replace("\\", "/").strip()
            source_id = (row.get(columns["source_id"] or "") or "").strip()
            manipulation = (row.get(columns["manipulation_type"] or "") or "").strip()
            if not key or not source_id or not manipulation:
                continue
            mapping[key] = {"group_id": source_id, "manipulation_type": manipulation}
    if not mapping:
        raise ValueError(f"{path} contains no complete official FaceForensics++ mappings")
    return mapping


def _find_mapping(video: Path, mapping: dict[str, dict[str, str]]) -> dict[str, str] | None:
    normalized = video.as_posix().replace("\\", "/")
    matches = [
        value for key, value in mapping.items()
        if normalized == key or normalized.endswith("/" + key.strip("/"))
    ]
    return matches[0] if len(matches) == 1 else None


def prepare_images(
    videos_root: Path,
    mapping_csv: Path,
    output: Path,
    *,
    source_metadata: Path,
    samples: int = 8,
    margin: float = 0.05,
) -> dict[str, int]:
    if not source_metadata.is_file():
        raise ValueError("production runs require a completed dataset-source.json")
    metadata = json.loads(source_metadata.read_text(encoding="utf-8"))
    if any(not metadata.get(field) for field in ("name", "version", "source_url", "license_or_access_terms", "permitted_intended_use", "date_obtained")):
        raise ValueError("dataset-source.json has incomplete provenance")
    mapping = load_official_mapping(mapping_csv)
    output.mkdir(parents=True, exist_ok=True)
    groups: list[dict[str, str]] = []
    manifest: list[dict[str, object]] = []
    exclusions: list[dict[str, str]] = []
    for video in sorted(videos_root.rglob("*.mp4")):
        relative = video.relative_to(videos_root).as_posix()
        is_original = relative.lower().startswith("original/")
        info = {"group_id": video.stem, "manipulation_type": "original"} if is_original else _find_mapping(video, mapping)
        if info is None:
            exclusions.append({"video": relative, "reason": "missing or ambiguous official source mapping"})
            continue
        label_name, label = ("real", 0) if is_original else ("fake", 1)
        frame_dir = output / label_name
        try:
            frames = extract_frames(video, frame_dir, samples=samples, margin=margin)
        except (OSError, ValueError) as exc:
            exclusions.append({"video": relative, "reason": str(exc)})
            continue
        for frame in frames:
            path = Path(str(frame["path"])).relative_to(output).as_posix()
            groups.append({"path": path, "group_id": info["group_id"]})
            manifest.append({
                "path": path, "label_name": label_name, "label": label,
                "group_id": info["group_id"], "source_video_key": relative,
                "manipulation_type": info["manipulation_type"],
                "frame_index": frame["frame_index"], "timestamp_seconds": frame["timestamp_seconds"],
                "extraction_settings": frame["extraction_settings"],
            })
    with (output / "groups.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "group_id"])
        writer.writeheader()
        writer.writerows(groups)
    with (output / "frame-manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["path", "label_name", "label", "group_id", "source_video_key", "manipulation_type", "frame_index", "timestamp_seconds", "extraction_settings"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest)
    with (output / "exclusions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video", "reason"])
        writer.writeheader()
        writer.writerows(exclusions)
    (output / "dataset-source.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"retained_frames": len(manifest), "excluded_videos": len(exclusions)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--videos", type=Path, required=True)
    parser.add_argument("--mapping-csv", type=Path, required=True)
    parser.add_argument("--source-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/raw/faceforensicspp-images-v1"))
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--margin", type=float, default=0.05)
    args = parser.parse_args()
    try:
        print(prepare_images(args.videos, args.mapping_csv, args.output, source_metadata=args.source_metadata, samples=args.samples, margin=args.margin))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FaceForensics++ image preparation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
