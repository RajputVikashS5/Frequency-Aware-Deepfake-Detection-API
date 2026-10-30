import numpy as np
import pandas as pd

from backend.training.external_evaluation import (
    balanced_sample,
    calculate_model_metrics,
    classification_report_dict,
)


def _result():
    return {
        "labels": np.array([0, 0, 1, 1]),
        "predictions": np.array([0, 1, 1, 0]),
        "scores": np.array([0.1, 0.8, 0.9, 0.2]),
    }


def test_external_metrics_include_rates_and_auc():
    metrics = calculate_model_metrics(_result())

    assert metrics["total_images"] == 4
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["specificity"] == 0.5
    assert metrics["false_positive_rate"] == 0.5
    assert metrics["false_negative_rate"] == 0.5
    assert metrics["roc_auc"] == 0.75
    assert metrics["average_precision"] == 0.8333333333333333


def test_classification_report_uses_task_labels():
    report = classification_report_dict(_result())

    assert "Real / Human" in report
    assert "Fake / AI" in report


def test_balanced_sample_is_reproducible():
    manifest = pd.DataFrame(
        [
            {"path": f"real-{index}", "label": 0}
            for index in range(3)
        ]
        + [
            {"path": f"fake-{index}", "label": 1}
            for index in range(2)
        ]
    )

    first = balanced_sample(manifest, 2, 42)
    second = balanced_sample(manifest, 2, 42)

    assert first["label"].value_counts().to_dict() == {0: 2, 1: 2}
    assert first["path"].tolist() == second["path"].tolist()
