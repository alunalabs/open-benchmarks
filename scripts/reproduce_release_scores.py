#!/usr/bin/env python3
"""Run all no-external-data release score reproduction checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.reproduce import (  # noqa: E402
    raise_if_drift,
    reproduce_atlas_orr_predictions,
    reproduce_crc_module_mean_cosine,
    reproduce_crc_moa_tailored_rank_score,
    reproduce_cscc_checkpoint_compartment,
    reproduce_depmap_orr_features,
    reproduce_gaia_cohort_orr,
)


def main() -> int:
    cohort_gaia = REPO_ROOT / "cohort-level-bench/model_scores/gaia"
    cohort_baseline = REPO_ROOT / "cohort-level-bench/baseline/results"
    crc = REPO_ROOT / "patient-level-bench/model_scores/crc_moa_tailored_20260525"
    cscc = REPO_ROOT / "patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604"
    cosine = REPO_ROOT / "patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604"

    reports = {
        "cohort_gaia_orr": reproduce_gaia_cohort_orr(
            scores_csv=cohort_gaia / "gaia_44_strict_orr_model_scores.csv",
            metrics_csv=cohort_gaia / "gaia_metrics.csv",
            by_disease_csv=cohort_gaia / "gaia_by_disease_metrics.csv",
        ),
        "atlas_orr_baseline": reproduce_atlas_orr_predictions(
            predictions_csv=cohort_baseline / "atlas_orr_predictions.csv",
            metrics_csv=cohort_baseline / "atlas_orr_metrics.csv",
        ),
        "depmap_orr_baseline": reproduce_depmap_orr_features(
            features_csv=cohort_baseline / "depmap_orr_features.csv",
            metrics_csv=cohort_baseline / "depmap_orr_metrics.csv",
        ),
        "crc_moa_tailored_rank_score": reproduce_crc_moa_tailored_rank_score(
            scores_csv=crc / "crc_patient_moa_tailored_rank_scores_20260525.csv",
            metrics_csv=crc / "crc_patient_moa_tailored_metrics_20260525.csv",
        ),
        "cscc_checkpoint_compartment": reproduce_cscc_checkpoint_compartment(
            scores_csv=cscc / "cscc_checkpoint_compartment_patient_scores_20260604.csv",
            metrics_csv=cscc / "cscc_checkpoint_compartment_metrics_20260604.csv",
        ),
        "crc_module_mean_cosine": reproduce_crc_module_mean_cosine(
            module_vectors_csv=cosine / "crc_module_mean_cosine_module_vectors.csv",
            patient_steps_csv=cosine / "crc_module_mean_cosine_patient_steps.csv",
            step_summary_csv=cosine / "crc_module_mean_cosine_step_summary.csv",
        ),
    }
    for report in reports.values():
        raise_if_drift(report)
    print(json.dumps(reports, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
