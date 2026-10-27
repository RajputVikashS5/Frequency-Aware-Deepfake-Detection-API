import csv
import json
from pathlib import Path

import pytest

from backend.app.dataset import scan_dataset
from backend.app.extract_forgerynet_frames import extract_frames
from backend.app.fetch_dataset_sample import fetch_sample, recover_samples
from backend.app.inventory_forgerynet import (
    build_cifake_image_manifest,
    inventory_dataset,
    parse_forgerynet_csv_bytes,
    parse_forgerynet_video_manifest,
)
from backend.app.prepare_cifake_images import prepare_cifake, reject_external_evaluation_manifest
from backend.app.prepare_cifake_images import validate_cifake
from backend.app.prepare_forgerynet_images import load_official_mapping


class PaginatedClient:
    def __init__(self):
        self.calls = []

    def list_objects_v2(self, **kwargs):
        self.calls.append(kwargs)
        if "ContinuationToken" not in kwargs:
            return {
                "Contents": [{"Key": "CIfake/train/REAL/a.jpg"}],
                "IsTruncated": True,
                "NextContinuationToken": "next",
            }
        return {"Contents": [{"Key": "CIfake/test/fake/b.png"}], "IsTruncated": False}


def test_inventory_is_paginated_bounded_and_reports_cifake_partitions():
    client = PaginatedClient()
    report = inventory_dataset(client, "deepfake", "cifake", "CIfake/", 2)

    assert report["objects_scanned"] == 2
    assert report["partition_label_counts"] == {
        "train": {"real": 1},
        "test": {"fake": 1},
    }
    assert len(client.calls) == 2
    assert all("Access" not in str(call) and "Secret" not in str(call) for call in client.calls)
    assert report["completed"] is True
    assert report["truncated_by_limit"] is False


def test_inventory_marks_limit_only_when_service_has_more_objects():
    class Client:
        def list_objects_v2(self, **kwargs):
            if "ContinuationToken" not in kwargs:
                return {
                    "Contents": [{"Key": "CIfake/train/real/a.jpg"}],
                    "IsTruncated": True,
                    "NextContinuationToken": "more",
                }
            return {"Contents": [{"Key": "CIfake/train/fake/b.jpg"}], "IsTruncated": False}

    report = inventory_dataset(Client(), "bucket", "cifake", "CIfake/", 1)

    assert report["completed"] is False
    assert report["truncated_by_limit"] is True
    assert "partial" in report["warnings"][0]


def test_cifake_inventory_reports_unknown_layout_and_manifest_is_deduplicated():
    keys = [
        "CIfake/train/REAL/a.jpg",
        "CIfake/train/REAL/a.jpg",
        "CIfake/test/FAKE/b.jpeg",
        "CIfake/README",
        "CIfake/other/image.png",
    ]

    report = inventory_dataset(
        type("Client", (), {"list_objects_v2": lambda self, **kwargs: {
            "Contents": [{"Key": key} for key in keys], "IsTruncated": False
        }})(),
        "bucket", "cifake", "CIfake/", 20,
    )

    assert report["recognized_image_objects"] == 3
    assert report["unknown_or_unclassified_objects"] == 2
    manifest = build_cifake_image_manifest(keys, "CIfake/")
    assert [row["object_key"] for row in manifest] == [
        "CIfake/test/FAKE/b.jpeg", "CIfake/train/REAL/a.jpg"
    ]


def test_forgerynet_csv_inspection_does_not_guess_unknown_schema():
    result = parse_forgerynet_csv_bytes(
        b"video_id,category\norig-1,original\n",
        "metadata.csv",
    )

    assert result.headers == ["video_id", "category"]
    assert result.rows == 1
    assert result.records[0]["category"] == "original"
    assert "labels remain unknown" in result.warnings[0]


def test_forgerynet_video_manifest_maps_verified_csv_labels_and_reports_missing_keys():
    result = parse_forgerynet_video_manifest(
        b", File Path, Label\n0,original/000.mp4,REAL\n"
        b"1,FaceSwap/001.mp4,FAKE\n2,FaceSwap/001.mp4,REAL\n",
        "original.csv",
        available_keys=("forgerynet/original/000.mp4",),
    )

    assert [row["label"] for row in result["records"]] == ["real", "fake"]
    assert result["records"][1]["manipulation_type"] == "FaceSwap"
    assert result["duplicate_entries"] == ["FaceSwap/001.mp4"]
    assert result["ambiguous_labels"] == ["FaceSwap/001.mp4"]
    assert result["unmatched_metadata_entries"] == ["FaceSwap/001.mp4"]


def test_forgerynet_mapping_requires_official_columns(tmp_path):
    path = tmp_path / "mapping.csv"
    path.write_text("video,source,method\nfake.mp4,orig-1,FaceSwap\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required official mapping columns"):
        load_official_mapping(path)


