from __future__ import annotations

from spatial_benchmarks.cohort_v2 import aggregate_patient_probabilities, summarize_predictions


def test_summarize_predictions() -> None:
    rows = [
        {"disease": "crc", "drug": "A", "orr_pct": 40, "apoptosis_prevalence_basic_score": 0.8},
        {"disease": "crc", "drug": "B", "orr_pct": 10, "apoptosis_prevalence_basic_score": 0.2},
        {"disease": "crc", "drug": "C", "orr_pct": 20, "apoptosis_prevalence_basic_score": 0.4},
        {"disease": "pdac", "drug": "A", "orr_pct": 30, "apoptosis_prevalence_basic_score": 0.7},
        {"disease": "pdac", "drug": "B", "orr_pct": 5, "apoptosis_prevalence_basic_score": 0.1},
        {"disease": "pdac", "drug": "C", "orr_pct": 10, "apoptosis_prevalence_basic_score": 0.3},
    ]
    summary = summarize_predictions(rows)
    global_row = summary[0]
    assert global_row["n_orr"] == 6
    assert global_row["pearson"] > 0.9
    assert global_row["auc_success_above_disease_median"] == 1.0


def test_aggregate_patient_probabilities() -> None:
    rows = [
        {
            "base_cohort_id": "crc::drug_a",
            "patient_id": "P1",
            "cohort": "crc",
            "drug": "Drug A",
            "relative_response_probability": 0.5,
        },
        {
            "base_cohort_id": "crc::drug_a",
            "patient_id": "P2",
            "cohort": "crc",
            "drug": "Drug A",
            "relative_response_probability": 0.5,
        },
    ]
    agg = aggregate_patient_probabilities(rows)
    assert agg[0]["patient_count"] == 2
    assert agg[0]["relative_response_probability_mean"] == 0.5
    assert agg[0]["prob_orr_ge_50pct"] == 0.75

