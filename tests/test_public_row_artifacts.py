from __future__ import annotations

import ast
import csv
import json
import math
from pathlib import Path

from spatial_benchmarks.metrics import module_mean_cosine
from spatial_benchmarks.reproduce import (
    reproduce_atlas_orr_predictions,
    reproduce_crc_module_mean_cosine,
    reproduce_crc_moa_tailored_rank_score,
    reproduce_cscc_checkpoint_compartment,
    reproduce_depmap_orr_features,
    reproduce_gaia_cohort_orr,
)


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
    assert summary["patient_level"]["cscc_checkpoint_compartment_patient_score_rows"] == 12
    assert summary["patient_level"]["cscc_checkpoint_compartment_default_score_column"] == (
        "relative_response_probability"
    )
    assert (
        round(summary["patient_level"]["cscc_checkpoint_compartment_auc_response_high"], 3)
        == 0.944
    )
    assert (
        round(summary["patient_level"]["cscc_checkpoint_compartment_spearman_response_high"], 3)
        == 0.772
    )
    assert summary["patient_level"]["crc_module_mean_cosine_patient_step_rows"] == 88
    assert summary["patient_level"]["crc_module_mean_cosine_module_vector_rows"] == 528
    assert summary["patient_level"]["crc_module_mean_cosine_best_step"] == 4
    assert round(summary["patient_level"]["crc_module_mean_cosine_step1_mean"], 3) == -0.106
    assert round(summary["patient_level"]["crc_module_mean_cosine_step4_mean"], 3) == 0.304
    assert round(summary["patient_level"]["crc_module_mean_cosine_step4_pr_mean"], 3) == 0.522
    assert round(summary["patient_level"]["crc_module_mean_cosine_step4_sd_mean"], 3) == 0.123
    assert summary["patient_level"]["crc_prior_control_patient_score_rows"] == 33
    assert summary["patient_level"]["crc_prior_control_patients_per_control"] == 11
    assert summary["patient_level"]["crc_prior_control_primary_surface"] == (
        "predicted_delta_moa_gate_response_probability"
    )
    assert round(summary["patient_level"]["crc_prior_control_gene_shuffled_auc"], 3) == 0.567
    assert (
        round(summary["patient_level"]["crc_prior_control_gene_shuffled_mean_abs_movement"], 3)
        == 0.297
    )
    assert round(summary["patient_level"]["crc_prior_control_hard_donor_auc"], 3) == 0.633
    assert (
        round(summary["patient_level"]["crc_prior_control_hard_donor_mean_abs_movement"], 3)
        == 0.014
    )

    cohort = summary["cohort_level"]
    assert cohort["cohort_benchmark_strict44_clinical_rows"] == 44
    assert cohort["gaia_44_strict_orr_model_score_rows"] == 44
    assert cohort["atlas_orr_prediction_rows"] == 44
    assert cohort["gaia_default_score_column"] == "gaia_predicted_orr_pct"
    assert round(cohort["gaia_pearson"], 3) == 0.650
    assert round(cohort["gaia_spearman"], 3) == 0.594
    assert round(cohort["gaia_mae_orr_pct"], 1) == 10.2
    assert round(cohort["atlas_fixed_k8_pearson"], 3) == 0.465
    assert round(cohort["atlas_fixed_k8_spearman"], 3) == 0.460
    assert cohort["depmap_covered_rows"] == 40
    assert round(cohort["depmap_primary_pearson"], 3) == -0.014
    assert round(cohort["depmap_primary_spearman"], 3) == -0.044
    assert cohort["cohort_robustness_hard_donor_control_rows"] == 69
    assert cohort["cohort_robustness_gene_shuffle_control_rows"] == 300
    assert cohort["cohort_robustness_primary_variant"] == "signed_mag_tail_soft_primary"
    assert round(cohort["cohort_robustness_real_wd_spearman"], 3) == 0.439
    assert round(cohort["cohort_robustness_hard_donor_null_p95"], 3) == 0.232
    assert round(cohort["cohort_robustness_gene_shuffle_null_p95"], 3) == 0.371


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
    assert "reproduce_crc_moa_tailored_rank_score.py" in manifest
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


