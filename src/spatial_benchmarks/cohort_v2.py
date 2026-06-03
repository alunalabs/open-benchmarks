"""Cohort benchmark v2 loading, aggregation, and metrics."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import read_csv_rows, read_json, require_columns
from .metrics import (
    auc_above_group_median,
    finite_float,
    mean,
    median,
    pearson,
    quantile,
    response_distribution,
    spearman,
    within_group_correlation,
)


DEFAULT_SCORE_COLUMN = "apoptosis_prevalence_basic_score"
DEFAULT_RISK_SCORE_COLUMN = "apoptosis_prevalence_nonresponse_score_mean"
DEFAULT_THRESHOLD_PROBABILITY_COLUMN = "prob_apoptosis_prevalence_orr_gt_20pct"

PREDICTION_REQUIRED_COLUMNS = ("disease", "drug", "orr_pct")
PATIENT_REQUIRED_COLUMNS = ("base_cohort_id", "patient_id", "relative_response_probability")


@dataclass(frozen=True)
class CohortBenchmarkV2:
    root: Path
    manifest: dict[str, Any]
    policy: dict[str, Any]
    metrics: list[dict[str, Any]]
    by_disease_metrics: list[dict[str, Any]]
    predictions: list[dict[str, Any]]
    patient_probabilities: list[dict[str, Any]]

    @classmethod
    def from_directory(
        cls,
        root: str | Path,
        *,
        load_predictions: bool = True,
        load_patient_probabilities: bool = False,
    ) -> "CohortBenchmarkV2":
        root_path = Path(root)
        manifest = read_json(root_path / "manifest.json")
        policy = read_json(root_path / "policy.json")
        metrics = read_csv_rows(root_path / "metrics.csv") if (root_path / "metrics.csv").exists() else []
        by_disease = (
            read_csv_rows(root_path / "by_disease_metrics.csv")
            if (root_path / "by_disease_metrics.csv").exists()
            else []
        )
        predictions = (
            read_csv_rows(root_path / "predictions.csv")
            if load_predictions and (root_path / "predictions.csv").exists()
            else []
        )
        patient_probabilities = (
            read_csv_rows(root_path / "patient_probabilities.csv")
            if load_patient_probabilities and (root_path / "patient_probabilities.csv").exists()
            else []
        )
        if predictions:
            require_columns(predictions, PREDICTION_REQUIRED_COLUMNS, table="cohort v2 predictions")
        if patient_probabilities:
            require_columns(patient_probabilities, PATIENT_REQUIRED_COLUMNS, table="cohort v2 patient probabilities")
        return cls(
            root=root_path,
            manifest=manifest,
            policy=policy,
            metrics=metrics,
            by_disease_metrics=by_disease,
            predictions=predictions,
            patient_probabilities=patient_probabilities,
        )

    @property
    def default_score_column(self) -> str:
        return str(self.policy.get("default_score_column") or self.manifest.get("default_score_column") or DEFAULT_SCORE_COLUMN)

    def recompute_metrics(self, *, score_col: str | None = None) -> list[dict[str, Any]]:
        if not self.predictions:
            raise ValueError("predictions.csv was not loaded")
        return summarize_predictions(self.predictions, score_col=score_col or self.default_score_column)


def orr_scored_rows(rows: list[dict[str, Any]], *, score_col: str, orr_col: str = "orr_pct") -> list[dict[str, Any]]:
    """Rows with finite observed ORR and finite score.

    Cohort benchmark v2 keeps `orr_missing=True` on several CRC rows whose ORR
    labels were later filled by the 2026-05-27 curation. The authoritative
    production metric denominator is therefore finite-label plus finite-score,
    not the stale `orr_missing` flag.
    """

    scored: list[dict[str, Any]] = []
    for row in rows:
        if math.isfinite(finite_float(row.get(orr_col))) and math.isfinite(finite_float(row.get(score_col))):
            scored.append(row)
    return scored


def metric_row(
    rows: list[dict[str, Any]],
    *,
    score_col: str,
    scope: str = "global",
    disease: str = "all",
    label: str | None = None,
) -> dict[str, Any]:
    scored = orr_scored_rows(rows, score_col=score_col)
    return {
        "scope": scope,
        "disease": disease,
        "score_policy": "cohort_benchmark_v2",
        "readout": "patient_apoptotic_fraction_axis_substitution",
        "score_col": score_col,
        "label": label or score_col,
        "n_orr": len(scored),
        "pearson": pearson([row["orr_pct"] for row in scored], [row[score_col] for row in scored]),
        "spearman": spearman([row["orr_pct"] for row in scored], [row[score_col] for row in scored]),
        "within_disease_pair_weighted_pearson": within_group_correlation(
            scored,
            group_col="disease",
            x_col="orr_pct",
            y_col=score_col,
            method="pearson",
        ),
        "within_disease_pair_weighted_spearman": within_group_correlation(
            scored,
            group_col="disease",
            x_col="orr_pct",
            y_col=score_col,
            method="spearman",
        ),
        "auc_success_above_disease_median": auc_above_group_median(
            scored,
            group_col="disease",
            value_col="orr_pct",
            score_col=score_col,
        ),
        "mean_response_probability": mean([row.get(score_col) for row in scored]),
        "mean_expected_response_pct": 100.0 * mean([row.get(score_col) for row in scored]),
    }


def summarize_predictions(rows: list[dict[str, Any]], *, score_col: str = DEFAULT_SCORE_COLUMN) -> list[dict[str, Any]]:
    summary = [metric_row(rows, score_col=score_col)]
    diseases = sorted({str(row.get("disease", "")) for row in rows if str(row.get("disease", "")).strip()})
    for disease in diseases:
        disease_rows = [row for row in rows if str(row.get("disease", "")) == disease]
        summary.append(metric_row(disease_rows, score_col=score_col, scope="disease", disease=disease))
    return summary


def aggregate_patient_probabilities(
    patient_rows: list[dict[str, Any]],
    *,
    group_col: str = "base_cohort_id",
    probability_col: str = "relative_response_probability",
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in patient_rows:
        groups.setdefault(str(row.get(group_col, "")), []).append(row)

    aggregates: list[dict[str, Any]] = []
    for group_id, rows in groups.items():
        probabilities = [finite_float(row.get(probability_col)) for row in rows]
        probabilities = [value for value in probabilities if math.isfinite(value)]
        dist = response_distribution(probabilities)
        first = rows[0]
        aggregates.append(
            {
                group_col: group_id,
                "cohort": first.get("cohort", first.get("disease", "")),
                "drug": first.get("drug", ""),
                "drug_norm": first.get("drug_norm", ""),
                "patient_count": len(probabilities),
                f"{probability_col}_mean": mean(probabilities),
                f"{probability_col}_median": median(probabilities),
                f"{probability_col}_p10": quantile(probabilities, 0.10),
                "response_count_pmf_json": json.dumps(dist["response_count_pmf"], separators=(",", ":")),
                **{key: value for key, value in dist.items() if key != "response_count_pmf"},
            }
        )
    return aggregates


def validate_default_score_formula(
    rows: list[dict[str, Any]],
    *,
    score_col: str = DEFAULT_SCORE_COLUMN,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Check the v2 default formula when the required columns are present."""

    required = (
        "engagement_support",
        "coverage_support",
        "apoptosis_step4_pred_fraction",
        "resistant_tail_control",
    )
    checked = 0
    max_abs_diff = 0.0
    for row in rows:
        if not all(key in row for key in (*required, score_col)):
            continue
        expected = 1.0
        ok = True
        for key in required:
            value = finite_float(row.get(key))
            if not math.isfinite(value):
                ok = False
                break
            expected *= max(0.0, min(1.0, value))
        observed = finite_float(row.get(score_col))
        if ok and math.isfinite(observed):
            checked += 1
            max_abs_diff = max(max_abs_diff, abs(expected - observed))
    return {
        "checked_rows": checked,
        "max_abs_diff": max_abs_diff,
        "passes": checked > 0 and max_abs_diff <= tolerance,
        "formula": "engagement_support * coverage_support * apoptosis_step4_pred_fraction * resistant_tail_control",
    }

