"""Recompute public release metrics from checked-in score artifacts."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .atlas_orr import metric_row
from .io import read_csv_rows
from .metrics import (
    auc_above_group_median,
    balanced_accuracy,
    finite_float,
    mean,
    median,
    module_mean_cosine,
    pearson,
    quantile,
    rankdata,
    roc_auc,
    sigmoid,
    spearman,
)


COHORT_GAIA_SCORE_COL = "gaia_predicted_orr_pct"
ATLAS_SCORE_COL = "atlas_mono_disease_therapy_shrink_k8"
DEPMAP_SCORE_COLS = (
    "depmap_lineage_sensitivity_rank",
    "depmap_lineage_auc_sensitivity",
    "depmap_global_auc_sensitivity",
)
CRC_RANK_SCORE_COL = "response_score_rank_calibrated"
CSCC_SCORE_COL = "relative_response_probability"
CRC_SUPPORT_COLS = (
    "kras_mapk_support",
    "egfr_support",
    "cytostasis_support",
    "escape_control_support",
    "kill_conversion_support",
)
CSCC_AXIS_COLS = (
    "engagement_support",
    "response_conversion_support",
    "coverage_support",
    "resistant_tail_control",
    "escape_refuge_control",
)


def _finite_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    score_col: str,
    observed_col: str = "observed_orr_pct",
) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if math.isfinite(finite_float(row.get(score_col)))
        and math.isfinite(finite_float(row.get(observed_col)))
    ]


def _nan_equal(left: float, right: float) -> bool:
    return math.isnan(left) and math.isnan(right)


def compare_metric_rows(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    keys: Sequence[str],
    tolerance: float = 1e-9,
) -> list[dict[str, Any]]:
    """Return metric drift rows for numeric/string keys that do not match."""

    drift: list[dict[str, Any]] = []
    for key in keys:
        actual_value = actual.get(key)
        expected_value = expected.get(key)
        actual_numeric = finite_float(actual_value)
        expected_numeric = finite_float(expected_value)
        if math.isfinite(actual_numeric) or math.isfinite(expected_numeric):
            if _nan_equal(actual_numeric, expected_numeric):
                continue
            if math.isclose(
                actual_numeric,
                expected_numeric,
                rel_tol=tolerance,
                abs_tol=tolerance,
            ):
                continue
            drift.append(
                {
                    "field": key,
                    "actual": actual_value,
                    "expected": expected_value,
                    "absolute_delta": actual_numeric - expected_numeric,
                }
            )
        elif str(actual_value) != str(expected_value):
            drift.append({"field": key, "actual": actual_value, "expected": expected_value})
    return drift


def _mean_square_error(rows: Sequence[Mapping[str, Any]], *, score_col: str) -> float:
    errors = [
        finite_float(row.get(score_col)) - finite_float(row.get("observed_orr_pct"))
        for row in rows
    ]
    return math.sqrt(sum(error * error for error in errors) / len(errors)) if errors else math.nan


def cohort_global_metric(
    rows: Sequence[Mapping[str, Any]],
    *,
    score_col: str,
    label: str | None = None,
    is_orr_scale: bool = True,
) -> dict[str, Any]:
    """Metric row for a cohort ORR score table."""

    scored = _finite_rows(rows, score_col=score_col)
    errors = [
        finite_float(row.get(score_col)) - finite_float(row.get("observed_orr_pct"))
        for row in scored
    ]
    row = metric_row(
        list(dict(item) for item in rows),
        score_col=score_col,
        label=label or score_col,
        is_orr_scale=is_orr_scale,
    )
    return {
        "score_col": score_col,
        "label": label or score_col,
        "n_orr": row["n_rows"],
        "n_rows": row["n_rows"],
        "pearson": row["pearson"],
        "spearman": row["spearman"],
        "auc_above_disease_median": row["auc_above_disease_median"],
        "mae_orr_pct": (
            sum(abs(error) for error in errors) / len(errors)
            if is_orr_scale and errors
            else math.nan
        ),
        "rmse_orr_pct": _mean_square_error(scored, score_col=score_col)
        if is_orr_scale
        else math.nan,
        "mean_prediction": row["mean_prediction"],
        "mean_observed_orr": row["mean_observed_orr"],
    }


def cohort_by_disease_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    score_col: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in _finite_rows(rows, score_col=score_col):
        grouped[str(row.get("cohort") or row.get("disease") or "")].append(row)

    out: list[dict[str, Any]] = []
    for cohort in sorted(grouped):
        group = grouped[cohort]
        observed = [finite_float(row.get("observed_orr_pct")) for row in group]
        scores = [finite_float(row.get(score_col)) for row in group]
        errors = [score - label for score, label in zip(scores, observed, strict=True)]
        out.append(
            {
                "cohort": cohort,
                "n_orr": len(group),
                "pearson": pearson(observed, scores),
                "spearman": spearman(observed, scores),
                "mae_orr_pct": sum(abs(error) for error in errors) / len(errors),
                "mean_prediction": mean(scores),
                "mean_observed_orr": mean(observed),
            }
        )
    return out


def reproduce_gaia_cohort_orr(
    *,
    scores_csv: str | Path,
    metrics_csv: str | Path | None = None,
    by_disease_csv: str | Path | None = None,
    score_col: str = COHORT_GAIA_SCORE_COL,
) -> dict[str, Any]:
    rows = read_csv_rows(scores_csv)
    metric = cohort_global_metric(rows, score_col=score_col, is_orr_scale=True)
    by_disease = cohort_by_disease_metrics(rows, score_col=score_col)
    drift: list[dict[str, Any]] = []
    if metrics_csv is not None:
        expected = read_csv_rows(metrics_csv)[0]
        drift.extend(
            compare_metric_rows(
                metric,
                expected,
                keys=(
                    "score_col",
                    "n_orr",
                    "n_rows",
                    "pearson",
                    "spearman",
                    "auc_above_disease_median",
                    "mae_orr_pct",
                    "rmse_orr_pct",
                    "mean_prediction",
                    "mean_observed_orr",
                ),
            )
        )
    if by_disease_csv is not None:
        expected_by_disease = {
            str(row["cohort"]): row for row in read_csv_rows(by_disease_csv)
        }
        for row in by_disease:
            expected = expected_by_disease.get(str(row["cohort"]))
            if not expected:
                drift.append({"cohort": row["cohort"], "field": "cohort", "actual": "present"})
                continue
            for item in compare_metric_rows(
                row,
                expected,
                keys=(
                    "cohort",
                    "n_orr",
                    "pearson",
                    "spearman",
                    "mae_orr_pct",
                    "mean_prediction",
                    "mean_observed_orr",
                ),
            ):
                drift.append({"cohort": row["cohort"], **item})
    return {
        "artifact": str(scores_csv),
        "model_score_artifact": str(scores_csv),
        "score_col": score_col,
        "metrics": metric,
        "by_disease_metrics": by_disease,
        "drift": drift,
    }


def reproduce_atlas_orr_predictions(
    *,
    predictions_csv: str | Path,
    metrics_csv: str | Path | None = None,
    score_col: str = ATLAS_SCORE_COL,
) -> dict[str, Any]:
    rows = read_csv_rows(predictions_csv)
    metric = metric_row(
        list(dict(item) for item in rows),
        score_col=score_col,
        label=score_col,
        is_orr_scale=True,
    )
    drift: list[dict[str, Any]] = []
    if metrics_csv is not None:
        expected = read_csv_rows(metrics_csv)[0]
        drift.extend(
            compare_metric_rows(
                metric,
                expected,
                keys=(
                    "label",
                    "score_col",
                    "n_rows",
                    "pearson",
                    "spearman",
                    "within_disease_pair_pearson",
                    "within_disease_pair_spearman",
                    "within_disease_pairs",
                    "auc_above_disease_median",
                    "mae_orr_pct",
                    "rmse_orr_pct",
                    "mean_prediction",
                    "mean_observed_orr",
                ),
            )
        )
    return {
        "artifact": str(predictions_csv),
        "baseline_score_artifact": str(predictions_csv),
        "score_col": score_col,
        "metrics": metric,
        "drift": drift,
    }


def reproduce_depmap_orr_features(
    *,
    features_csv: str | Path,
    metrics_csv: str | Path | None = None,
) -> dict[str, Any]:
    rows = read_csv_rows(features_csv)
    metrics = [
        metric_row(
            list(dict(item) for item in rows),
            score_col=score_col,
            label=score_col,
            is_orr_scale=False,
        )
        for score_col in DEPMAP_SCORE_COLS
    ]
    drift: list[dict[str, Any]] = []
    if metrics_csv is not None:
        expected_rows = {str(row["score_col"]): row for row in read_csv_rows(metrics_csv)}
        for row in metrics:
            expected = expected_rows.get(str(row["score_col"]))
            if not expected:
                drift.append(
                    {"score_col": row["score_col"], "field": "score_col", "actual": "present"}
                )
                continue
            for item in compare_metric_rows(
                row,
                expected,
                keys=(
                    "label",
                    "score_col",
                    "n_rows",
                    "pearson",
                    "spearman",
                    "within_disease_pair_pearson",
                    "within_disease_pair_spearman",
                    "within_disease_pairs",
                    "auc_above_disease_median",
                    "mae_orr_pct",
                    "rmse_orr_pct",
                    "mean_prediction",
                    "mean_observed_orr",
                ),
            ):
                drift.append({"score_col": row["score_col"], **item})
    primary = next(row for row in metrics if row["score_col"] == DEPMAP_SCORE_COLS[0])
    return {
        "artifact": str(features_csv),
        "baseline_feature_artifact": str(features_csv),
        "primary_score_col": DEPMAP_SCORE_COLS[0],
        "primary_metrics": primary,
        "metrics": metrics,
        "drift": drift,
    }


def _crc_intermediate(row: Mapping[str, Any]) -> dict[str, float]:
    supports = [finite_float(row.get(col)) for col in CRC_SUPPORT_COLS]
    coverage = sum(value > 0.0 for value in supports) / len(supports)
    mean_support = sum(supports) / len(supports)
    p10_support = quantile(supports, 0.10)
    effective_coverage = min(1.0, coverage / 0.80)
    intermediate = min(
        sigmoid(effective_coverage, center=0.90, scale=0.05),
        sigmoid(mean_support, center=0.0, scale=0.015),
        sigmoid(p10_support, center=-0.02, scale=0.015),
    )
    return {
        "ct_hetero_conversion_fraction_positive": coverage,
        "ct_hetero_conversion_mean": mean_support,
        "ct_hetero_conversion_p10": p10_support,
        "module_coverage_effective": effective_coverage,
        "module_calibrated_intermediate": intermediate,
    }


def crc_rank_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for row in rows:
        scored.append({**dict(row), **_crc_intermediate(row)})
    ranks = rankdata([finite_float(row["module_calibrated_intermediate"]) for row in scored])
    n_rows = len(scored)
    for row, rank in zip(scored, ranks, strict=True):
        score = rank / n_rows if n_rows else math.nan
        row[CRC_RANK_SCORE_COL] = score
        row["predicted_responder_rank_ge_0p5"] = score >= 0.5
    return scored


def crc_rank_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = [int(finite_float(row.get("observed_responder"), 0.0)) for row in rows]
    scores = [finite_float(row.get(CRC_RANK_SCORE_COL)) for row in rows]
    predictions = [score >= 0.5 for score in scores]
    responder_scores = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    nonresponder_scores = [
        score for label, score in zip(labels, scores, strict=True) if label != 1
    ]
    return {
        "score_col": CRC_RANK_SCORE_COL,
        "n": len(rows),
        "n_pr": len(responder_scores),
        "n_sd": len(nonresponder_scores),
        "auc_response_high": roc_auc(labels, scores),
        "fixed_0p5_balanced_accuracy": balanced_accuracy(labels, predictions),
        "predicted_responder_count_fixed_0p5": sum(predictions),
        "mean_pr": mean(responder_scores),
        "mean_sd": mean(nonresponder_scores),
        "pr_minus_sd_mean": mean(responder_scores) - mean(nonresponder_scores),
    }


def reproduce_crc_moa_tailored_rank_score(
    *,
    scores_csv: str | Path,
    metrics_csv: str | Path | None = None,
) -> dict[str, Any]:
    released_rows = read_csv_rows(scores_csv)
    recomputed_rows = crc_rank_rows(released_rows)
    metrics = crc_rank_metrics(recomputed_rows)
    drift: list[dict[str, Any]] = []
    for released, recomputed in zip(released_rows, recomputed_rows, strict=True):
        row_id = released.get("source_patient_id") or released.get("source_sample_id")
        for key in (
            "ct_hetero_conversion_fraction_positive",
            "ct_hetero_conversion_mean",
            "ct_hetero_conversion_p10",
            "module_coverage_effective",
            CRC_RANK_SCORE_COL,
        ):
            diff = compare_metric_rows(recomputed, released, keys=(key,))
            drift.extend({"row_id": row_id, **item} for item in diff)
        expected_call = str(released.get("predicted_responder_rank_ge_0p5")) == "True"
        if bool(recomputed["predicted_responder_rank_ge_0p5"]) != expected_call:
            drift.append(
                {
                    "row_id": row_id,
                    "field": "predicted_responder_rank_ge_0p5",
                    "actual": recomputed["predicted_responder_rank_ge_0p5"],
                    "expected": released.get("predicted_responder_rank_ge_0p5"),
                }
            )
    if metrics_csv is not None:
        expected = read_csv_rows(metrics_csv)[0]
        drift.extend(
            compare_metric_rows(
                metrics,
                expected,
                keys=(
                    "score_col",
                    "n",
                    "n_pr",
                    "n_sd",
                    "auc_response_high",
                    "fixed_0p5_balanced_accuracy",
                    "predicted_responder_count_fixed_0p5",
                    "mean_pr",
                    "mean_sd",
                    "pr_minus_sd_mean",
                ),
            )
        )
    return {
        "artifact": str(scores_csv),
        "model_score_artifact": str(scores_csv),
        "score_col": CRC_RANK_SCORE_COL,
        "metrics": metrics,
        "drift": drift,
    }


def _product(values: Sequence[float]) -> float:
    out = 1.0
    for value in values:
        out *= value
    return out


def cscc_recomputed_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        axes = [finite_float(row.get(col)) for col in CSCC_AXIS_COLS]
        product_score = _product(axes)
        geomean = product_score ** (1.0 / len(axes))
        out.append(
            {
                **dict(row),
                CSCC_SCORE_COL: product_score,
                "nonresponse_probability": 1.0 - product_score,
                "universal_axis_geomean_response_probability": geomean,
                "universal_axis_softmin_response_probability": min(axes),
            }
        )
    return out


def cscc_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = [int(finite_float(row.get("response_label"), 0.0)) for row in rows]
    scores = [finite_float(row.get(CSCC_SCORE_COL)) for row in rows]
    responder_scores = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    nonresponder_scores = [
        score for label, score in zip(labels, scores, strict=True) if label != 1
    ]
    return {
        "axis_variant": rows[0].get("axis_variant", "") if rows else "",
        "mode": rows[0].get("mode", "") if rows else "",
        "cascade_step": rows[0].get("cascade_step", "") if rows else "",
        "n_patients": len(rows),
        "n_responders": len(responder_scores),
        "n_nonresponders": len(nonresponder_scores),
        "auc_response_high": roc_auc(labels, scores),
        "spearman_response_high": spearman(labels, scores),
        "response_mean": mean(responder_scores),
        "nonresponse_mean": mean(nonresponder_scores),
        "response_minus_nonresponse": mean(responder_scores) - mean(nonresponder_scores),
        "mean_probability": mean(scores),
    }


def reproduce_cscc_checkpoint_compartment(
    *,
    scores_csv: str | Path,
    metrics_csv: str | Path | None = None,
) -> dict[str, Any]:
    released_rows = read_csv_rows(scores_csv)
    recomputed_rows = cscc_recomputed_rows(released_rows)
    metrics = cscc_metrics(recomputed_rows)
    drift: list[dict[str, Any]] = []
    for released, recomputed in zip(released_rows, recomputed_rows, strict=True):
        row_id = released.get("patient_id")
        for key in (
            CSCC_SCORE_COL,
            "nonresponse_probability",
            "universal_axis_geomean_response_probability",
            "universal_axis_softmin_response_probability",
        ):
            diff = compare_metric_rows(recomputed, released, keys=(key,))
            drift.extend({"row_id": row_id, **item} for item in diff)
    if metrics_csv is not None:
        expected = read_csv_rows(metrics_csv)[0]
        drift.extend(
            compare_metric_rows(
                metrics,
                expected,
                keys=(
                    "axis_variant",
                    "mode",
                    "cascade_step",
                    "n_patients",
                    "n_responders",
                    "n_nonresponders",
                    "auc_response_high",
                    "spearman_response_high",
                    "response_mean",
                    "nonresponse_mean",
                    "response_minus_nonresponse",
                    "mean_probability",
                ),
            )
        )
    return {
        "artifact": str(scores_csv),
        "model_score_artifact": str(scores_csv),
        "score_col": CSCC_SCORE_COL,
        "metrics": metrics,
        "drift": drift,
    }


def _outcome_label(row: Mapping[str, Any]) -> int:
    return int(str(row.get("clinical_outcome") or "").strip().lower() == "partial response")


def crc_module_patient_steps(
    module_vectors: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in module_vectors:
        grouped[(str(row.get("cascade_step")), str(row.get("source_patient_id")))].append(row)

    out: list[dict[str, Any]] = []
    for (step, patient_id), rows in sorted(
        grouped.items(),
        key=lambda item: (int(item[0][0]), item[0][1]),
    ):
        first = rows[0]
        out.append(
            {
                "cascade_step": int(step),
                "source_patient_id": patient_id,
                "clinical_outcome": first.get("clinical_outcome", ""),
                "regimen": first.get("regimen", ""),
                "n_genes": 41,
                "n_modules": len({str(row.get("module")) for row in rows}),
                "module_mean_cosine": module_mean_cosine(rows),
            }
        )
    return out


def crc_module_step_summary(patient_steps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in patient_steps:
        grouped[int(finite_float(row.get("cascade_step")))].append(row)

    out: list[dict[str, Any]] = []
    for step in sorted(grouped):
        rows = grouped[step]
        scores = [finite_float(row.get("module_mean_cosine")) for row in rows]
        pr_scores = [
            finite_float(row.get("module_mean_cosine")) for row in rows if _outcome_label(row) == 1
        ]
        sd_scores = [
            finite_float(row.get("module_mean_cosine")) for row in rows if _outcome_label(row) == 0
        ]
        highest = max(rows, key=lambda row: finite_float(row.get("module_mean_cosine")))
        out.append(
            {
                "cascade_step": step,
                "n_patients": len(rows),
                "mean": mean(scores),
                "median": median(scores),
                "q25": quantile(scores, 0.25),
                "q75": quantile(scores, 0.75),
                "pr_mean": mean(pr_scores),
                "sd_mean": mean(sd_scores),
                "pr_high_auc": roc_auc(
                    [_outcome_label(row) for row in rows],
                    [finite_float(row.get("module_mean_cosine")) for row in rows],
                ),
                "highest_patient": highest.get("source_patient_id"),
                "highest_outcome": highest.get("clinical_outcome"),
                "highest_value": finite_float(highest.get("module_mean_cosine")),
            }
        )
    return out


def reproduce_crc_module_mean_cosine(
    *,
    module_vectors_csv: str | Path,
    patient_steps_csv: str | Path | None = None,
    step_summary_csv: str | Path | None = None,
) -> dict[str, Any]:
    module_vectors = read_csv_rows(module_vectors_csv)
    patient_steps = crc_module_patient_steps(module_vectors)
    step_summary = crc_module_step_summary(patient_steps)
    drift: list[dict[str, Any]] = []
    if patient_steps_csv is not None:
        expected_patient_steps = {
            (str(row["cascade_step"]), str(row["source_patient_id"])): row
            for row in read_csv_rows(patient_steps_csv)
        }
        for row in patient_steps:
            key = (str(row["cascade_step"]), str(row["source_patient_id"]))
            expected = expected_patient_steps.get(key)
            if not expected:
                drift.append(
                    {"row_id": "::".join(key), "field": "patient_step", "actual": "present"}
                )
                continue
            for item in compare_metric_rows(
                row,
                expected,
                keys=(
                    "cascade_step",
                    "source_patient_id",
                    "clinical_outcome",
                    "regimen",
                    "n_genes",
                    "n_modules",
                    "module_mean_cosine",
                ),
            ):
                drift.append({"row_id": "::".join(key), **item})
    if step_summary_csv is not None:
        expected_summary = {
            str(row["cascade_step"]): row for row in read_csv_rows(step_summary_csv)
        }
        for row in step_summary:
            expected = expected_summary.get(str(row["cascade_step"]))
            if not expected:
                drift.append(
                    {
                        "cascade_step": row["cascade_step"],
                        "field": "cascade_step",
                        "actual": "present",
                    }
                )
                continue
            for item in compare_metric_rows(
                row,
                expected,
                keys=(
                    "cascade_step",
                    "n_patients",
                    "mean",
                    "median",
                    "q25",
                    "q75",
                    "pr_mean",
                    "sd_mean",
                    "pr_high_auc",
                    "highest_patient",
                    "highest_outcome",
                    "highest_value",
                ),
            ):
                drift.append({"cascade_step": row["cascade_step"], **item})
    best = max(step_summary, key=lambda row: finite_float(row.get("mean"))) if step_summary else {}
    return {
        "artifact": str(module_vectors_csv),
        "readout_artifact": str(module_vectors_csv),
        "metric": "module_mean_cosine",
        "best_step": best,
        "step_summary": step_summary,
        "drift": drift,
    }


def raise_if_drift(report: Mapping[str, Any]) -> None:
    drift = report.get("drift") or []
    if drift:
        raise SystemExit(f"recomputed metrics differ from checked-in artifacts: {drift}")
