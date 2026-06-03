from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_public_row_artifact_counts() -> None:
    summary = json.loads((ROOT / "docs/row_artifacts_summary.json").read_text())

    assert summary["biobench_legacy_v2"]["clean_rows"] == 630
    assert summary["biobench_legacy_v2"]["unfiltered_rows"] == 805
    assert summary["patient_level"]["universal_patient_response_axes_clinical_rows"] == 23
    assert summary["patient_level"]["crc_patient_clinical_rows"] == 11
    assert summary["patient_level"]["crc_moa_tailored_rank_score_rows"] == 11
    assert (
        summary["patient_level"]["crc_moa_tailored_default_score_column"]
        == "response_score_rank_calibrated"
    )
    assert round(summary["patient_level"]["crc_moa_tailored_default_auc_response_high"], 3) == 0.800
    assert (
        round(summary["patient_level"]["crc_moa_tailored_default_fixed_0p5_balanced_accuracy"], 3)
        == 0.733
    )
    assert summary["cohort_level"]["cohort_benchmark_v2_clinical_rows"] == 69
    assert summary["cohort_level"]["cohort_benchmark_v2_orr_labeled_clinical_rows"] == 66
    assert summary["cohort_level"]["cohort_benchmark_v2_eval_clinical_rows"] == 63
    assert summary["cohort_level"]["gaia_63_model_score_rows"] == 63
    assert summary["cohort_level"]["gaia_best_63_model_score_rows"] == 63
    assert summary["cohort_level"]["gaia_candidate_score_columns"] == 9
    assert (
        summary["cohort_level"]["gaia_best_packaged_pearson_score_column"]
        == "prob_apoptosis_prevalence_orr_gt_20pct"
    )
    assert round(summary["cohort_level"]["gaia_best_packaged_pearson"], 3) == 0.650
    assert (
        summary["cohort_level"]["gaia_universal_softmin_score_column"]
        == "universal_axis_softmin_response_probability_mean"
    )
    assert round(summary["cohort_level"]["gaia_universal_softmin_pearson"], 3) == 0.646


def test_public_clinical_rows_are_metadata_only() -> None:
    patient_rows = read_csv(
        "patient-level-bench/clinical_rows/"
        "universal_patient_response_axes_clinical_rows_20260525.csv"
    )
    cohort_rows = read_csv(
        "cohort-level-bench/clinical_rows/cohort_benchmark_v2_eval_clinical_rows.csv"
    )

    patient_forbidden = {"relative_response_probability", "nonresponse_probability", "risk_score"}
    cohort_forbidden = {
        "default_score",
        "patient_probabilities",
        "relative_response_probability_mean",
    }

    assert patient_rows
    assert cohort_rows
    assert patient_forbidden.isdisjoint(patient_rows[0])
    assert cohort_forbidden.isdisjoint(cohort_rows[0])


def test_crc_patient_moa_tailored_rank_score_rows() -> None:
    rows = read_csv(
        "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
        "crc_patient_moa_tailored_rank_scores_20260525.csv"
    )
    metrics = read_csv(
        "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
        "crc_patient_moa_tailored_metrics_20260525.csv"
    )
    summary = json.loads(
        (
            ROOT
            / "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
            "crc_patient_moa_tailored_summary.json"
        ).read_text()
    )
    manifest = json.loads(
        (
            ROOT
            / "patient-level-bench/model_scores/crc_moa_tailored_20260525/MANIFEST.json"
        ).read_text()
    )

    forbidden = {
        "response_probability_uncalibrated",
        "response_probability_module_calibrated",
        "nonresponse_risk_module_calibrated",
        "response_probability_isotonic_apparent",
        "nonresponse_risk_isotonic_apparent",
        "predicted_responder_module_p_ge_0p5",
        "predicted_responder_isotonic_ge_0p5",
    }
    support_cols = [
        "kras_mapk_support",
        "egfr_support",
        "cytostasis_support",
        "escape_control_support",
        "kill_conversion_support",
    ]

    assert len(rows) == 11
    assert forbidden.isdisjoint(rows[0])
    assert summary["default_score_column"] == "response_score_rank_calibrated"
    assert summary["n_responders"] == 5
    assert summary["n_nonresponders"] == 6
    assert summary["uses_patient_labels_for_default_probability_assignment"] is False
    assert summary["uses_observed_orr_calibration"] is False
    assert summary["uses_z_scores"] is False
    assert summary["uses_drug_prior"] is False
    assert "crc_patient_moa_tailored_rank_scores_20260525.csv" in manifest
    assert "crc_patient_moa_tailored_probabilities_20260525.csv" not in manifest
    assert round(summary["default_metrics"]["auc_response_high"], 3) == 0.800
    assert round(summary["default_metrics"]["fixed_0p5_balanced_accuracy"], 3) == 0.733

    assert len(metrics) == 1
    default_metric = metrics[0]
    assert default_metric["score_col"] == "response_score_rank_calibrated"
    assert default_metric["label_use"] == "none"
    assert default_metric["n"] == "11"

    intermediate_by_patient: dict[str, float] = {}
    for row in rows:
        supports = [float(row[col]) for col in support_cols]
        coverage = sum(value > 0.0 for value in supports) / len(supports)
        mean_support = sum(supports) / len(supports)
        p10_support = float(row["ct_hetero_conversion_p10"])
        effective_coverage = min(1.0, coverage / 0.80)

        intermediate = min(
            _sigmoid(effective_coverage, center=0.90, scale=0.05),
            _sigmoid(mean_support, center=0.0, scale=0.015),
            _sigmoid(p10_support, center=-0.02, scale=0.015),
        )

        assert abs(float(row["ct_hetero_conversion_fraction_positive"]) - coverage) < 1e-12
        assert abs(float(row["ct_hetero_conversion_mean"]) - mean_support) < 1e-12
        assert abs(float(row["module_coverage_effective"]) - effective_coverage) < 1e-12
        intermediate_by_patient[row["source_patient_id"]] = intermediate

    ranked_patients = sorted(intermediate_by_patient, key=intermediate_by_patient.get)
    expected_rank = {
        patient_id: (rank + 1) / len(ranked_patients)
        for rank, patient_id in enumerate(ranked_patients)
    }
    for row in rows:
        rank_score = float(row["response_score_rank_calibrated"])
        assert abs(rank_score - expected_rank[row["source_patient_id"]]) < 1e-12
        assert (rank_score >= 0.5) == (row["predicted_responder_rank_ge_0p5"] == "True")


