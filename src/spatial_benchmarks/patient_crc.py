"""CRC-only patient benchmark scoring utilities."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .metrics import (
    balanced_accuracy,
    best_balanced_accuracy,
    finite_float,
    geometric_mean,
    quantile,
    roc_auc,
    sigmoid,
)


CRC_COHORT_LABEL = "CRC"
DEFAULT_PATIENT_SCORE_COLUMN = "relative_response_probability"
DEFAULT_PATIENT_LABEL_COLUMN = "success_label"
DEFAULT_RESPONSE_THRESHOLD = 0.5


@dataclass(frozen=True)
class RiskTerm:
    risk_reason: str
    risk_delta_column: str
    family: str
    description: str


RISK_TERMS: tuple[RiskTerm, ...] = (
    RiskTerm(
        risk_reason="target_pathway_failure",
        risk_delta_column="module_target_pathway_risk_delta",
        family="pathway_moa_support",
        description="MAPK/KRAS plus EGFR engagement moves in the wrong direction or is insufficiently suppressed.",
    ),
    RiskTerm(
        risk_reason="failed_cytostasis",
        risk_delta_column="module_failed_cytostasis_risk_delta",
        family="response_conversion",
        description="Proliferation rises or is not adequately suppressed.",
    ),
    RiskTerm(
        risk_reason="escape_refuge",
        risk_delta_column="module_escape_refuge_risk_delta",
        family="escape_resistance",
        description="EMT/invasion plus hypoxia/stress refuge increases.",
    ),
    RiskTerm(
        risk_reason="weak_kill_conversion",
        risk_delta_column="module_weak_kill_conversion_risk_delta",
        family="response_conversion",
        description="Apoptosis/death conversion fails to increase enough.",
    ),
)

SUPPORT_COLUMNS = {
    "kras_mapk_support": "module_target_kras_risk_delta",
    "egfr_support": "module_target_egfr_risk_delta",
    "cytostasis_support": "module_failed_cytostasis_risk_delta",
    "escape_control_support": "module_escape_refuge_risk_delta",
    "kill_conversion_support": "module_weak_kill_conversion_risk_delta",
}


def is_crc_row(row: Mapping[str, Any]) -> bool:
    cohort = str(row.get("cohort", row.get("benchmark_slice", ""))).strip().upper()
    benchmark_id = str(row.get("benchmark_id", "")).strip().lower()
    return cohort == CRC_COHORT_LABEL or benchmark_id.startswith("crc_")


def filter_crc_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if is_crc_row(row)]


def add_reference_relative_patient_scores(
    rows: Sequence[Mapping[str, Any]],
    *,
    cohort_col: str = "cohort",
    warning_col: str = "warning_points",
) -> list[dict[str, Any]]:
    """Map warning pressure to a within-cohort response probability.

    This mirrors the production universal patient response-axis transform:
    raw response score is `-warning_points`, then each cohort is z-normalized
    without using labels and mapped through a logistic transform.
    """

    out = [dict(row) for row in rows]
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(out):
        groups.setdefault(str(row.get(cohort_col, "")), []).append(idx)

    for group_name, indices in groups.items():
        raw_scores = [-finite_float(out[idx].get(warning_col), 0.0) for idx in indices]
        mean = sum(raw_scores) / len(raw_scores) if raw_scores else 0.0
        variance = sum((value - mean) ** 2 for value in raw_scores) / len(raw_scores) if raw_scores else 0.0
        std = math.sqrt(variance) if variance > 0.0 else 1.0
        for idx, raw_score in zip(indices, raw_scores, strict=True):
            z = (raw_score - mean) / std
            probability = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, z))))
            out[idx].update(
                {
                    "raw_nonresponse_pressure": finite_float(out[idx].get(warning_col), 0.0),
                    "raw_response_score": raw_score,
                    "cohort_relative_response_z": z,
                    "relative_response_probability": probability,
                    "nonresponse_probability": 1.0 - probability,
                    "predicted_responder_p_ge_0p5": probability >= 0.5,
                    "axis_policy": "patient_warning_pressure_reference_normalized_v1",
                    "axis_reference_group": group_name,
                }
            )
    return out


def crc_module_risk_from_deltas(
    row: Mapping[str, Any],
    *,
    mapk_col: str = "predicted_mapk_kras_delta",
    egfr_col: str = "predicted_egfr_engagement_delta",
    proliferation_col: str = "predicted_proliferation_delta",
    emt_col: str = "predicted_emt_invasion_delta",
    hypoxia_col: str = "predicted_hypoxia_stress_delta",
    apoptosis_col: str = "predicted_apoptosis_response_delta",
) -> dict[str, float]:
    """Build the CRC KRAS/EGFR module-risk terms from signed module deltas."""

    target = finite_float(row.get(mapk_col), 0.0) + finite_float(row.get(egfr_col), 0.0)
    cytostasis = finite_float(row.get(proliferation_col), 0.0)
    escape = finite_float(row.get(emt_col), 0.0) + finite_float(row.get(hypoxia_col), 0.0)
    weak_kill = -finite_float(row.get(apoptosis_col), 0.0)
    return {
        "module_target_pathway_risk_delta": target,
        "module_failed_cytostasis_risk_delta": cytostasis,
        "module_escape_refuge_risk_delta": escape,
        "module_weak_kill_conversion_risk_delta": weak_kill,
        "zero_centered_module_risk_score": target + cytostasis + escape + weak_kill,
    }


def no_failure_probability(risk_delta: Any, *, temperature: float = 0.10) -> float:
    """Positive risk deltas decrease no-failure probability below 0.5."""

    z = max(-60.0, min(60.0, finite_float(risk_delta, 0.0) / temperature))
    return 1.0 / (1.0 + math.exp(z))


def score_crc_moa_delta_probability(
    row: Mapping[str, Any],
    *,
    temperature: float = 0.10,
    threshold: float = DEFAULT_RESPONSE_THRESHOLD,
) -> dict[str, Any]:
    """Score one CRC patient row from four MOA-specific risk deltas."""

    scored = dict(row)
    if not all(term.risk_delta_column in scored for term in RISK_TERMS):
        scored.update(crc_module_risk_from_deltas(scored))

    no_failure_values = []
    failure_probabilities: dict[str, float] = {}
    activated_reasons: list[str] = []
    for term in RISK_TERMS:
        risk_delta = finite_float(scored.get(term.risk_delta_column), 0.0)
        p_no_failure = no_failure_probability(risk_delta, temperature=temperature)
        no_failure_values.append(p_no_failure)
        failure_probability = 1.0 - p_no_failure
        failure_probabilities[term.risk_reason] = failure_probability
        scored[f"{term.risk_reason}_failure_probability_temp0p10"] = failure_probability
        scored[f"{term.risk_reason}_no_failure_probability_temp0p10"] = p_no_failure
        scored[f"{term.risk_reason}_activated"] = risk_delta > 0.0
        if risk_delta > 0.0:
            activated_reasons.append(term.risk_reason)

    probability = geometric_mean(no_failure_values)
    dominant = max(failure_probabilities.items(), key=lambda item: item[1])[0]
    scored.update(
        {
            "probability_method": f"moa_gate_geomean_temp{temperature:.2f}",
            "response_probability_mean": probability,
            "nonresponse_risk_mean": 1.0 - probability,
            "predicted_responder_p_ge_0p5": probability >= threshold,
            "predicted_non_responder_p_lt_0p5": probability < threshold,
            "dominant_failure_reason": dominant,
            "activated_failure_reasons": ";".join(activated_reasons),
        }
    )
    return scored


def score_crc_moa_delta_rows(rows: Sequence[Mapping[str, Any]], *, temperature: float = 0.10) -> list[dict[str, Any]]:
    return [score_crc_moa_delta_probability(row, temperature=temperature) for row in filter_crc_rows(rows)]


def variant_probability(variant: str, coverage: float, magnitude: float, tail: float) -> float:
    if variant == "softmin_cov09_mag0_tailm002":
        return min(
            sigmoid(coverage, center=0.90, scale=0.05),
            sigmoid(magnitude, center=0.0, scale=0.015),
            sigmoid(tail, center=-0.02, scale=0.015),
        )
    if variant == "signed_mag_tail_soft_primary":
        return (
            sigmoid(coverage, center=0.90, scale=0.05)
            * sigmoid(magnitude, center=0.010, scale=0.015)
            * sigmoid(tail, center=0.0, scale=0.015)
        )
    raise ValueError(f"unsupported CRC patient MOA-tailored variant: {variant}")


def module_calibrated_probability(coverage: float, magnitude: float, tail: float) -> float:
    """Label-free calibration used by the CRC patient MOA-tailored adapter."""

    effective_coverage = min(1.0, coverage / 0.80)
    return min(
        sigmoid(effective_coverage, center=0.90, scale=0.05),
        sigmoid(magnitude, center=0.0, scale=0.015),
        sigmoid(tail, center=-0.02, scale=0.015),
    )


def score_crc_moa_tailored_adapter(
    row: Mapping[str, Any],
    *,
    variant: str = "softmin_cov09_mag0_tailm002",
) -> dict[str, Any]:
    """Apply the CRC patient transfer of the cohort MOA-tailored default."""

    scored = dict(row)
    supports: dict[str, float] = {}
    for support_col, risk_col in SUPPORT_COLUMNS.items():
        if support_col in scored:
            supports[support_col] = finite_float(scored[support_col])
        else:
            supports[support_col] = -finite_float(scored.get(risk_col), 0.0)

    support_values = list(supports.values())
    coverage = sum(value > 0.0 for value in support_values) / len(support_values)
    magnitude = sum(support_values) / len(support_values)
    tail = quantile(support_values, 0.10)
    raw_probability = variant_probability(variant, coverage, magnitude, tail)
    calibrated_probability = module_calibrated_probability(coverage, magnitude, tail)
    scored.update(
        {
            **supports,
            "selected_variant": variant,
            "ct_hetero_conversion_fraction_positive": coverage,
            "ct_hetero_conversion_mean": magnitude,
            "ct_hetero_conversion_p10": tail,
            "response_probability_uncalibrated": raw_probability,
            "nonresponse_risk_uncalibrated": 1.0 - raw_probability,
            "module_coverage_effective": min(1.0, coverage / 0.80),
            "response_probability_module_calibrated": calibrated_probability,
            "nonresponse_risk_module_calibrated": 1.0 - calibrated_probability,
            "predicted_responder_module_p_ge_0p5": calibrated_probability >= DEFAULT_RESPONSE_THRESHOLD,
        }
    )
    return scored


def patient_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    score_col: str = DEFAULT_PATIENT_SCORE_COLUMN,
    label_col: str = DEFAULT_PATIENT_LABEL_COLUMN,
    threshold: float = DEFAULT_RESPONSE_THRESHOLD,
) -> dict[str, Any]:
    crc_rows = filter_crc_rows(rows)
    labels = [row.get(label_col) for row in crc_rows]
    scores = [row.get(score_col) for row in crc_rows]
    predictions = [int(finite_float(score) >= threshold) for score in scores]
    best = best_balanced_accuracy(labels, scores)
    return {
        "cohort": CRC_COHORT_LABEL,
        "score_col": score_col,
        "label_col": label_col,
        "threshold": threshold,
        "n": len([score for score in scores if math.isfinite(finite_float(score))]),
        "n_responders": sum(int(finite_float(label, 0.0) == 1.0) for label in labels),
        "auc_response_high": roc_auc(labels, scores),
        "fixed_threshold_balanced_accuracy": balanced_accuracy(labels, predictions),
        "predicted_responders_fixed_threshold": sum(predictions),
        "best_balanced_accuracy": best["balanced_accuracy"],
        "best_threshold": best["threshold"],
        "best_threshold_predicted_responders": best["predicted_positive"],
    }

