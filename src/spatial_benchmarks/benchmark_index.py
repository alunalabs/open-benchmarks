"""Build benchmark-level summary indexes from released artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_csv_rows, write_csv_rows


SUMMARY_FIELDS = (
    "benchmark_level",
    "benchmark_id",
    "result_type",
    "metric",
    "direction",
    "score_col",
    "n_rows",
    "metric_value",
    "control_family",
    "control_p95",
    "empirical_p_ge_real",
    "artifact",
    "description",
)


def _row(
    *,
    benchmark_level: str,
    benchmark_id: str,
    result_type: str,
    metric: str,
    direction: str,
    score_col: str,
    n_rows: Any,
    metric_value: Any,
    artifact: str,
    description: str,
    control_family: str = "",
    control_p95: Any = "",
    empirical_p_ge_real: Any = "",
) -> dict[str, Any]:
    return {
        "benchmark_level": benchmark_level,
        "benchmark_id": benchmark_id,
        "result_type": result_type,
        "metric": metric,
        "direction": direction,
        "score_col": score_col,
        "n_rows": n_rows,
        "metric_value": metric_value,
        "control_family": control_family,
        "control_p95": control_p95,
        "empirical_p_ge_real": empirical_p_ge_real,
        "artifact": artifact,
        "description": description,
    }


def _first(path: Path) -> dict[str, Any]:
    rows = read_csv_rows(path)
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows[0]


def build_cohort_benchmark_summary(root: str | Path) -> list[dict[str, Any]]:
    """Return cohort benchmark rows, including matched formula-control rows."""

    root = Path(root)
    rows: list[dict[str, Any]] = []

    gaia_metrics_path = "cohort-level-bench/model_scores/gaia/gaia_metrics.csv"
    gaia = _first(root / gaia_metrics_path)
    for metric, direction in (
        ("pearson", "higher_is_better"),
        ("spearman", "higher_is_better"),
        ("mae_orr_pct", "lower_is_better"),
        ("auc_above_disease_median", "higher_is_better"),
    ):
        rows.append(
            _row(
                benchmark_level="cohort",
                benchmark_id="gaia_44_strict_orr",
                result_type="model_score",
                metric=metric,
                direction=direction,
                score_col=gaia["score_col"],
                n_rows=gaia.get("n_orr") or gaia.get("n_rows"),
                metric_value=gaia[metric],
                artifact=gaia_metrics_path,
                description="Gaia strict 44-row ORR benchmark.",
            )
        )

    atlas_metrics_path = "cohort-level-bench/baseline/results/atlas_orr_metrics.csv"
    atlas = _first(root / atlas_metrics_path)
    for metric, direction in (
        ("pearson", "higher_is_better"),
        ("spearman", "higher_is_better"),
        ("mae_orr_pct", "lower_is_better"),
        ("auc_above_disease_median", "higher_is_better"),
    ):
        rows.append(
            _row(
                benchmark_level="cohort",
                benchmark_id="atlas_fixed_k8_orr_prior",
                result_type="baseline",
                metric=metric,
                direction=direction,
                score_col=atlas["score_col"],
                n_rows=atlas["n_rows"],
                metric_value=atlas[metric],
                artifact=atlas_metrics_path,
                description="Exact-drug-excluded Atlas historical ORR prior.",
            )
        )

    depmap_metrics_path = "cohort-level-bench/baseline/results/depmap_orr_metrics.csv"
    depmap = _first(root / depmap_metrics_path)
    for metric in ("pearson", "spearman", "auc_above_disease_median"):
        rows.append(
            _row(
                benchmark_level="cohort",
                benchmark_id="depmap_lineage_sensitivity",
                result_type="baseline",
                metric=metric,
                direction="higher_is_better",
                score_col=depmap["score_col"],
                n_rows=depmap["n_rows"],
                metric_value=depmap[metric],
                artifact=depmap_metrics_path,
                description="DepMap matched-lineage drug sensitivity baseline.",
            )
        )

    control_summary_path = (
        "cohort-level-bench/baseline/formula_controls_20260605/"
        "cohort_formula_control_summary.csv"
    )
    for control in read_csv_rows(root / control_summary_path):
        rows.append(
            _row(
                benchmark_level="cohort",
                benchmark_id=control["benchmark_name"],
                result_type="formula_control",
                metric=control["metric"],
                direction="higher_is_better",
                score_col="gaia_predicted_orr_pct",
                n_rows=44,
                metric_value=control["real_value"],
                control_family=control["control_family"],
                control_p95=control["control_p95"],
                empirical_p_ge_real=control["empirical_p_ge_real"],
                artifact=control_summary_path,
                description=(
                    "Released Gaia score kept fixed; ORR-label alignment is shuffled and "
                    "the same cohort metric is recomputed."
                ),
            )
        )

    return rows


def build_patient_benchmark_summary(root: str | Path) -> list[dict[str, Any]]:
    """Return patient benchmark rows, including matched formula-control rows."""

    root = Path(root)
    rows: list[dict[str, Any]] = []

    crc_metrics_path = (
        "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
        "crc_patient_moa_tailored_metrics_20260525.csv"
    )
    crc = _first(root / crc_metrics_path)
    for metric in ("auc_response_high", "fixed_0p5_balanced_accuracy", "pr_minus_sd_mean"):
        rows.append(
            _row(
                benchmark_level="patient",
                benchmark_id="crc_moa_tailored_rank",
                result_type="model_score",
                metric=metric,
                direction="higher_is_better",
                score_col=crc["score_col"],
                n_rows=crc["n"],
                metric_value=crc[metric],
                artifact=crc_metrics_path,
                description="CRC pretreatment MOA-tailored rank-score benchmark.",
            )
        )

    cscc_metrics_path = (
        "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/"
        "cscc_checkpoint_compartment_metrics_20260604.csv"
    )
    cscc = _first(root / cscc_metrics_path)
    for metric in ("auc_response_high", "spearman_response_high", "response_minus_nonresponse"):
        rows.append(
            _row(
                benchmark_level="patient",
                benchmark_id="cscc_checkpoint_compartment",
                result_type="model_score",
                metric=metric,
                direction="higher_is_better",
                score_col="relative_response_probability",
                n_rows=cscc["n_patients"],
                metric_value=cscc[metric],
                artifact=cscc_metrics_path,
                description="cSCC checkpoint compartment relative response benchmark.",
            )
        )

    cosine_summary_path = (
        "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/"
        "crc_module_mean_cosine_step_summary.csv"
    )
    cosine_by_step = {row["cascade_step"]: row for row in read_csv_rows(root / cosine_summary_path)}
    cosine_metrics = (
        ("step1_mean", cosine_by_step["1"], "mean"),
        ("step4_mean", cosine_by_step["4"], "mean"),
        ("step4_pr_mean", cosine_by_step["4"], "pr_mean"),
        ("step4_sd_mean", cosine_by_step["4"], "sd_mean"),
    )
    for metric, source, source_metric in cosine_metrics:
        rows.append(
            _row(
                benchmark_level="patient",
                benchmark_id="crc_module_mean_cosine",
                result_type="observed_readout",
                metric=metric,
                direction="higher_is_better",
                score_col="module_mean_cosine",
                n_rows=source["n_patients"],
                metric_value=source[source_metric],
                artifact=cosine_summary_path,
                description=(
                    "Observed on-treatment module-mean cosine readout, not a pretreatment "
                    "prediction benchmark."
                ),
            )
        )

    control_summary_path = (
        "patient-level-bench/baseline/formula_controls_20260605/"
        "patient_formula_control_summary.csv"
    )
    score_by_benchmark = {
        "crc_moa_tailored_rank": "response_score_rank_calibrated",
        "cscc_checkpoint_compartment": "relative_response_probability",
    }
    n_by_benchmark = {
        "crc_moa_tailored_rank": 11,
        "cscc_checkpoint_compartment": 12,
    }
    for control in read_csv_rows(root / control_summary_path):
        rows.append(
            _row(
                benchmark_level="patient",
                benchmark_id=control["benchmark_name"],
                result_type="formula_control",
                metric=control["metric"],
                direction="higher_is_better",
                score_col=score_by_benchmark[control["benchmark_name"]],
                n_rows=n_by_benchmark[control["benchmark_name"]],
                metric_value=control["real_value"],
                control_family=control["control_family"],
                control_p95=control["control_p95"],
                empirical_p_ge_real=control["empirical_p_ge_real"],
                artifact=control_summary_path,
                description=(
                    "Released patient formula is recomputed after label or full "
                    "axis/module-vector shuffling."
                ),
            )
        )

    return rows


def write_benchmark_summary_artifacts(root: str | Path) -> dict[str, str]:
    """Write cohort, patient, and combined benchmark summary CSV files."""

    root = Path(root)
    cohort_rows = build_cohort_benchmark_summary(root)
    patient_rows = build_patient_benchmark_summary(root)
    all_rows = cohort_rows + patient_rows

    cohort_path = root / "cohort-level-bench/benchmark_summary.csv"
    patient_path = root / "patient-level-bench/benchmark_summary.csv"
    combined_path = root / "benchmark_summary.csv"
    write_csv_rows(cohort_path, cohort_rows, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(patient_path, patient_rows, fieldnames=SUMMARY_FIELDS)
    write_csv_rows(combined_path, all_rows, fieldnames=SUMMARY_FIELDS)
    return {
        "cohort_summary": str(cohort_path),
        "patient_summary": str(patient_path),
        "combined_summary": str(combined_path),
    }
