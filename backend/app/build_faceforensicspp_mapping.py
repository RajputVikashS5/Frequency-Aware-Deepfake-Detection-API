"""Create a verified FaceForensics++ C23 mapping from the official filename convention.

The official FaceForensics++ guide specifies ``<target sequence>_<source
sequence>`` filenames for the standard manipulation methods.  The target
sequence is used as the source-group ID because it supplies the video content
being manipulated.  DeepFakeDetection uses a separate actor naming scheme and
is deliberately excluded until an actor-to-original mapping is supplied.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import settings
from .inventory_faceforensicspp import _list_objects
from .r2 import R2ArtifactStore
from .r2_verify import dataset_prefixes, validate_configuration


METHODS = {"Deepfakes", "Face2Face", "FaceSwap", "NeuralTextures", "FaceShifter"}
PAIR_NAME = re.compile(r"^(?P<target>\d{3})_(?P<source>\d{3})\.mp4$", re.IGNORECASE)
OFFICIAL_GUIDE = "https://github.com/ondyari/FaceForensics/blob/master/dataset/README.md"
TERMS_URL = "https://kaldir.vc.in.tum.de/faceforensics/webpage/FaceForensics_TOS.pdf"


def build_mapping(output_dir: Path) -> dict[str, int]:
    """Write new mapping and provenance files without overwriting prior runs."""

    mapping_path = output_dir / "mapping.csv"
    source_path = output_dir / "dataset-source.json"
    if mapping_path.exists() or source_path.exists():
        raise FileExistsError(f"refusing to overwrite existing mapping output: {output_dir}")

    validate_configuration(settings)
    prefix = dataset_prefixes(settings)["faceforensicspp"]
    client = R2ArtifactStore(settings)._get_client()
    listing = _list_objects(client, settings.r2_bucket, prefix, 1_000_000)
    if not listing.completed or listing.truncated_by_limit or listing.warnings:
        raise ValueError(f"incomplete R2 listing: {listing.warnings}")

    rows: list[dict[str, str]] = []
    excluded = 0
    for key in sorted(listing.keys):
        relative = key.removeprefix(prefix).lstrip("/")
        parts = relative.split("/")
        if len(parts) != 2 or parts[0] not in METHODS:
            continue
        match = PAIR_NAME.fullmatch(parts[1])
        if match is None:
            excluded += 1
            continue
        rows.append(
            {
                "manipulated_key": relative,
                "source_id": f"ffpp-target-{match.group('target')}",
                "manipulation_type": parts[0],
                "donor_sequence_id": match.group("source"),
            }
        )
    if not rows:
        raise ValueError("no standard FaceForensics++ pairs were found")

    output_dir.mkdir(parents=True, exist_ok=False)
    with mapping_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["manipulated_key", "source_id", "manipulation_type", "donor_sequence_id"])
        writer.writeheader()
        writer.writerows(rows)
    source_path.write_text(
        json.dumps(
            {
                "name": "FaceForensics++ C23 standard-method subset",
                "version": "r2-c23-standard-methods-v1",
                "source_url": OFFICIAL_GUIDE,
                "license_or_access_terms": TERMS_URL,
                "permitted_intended_use": "Research and development after user-confirmed acceptance of the FaceForensics++ Terms of Use.",
                "date_obtained": datetime.now(timezone.utc).isoformat(),
                "r2_prefix": prefix,
                "grouping_policy": "Official <target sequence>_<source sequence> convention; group by target sequence.",
                "excluded_component": "DeepFakeDetection excluded because its actor-pair naming cannot be mapped to the available original-video collection.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"mapping_rows": len(rows), "unpaired_standard_files": excluded, "r2_objects": len(listing.keys)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build_mapping(args.output_dir), indent=2))
    except (OSError, ValueError, FileExistsError) as exc:
        print(f"FaceForensics++ mapping build failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
