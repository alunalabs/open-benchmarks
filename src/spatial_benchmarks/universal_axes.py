"""Universal response-axis scoring primitives shared by cohort and patient layers."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Any

from .metrics import finite_float, geometric_mean, product, sigmoid, softmin


AXIS_CONTRACT_VERSION = "universal_response_axes_v1"
NEUTRAL_SUPPORT = 1.0

MOA_CONVERSION_CONTROL_COMPONENTS = {
    "androgen_receptor_axis",
    "antifolate_tyms",
    "cdk4_6_cell_cycle",
    "egfr_her2_mapk",
    "hif2a_hypoxia",
    "hormone_receptor_modulator",
    "mek_mapk",
    "mtor_transcript_safe",
    "parp_hrd_proxy",
    "topo1",
    "vegf_multikinase",
}


@dataclass(frozen=True)
class UniversalResponseAxes:
    axis_contract_version: str
    benchmark_level: str
    cohort: str
    item_id: str
    therapy_context: str
    engagement_support: float
    engagement_support_available: bool
    response_conversion_support: float
    response_conversion_support_available: bool
    escape_refuge_control: float
    escape_refuge_control_available: bool
    coverage_support: float
    coverage_support_available: bool
    resistant_tail_control: float
    resistant_tail_control_available: bool
    relative_response_probability: float
    nonresponse_probability: float
    raw_axis_response_score: float
    axis_policy: str
    axis_notes: str

    def as_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MoaTailoredVariantSpec:
    name: str
    mode: str
    coverage_center: float | None
    magnitude_center: float | None
    tail_center: float | None
    coverage_scale: float = 0.05
    magnitude_scale: float = 0.015
    tail_scale: float = 0.015
    hard: bool = False


def encoded_decimal(value: str) -> float | None:
    if value == "none":
        return None
    if not re.fullmatch(r"[pm]\d{4}", value):
        raise ValueError(f"unsupported encoded decimal: {value}")
    sign = -1.0 if value[0] == "m" else 1.0
    return sign * int(value[1:]) / 1000.0


def parse_moa_tailored_variant(name: str) -> MoaTailoredVariantSpec:
    """Parse cohort-selected MOA-tailored variant names into gate parameters."""

    known = {
        "softmin_cov09_mag0_tailm002": MoaTailoredVariantSpec(
            name=name,
            mode="soft_min",
            coverage_center=0.90,
            magnitude_center=0.0,
            tail_center=-0.02,
        ),
        "signed_mag_tail_soft_primary": MoaTailoredVariantSpec(
            name=name,
            mode="coverage_gate_product",
            coverage_center=0.90,
            magnitude_center=0.010,
            tail_center=0.0,
        ),
        "signed_mag_tail_hard_reference": MoaTailoredVariantSpec(
            name=name,
            mode="hard_and",
            coverage_center=0.80,
            magnitude_center=0.005,
            tail_center=-0.01,
            hard=True,
        ),
        "magnitude_only_mag0": MoaTailoredVariantSpec(
            name=name,
            mode="magnitude_only",
            coverage_center=None,
            magnitude_center=0.0,
            tail_center=None,
        ),
        "hard_cov09_mag0_tailm002": MoaTailoredVariantSpec(
            name=name,
            mode="hard_and",
            coverage_center=0.90,
            magnitude_center=0.0,
            tail_center=-0.02,
            hard=True,
        ),
    }
    if name in known:
        return known[name]

    match = re.fullmatch(
        r"grid_(rawcov|covgate|hard)(?:_?cov)?(\d+)?_mag([pm]\d{4})_tail((?:[pm]\d{4})|none)",
        name,
    )
    if not match:
        raise ValueError(f"unsupported MOA-tailored variant: {name}")
    kind, coverage_digits, magnitude_token, tail_token = match.groups()
    return MoaTailoredVariantSpec(
        name=name,
        mode={"rawcov": "raw_coverage_product", "covgate": "coverage_gate_product", "hard": "hard_and"}[kind],
        coverage_center=None if coverage_digits is None else int(coverage_digits) / 100.0,
        magnitude_center=encoded_decimal(magnitude_token),
        tail_center=encoded_decimal(tail_token),
        hard=kind == "hard",
    )


def axis_gate(value: Any, center: float | None, scale: float, *, hard: bool) -> tuple[float, bool]:
    if center is None:
        return NEUTRAL_SUPPORT, False
    numeric = finite_float(value)
    if not math.isfinite(numeric):
        return math.nan, True
    if hard:
        return float(numeric >= center), True
    return sigmoid(numeric, center=center, scale=scale), True


def _cohort_key(value: str) -> str:
    text = str(value or "").strip().lower()
    return "pdac" if text == "pdac_1l" else text


def conversion_control_context_support(cohort: str, therapy_context: str) -> float:
    """Disease-context support for optional MOA conversion-control axes."""

    component = str(therapy_context or "").strip().lower()
    disease = _cohort_key(cohort)
    if component == "vegf_multikinase":
        return 1.0 if disease in {"rcc", "kidney"} else 0.08
    if component == "hif2a_hypoxia":
        return 1.0 if disease in {"rcc", "kidney"} else 0.10
    if component == "topo1":
        if disease == "ovarian":
            return 0.30
        if disease in {"nsclc", "lung"}:
            return 0.25
        if disease == "gastric":
            return 0.20
        if disease == "crc":
            return 0.18
        return 0.20
    if component == "antifolate_tyms":
        if disease == "ovarian":
            return 0.25
        if disease == "gastric":
            return 0.22
        if disease in {"nsclc", "lung"}:
            return 0.20
        if disease == "crc":
            return 0.16
        if disease == "hnscc":
            return 0.12
        return 0.18
    if component == "mtor_transcript_safe":
        return 0.45 if disease in {"rcc", "kidney"} else 0.25
    if component in {"egfr_her2_mapk", "mek_mapk"}:
        if disease in {"nsclc", "lung"}:
            return 0.85
        if disease in {"crc", "gastric"}:
            return 0.35
        return 0.25
    if component == "cdk4_6_cell_cycle":
        if disease == "breast":
            return 0.85
        if disease in {"pdac", "pancreas"}:
            return 0.12
        return 0.25
    if component == "hormone_receptor_modulator":
        return 0.15 if disease == "ovarian" else 0.35
    if component == "androgen_receptor_axis":
        return 0.90 if disease == "prostate" else 0.10
    if component == "parp_hrd_proxy":
        return 0.70 if disease in {"ovarian", "breast"} else 0.25
    return NEUTRAL_SUPPORT


def moa_conversion_control_probability(
    *,
    cohort: str,
    therapy_context: str,
    moa_coverage: Any,
    moa_magnitude: Any,
    moa_tail: Any,
) -> dict[str, Any]:
    component = str(therapy_context or "").strip().lower()
    if component not in MOA_CONVERSION_CONTROL_COMPONENTS:
        return {
            "moa_conversion_control_applied": False,
            "conversion_control_context_support": math.nan,
            "moa_conversion_control_response_probability": math.nan,
            "moa_engagement_support": math.nan,
            "moa_coverage_support": math.nan,
            "moa_resistant_tail_control": math.nan,
        }

    context_support = conversion_control_context_support(cohort, component)
    engagement_support, engagement_available = axis_gate(moa_magnitude, 0.0, 0.015, hard=False)
    coverage_support, coverage_available = axis_gate(moa_coverage, 0.60, 0.10, hard=False)
    tail_control, tail_available = axis_gate(moa_tail, -0.01, 0.015, hard=False)
    values = [
        context_support,
        *[
            value
            for value, available in (
                (engagement_support, engagement_available),
                (coverage_support, coverage_available),
                (tail_control, tail_available),
            )
            if available and math.isfinite(value)
        ],
    ]
    probability = product(values) if len(values) > 1 else math.nan
    return {
        "moa_conversion_control_applied": math.isfinite(probability),
        "conversion_control_context_support": context_support,
        "moa_conversion_control_response_probability": probability,
        "moa_engagement_support": engagement_support,
        "moa_coverage_support": coverage_support,
        "moa_resistant_tail_control": tail_control,
    }


def moa_tailored_patient_axis_row(
    *,
    benchmark_level: str,
    cohort: str,
    item_id: str,
    therapy_context: str,
    selected_variant: str,
    response_probability: Any,
    coverage: Any,
    magnitude: Any,
    tail: Any,
    moa_coverage: Any = math.nan,
    moa_magnitude: Any = math.nan,
    moa_tail: Any = math.nan,
) -> dict[str, Any]:
    """Create one universal response-axis row from MOA-tailored patient features."""

    spec = parse_moa_tailored_variant(selected_variant)
    coverage_support, coverage_available = axis_gate(
        coverage,
        spec.coverage_center,
        spec.coverage_scale,
        hard=spec.hard,
    )
    conversion_support, conversion_available = axis_gate(
        magnitude,
        spec.magnitude_center,
        spec.magnitude_scale,
        hard=spec.hard,
    )
    tail_control, tail_available = axis_gate(tail, spec.tail_center, spec.tail_scale, hard=spec.hard)
    available_values = [
        value
        for value, available in (
            (coverage_support, coverage_available),
            (conversion_support, conversion_available),
            (tail_control, tail_available),
        )
        if available and math.isfinite(value)
    ]
    source_axis_product = product(available_values)
    control = moa_conversion_control_probability(
        cohort=cohort,
        therapy_context=therapy_context,
        moa_coverage=moa_coverage,
        moa_magnitude=moa_magnitude,
        moa_tail=moa_tail,
    )
    control_probability = finite_float(control["moa_conversion_control_response_probability"])
    use_control = bool(control["moa_conversion_control_applied"]) and math.isfinite(control_probability)
    universal_product = control_probability if use_control else source_axis_product
    source_probability = max(0.0, min(1.0, finite_float(response_probability, source_axis_product)))

    axis_engagement = (
        finite_float(control["conversion_control_context_support"], NEUTRAL_SUPPORT)
        if use_control
        else NEUTRAL_SUPPORT
    )
    axis_conversion = (
        finite_float(control["moa_engagement_support"], conversion_support)
        if use_control
        else conversion_support
    )
    axis_coverage = (
        finite_float(control["moa_coverage_support"], coverage_support)
        if use_control
        else coverage_support
    )
    axis_tail = finite_float(control["moa_resistant_tail_control"], tail_control) if use_control else tail_control
    final_values = [axis_engagement, axis_coverage, axis_conversion, axis_tail] if use_control else available_values
    axis_policy = (
        "moa_tailored_moa_conversion_control_axis_product_v1"
        if use_control
        else "moa_tailored_available_axis_product_v1"
    )
    axis_notes = (
        "MOA-aware conversion-control axis is active."
        if use_control
        else "Engagement support is neutral; coverage, conversion, and tail/refuge gates come from the selected variant."
    )

    axes = UniversalResponseAxes(
        axis_contract_version=AXIS_CONTRACT_VERSION,
        benchmark_level=benchmark_level,
        cohort=cohort,
        item_id=item_id,
        therapy_context=therapy_context,
        engagement_support=axis_engagement,
        engagement_support_available=use_control,
        response_conversion_support=axis_conversion,
        response_conversion_support_available=conversion_available,
        escape_refuge_control=axis_tail,
        escape_refuge_control_available=tail_available,
        coverage_support=axis_coverage,
        coverage_support_available=coverage_available,
        resistant_tail_control=axis_tail,
        resistant_tail_control_available=tail_available,
        relative_response_probability=universal_product,
        nonresponse_probability=1.0 - universal_product,
        raw_axis_response_score=universal_product,
        axis_policy=axis_policy,
        axis_notes=axis_notes,
    )
    row = axes.as_row()
    row.update(
        {
            "selected_variant": selected_variant,
            "selected_variant_mode": spec.mode,
            "selected_variant_hard": spec.hard,
            "selected_variant_coverage_center": spec.coverage_center,
            "selected_variant_magnitude_center": spec.magnitude_center,
            "selected_variant_tail_center": spec.tail_center,
            "source_response_probability": source_probability,
            "source_axis_product_response_probability": source_axis_product,
            "universal_axis_product_response_probability": universal_product,
            "universal_axis_softmin_response_probability": softmin(final_values),
            "universal_axis_geomean_response_probability": geometric_mean(final_values),
            "axis_available_count": len(final_values),
            **control,
        }
    )
    return row

