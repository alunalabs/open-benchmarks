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

    assert summary["patient_level"]["universal_patient_response_axes_clinical_rows"] == 23
    assert summary["patient_level"]["crc_patient_clinical_rows"] == 11
    assert summary["patient_level"]["crc_moa_tailored_rank_score_rows"] == 11
    assert summary["patient_level"]["crc_moa_tailored_default_score_column"] == (
        "response_score_rank_calibrated"
    )
    assert round(summary["patient_level"]["crc_moa_tailored_default_auc_response_high"], 3) == 0.800
    assert (
        round(summary["patient_level"]["crc_moa_tailored_default_fixed_0p5_balanced_accuracy"], 3)
        == 0.733
    )
    assert summary["patient_level"]["crc_on_treatment_p_response_patient_rows"] == 11
    assert (
        round(summary["patient_level"]["crc_on_treatment_p_response_absolute_state_auc"], 3)
        == 0.867
    )
    assert (
        round(
            summary["patient_level"][
                "crc_on_treatment_p_response_absolute_state_balanced_accuracy"
            ],
            3,
        )
        == 0.917
    )
    assert round(summary["patient_level"]["crc_on_treatment_p_response_delta_auc"], 3) == 0.600
    assert (
        round(summary["patient_level"]["crc_on_treatment_signed_risk_adapter_auc_sd_high"], 3)
        == 0.900
    )

    cohort = summary["cohort_level"]
    assert cohort["cohort_benchmark_strict44_clinical_rows"] == 44
    assert cohort["gaia_44_strict_orr_model_score_rows"] == 44
    assert cohort["gaia_default_score_column"] == "gaia_predicted_orr_pct"
    assert round(cohort["gaia_pearson"], 3) == 0.650
    assert round(cohort["gaia_spearman"], 3) == 0.594
    assert round(cohort["gaia_mae_orr_pct"], 1) == 10.2
    assert round(cohort["atlas_fixed_k8_pearson"], 3) == 0.465
    assert round(cohort["atlas_fixed_k8_spearman"], 3) == 0.460
    assert cohort["depmap_covered_rows"] == 40
    assert round(cohort["depmap_primary_pearson"], 3) == -0.014
    assert round(cohort["depmap_primary_spearman"], 3) == -0.044


def test_public_clinical_rows_are_metadata_only() -> None:
    patient_rows = read_csv(
        "patient-level-bench/clinical_rows/"
        "universal_patient_response_axes_clinical_rows_20260525.csv"
    )
    cohort_rows = read_csv(
        "cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv"
    )

    patient_forbidden = {"relative_response_probability", "nonresponse_probability", "risk_score"}
    cohort_forbidden = {
        "default_score",
        "gaia_predicted_orr_pct",
        "patient_probabilities",
        "relative_response_probability_mean",
    }

    assert len(cohort_rows) == 44
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


def test_crc_observed_on_treatment_p_response_readout() -> None:
    base = "patient-level-bench/observed_readouts/crc_on_treatment_p_response_20260604"
    rows = read_csv(f"{base}/crc_on_treatment_p_response_patient_scores.csv")
    metrics = read_csv(f"{base}/crc_on_treatment_p_response_readout_metrics.csv")
    modules = read_csv(f"{base}/crc_on_treatment_p2_p12_module_reference.csv")
    summary = json.loads((ROOT / base / "crc_on_treatment_p_response_summary.json").read_text())
    manifest = json.loads((ROOT / base / "MANIFEST.json").read_text())

    assert len(rows) == 11
    assert len(metrics) == 3
    assert len(modules) == 5
    assert "README.md" in manifest
    assert "predicted_delta_moa_gate_response_probability" not in rows[0]
    assert summary["boundary"]["uses_measured_on_treatment_state"] is True
    assert summary["boundary"]["is_pretreatment_prediction_benchmark"] is False
    assert summary["boundary"]["is_public_crc_rank_score"] is False

    by_readout = {row["readout"]: row for row in metrics}
    absolute = by_readout["observed_absolute_state_p_response"]
    delta = by_readout["observed_delta_p_response"]
    risk = by_readout["observed_signed_moa_risk_adapter"]

    assert absolute["direction"] == "PR high"
    assert round(float(absolute["auc"]), 3) == 0.867
    assert round(float(absolute["balanced_accuracy"]), 3) == 0.917
    assert round(float(absolute["pr_mean"]), 4) == 0.6128
    assert round(float(absolute["sd_mean"]), 4) == 0.3545

    assert round(float(delta["auc"]), 3) == 0.600
    assert round(float(delta["balanced_accuracy"]), 3) == 0.533
    assert risk["direction"] == "SD high"
    assert round(float(risk["auc"]), 3) == 0.900

    by_patient = {row["source_patient_id"]: row for row in rows}
    assert round(float(by_patient["P2"]["observed_absolute_state_p_response"]), 4) == 0.6180
    assert round(float(by_patient["P12"]["observed_absolute_state_p_response"]), 4) == 0.3428
    assert by_patient["P2"]["absolute_state_correct_at_0p5"] == "True"
    assert by_patient["P12"]["absolute_state_correct_at_0p5"] == "True"
    assert by_patient["P11"]["absolute_state_correct_at_0p5"] == "False"