def test_cscc_checkpoint_compartment_score_rows() -> None:
    base = "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604"
    rows = read_csv(f"{base}/cscc_checkpoint_compartment_patient_scores_20260604.csv")
    metrics = read_csv(f"{base}/cscc_checkpoint_compartment_metrics_20260604.csv")
    summary = json.loads((ROOT / base / "cscc_checkpoint_compartment_summary.json").read_text())
    manifest = json.loads((ROOT / base / "MANIFEST.json").read_text())

    forbidden = {
        "universal_axis_product_response_probability",
        "axis_available_count",
        "drug_norm",
        "dataset",
        "proxy_policy",
    }

    assert len(rows) == 12
    assert forbidden.isdisjoint(rows[0])
    assert len(metrics) == 1
    assert "cscc_checkpoint_compartment_patient_scores_20260604.csv" in manifest
    assert "cscc_checkpoint_compartment_metrics_20260604.csv" in manifest
    assert "reproduce_cscc_checkpoint_compartment.py" in manifest
    assert summary["default_score_column"] == "relative_response_probability"
    assert summary["default_risk_score_column"] == "nonresponse_probability"
    assert summary["n_responders"] == 6
    assert summary["n_nonresponders"] == 6
    assert summary["axis_source_map"] == {
        "coverage_support": "immune_primary_cells",
        "engagement_support": "immune_primary_cells",
        "escape_refuge_control": "immune_primary_cells",
        "resistant_tail_control": "epithelial",
        "response_conversion_support": "immune_primary_cells",
    }
    assert summary["boundary"]["uses_patient_labels_for_default_probability_assignment"] is False
    assert summary["boundary"]["uses_z_scores"] is False
    assert summary["boundary"]["uses_drug_prior"] is False
    assert summary["boundary"]["is_absolute_clinical_orr_probability"] is False
    assert round(summary["default_metrics"]["auc_response_high"], 3) == 0.944
    assert round(summary["default_metrics"]["spearman_response_high"], 3) == 0.772

    for row in rows:
        assert row["axis_contract_version"] == "cscc_compartment_specific_checkpoint_axes_v1"
        assert row["axis_variant"] == "checkpoint_compartment_default_v1"
        assert row["mode"] == "visible_persistent"
        assert row["cascade_step"] == "4"
        assert row["engagement_support_source_scope"] == "immune_primary_cells"
        assert row["response_conversion_support_source_scope"] == "immune_primary_cells"
        assert row["coverage_support_source_scope"] == "immune_primary_cells"
        assert row["resistant_tail_control_source_scope"] == "epithelial"
        assert row["escape_refuge_control_source_scope"] == "immune_primary_cells"
        expected = (
            float(row["engagement_support"])
            * float(row["response_conversion_support"])
            * float(row["coverage_support"])
            * float(row["resistant_tail_control"])
            * float(row["escape_refuge_control"])
        )
        assert abs(float(row["relative_response_probability"]) - expected) < 1e-12

    metric = metrics[0]
    assert metric["n_patients"] == "12"
    assert round(float(metric["auc_response_high"]), 3) == 0.944
    assert round(float(metric["spearman_response_high"]), 3) == 0.772


def test_crc_module_mean_cosine_readout() -> None:
    base = "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604"
    step_summary = read_csv(f"{base}/crc_module_mean_cosine_step_summary.csv")
    patient_steps = read_csv(f"{base}/crc_module_mean_cosine_patient_steps.csv")
    module_vectors = read_csv(f"{base}/crc_module_mean_cosine_module_vectors.csv")
    summary = json.loads((ROOT / base / "crc_module_mean_cosine_summary.json").read_text())
    manifest = json.loads((ROOT / base / "MANIFEST.json").read_text())

    assert len(step_summary) == 8
    assert len(patient_steps) == 88
    assert len(module_vectors) == 528
    assert "README.md" in manifest
    assert "crc_module_mean_cosine_step_summary.csv" in manifest
    assert "reproduce_crc_module_mean_cosine.py" in manifest
    assert summary["metric"] == "module_mean_cosine"
    assert summary["boundary"]["uses_measured_on_treatment_delta"] is True
    assert summary["boundary"]["is_pretreatment_prediction_benchmark"] is False
    assert summary["boundary"]["is_public_crc_rank_score"] is False
    assert summary["boundary"]["is_public_crc_cosine_readout"] is True

    by_step = {int(row["cascade_step"]): row for row in step_summary}
    assert round(float(by_step[1]["mean"]), 3) == -0.106
    assert round(float(by_step[4]["mean"]), 3) == 0.304
    assert round(float(by_step[4]["pr_mean"]), 3) == 0.522
    assert round(float(by_step[4]["sd_mean"]), 3) == 0.123
    assert by_step[4]["highest_patient"] == "P5"

    p5_step4_vectors = [
        row
        for row in module_vectors
        if row["source_patient_id"] == "P5" and row["cascade_step"] == "4"
    ]
    p5_step4_score = next(
        row
        for row in patient_steps
        if row["source_patient_id"] == "P5" and row["cascade_step"] == "4"
    )
    assert round(module_mean_cosine(p5_step4_vectors), 3) == round(
        float(p5_step4_score["module_mean_cosine"]),
        3,
    )