def _sigmoid(value: float, *, center: float, scale: float) -> float:
    z = max(-40.0, min(40.0, (value - center) / scale))
    return 1.0 / (1.0 + math.exp(-z))


def test_atlas_support_reasonableness_audit_counts() -> None:
    summary = json.loads(
        (
            ROOT
            / "cohort-level-bench/baseline/results/"
            "atlas_orr_support_reasonableness_summary.json"
        ).read_text()
    )

    assert summary["target_eval_rows"] == 63
    assert summary["verified_cleaned_support_rows"] == 191
    assert summary["strict_release_support_rows"] == 189
    assert summary["strict_release_support_ncts"] == 114
    assert summary["exact_drug_leakage_hits"] == 0
    assert summary["all_support_rows_biomarker_unselected"] is True
    assert summary["all_support_rows_non_combination"] is True
    assert summary["support_reasonableness_classes"]["exclude_in_strict_orr_sensitivity"] == 2
    assert (
        summary["support_reasonableness_classes"]["optional_exclude_for_confirmed_orr_only"]
        == 1
    )


def test_atlas_strict_release_metrics() -> None:
    summary = json.loads(
        (ROOT / "cohort-level-bench/baseline/results/atlas_orr_summary.json").read_text()
    )
    lodo_summary = json.loads(
        (
            ROOT / "cohort-level-bench/baseline/results/atlas_orr_lodo_summary.json"
        ).read_text()
    )
    metrics = read_csv("cohort-level-bench/baseline/results/atlas_orr_metrics.csv")

    assert summary["target_rows"] == 63
    assert summary["removed_support_rows"] == 13
    assert summary["remaining_audited_support_rows"] == 189
    assert summary["excluded_raw_atlas_row_indices"] == [
        582,
        1519,
        2448,
        2568,
        3862,
        4782,
        9268,
        10228,
        11729,
        12033,
        14965,
        14966,
        17451,
    ]
    assert round(summary["primary_metrics"]["pearson"], 3) == 0.409
    assert round(summary["primary_metrics"]["spearman"], 3) == 0.464
    assert round(summary["lodo_spearman_sensitivity"]["pearson"], 3) == 0.292
    assert round(summary["lodo_spearman_sensitivity"]["spearman"], 3) == 0.419
    assert lodo_summary["excluded_raw_atlas_row_indices"] == summary[
        "excluded_raw_atlas_row_indices"
    ]

    assert metrics[0]["run_id"] == "strict_release_fixed_k8"
    assert metrics[0]["remaining_audited_support_rows"] == "189"
    assert metrics[1]["run_id"] == "strict_release_lodo_spearman"


