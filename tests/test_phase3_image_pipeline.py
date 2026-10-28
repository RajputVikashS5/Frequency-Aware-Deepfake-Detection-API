import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from backend.app.dataset import scan_dataset, split_records
from backend.app.frequency import fft_log_magnitude, preprocess_fft
from backend.app.preprocessing import Normalization, preprocess_rgb


def image_bytes(color: tuple[int, int, int] = (20, 40, 60)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 20), color).save(buffer, format="PNG")
    return buffer.getvalue()


def write_image(path: Path, color: tuple[int, int, int] = (20, 40, 60)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes(color))


def make_dataset(root: Path, groups_per_class: int = 3) -> None:
    for label in ("real", "fake"):
        for index in range(groups_per_class):
            color = (index + 1, 20, 40) if label == "real" else (index + 1, 80, 120)
            write_image(root / label / f"{label}_{index}.png", color)


def test_dataset_maps_labels_and_reports_corrupt_and_unsupported_files(tmp_path):
    make_dataset(tmp_path)
    (tmp_path / "real" / "broken.png").write_bytes(b"not an image")
    (tmp_path / "fake" / "notes.txt").write_text("not supported", encoding="utf-8")

    report = scan_dataset(tmp_path)

    assert {record.label for record in report.records} == {0, 1}
    assert {record.label_name for record in report.records} == {"real", "fake"}
    assert len(report.exclusions) == 2
    assert any("corrupt" in item.reason for item in report.exclusions)
    assert any("unsupported" in item.reason for item in report.exclusions)


def test_dataset_detects_content_duplicates(tmp_path):
    make_dataset(tmp_path)
    duplicate = tmp_path / "fake" / "duplicate.png"
    duplicate.write_bytes((tmp_path / "real" / "real_0.png").read_bytes())

    report = scan_dataset(tmp_path)

    assert str(duplicate) in report.content_duplicate_paths
    assert report.statistics["content_duplicates"] == 1


def test_rgb_preprocessing_returns_normalized_chw_224_tensor():
    output = preprocess_rgb(
        image_bytes(),
        target_size=(224, 224),
        normalization=None,
    )

    assert output.shape == (3, 224, 224)
    assert output.dtype == np.float32
    assert 0 <= output.min() <= output.max() <= 1


def test_rgb_normalization_is_configurable():
    output = preprocess_rgb(
        image_bytes(),
        target_size=(8, 8),
        normalization=Normalization(mean=(0, 0, 0), std=(1, 1, 1)),
    )

    assert output.shape == (3, 8, 8)
    assert np.isfinite(output).all()


def test_fft_shape_and_numerical_stability():
    spectrum = fft_log_magnitude(np.full((16, 12), np.nan, dtype=np.float32))

    assert spectrum.shape == (16, 12)
    assert spectrum.dtype == np.float32
    assert np.isfinite(spectrum).all()
    assert 0 <= spectrum.min() <= spectrum.max() <= 1


def test_fft_rejects_invalid_input():
    with pytest.raises(ValueError, match="2D"):
        fft_log_magnitude(np.zeros((2, 2, 2, 2)))


def test_fft_image_preprocessing_is_rgb_aware_deterministic_and_three_channel():
    data = image_bytes()
    first = preprocess_fft(data)
    second = preprocess_fft(data)

    assert first.shape == (3, 224, 224)
    assert first.dtype == np.float32
    assert np.isfinite(first).all()
    assert np.array_equal(first, second)
    assert np.array_equal(first[0], first[1])
    assert 0 <= first.min() <= first.max() <= 1


def test_fft_image_preprocessing_rejects_invalid_image_bytes():
    with pytest.raises(ValueError, match="Unable to decode|empty"):
        preprocess_fft(b"not an image")


def test_group_aware_split_is_reproducible_and_has_no_group_leakage(tmp_path):
    make_dataset(tmp_path, groups_per_class=4)
    groups = {}
    for label in ("real", "fake"):
        for index in range(4):
            groups[f"{label}/{label}_{index}.png"] = f"source-{label}-{index}"
    report = scan_dataset(tmp_path, groups=groups)
    first = split_records(report.records, seed=17)
    second = split_records(report.records, seed=17)

    assert first == second
    group_sets = {name: {item.group_id for item in records} for name, records in first.items()}
    assert group_sets["train"].isdisjoint(group_sets["val"])
    assert group_sets["train"].isdisjoint(group_sets["test"])
    assert group_sets["val"].isdisjoint(group_sets["test"])


def test_related_images_remain_in_the_same_split(tmp_path):
    for label in ("real", "fake"):
        for group_index in range(3):
            for variant in range(2):
                write_image(
                    tmp_path / label / f"{label}_{group_index}_{variant}.png",
                    (group_index + variant + 1, 30 if label == "real" else 90, 40),
                )
    groups = {
        f"{label}/{label}_{group_index}_{variant}.png": f"{label}-source-{group_index}"
        for label in ("real", "fake")
        for group_index in range(3)
        for variant in range(2)
    }

    splits = split_records(scan_dataset(tmp_path, groups=groups).records, seed=5)
    report = scan_dataset(tmp_path, groups=groups)
    splits = split_records(report.records, seed=5)
    locations = {
        group_id: {
            split
            for split, records in splits.items()
            if any(record.group_id == group_id for record in records)
        }
        for group_id in {record.group_id for record in report.records}
    }
    assert len(locations) == 6
    assert all(len(split_names) == 1 for split_names in locations.values())


def test_split_fails_when_class_groups_are_insufficient(tmp_path):
    make_dataset(tmp_path, groups_per_class=2)
    report = scan_dataset(tmp_path)

    with pytest.raises(ValueError, match="at least three groups"):
        split_records(report.records)