def test_crc_prior_control_baseline_artifacts() -> None:
    base = "patient-level-bench/baseline/crc_prior_controls_20260525"
    rows = read_csv(f"{base}/crc_patient_prior_control_patient_scores.csv")
    metrics = read_csv(f"{base}/crc_patient_prior_control_metrics.csv")
    movement = read_csv(f"{base}/crc_patient_prior_control_vs_baseline.csv")
    manifest = json.loads((ROOT / base / "MANIFEST.json").read_text())

    forbidden = {"run_id", "model_label", "checkpoint_path"}
    assert len(rows) == 33
    assert len(metrics) == 30
    assert len(movement) == 10
    assert forbidden.isdisjoint(rows[0])
    assert forbidden.isdisjoint(metrics[0])
    assert set(row["control"] for row in rows) == {"baseline", "gene_shuffled", "hard_donor"}
    assert all(row["model_family"] == "gaia" for row in metrics)
    assert "crc_patient_prior_control_patient_scores.csv" in manifest

    surface = "predicted_delta_moa_gate_response_probability"
    by_metric = {(row["control"], row["surface"]): row for row in metrics}
    by_movement = {(row["control"], row["surface"]): row for row in movement}

    assert round(float(by_metric[("baseline", surface)]["auc_response_high"]), 3) == 0.633
    assert round(float(by_metric[("gene_shuffled", surface)]["auc_response_high"]), 3) == 0.567
    assert round(float(by_metric[("hard_donor", surface)]["auc_response_high"]), 3) == 0.633
    assert (
        round(float(by_movement[("gene_shuffled", surface)]["mean_abs_movement"]), 3)
        == 0.297
    )
    assert (
        round(float(by_movement[("hard_donor", surface)]["mean_abs_movement"]), 3)
        == 0.014
    )


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
        "reproduce_gaia_metrics.py",
    ]


def test_baseline_metrics_use_44_row_target() -> None:
    atlas_summary = json.loads(
        (ROOT / "cohort-level-bench/baseline/results/atlas_orr_summary.json").read_text()
    )
    depmap_summary = json.loads(
        (ROOT / "cohort-level-bench/baseline/results/depmap_orr_summary.json").read_text()
    )
    atlas_metrics = read_csv("cohort-level-bench/baseline/results/atlas_orr_metrics.csv")
    atlas_predictions = read_csv("cohort-level-bench/baseline/results/atlas_orr_predictions.csv")
    depmap_features = read_csv("cohort-level-bench/baseline/results/depmap_orr_features.csv")

    assert atlas_summary["target_eval_rows"] == 44
    assert depmap_summary["target_eval_rows"] == 44
    assert len(atlas_predictions) == 44
    assert len(depmap_features) == 44

    assert round(atlas_summary["primary_baseline"]["pearson"], 3) == 0.465
    assert round(atlas_summary["primary_baseline"]["spearman"], 3) == 0.460
    assert depmap_summary["depmap_covered_rows"] == 40
    assert round(depmap_summary["primary_baseline"]["pearson"], 3) == -0.014
    assert round(depmap_summary["primary_baseline"]["spearman"], 3) == -0.044

    assert atlas_metrics[0]["score_col"] == "atlas_mono_disease_therapy_shrink_k8"
    assert atlas_metrics[0]["n_rows"] == "44"
    assert len(atlas_metrics) == 1
    assert "gaia_predicted_orr_pct" not in atlas_predictions[0]
    assert "default_score" not in atlas_predictions[0]
    assert "gaia_predicted_orr_pct" not in depmap_features[0]
    assert "default_score" not in depmap_features[0]


def test_cohort_robustness_control_artifacts() -> None:
    base = "cohort-level-bench/baseline/robustness_controls_20260525"
    hard_controls = read_csv(f"{base}/heterogeneity_hard_donor_controls.csv")
    hard_summary = read_csv(f"{base}/heterogeneity_hard_donor_random_summary.csv")
    gene_controls = read_csv(f"{base}/heterogeneity_gene_shuffle_controls.csv")
    gene_summary = read_csv(f"{base}/heterogeneity_gene_shuffle_random_summary.csv")
    manifest = json.loads((ROOT / base / "MANIFEST.json").read_text())

    assert len(hard_controls) == 69
    assert len(hard_summary) == 3
    assert len(gene_controls) == 300
    assert len(gene_summary) == 3
    assert "heterogeneity_gene_shuffle_controls.csv" in manifest
    assert "heterogeneity_hard_donor_controls.csv" in manifest

    variant = "signed_mag_tail_soft_primary"
    primary_hard = next(row for row in hard_summary if row["variant"] == variant)
    primary_gene = next(row for row in gene_summary if row["variant"] == variant)

    assert round(float(primary_hard["real_within_disease_spearman"]), 3) == 0.439
    assert round(float(primary_hard["control_wd_spearman_p95"]), 3) == 0.232
    assert float(primary_hard["empirical_p_wd_spearman_ge_real"]) == 0.0
    assert round(float(primary_gene["control_wd_spearman_p95"]), 3) == 0.371
    assert float(primary_gene["empirical_p_wd_spearman_ge_real"]) == 0.01