def test_gaia_public_model_score_rows() -> None:
    rows = read_csv("cohort-level-bench/model_scores/gaia/gaia_63_model_scores.csv")
    best_rows = read_csv(
        "cohort-level-bench/model_scores/gaia/gaia_best_63_model_scores.csv"
    )
    metrics = read_csv("cohort-level-bench/model_scores/gaia/gaia_metrics.csv")
    summary = json.loads(
        (
            ROOT / "cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json"
        ).read_text()
    )

    assert len(rows) == 63
    assert len(best_rows) == 63
    assert all(row["default_score_column"] == "apoptosis_prevalence_no_prior_score" for row in rows)
    assert all(row["default_score"] == row["apoptosis_prevalence_no_prior_score"] for row in rows)
    assert all(
        row["best_packaged_pearson_score_column"]
        == "prob_apoptosis_prevalence_orr_gt_20pct"
        for row in best_rows
    )
    assert all(
        row["best_packaged_spearman_score_column"]
        == "universal_axis_geomean_response_probability_mean"
        for row in best_rows
    )
    assert all(
        row["universal_softmin_score_column"]
        == "universal_axis_softmin_response_probability_mean"
        for row in best_rows
    )
    assert "universal_softmin_response_probability_mean" in best_rows[0]
    assert summary["target_rows_with_finite_orr_and_default_score"] == 63
    assert summary["active_default_score_column"] == "apoptosis_prevalence_no_prior_score"
    assert round(summary["active_default_metrics"]["pearson"], 3) == 0.511
    assert round(summary["active_default_metrics"]["spearman"], 3) == 0.520
    assert (
        summary["best_packaged_63_row_score_by_pearson"]["score_col"]
        == "prob_apoptosis_prevalence_orr_gt_20pct"
    )
    assert round(summary["best_packaged_63_row_score_by_pearson"]["pearson"], 3) == 0.650
    assert round(summary["best_packaged_63_row_score_by_pearson"]["spearman"], 3) == 0.564
    assert (
        summary["best_packaged_63_row_score_by_spearman"]["score_col"]
        == "universal_axis_geomean_response_probability_mean"
    )
    assert round(summary["best_packaged_63_row_score_by_spearman"]["pearson"], 3) == 0.614
    assert round(summary["best_packaged_63_row_score_by_spearman"]["spearman"], 3) == 0.580
    assert (
        summary["universal_softmin_63_row_score"]["score_col"]
        == "universal_axis_softmin_response_probability_mean"
    )
    assert round(summary["universal_softmin_63_row_score"]["pearson"], 3) == 0.646
    assert round(summary["universal_softmin_63_row_score"]["spearman"], 3) == 0.519
    assert (
        summary["universal_softmin_calculation"]["per_patient_formula"]
        == "min(final axis support values)"
    )
    assert (
        summary["exploratory_label_aware_threshold_sweep_best_by_pearson"]["status"]
        == "label_aware_sensitivity_not_public_release_score"
    )
    assert (
        round(summary["exploratory_label_aware_threshold_sweep_best_by_pearson"]["pearson"], 3)
        == 0.659
    )
    assert len(summary["candidate_score_columns_in_row_file"]) == 9

    active_metric = next(
        row for row in metrics if row["score_col"] == "apoptosis_prevalence_no_prior_score"
    )
    best_metric = next(
        row for row in metrics if row["score_col"] == "prob_apoptosis_prevalence_orr_gt_20pct"
    )
    softmin_metric = next(
        row for row in metrics if row["score_col"] == "universal_axis_softmin_response_probability_mean"
    )
    assert active_metric["n_orr"] == "63"
    assert round(float(active_metric["pearson"]), 3) == 0.511
    assert round(float(active_metric["spearman"]), 3) == 0.520
    assert best_metric["n_orr"] == "63"
    assert round(float(best_metric["pearson"]), 3) == 0.650
    assert round(float(best_metric["spearman"]), 3) == 0.564
    assert softmin_metric["n_orr"] == "63"
    assert round(float(softmin_metric["pearson"]), 3) == 0.646
    assert round(float(softmin_metric["spearman"]), 3) == 0.519


def test_gaia_public_audit_logs_are_sanitized() -> None:
    audit_dir = ROOT / "cohort-level-bench/model_scores/gaia/audit_logs"
    nominal_rows = read_csv(
        "cohort-level-bench/model_scores/gaia/audit_logs/"
        "active_default_input_comparability_nominal_sample_source_split_sanitized.csv"
    )
    required_rows = read_csv(
        "cohort-level-bench/model_scores/gaia/audit_logs/"
        "active_default_input_comparability_required_inputs.csv"
    )

    assert len(nominal_rows) > 0
    assert len(required_rows) == 4
    assert "patient_id" not in nominal_rows[0]
    assert (audit_dir / "active_default_input_comparability_report_excerpt.md").exists()
    assert not (ROOT / "cohort-level-bench/model_scores/gaia/patient_probabilities.csv").exists()
