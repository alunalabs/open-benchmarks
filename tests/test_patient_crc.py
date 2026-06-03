from __future__ import annotations

from spatial_benchmarks.patient_crc import (
    filter_crc_rows,
    patient_metrics,
    score_crc_moa_delta_probability,
    score_crc_moa_tailored_adapter,
)


def test_crc_filter_and_metrics() -> None:
    rows = [
        {"cohort": "CRC", "success_label": 1, "relative_response_probability": 0.8},
        {"cohort": "CRC", "success_label": 0, "relative_response_probability": 0.2},
        {"cohort": "cSCC", "success_label": 1, "relative_response_probability": 0.9},
    ]
    assert len(filter_crc_rows(rows)) == 2
    metrics = patient_metrics(rows)
    assert metrics["n"] == 2
    assert metrics["auc_response_high"] == 1.0
    assert metrics["fixed_threshold_balanced_accuracy"] == 1.0


def test_crc_moa_delta_probability() -> None:
    row = {
        "cohort": "CRC",
        "predicted_mapk_kras_delta": -0.1,
        "predicted_egfr_engagement_delta": -0.1,
        "predicted_proliferation_delta": -0.1,
        "predicted_emt_invasion_delta": -0.1,
        "predicted_hypoxia_stress_delta": -0.1,
        "predicted_apoptosis_response_delta": 0.1,
    }
    scored = score_crc_moa_delta_probability(row)
    assert scored["response_probability_mean"] > 0.5
    assert scored["predicted_responder_p_ge_0p5"] is True


def test_crc_moa_tailored_adapter() -> None:
    row = {
        "cohort": "CRC",
        "module_target_kras_risk_delta": -0.1,
        "module_target_egfr_risk_delta": -0.1,
        "module_failed_cytostasis_risk_delta": -0.1,
        "module_escape_refuge_risk_delta": -0.1,
        "module_weak_kill_conversion_risk_delta": -0.1,
    }
    scored = score_crc_moa_tailored_adapter(row)
    assert scored["ct_hetero_conversion_fraction_positive"] == 1.0
    assert scored["response_probability_module_calibrated"] > 0.5

