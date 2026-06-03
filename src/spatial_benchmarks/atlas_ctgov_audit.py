"""ClinicalTrials.gov citation audit for Atlas ORR support rows."""

from __future__ import annotations

import csv
import json
import math
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .atlas_orr import (
    ATLAS_TEXT_COLUMNS,
    DISEASE_TO_ATLAS_TISSUES,
    SHRINKAGE_K_VALUES,
    atlas_row_mentions_target_drug,
    finite_float,
    infer_moa_components,
    is_real_therapy,
    line_bucket,
    load_target_rows,
    norm_text,
    summarize_subset,
    target_aliases,
    therapy_families,
)
from .io import write_csv_rows, write_json


CTGOV_API = "https://clinicaltrials.gov/api/v2/studies/{nct_id}"
CTGOV_STUDY_URL = "https://clinicaltrials.gov/study/{nct_id}"
AUDIT_SCORE_COL = "atlas_mono_disease_therapy_shrink_k8"


def split_terms(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.replace("|", ";").split(";") if part.strip()]


def parse_float(value: Any) -> float:
    text = str(value or "").strip().replace("%", "")
    return finite_float(text)


def denominator_by_group(outcome: dict[str, Any]) -> dict[str, float]:
    denominators: dict[str, float] = {}
    for denom in outcome.get("denoms", []):
        for count in denom.get("counts", []):
            group_id = str(count.get("groupId") or "")
            value = finite_float(count.get("value"))
            if group_id and math.isfinite(value) and value > 0:
                denominators[group_id] = value
    return denominators


def value_as_percent(
    *,
    value: float,
    denominator: float,
    param_type: str,
    unit: str,
) -> float:
    param_norm = norm_text(param_type)
    unit_norm = norm_text(unit)
    if "percent" in param_norm or "percentage" in param_norm or "percent" in unit_norm:
        return value
    if unit_norm in {"participants", "participant"} or "count" in param_norm:
        return value / denominator * 100.0 if denominator > 0 else math.nan
    return value


def load_raw_atlas_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for idx, raw in enumerate(reader):
            orr = finite_float(raw.get("model_orr_pct"))
            if not math.isfinite(orr) or orr < 0.0 or orr > 100.0:
                continue
            therapy_set = therapy_families(raw.get("therapy_class"))
            if not is_real_therapy(therapy_set):
                continue
            text_norm = norm_text(" | ".join(str(raw.get(col) or "") for col in ATLAS_TEXT_COLUMNS))
            weight = finite_float(raw.get("orr_denom"), 1.0)
            row = dict(raw)
            row["_atlas_row_index"] = idx
            row["_atlas_orr_pct"] = orr
            row["_atlas_weight"] = weight if math.isfinite(weight) and weight > 0 else 1.0
            row["_atlas_text_norm"] = text_norm
            row["_atlas_therapy_set"] = therapy_set
            row["_atlas_moa_set"] = infer_moa_components(text_norm)
            row["_line_bucket"] = line_bucket(raw.get("line_of_therapy"))
            rows.append(row)
    return rows


def summary_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return summarize_subset(
        [
            {
                "atlas_weight": row["_atlas_weight"],
                "atlas_orr_pct": row["_atlas_orr_pct"],
                "model_orr_pct_source": row.get("model_orr_pct_source"),
                "nct_id": row.get("nct_id"),
            }
            for row in rows
        ]
    )


