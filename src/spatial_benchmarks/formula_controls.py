"""Formula-preserving public benchmark controls."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .io import read_csv_rows, write_csv_rows, write_json
from .metrics import mean, quantile
from .reproduce import (
    COHORT_GAIA_SCORE_COL,
    CRC_RANK_SCORE_COL,
    CRC_SUPPORT_COLS,
    CSCC_AXIS_COLS,
    CSCC_SCORE_COL,
    cohort_global_metric,
    crc_rank_metrics,
    crc_rank_rows,
    cscc_metrics,
    cscc_recomputed_rows,
)


CONTROL_SEED = 20260605
CONTROL_ITERATIONS = 1000
COHORT_CONTROL_METRICS = (
    "pearson",
    "spearman",
    "auc_above_disease_median",
)
CRC_CONTROL_METRICS = (
    "auc_response_high",
    "fixed_0p5_balanced_accuracy",
    "pr_minus_sd_mean",
)
CSCC_CONTROL_METRICS = (
    "auc_response_high",
    "spearman_response_high",
    "response_minus_nonresponse",
)


def _metric_summary(
    *,
    benchmark_level: str,
    benchmark_name: str,
    control_family: str,
    metric: str,
    real_value: float,
    control_values: Sequence[float],
) -> dict[str, Any]:
    clean = [value for value in control_values if math.isfinite(value)]
    return {
        "benchmark_level": benchmark_level,
        "benchmark_name": benchmark_name,
        "control_family": control_family,
        "metric": metric,
        "real_value": real_value,
        "control_n": len(clean),
        "control_mean": mean(clean),
        "control_p05": quantile(clean, 0.05),
        "control_median": quantile(clean, 0.50),
        "control_p95": quantile(clean, 0.95),
        "control_max": max(clean) if clean else math.nan,
        "empirical_p_ge_real": (
            sum(value >= real_value for value in clean) / len(clean)
            if clean and math.isfinite(real_value)
            else math.nan
        ),
    }


def _shuffle_rows_globally(
    rows: Sequence[Mapping[str, Any]],
    *,
    column: str,
    rng: random.Random,
) -> list[dict[str, Any]]:
    values = [row.get(column, "") for row in rows]
    rng.shuffle(values)
    return [{**dict(row), column: value} for row, value in zip(rows, values, strict=True)]


def _shuffle_rows_within_group(
    rows: Sequence[Mapping[str, Any]],
    *,
    column: str,
    group_column: str,
    rng: random.Random,
) -> list[dict[str, Any]]:
    grouped_values: dict[str, list[Any]] = {}
    for row in rows:
        grouped_values.setdefault(str(row.get(group_column, "")), []).append(row.get(column, ""))
    for values in grouped_values.values():
        rng.shuffle(values)

    offsets = {group: 0 for group in grouped_values}
    out = []
    for row in rows:
        group = str(row.get(group_column, ""))
        offset = offsets[group]
        offsets[group] += 1
        out.append({**dict(row), column: grouped_values[group][offset]})
    return out


def build_cohort_formula_controls(
    rows: Sequence[Mapping[str, Any]],
    *,
    n_iter: int = CONTROL_ITERATIONS,
    seed: int = CONTROL_SEED,
    score_col: str = COHORT_GAIA_SCORE_COL,
) -> dict[str, list[dict[str, Any]]]:
    """Controls for the released cohort score table and metric path.

    These controls do not claim to be hard-donor or gene-shuffle controls. The
    public 44-row release contains the final cohort score, not per-patient axis
    values, so the exact public control is a score/label-alignment control over
    the released score and the released ORR labels.
    """

    rng = random.Random(seed)
    real = cohort_global_metric(rows, score_col=score_col, is_orr_scale=True)
    metric_rows: list[dict[str, Any]] = []

    control_specs = (
        ("label_shuffle_global", "observed_orr_pct", None),
        ("label_shuffle_within_disease", "observed_orr_pct", "cohort"),
    )
    for control_family, column, group_column in control_specs:
        for iteration in range(n_iter):
            shuffled = (
                _shuffle_rows_within_group(rows, column=column, group_column=group_column, rng=rng)
                if group_column
                else _shuffle_rows_globally(rows, column=column, rng=rng)
            )
            metrics = cohort_global_metric(shuffled, score_col=score_col, is_orr_scale=True)
            metric_rows.append(
                {
                    "benchmark_level": "cohort",
                    "benchmark_name": "gaia_44_strict_orr",
                    "control_family": control_family,
                    "control_iter": iteration,
                    "score_col": score_col,
                    "n_rows": metrics["n_rows"],
                    "pearson": metrics["pearson"],
                    "spearman": metrics["spearman"],
                    "auc_above_disease_median": metrics["auc_above_disease_median"],
                }
            )

    summary_rows = []
    for control_family, _, _ in control_specs:
        family_rows = [row for row in metric_rows if row["control_family"] == control_family]
        for metric in COHORT_CONTROL_METRICS:
            summary_rows.append(
                _metric_summary(
                    benchmark_level="cohort",
                    benchmark_name="gaia_44_strict_orr",
                    control_family=control_family,
                    metric=metric,
                    real_value=float(real[metric]),
                    control_values=[float(row[metric]) for row in family_rows],
                )
            )

    return {
        "real_metrics": [
            {
                "benchmark_level": "cohort",
                "benchmark_name": "gaia_44_strict_orr",
                "score_col": score_col,
                "n_rows": real["n_rows"],
                "pearson": real["pearson"],
                "spearman": real["spearman"],
                "auc_above_disease_median": real["auc_above_disease_median"],
            }
        ],
        "control_metrics": metric_rows,
        "control_summary": summary_rows,
    }


def _shuffle_vectors(
    rows: Sequence[Mapping[str, Any]],
    *,
    columns: Sequence[str],
    rng: random.Random,
) -> list[dict[str, Any]]:
    vectors = [{column: row.get(column, "") for column in columns} for row in rows]
    rng.shuffle(vectors)
    return [{**dict(row), **vector} for row, vector in zip(rows, vectors, strict=True)]


def _crc_label_shuffle_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    rng: random.Random,
) -> dict[str, Any]:
    recomputed = crc_rank_rows(rows)
    labels = [row.get("observed_responder", "") for row in recomputed]
    rng.shuffle(labels)
    controlled = [
        {**dict(row), "observed_responder": label}
        for row, label in zip(recomputed, labels, strict=True)
    ]
    return crc_rank_metrics(controlled)


def _crc_support_shuffle_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    rng: random.Random,
) -> dict[str, Any]:
    controlled = _shuffle_vectors(rows, columns=CRC_SUPPORT_COLS, rng=rng)
    return crc_rank_metrics(crc_rank_rows(controlled))


def _cscc_label_shuffle_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    rng: random.Random,
) -> dict[str, Any]:
    recomputed = cscc_recomputed_rows(rows)
    labels = [row.get("response_label", "") for row in recomputed]
    rng.shuffle(labels)
    controlled = [
        {**dict(row), "response_label": label} for row, label in zip(recomputed, labels, strict=True)
    ]
    return cscc_metrics(controlled)


def _cscc_axis_shuffle_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    rng: random.Random,
) -> dict[str, Any]:
    controlled = _shuffle_vectors(rows, columns=CSCC_AXIS_COLS, rng=rng)
    return cscc_metrics(cscc_recomputed_rows(controlled))


def build_patient_formula_controls(
    *,
    crc_rows: Sequence[Mapping[str, Any]],
    cscc_rows: Sequence[Mapping[str, Any]],
    n_iter: int = CONTROL_ITERATIONS,
    seed: int = CONTROL_SEED,
) -> dict[str, list[dict[str, Any]]]:
    """Formula controls for released CRC and cSCC patient benchmark tables."""

    rng = random.Random(seed)
    crc_real = crc_rank_metrics(crc_rank_rows(crc_rows))
    cscc_real = cscc_metrics(cscc_recomputed_rows(cscc_rows))

    control_fns = (
        ("crc_moa_tailored_rank", "crc_label_shuffle", _crc_label_shuffle_metrics),
        ("crc_moa_tailored_rank", "crc_support_vector_shuffle", _crc_support_shuffle_metrics),
        ("cscc_checkpoint_compartment", "cscc_label_shuffle", _cscc_label_shuffle_metrics),
        ("cscc_checkpoint_compartment", "cscc_axis_vector_shuffle", _cscc_axis_shuffle_metrics),
    )
    source_rows = {
        "crc_moa_tailored_rank": crc_rows,
        "cscc_checkpoint_compartment": cscc_rows,
    }
    real_by_benchmark = {
        "crc_moa_tailored_rank": crc_real,
        "cscc_checkpoint_compartment": cscc_real,
    }
    metrics_by_benchmark = {
        "crc_moa_tailored_rank": CRC_CONTROL_METRICS,
        "cscc_checkpoint_compartment": CSCC_CONTROL_METRICS,
    }
    score_col_by_benchmark = {
        "crc_moa_tailored_rank": CRC_RANK_SCORE_COL,
        "cscc_checkpoint_compartment": CSCC_SCORE_COL,
    }

    metric_rows: list[dict[str, Any]] = []
    for benchmark_name, control_family, control_fn in control_fns:
        for iteration in range(n_iter):
            metrics = control_fn(source_rows[benchmark_name], rng=rng)
            row = {
                "benchmark_level": "patient",
                "benchmark_name": benchmark_name,
                "control_family": control_family,
                "control_iter": iteration,
                "score_col": score_col_by_benchmark[benchmark_name],
            }
            for metric in metrics_by_benchmark[benchmark_name]:
                row[metric] = metrics[metric]
            row["n"] = metrics.get("n", metrics.get("n_patients", ""))
            metric_rows.append(row)

    summary_rows = []
    for benchmark_name, control_family, _ in control_fns:
        family_rows = [
            row
            for row in metric_rows
            if row["benchmark_name"] == benchmark_name and row["control_family"] == control_family
        ]
        for metric in metrics_by_benchmark[benchmark_name]:
            summary_rows.append(
                _metric_summary(
                    benchmark_level="patient",
                    benchmark_name=benchmark_name,
                    control_family=control_family,
                    metric=metric,
                    real_value=float(real_by_benchmark[benchmark_name][metric]),
                    control_values=[float(row[metric]) for row in family_rows],
                )
            )

    return {
        "real_metrics": [
            {
                "benchmark_level": "patient",
                "benchmark_name": "crc_moa_tailored_rank",
                "score_col": CRC_RANK_SCORE_COL,
                "n": crc_real["n"],
                "auc_response_high": crc_real["auc_response_high"],
                "fixed_0p5_balanced_accuracy": crc_real["fixed_0p5_balanced_accuracy"],
                "pr_minus_sd_mean": crc_real["pr_minus_sd_mean"],
            },
            {
                "benchmark_level": "patient",
                "benchmark_name": "cscc_checkpoint_compartment",
                "score_col": CSCC_SCORE_COL,
                "n": cscc_real["n_patients"],
                "auc_response_high": cscc_real["auc_response_high"],
                "spearman_response_high": cscc_real["spearman_response_high"],
                "response_minus_nonresponse": cscc_real["response_minus_nonresponse"],
            },
        ],
        "control_metrics": metric_rows,
        "control_summary": summary_rows,
    }


def write_formula_control_artifacts(
    *,
    root: str | Path,
    n_iter: int = CONTROL_ITERATIONS,
    seed: int = CONTROL_SEED,
) -> dict[str, Any]:
    """Write deterministic formula-control artifacts into the release tree."""

    root = Path(root)
    cohort_dir = root / "cohort-level-bench/baseline/formula_controls_20260605"
    patient_dir = root / "patient-level-bench/baseline/formula_controls_20260605"

    cohort = build_cohort_formula_controls(
        read_csv_rows(
            root / "cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv"
        ),
        n_iter=n_iter,
        seed=seed,
    )
    patient = build_patient_formula_controls(
        crc_rows=read_csv_rows(
            root
            / "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
            "crc_patient_moa_tailored_rank_scores_20260525.csv"
        ),
        cscc_rows=read_csv_rows(
            root
            / "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/"
            "cscc_checkpoint_compartment_patient_scores_20260604.csv"
        ),
        n_iter=n_iter,
        seed=seed,
    )

    write_csv_rows(cohort_dir / "cohort_formula_control_real_metrics.csv", cohort["real_metrics"])
    write_csv_rows(
        cohort_dir / "cohort_formula_control_metrics.csv",
        cohort["control_metrics"],
    )
    write_csv_rows(
        cohort_dir / "cohort_formula_control_summary.csv",
        cohort["control_summary"],
    )
    write_json(
        cohort_dir / "MANIFEST.json",
        [
            "README.md",
            "MANIFEST.json",
            "cohort_formula_control_real_metrics.csv",
            "cohort_formula_control_metrics.csv",
            "cohort_formula_control_summary.csv",
        ],
    )

    write_csv_rows(patient_dir / "patient_formula_control_real_metrics.csv", patient["real_metrics"])
    write_csv_rows(
        patient_dir / "patient_formula_control_metrics.csv",
        patient["control_metrics"],
    )
    write_csv_rows(
        patient_dir / "patient_formula_control_summary.csv",
        patient["control_summary"],
    )
    write_json(
        patient_dir / "MANIFEST.json",
        [
            "README.md",
            "MANIFEST.json",
            "patient_formula_control_real_metrics.csv",
            "patient_formula_control_metrics.csv",
            "patient_formula_control_summary.csv",
        ],
    )

    return {
        "cohort_dir": str(cohort_dir),
        "patient_dir": str(patient_dir),
        "cohort": cohort,
        "patient": patient,
    }