def test_cifake_uppercase_labels_and_train_only_split(tmp_path):
    root = tmp_path / "CIfake"
    for partition, labels in {"train": ("REAL", "fake"), "test": ("real", "FAKE")}.items():
        for label in labels:
            target = root / partition / label
            target.mkdir(parents=True)
            for index in range(3):
                (target / f"{index}.png").write_bytes(b"not-an-image")
    # Replace files with valid images through the existing test dependency.
    from PIL import Image
    for index, path in enumerate(root.rglob("*.png")):
        Image.new("RGB", (4, 4), (20 + index, 30, 40)).save(path)

    output = tmp_path / "out"
    result = prepare_cifake(root, output, seed=7)
    assert result["external_test"] == 6
    assert (output / "external-test.csv").is_file()
    assert json.loads((output / "external-test-dataset-card.json").read_text())["external_evaluation_only"] is True
    with pytest.raises(ValueError, match="evaluation-only"):
        reject_external_evaluation_manifest(output / "external-test-dataset-card.json")
    train_paths = set()
    for split in ("train", "val", "test"):
        with (output / f"{split}.csv").open(newline="", encoding="utf-8") as handle:
            train_paths.update(row["path"] for row in csv.DictReader(handle))
    assert all("/test/" not in path.replace("\\", "/") for path in train_paths)


def test_case_insensitive_generic_image_scan(tmp_path):
    from PIL import Image
    for index, label in enumerate(("REAL", "fake")):
        target = tmp_path / label
        target.mkdir()
        Image.new("RGB", (4, 4), (index + 1, 0, 0)).save(target / f"{label}.jpg")
    report = scan_dataset(tmp_path)
    assert {record.label_name for record in report.records} == {"real", "fake"}


def test_frame_extraction_records_deterministic_metadata(tmp_path):
    import cv2
    import numpy as np

    video_path = tmp_path / "source.mp4"
    writer = cv2.VideoWriter(
        str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (16, 16)
    )
    for index in range(10):
        writer.write(np.full((16, 16, 3), index * 10, dtype=np.uint8))
    writer.release()

    records = extract_frames(video_path, tmp_path / "frames", samples=3, margin=0.1)

    assert len(records) == 3
    assert [record["frame_index"] for record in records] == [1, 4, 8]
    assert all("samples=3;margin=0.1" in record["extraction_settings"] for record in records)
    assert len({record["path"] for record in records}) == 3


class CifakeClient:
    def __init__(self, objects):
        self.objects = objects
        self.calls = []

    def list_objects_v2(self, **kwargs):
        self.calls.append(kwargs)
        start = 2 if kwargs.get("ContinuationToken") else 0
        page = self.objects[start:start + 2]
        result = {"Contents": [{"Key": key} for key in page], "IsTruncated": start == 0}
        if start == 0:
            result["NextContinuationToken"] = "page-2"
        return result

    def download_fileobj(self, bucket, key, body):
        from PIL import Image
        import io
        image = Image.new("RGB", (4, 4), (20, 40, 60))
        image.save(body, format="JPEG")


def test_fetch_sample_paginates_and_downloads_both_classes(tmp_path):
    client = CifakeClient([
        "CIfake/train/FAKE/01.jpg",
        "CIfake/train/FAKE/02.jpg",
        "CIfake/train/REAL/01.jpg",
        "CIfake/train/REAL/02.jpg",
    ])
    result = fetch_sample(
        "cifake", tmp_path, partition="train", per_label=1,
        client=client, config=type("Config", (), {
            "r2_bucket": "bucket", "r2_cifake_prefix": "CIfake",
            "r2_forgerynet_prefix": "forgerynet",
        })(),
    )

    assert result["counts"] == {"real": 1, "fake": 1}
    assert len(client.calls) == 2
    assert (tmp_path / "train" / "real" / "00.jpg").is_file()
    assert (tmp_path / "train" / "fake" / "00.jpg").is_file()


def test_recovery_merges_separate_samples_without_overwriting(tmp_path):
    source_train = tmp_path / "old-train"
    source_test = tmp_path / "old-test"
    from PIL import Image
    for source, partition, label, key in (
        (source_train, "train", "fake", "CIfake/train/FAKE/a.jpg"),
        (source_test, "test", "fake", "CIfake/test/FAKE/b.jpg"),
    ):
        image_path = source / partition / label / "00.jpg"
        image_path.parent.mkdir(parents=True)
        Image.new("RGB", (4, 4), (1, 2, 3)).save(image_path)
        (source / "sample-manifest.json").write_text(json.dumps({
            "dataset": "cifake", "prefix": f"CIfake/{partition}/",
            "objects": [{"key": key, "local_path": str(image_path),
                         "label_name": label, "status": "downloaded"}]
        }), encoding="utf-8")
    output = tmp_path / "canonical"
    report = recover_samples([source_train, source_test], output)

    assert len(report["reused"]) == 2
    assert (output / "train" / "fake" / "00.jpg").is_file()
    assert (output / "test" / "fake" / "00.jpg").is_file()
    assert (output / "recovery-report.json").is_file()


def test_validate_cifake_reports_missing_classes_and_corrupt_files(tmp_path):
    (tmp_path / "train" / "REAL").mkdir(parents=True)
    (tmp_path / "train" / "REAL" / "bad.jpg").write_bytes(b"not-image")

    report = validate_cifake(tmp_path)

    assert report["valid"] is False
    assert "test/fake" in report["missing_combinations"]
    assert report["invalid_files"]