def cell_rows(
    rows: list[dict[str, Any]],
    *,
    tissues: set[str],
    target_family: str,
    target_moa: str,
    cell_name: str,
) -> list[dict[str, Any]]:
    def disease_match(row: dict[str, Any]) -> bool:
        return bool(tissues) and str(row.get("tissue_type") or "") in tissues

    def therapy_match(row: dict[str, Any]) -> bool:
        return bool(target_family) and target_family in row["_atlas_therapy_set"]

    def moa_match(row: dict[str, Any]) -> bool:
        return bool(target_moa) and target_moa in row["_atlas_moa_set"]

    if cell_name == "disease_therapy":
        return [row for row in rows if disease_match(row) and therapy_match(row)]
    if cell_name == "global_therapy":
        return [row for row in rows if therapy_match(row)]
    if cell_name == "disease_baseline":
        return [row for row in rows if disease_match(row)]
    if cell_name == "global_moa":
        return [row for row in rows if moa_match(row)]
    if cell_name == "global_baseline":
        return list(rows)
    raise ValueError(f"unsupported Atlas support cell: {cell_name}")


def select_legacy_fallback_cell(
    rows: list[dict[str, Any]],
    *,
    tissues: set[str],
    target_family: str,
    target_moa: str,
) -> str:
    hierarchy = [
        ("disease_therapy", 8),
        ("disease_baseline", 15),
        ("global_therapy", 25),
        ("global_moa", 5),
        ("global_baseline", 25),
    ]
    for cell_name, min_arms in hierarchy:
        support = cell_rows(
            rows,
            tissues=tissues,
            target_family=target_family,
            target_moa=target_moa,
            cell_name=cell_name,
        )
        summary = summary_for(support)
        if summary["n_arms"] >= min_arms and math.isfinite(finite_float(summary["prior_orr_pct"])):
            return cell_name
    return "global_baseline"