def test_reproduction_scripts_have_no_metric_drift() -> None:
    gaia = reproduce_gaia_cohort_orr(
        scores_csv=(
            ROOT / "cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv"
        ),
        metrics_csv=ROOT / "cohort-level-bench/model_scores/gaia/gaia_metrics.csv",
        by_disease_csv=ROOT / "cohort-level-bench/model_scores/gaia/gaia_by_disease_metrics.csv",
    )
    atlas = reproduce_atlas_orr_predictions(
        predictions_csv=ROOT / "cohort-level-bench/baseline/results/atlas_orr_predictions.csv",
        metrics_csv=ROOT / "cohort-level-bench/baseline/results/atlas_orr_metrics.csv",
    )
    depmap = reproduce_depmap_orr_features(
        features_csv=ROOT / "cohort-level-bench/baseline/results/depmap_orr_features.csv",
        metrics_csv=ROOT / "cohort-level-bench/baseline/results/depmap_orr_metrics.csv",
    )
    crc = reproduce_crc_moa_tailored_rank_score(
        scores_csv=(
            ROOT
            / "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
            "crc_patient_moa_tailored_rank_scores_20260525.csv"
        ),
        metrics_csv=(
            ROOT
            / "patient-level-bench/model_scores/crc_moa_tailored_20260525/"
            "crc_patient_moa_tailored_metrics_20260525.csv"
        ),
    )
    cscc = reproduce_cscc_checkpoint_compartment(
        scores_csv=(
            ROOT
            / "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/"
            "cscc_checkpoint_compartment_patient_scores_20260604.csv"
        ),
        metrics_csv=(
            ROOT
            / "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/"
            "cscc_checkpoint_compartment_metrics_20260604.csv"
        ),
    )
    cosine = reproduce_crc_module_mean_cosine(
        module_vectors_csv=(
            ROOT
            / "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/"
            "crc_module_mean_cosine_module_vectors.csv"
        ),
        patient_steps_csv=(
            ROOT
            / "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/"
            "crc_module_mean_cosine_patient_steps.csv"
        ),
        step_summary_csv=(
            ROOT
            / "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/"
            "crc_module_mean_cosine_step_summary.csv"
        ),
    )

    for report in (gaia, atlas, depmap, crc, cscc, cosine):
        assert report["drift"] == []


def test_reproducibility_notebooks_are_valid_json() -> None:
    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    assert [notebook.name for notebook in notebooks] == [
        "01_cohort_benchmarks.ipynb",
        "02_patient_benchmarks.ipynb",
    ]
    for notebook in notebooks:
        payload = json.loads(notebook.read_text(encoding="utf-8"))
        assert payload["nbformat"] == 4
        assert payload["cells"]
        source = "".join("".join(cell.get("source", [])) for cell in payload["cells"])
        assert "open-benchmarks" in source
        assert "artifacts/notebook_figures" in source
        for cell_index, cell in enumerate(payload["cells"]):
            if cell.get("cell_type") == "code":
                code = "".join(cell.get("source", []))
                ast.parse(code, filename=f"{notebook.name}:cell{cell_index}")


def test_methodology_doc_covers_public_release() -> None:
    methodology = (ROOT / "docs/methodology.md").read_text(encoding="utf-8")

    required_phrases = [
        "Patient-Level CRC Benchmark",
        "Patient-Level cSCC Checkpoint Benchmark",
        "Patient-Level CRC Module Mean Cosine Readout",
        "Patient-Level CRC Prior-Control Baselines",
        "Cohort-Level Gaia ORR Benchmark",
        "Atlas Fixed `k=8` ORR Baseline",
        "DepMap ORR Baseline",
        "Cohort-Level Hard-Donor and Gene-Swap Controls",
        "reproduce_release_scores.py",
        "Pearson r",
        "Spearman rho",
        "This release excludes BioBench",
    ]
    for phrase in required_phrases:
        assert phrase in methodology
