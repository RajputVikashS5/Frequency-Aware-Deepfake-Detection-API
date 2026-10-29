import numpy as np

from backend.training.evaluate import bootstrap_intervals


def test_bootstrap_intervals_are_bounded_and_reproducible():
    labels = np.array([0, 0, 1, 1, 0, 1])
    scores = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.7])

    first = bootstrap_intervals(labels, scores, seed=7, iterations=100)
    second = bootstrap_intervals(labels, scores, seed=7, iterations=100)

    assert first == second
    for interval in first.values():
        assert 0.0 <= interval["lower_95"] <= interval["upper_95"] <= 1.0
