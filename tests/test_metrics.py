from __future__ import annotations

import math

from spatial_benchmarks.metrics import (
    balanced_accuracy,
    cosine,
    module_mean_cosine,
    pearson,
    poisson_binomial_pmf,
    response_distribution,
    roc_auc,
    spearman,
)


def test_basic_metrics() -> None:
    assert pearson([1, 2, 3], [2, 4, 6]) == 1.0
    assert cosine([1, 0], [1, 0]) == 1.0
    assert spearman([10, 20, 30], [1, 2, 3]) == 1.0
    assert roc_auc([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == 1.0
    assert balanced_accuracy([1, 1, 0, 0], [1, 0, 0, 0]) == 0.75


def test_module_mean_cosine() -> None:
    rows = [
        {"module": "a", "module_predicted_delta": 1.0, "module_observed_delta": 2.0},
        {"module": "a", "module_predicted_delta": 3.0, "module_observed_delta": 4.0},
        {"module": "b", "module_predicted_delta": -1.0, "module_observed_delta": -2.0},
        {"module": "b", "module_predicted_delta": -3.0, "module_observed_delta": -4.0},
    ]
    expected = cosine([2.0, -2.0], [3.0, -3.0])
    assert math.isclose(module_mean_cosine(rows), expected)


def test_poisson_binomial_distribution() -> None:
    pmf = poisson_binomial_pmf([0.5, 0.5])
    assert pmf == [0.25, 0.5, 0.25]
    dist = response_distribution([1.0, 0.0, 0.5], thresholds=(0.5,))
    assert math.isclose(dist["expected_responders"], 1.5)
    assert math.isclose(dist["prob_orr_gt_50pct"], 0.5)