def atlas_score_contributors(
    *,
    atlas_csv: str | Path,
    cohort_predictions_csv: str | Path,
    surface_score_col: str | None = "default_score",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    atlas_rows = load_raw_atlas_rows(atlas_csv)
    target_rows = load_target_rows(cohort_predictions_csv, surface_score_col=surface_score_col)
    target_arm_rows: list[dict[str, Any]] = []
    by_arm: dict[int, dict[str, Any]] = {}
    arm_targets: dict[int, set[str]] = defaultdict(set)
    arm_cells: dict[int, set[str]] = defaultdict(set)

    for target in target_rows:
        target_id = str(target.get("surface_pair_id") or "")
        disease = str(target.get("cohort") or "")
        tissues = DISEASE_TO_ATLAS_TISSUES.get(disease, set())
        target_moa = str(target.get("moa_component") or "")
        target_family = str(target.get("target_therapy_family") or "")
        aliases = target_aliases(target.get("drug"), target.get("drug_norm_clean"))
        eligible = [
            row
            for row in atlas_rows
            if not atlas_row_mentions_target_drug(
                {"atlas_text_norm": row["_atlas_text_norm"]},
                aliases,
            )
        ]
        mono = [
            row
            for row in eligible
            if str(row.get("is_combination") or "").lower() != "true"
            and str(row.get("biomarker") or "").lower() != "yes"
        ]
        disease_therapy = cell_rows(
            mono,
            tissues=tissues,
            target_family=target_family,
            target_moa=target_moa,
            cell_name="disease_therapy",
        )
        global_therapy = cell_rows(
            mono,
            tissues=tissues,
            target_family=target_family,
            target_moa=target_moa,
            cell_name="global_therapy",
        )
        disease_prior = finite_float(summary_for(disease_therapy)["prior_orr_pct"])
        global_prior = finite_float(summary_for(global_therapy)["prior_orr_pct"])
        if math.isfinite(disease_prior) and math.isfinite(global_prior):
            support_cells = [
                ("disease_therapy", disease_therapy),
                ("global_therapy", global_therapy),
            ]
        else:
            fallback_cell = select_legacy_fallback_cell(
                mono,
                tissues=tissues,
                target_family=target_family,
                target_moa=target_moa,
            )
            support_cells = [
                (
                    f"fallback_{fallback_cell}",
                    cell_rows(
                        mono,
                        tissues=tissues,
                        target_family=target_family,
                        target_moa=target_moa,
                        cell_name=fallback_cell,
                    ),
                )
            ]

        for support_cell, support_rows in support_cells:
            for row in support_rows:
                arm_idx = int(row["_atlas_row_index"])
                arm_targets[arm_idx].add(target_id)
                arm_cells[arm_idx].add(support_cell)
                by_arm[arm_idx] = row
                target_arm_rows.append(
                    {
                        "target_surface_pair_id": target_id,
                        "target_cohort": disease,
                        "target_drug": target.get("drug"),
                        "target_therapy_family": target_family,
                        "support_cell": support_cell,
                        "atlas_row_index": arm_idx,
                        "nct_id": row.get("nct_id"),
                        "source_url": row.get("source_url")
                        or CTGOV_STUDY_URL.format(nct_id=row.get("nct_id")),
                        "api_url": row.get("api_url")
                        or CTGOV_API.format(nct_id=row.get("nct_id")),
                        "arm_group_id": row.get("arm_group_id"),
                        "ctgov_result_group_ids": row.get("ctgov_result_group_ids"),
                        "arm_title": row.get("arm_title"),
                        "model_orr_pct": row.get("model_orr_pct"),
                        "model_orr_pct_source": row.get("model_orr_pct_source"),
                    }
                )

    support_rows = []
    for arm_idx, row in sorted(by_arm.items()):
        support_rows.append(
            {
                "atlas_row_index": arm_idx,
                "nct_id": row.get("nct_id"),
                "source_url": row.get("source_url")
                or CTGOV_STUDY_URL.format(nct_id=row.get("nct_id")),
                "api_url": row.get("api_url") or CTGOV_API.format(nct_id=row.get("nct_id")),
                "brief_title": row.get("brief_title"),
                "tissue_type": row.get("tissue_type"),
                "line_of_therapy": row.get("line_of_therapy"),
                "biomarker": row.get("biomarker"),
                "arm_group_id": row.get("arm_group_id"),
                "ctgov_result_group_ids": row.get("ctgov_result_group_ids"),
                "ctgov_result_group_titles": row.get("ctgov_result_group_titles"),
                "arm_title": row.get("arm_title"),
                "arm_description": row.get("arm_description"),
                "interventions": row.get("interventions"),
                "regimen": row.get("regimen"),
                "therapy_class": row.get("therapy_class"),
                "is_combination": row.get("is_combination"),
                "orr_pct": row.get("orr_pct"),
                "orr_n": row.get("orr_n"),
                "orr_denom": row.get("orr_denom"),
                "orr_endpoint_title": row.get("orr_endpoint_title"),
                "orr_time_frame": row.get("orr_time_frame"),
                "model_orr_pct": row.get("model_orr_pct"),
                "model_orr_pct_source": row.get("model_orr_pct_source"),
                "model_orr_pct_pmid": row.get("model_orr_pct_pmid"),
                "pubmed_orr_pct": row.get("pubmed_orr_pct"),
                "pubmed_orr_pct_pmid": row.get("pubmed_orr_pct_pmid"),
                "used_by_n_target_rows": len(arm_targets[arm_idx]),
                "used_as_support_cells": ";".join(sorted(arm_cells[arm_idx])),
                "target_surface_pair_ids": ";".join(sorted(arm_targets[arm_idx])),
            }
        )
    return support_rows, target_arm_rows


def fetch_ctgov_study(nct_id: str, *, cache_dir: str | Path | None = None) -> dict[str, Any]:
    if cache_dir:
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        cached = cache / f"{nct_id}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    url = CTGOV_API.format(nct_id=nct_id)
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if cache_dir:
        cached.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


def iter_measurements(study: dict[str, Any]) -> list[dict[str, Any]]:
    outcome_measures = (
        study.get("resultsSection", {})
        .get("outcomeMeasuresModule", {})
        .get("outcomeMeasures", [])
    )
    rows: list[dict[str, Any]] = []
    for outcome in outcome_measures:
        denominators = denominator_by_group(outcome)
        param_type = outcome.get("paramType", "")
        unit = outcome.get("unitOfMeasure", "")
        groups = {str(group.get("id") or ""): group for group in outcome.get("groups", [])}
        outcome_rows: list[dict[str, Any]] = []
        for class_row in outcome.get("classes", []):
            class_title = class_row.get("title", "")
            for category in class_row.get("categories", []):
                category_title = category.get("title", "")
                for measurement in category.get("measurements", []):
                    group_id = str(measurement.get("groupId") or "")
                    group = groups.get(group_id, {})
                    value = parse_float(measurement.get("value"))
                    denominator = denominators.get(group_id, math.nan)
                    outcome_rows.append(
                        {
                            "outcome_title": outcome.get("title", ""),
                            "outcome_type": outcome.get("type", ""),
                            "outcome_time_frame": outcome.get("timeFrame", ""),
                            "param_type": param_type,
                            "unit_of_measure": unit,
                            "class_title": class_title,
                            "category_title": category_title,
                            "group_id": group_id,
                            "group_title": group.get("title", ""),
                            "group_description": group.get("description", ""),
                            "value": measurement.get("value", ""),
                            "value_numeric": value,
                            "denominator": denominator,
                            "value_as_pct": value_as_percent(
                                value=value,
                                denominator=denominator,
                                param_type=str(param_type),
                                unit=str(unit),
                            ),
                            "lower_limit": measurement.get("lowerLimit", ""),
                            "upper_limit": measurement.get("upperLimit", ""),
                        }
                    )
        rows.extend(outcome_rows)
        rows.extend(aggregate_response_measurements(outcome_rows))
    return rows


def aggregate_response_measurements(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        detail_norm = norm_text(f"{row.get('class_title', '')} {row.get('category_title', '')}")
        if detail_norm and response_category_candidate(row):
            grouped[str(row.get("group_id") or "")].append(row)

    aggregates: list[dict[str, Any]] = []
    for group_id, group_rows in grouped.items():
        if len(group_rows) < 2:
            continue
        first = group_rows[0]
        denominator = finite_float(first.get("denominator"))
        raw_sum = sum(finite_float(row.get("value_numeric"), 0.0) for row in group_rows)
        pct_values = [finite_float(row.get("value_as_pct")) for row in group_rows]
        pct_values = [value for value in pct_values if math.isfinite(value)]
        if math.isfinite(denominator) and denominator > 0:
            value_pct = raw_sum / denominator * 100.0
        else:
            value_pct = sum(pct_values) if pct_values else math.nan
        aggregate = dict(first)
        aggregate.update(
            {
                "class_title": "Aggregate response categories",
                "category_title": "; ".join(
                    filter(
                        None,
                        [
                            str(row.get("class_title") or row.get("category_title") or "")
                            for row in group_rows
                        ],
                    )
                ),
                "value": raw_sum,
                "value_numeric": raw_sum,
                "value_as_pct": value_pct,
                "lower_limit": "",
                "upper_limit": "",
            }
        )
        aggregates.append(aggregate)
    return aggregates


def title_matches(row_endpoint_title: str, outcome_title: str) -> bool:
    row_norm = norm_text(row_endpoint_title)
    outcome_norm = norm_text(outcome_title)
    if row_norm:
        return row_norm == outcome_norm or row_norm in outcome_norm or outcome_norm in row_norm
    keywords = [
        "objective_response",
        "overall_response",
        "response_rate",
        "recist_response",
        "orr",
    ]
    return any(keyword in outcome_norm for keyword in keywords)


def group_matches(row: dict[str, Any], measurement: dict[str, Any]) -> bool:
    group_ids = set(split_terms(row.get("ctgov_result_group_ids")))
    if group_ids and str(measurement.get("group_id") or "") in group_ids:
        return True
    group_titles = {norm_text(value) for value in split_terms(row.get("ctgov_result_group_titles"))}
    group_titles.add(norm_text(row.get("arm_title")))
    measurement_title = norm_text(measurement.get("group_title"))
    return bool(measurement_title and measurement_title in group_titles)


def response_category_candidate(measurement: dict[str, Any]) -> bool:
    class_norm = norm_text(measurement.get("class_title"))
    category_norm = norm_text(measurement.get("category_title"))
    detail_norm = f"{class_norm}_{category_norm}".strip("_")
    if not detail_norm:
        return True
    negative_terms = [
        "non_responder",
        "non_response",
        "no_response",
        "not_respond",
        "progression",
        "progressive_disease",
        "stable_disease",
        "disease_stabilization",
    ]
    if any(term in detail_norm for term in negative_terms):
        return False
    positive_terms = [
        "responder",
        "response",
        "objective_response",
        "overall_response",
        "complete_response",
        "partial_response",
        "partial_remission",
        "cr_pr",
    ]
    tokens = set(detail_norm.split("_"))
    return any(term in detail_norm for term in positive_terms) or bool(tokens & {"cr", "pr"})


def audit_support_row(
    row: dict[str, Any],
    study: dict[str, Any] | None,
    *,
    fetch_error: str = "",
    retrieved_date: str,
) -> dict[str, Any]:
    nct_id = str(row.get("nct_id") or "")
    atlas_orr = finite_float(row.get("model_orr_pct"))
    out = {
        **row,
        "ctgov_audit_status": "",
        "ctgov_verified_orr_pct": "",
        "ctgov_value_delta": "",
        "ctgov_outcome_title": "",
        "ctgov_outcome_type": "",
        "ctgov_outcome_time_frame": "",
        "ctgov_param_type": "",
        "ctgov_unit_of_measure": "",
        "ctgov_class_title": "",
        "ctgov_category_title": "",
        "ctgov_group_id": "",
        "ctgov_group_title": "",
        "ctgov_measurement_value": "",
        "ctgov_measurement_denominator": "",
        "ctgov_measurement_pct": "",
        "ctgov_lower_limit": "",
        "ctgov_upper_limit": "",
        "ctgov_citation": CTGOV_STUDY_URL.format(nct_id=nct_id),
        "ctgov_api_citation": CTGOV_API.format(nct_id=nct_id),
        "ctgov_retrieved_date": retrieved_date,
        "ctgov_audit_note": "",
    }
    if study is None:
        out["ctgov_audit_status"] = "ctgov_fetch_error"
        out["ctgov_audit_note"] = fetch_error
        return out

    measurements = [
        measurement
        for measurement in iter_measurements(study)
        if group_matches(row, measurement)
        and title_matches(
            str(row.get("orr_endpoint_title") or ""),
            str(measurement["outcome_title"]),
        )
        and response_category_candidate(measurement)
        and math.isfinite(measurement["value_as_pct"])
    ]
    if not measurements:
        out["ctgov_audit_status"] = "ctgov_no_matching_orr_measurement"
        if str(row.get("model_orr_pct_source") or "") != "ctgov":
            out["ctgov_audit_note"] = (
                f"Atlas model ORR source is {row.get('model_orr_pct_source')}; "
                "no matching CTGov ORR measurement was found by group/title."
            )
        return out

    best = sorted(measurements, key=lambda item: abs(item["value_as_pct"] - atlas_orr))[0]
    delta = best["value_as_pct"] - atlas_orr
    out.update(
        {
            "ctgov_verified_orr_pct": best["value_as_pct"],
            "ctgov_value_delta": delta,
            "ctgov_outcome_title": best["outcome_title"],
            "ctgov_outcome_type": best["outcome_type"],
            "ctgov_outcome_time_frame": best["outcome_time_frame"],
            "ctgov_param_type": best["param_type"],
            "ctgov_unit_of_measure": best["unit_of_measure"],
            "ctgov_class_title": best["class_title"],
            "ctgov_category_title": best["category_title"],
            "ctgov_group_id": best["group_id"],
            "ctgov_group_title": best["group_title"],
            "ctgov_measurement_value": best["value"],
            "ctgov_measurement_denominator": best["denominator"],
            "ctgov_measurement_pct": best["value_as_pct"],
            "ctgov_lower_limit": best["lower_limit"],
            "ctgov_upper_limit": best["upper_limit"],
        }
    )
    out["ctgov_audit_status"] = (
        "ctgov_verified_match" if abs(delta) <= 0.5 else "ctgov_value_mismatch"
    )
    if str(row.get("model_orr_pct_source") or "") != "ctgov":
        out["ctgov_audit_note"] = f"Atlas model ORR source is {row.get('model_orr_pct_source')}."
    return out


def audit_atlas_ctgov_support(
    *,
    atlas_csv: str | Path,
    cohort_predictions_csv: str | Path,
    surface_score_col: str | None = "default_score",
    cache_dir: str | Path | None = None,
    sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    support_rows, target_arm_rows = atlas_score_contributors(
        atlas_csv=atlas_csv,
        cohort_predictions_csv=cohort_predictions_csv,
        surface_score_col=surface_score_col,
    )
    retrieved_date = datetime.now(UTC).date().isoformat()
    studies: dict[str, dict[str, Any] | None] = {}
    fetch_errors: dict[str, str] = {}
    nct_ids = sorted({str(row.get("nct_id") or "") for row in support_rows if row.get("nct_id")})
    for nct_id in nct_ids:
        try:
            studies[nct_id] = fetch_ctgov_study(nct_id, cache_dir=cache_dir)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            studies[nct_id] = None
            fetch_errors[nct_id] = str(error)
        if sleep_seconds:
            time.sleep(sleep_seconds)

    audited_rows = [
        audit_support_row(
            row,
            studies.get(str(row.get("nct_id") or "")),
            fetch_error=fetch_errors.get(str(row.get("nct_id") or ""), ""),
            retrieved_date=retrieved_date,
        )
        for row in support_rows
    ]
    status_counts = Counter(str(row.get("ctgov_audit_status") or "") for row in audited_rows)
    source_counts = Counter(str(row.get("model_orr_pct_source") or "") for row in audited_rows)
    summary = {
        "score_col": AUDIT_SCORE_COL,
        "target_eval_rows": len({row["target_surface_pair_id"] for row in target_arm_rows}),
        "target_support_contributor_rows": len(target_arm_rows),
        "unique_atlas_support_rows": len(audited_rows),
        "unique_nct_ids": len({row["nct_id"] for row in audited_rows}),
        "ctgov_retrieved_date": retrieved_date,
        "status_counts": dict(sorted(status_counts.items())),
        "model_orr_pct_source_counts": dict(sorted(source_counts.items())),
        "methodology": {
            "support_scope": (
                "unique Atlas arm rows contributing to fixed k=8 Atlas ORR score "
                "on the 63 cohort benchmark v2 ORR rows"
            ),
            "ctgov_match_rule": (
                "match ClinicalTrials.gov outcome measurement by result group and ORR-like "
                "outcome title; verified if API value differs from Atlas model_orr_pct by <= 0.5"
            ),
        },
    }
    return {
        "audited_support_rows": audited_rows,
        "target_support_contributors": target_arm_rows,
        "summary": summary,
    }


def write_atlas_ctgov_audit_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    write_csv_rows(output / "atlas_orr_ctgov_audit.csv", result["audited_support_rows"])
    write_csv_rows(
        output / "atlas_orr_ctgov_audit_exceptions.csv",
        [
            row
            for row in result["audited_support_rows"]
            if row.get("ctgov_audit_status") != "ctgov_verified_match"
        ],
    )
    write_csv_rows(
        output / "atlas_orr_target_support_contributors.csv",
        result["target_support_contributors"],
    )
    write_json(output / "atlas_orr_ctgov_audit_summary.json", result["summary"])
