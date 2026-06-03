"""Shared metric and probability-distribution utilities."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def finite_float(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def finite_pairs(xs: Iterable[Any], ys: Iterable[Any]) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for x_raw, y_raw in zip(xs, ys, strict=False):
        x = finite_float(x_raw)
        y = finite_float(y_raw)
        if math.isfinite(x) and math.isfinite(y):
            pairs.append((x, y))
    return pairs


def pearson(xs: Iterable[Any], ys: Iterable[Any]) -> float:
    pairs = finite_pairs(xs, ys)
    if len(pairs) < 2:
        return math.nan
    x_values = [x for x, _ in pairs]
    y_values = [y for _, y in pairs]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    x_ss = sum((x - x_mean) ** 2 for x in x_values)
    y_ss = sum((y - y_mean) ** 2 for y in y_values)
    if x_ss <= 0.0 or y_ss <= 0.0:
        return math.nan
    cov = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    return cov / math.sqrt(x_ss * y_ss)


def rankdata(values: Sequence[float]) -> list[float]:
    """Average ranks, 1-indexed, with ties handled like scipy.stats.rankdata."""

    order = sorted(range(len(values)), key=lambda idx: values[idx])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end + 1) / 2.0
        for pos in range(start, end + 1):
            ranks[order[pos]] = rank
        start = end + 1
    return ranks


def spearman(xs: Iterable[Any], ys: Iterable[Any]) -> float:
    pairs = finite_pairs(xs, ys)
    if len(pairs) < 2:
        return math.nan
    x_ranks = rankdata([x for x, _ in pairs])
    y_ranks = rankdata([y for _, y in pairs])
    return pearson(x_ranks, y_ranks)


def roc_auc(labels: Iterable[Any], scores: Iterable[Any], *, positive: int = 1) -> float:
    pairs: list[tuple[int, float]] = []
    for label_raw, score_raw in zip(labels, scores, strict=False):
        score = finite_float(score_raw)
        if not math.isfinite(score):
            continue
        try:
            label = int(float(label_raw))
        except (TypeError, ValueError):
            continue
        pairs.append((label, score))

    positives = [score for label, score in pairs if label == positive]
    negatives = [score for label, score in pairs if label != positive]
    if not positives or not negatives:
        return math.nan

    wins = 0.0
    for positive_score in positives:
        for negative_score in negatives:
            if positive_score > negative_score:
                wins += 1.0
            elif positive_score == negative_score:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def balanced_accuracy(labels: Iterable[Any], predictions: Iterable[Any], *, positive: int = 1) -> float:
    y_true: list[int] = []
    y_pred: list[int] = []
    for label_raw, prediction_raw in zip(labels, predictions, strict=False):
        try:
            label = int(float(label_raw))
        except (TypeError, ValueError):
            continue
        if isinstance(prediction_raw, bool):
            prediction = int(prediction_raw)
        else:
            try:
                prediction = int(float(prediction_raw))
            except (TypeError, ValueError):
                continue
        y_true.append(label)
        y_pred.append(prediction)

    positives = [pred for label, pred in zip(y_true, y_pred, strict=True) if label == positive]
    negatives = [pred for label, pred in zip(y_true, y_pred, strict=True) if label != positive]
    if not positives or not negatives:
        return math.nan
    sensitivity = sum(pred == positive for pred in positives) / len(positives)
    specificity = sum(pred != positive for pred in negatives) / len(negatives)
    return 0.5 * (sensitivity + specificity)


def candidate_thresholds(scores: Iterable[Any]) -> list[float]:
    values = sorted({finite_float(score) for score in scores if math.isfinite(finite_float(score))})
    if not values:
        return []
    if len(values) == 1:
        epsilon = max(abs(values[0]) * 1e-9, 1e-12)
        return [values[0] - epsilon, values[0], values[0] + epsilon]
    epsilon = max((values[-1] - values[0]) * 1e-9, 1e-12)
    return [
        values[0] - epsilon,
        *((left + right) / 2.0 for left, right in zip(values, values[1:], strict=False)),
        values[-1] + epsilon,
    ]


def best_balanced_accuracy(
    labels: Sequence[Any],
    scores: Sequence[Any],
    *,
    positive: int = 1,
) -> dict[str, float | int]:
    best = {"threshold": math.nan, "balanced_accuracy": -math.inf, "predicted_positive": 0}
    score_values = [finite_float(score) for score in scores]
    for threshold in candidate_thresholds(score_values):
        predictions = [int(score >= threshold) if math.isfinite(score) else 0 for score in score_values]
        current = balanced_accuracy(labels, predictions, positive=positive)
        if current > float(best["balanced_accuracy"]):
            best = {
                "threshold": threshold,
                "balanced_accuracy": current,
                "predicted_positive": int(sum(predictions)),
            }
    if best["balanced_accuracy"] == -math.inf:
        return {"threshold": math.nan, "balanced_accuracy": math.nan, "predicted_positive": 0}
    return best


def sigmoid(value: Any, center: float = 0.0, scale: float = 1.0) -> float:
    numeric = finite_float(value)
    if not math.isfinite(numeric):
        return math.nan
    z = max(-40.0, min(40.0, (numeric - center) / scale))
    return 1.0 / (1.0 + math.exp(-z))


def mean(values: Iterable[Any]) -> float:
    clean = [finite_float(value) for value in values]
    clean = [value for value in clean if math.isfinite(value)]
    return sum(clean) / len(clean) if clean else math.nan


def quantile(values: Iterable[Any], q: float) -> float:
    clean = sorted(finite_float(value) for value in values)
    clean = [value for value in clean if math.isfinite(value)]
    if not clean:
        return math.nan
    if len(clean) == 1:
        return clean[0]
    pos = q * (len(clean) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return clean[lo]
    frac = pos - lo
    return clean[lo] * (1.0 - frac) + clean[hi] * frac


def median(values: Iterable[Any]) -> float:
    return quantile(values, 0.50)


def product(values: Iterable[Any], *, default: float = 1.0) -> float:
    out = 1.0
    used = False
    for value_raw in values:
        value = finite_float(value_raw)
        if math.isfinite(value):
            out *= max(0.0, min(1.0, value))
            used = True
    return out if used else default


def geometric_mean(values: Iterable[Any], *, default: float = 1.0) -> float:
    clean = [max(0.0, min(1.0, finite_float(value))) for value in values]
    clean = [value for value in clean if math.isfinite(value)]
    if not clean:
        return default
    return product(clean) ** (1.0 / len(clean))


def softmin(values: Iterable[Any], *, default: float = 1.0) -> float:
    clean = [max(0.0, min(1.0, finite_float(value))) for value in values]
    clean = [value for value in clean if math.isfinite(value)]
    return min(clean) if clean else default


def poisson_binomial_pmf(probabilities: Iterable[Any]) -> list[float]:
    """Return the response-count PMF for independent Bernoulli probabilities."""

    pmf = [1.0]
    for raw_probability in probabilities:
        probability = finite_float(raw_probability)
        if not math.isfinite(probability):
            continue
        p = max(0.0, min(1.0, probability))
        next_pmf = [0.0] * (len(pmf) + 1)
        for count, mass in enumerate(pmf):
            next_pmf[count] += mass * (1.0 - p)
            next_pmf[count + 1] += mass * p
        pmf = next_pmf
    return pmf


def count_quantile(pmf: Sequence[float], quantile: float) -> int:
    cumulative = 0.0
    for idx, mass in enumerate(pmf):
        cumulative += mass
        if cumulative >= quantile:
            return idx
    return max(0, len(pmf) - 1)


def threshold_probability(pmf: Sequence[float], threshold: float, *, strict: bool) -> float:
    n = len(pmf) - 1
    if n <= 0:
        return math.nan
    total = 0.0
    for count, mass in enumerate(pmf):
        rate = count / n
        passes = rate > threshold + 1e-12 if strict else rate + 1e-12 >= threshold
        if passes:
            total += mass
    return total


def response_distribution(probabilities: Iterable[Any], thresholds: Sequence[float] = (0.1, 0.2, 0.3, 0.5)) -> dict[str, Any]:
    pmf = poisson_binomial_pmf(probabilities)
    n = len(pmf) - 1
    expected = sum(count * mass for count, mass in enumerate(pmf))
    row: dict[str, Any] = {
        "response_count_pmf": pmf,
        "expected_responders": expected,
        "expected_response_pct": 100.0 * expected / n if n else math.nan,
        "median_responders": count_quantile(pmf, 0.50),
        "p10_responders": count_quantile(pmf, 0.10),
        "p90_responders": count_quantile(pmf, 0.90),
        "prob_any_response": 1.0 - pmf[0] if pmf else math.nan,
    }
    for threshold in thresholds:
        suffix = f"{int(round(threshold * 100)):02d}pct"
        row[f"prob_orr_gt_{suffix}"] = threshold_probability(pmf, threshold, strict=True)
        row[f"prob_orr_ge_{suffix}"] = threshold_probability(pmf, threshold, strict=False)
    return row


def group_rows(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    return dict(grouped)


def within_group_correlation(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_col: str,
    x_col: str,
    y_col: str,
    method: str = "pearson",
) -> float:
    total = 0.0
    total_weight = 0.0
    corr_fn = spearman if method == "spearman" else pearson
    for group in group_rows(rows, group_col).values():
        xs = [row.get(x_col) for row in group]
        ys = [row.get(y_col) for row in group]
        corr = corr_fn(xs, ys)
        n = len(finite_pairs(xs, ys))
        if n >= 3 and math.isfinite(corr):
            weight = n * (n - 1) / 2.0
            total += corr * weight
            total_weight += weight
    return total / total_weight if total_weight else math.nan


def auc_above_group_median(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_col: str,
    value_col: str,
    score_col: str,
) -> float:
    medians: dict[str, float] = {}
    for group_name, group in group_rows(rows, group_col).items():
        values = sorted(finite_float(row.get(value_col)) for row in group)
        values = [value for value in values if math.isfinite(value)]
        if not values:
            continue
        mid = len(values) // 2
        medians[group_name] = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2.0

    labels: list[int] = []
    scores: list[float] = []
    for row in rows:
        group = str(row.get(group_col, ""))
        value = finite_float(row.get(value_col))
        score = finite_float(row.get(score_col))
        if group in medians and math.isfinite(value) and math.isfinite(score):
            labels.append(int(value > medians[group]))
            scores.append(score)
    return roc_auc(labels, scores)