def test_gaia_public_model_score_rows() -> None:
    rows = read_csv("cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv")
    clinical_rows = read_csv(
        "cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv"
    )
    metrics = read_csv("cohort-level-bench/model_scores/gaia/gaia_metrics.csv")
    summary = json.loads(
        (
            ROOT / "cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json"
        ).read_text()
    )
    manifest = json.loads(
        (ROOT / "cohort-level-bench/model_scores/gaia/MANIFEST.json").read_text()
    )

    assert len(rows) == 44
    assert len(clinical_rows) == 44
    assert all(row["default_score_column"] == "gaia_predicted_orr_pct" for row in rows)
    assert all(row["default_score"] == row["gaia_predicted_orr_pct"] for row in rows)
    assert all(row["expected_orr_pct"] == row["gaia_predicted_orr_pct"] for row in rows)
    assert all(row["label_scope"] == "strict_observed_orr_pair" for row in rows)
    assert all("gaia_predicted_orr_pct" not in row for row in clinical_rows)

    metric = metrics[0]
    assert metric["score_col"] == "gaia_predicted_orr_pct"
    assert metric["n_orr"] == "44"
    assert round(float(metric["pearson"]), 3) == 0.650
    assert round(float(metric["spearman"]), 3) == 0.594
    assert round(float(metric["mae_orr_pct"]), 1) == 10.2

    assert summary["target_rows_with_finite_orr_and_prediction"] == 44
    assert summary["active_default_score_column"] == "gaia_predicted_orr_pct"
    assert round(summary["active_default_metrics"]["pearson"], 3) == 0.650
    assert round(summary["active_default_metrics"]["spearman"], 3) == 0.594
    assert sorted(manifest) == [
        "README.md",
        "gaia_44_strict_orr_model_scores.csv",
        "gaia_by_disease_metrics.csv",
        "gaia_metrics.csv",
        "gaia_model_score_summary.json",
    ]


def test_baseline_metrics_use_44_row_target() -> None:
    atlas_summary = json.loads(
        (ROOT / "cohort-level-bench/baseline/results/atlas_orr_summary.json").read_text()
    )
    depmap_summary = json.loads(
        (ROOT / "cohort-level-bench/baseline/results/depmap_orr_summary.json").read_text()
    )
    atlas_metrics = read_csv("cohort-level-bench/baseline/results/atlas_orr_metrics.csv")
    depmap_features = read_csv("cohort-level-bench/baseline/results/depmap_orr_features.csv")

    assert atlas_summary["target_eval_rows"] == 44
    assert depmap_summary["target_eval_rows"] == 44
    assert len(depmap_features) == 44

    assert round(atlas_summary["primary_baseline"]["pearson"], 3) == 0.465
    assert round(atlas_summary["primary_baseline"]["spearman"], 3) == 0.460
    assert depmap_summary["depmap_covered_rows"] == 40
    assert round(depmap_summary["primary_baseline"]["pearson"], 3) == -0.014
    assert round(depmap_summary["primary_baseline"]["spearman"], 3) == -0.044

    assert atlas_metrics[0]["score_col"] == "atlas_mono_disease_therapy_shrink_k8"
    assert atlas_metrics[0]["n_rows"] == "44"
    assert len(atlas_metrics) == 1
    assert "gaia_predicted_orr_pct" not in depmap_features[0]
    assert "default_score" not in depmap_features[0]


def test_methodology_doc_covers_public_release() -> None:
    methodology = (ROOT / "docs/methodology.md").read_text(encoding="utf-8")

    required_phrases = [
        "Patient-Level CRC Benchmark",
        "Patient-Level CRC Observed On-Treatment p_response Readout",
        "Cohort-Level Gaia ORR Benchmark",
        "Atlas Fixed `k=8` ORR Baseline",
        "DepMap ORR Baseline",
        "Pearson r",
        "Spearman rho",
        "This release excludes BioBench",
    ]
    for phrase in required_phrases:
        assert phrase in methodology
