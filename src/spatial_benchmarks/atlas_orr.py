"""Atlas-derived ORR baselines for the strict 44-row cohort benchmark."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .io import read_csv_rows, write_csv_rows, write_json
from .metrics import auc_above_group_median, finite_float, pearson, spearman


DISEASE_TO_ATLAS_TISSUES = {
    "breast": {"breast"},
    "crc": {"colorectal"},
    "gastric": {"gastric_gej"},
    "hnscc": {"head_neck"},
    "nsclc": {"nsclc"},
    "ovarian": {"ovarian_fallopian_peritoneal"},
    "pdac": {"pancreatic"},
    "prostate": {"prostate"},
    "rcc": {"renal"},
}

SALT_WORDS = {
    "acetate",
    "dihydrochloride",
    "disodium",
    "ditosylate",
    "hcl",
    "hydrochloride",
    "malate",
    "mesylate",
    "phosphate",
    "s",
    "sodium",
}

MOA_KEYWORDS = {
    "proteasome": ["bortezomib", "carfilzomib", "ixazomib"],
    "taxane": ["docetaxel", "paclitaxel", "nab paclitaxel", "cabazitaxel"],
    "topo2_anthracycline": ["doxorubicin", "epirubicin", "idarubicin", "mitoxantrone"],
    "egfr_her2_mapk": [
        "erlotinib",
        "gefitinib",
        "afatinib",
        "lapatinib",
        "cetuximab",
        "panitumumab",
        "trastuzumab",
        "pertuzumab",
        "osimertinib",
        "dacomitinib",
        "neratinib",
        "binimetinib",
        "trametinib",
        "cobimetinib",
        "selumetinib",
    ],
    "gemcitabine_nucleoside": ["gemcitabine", "cytarabine", "decitabine"],
    "fluoropyrimidine_tyms": [
        "fluorouracil",
        "5 fluorouracil",
        "5-fu",
        "5 fu",
        "capecitabine",
        "tegafur",
    ],
    "platinum_dna_damage": ["oxaliplatin", "cisplatin", "carboplatin"],
    "topo1": ["irinotecan", "topotecan", "nal iri", "nal-iri", "sn 38", "sn-38"],
    "antifolate_tyms": ["pemetrexed", "methotrexate", "raltitrexed", "pralatrexate"],
    "vegf_multikinase": [
        "sunitinib",
        "cabozantinib",
        "regorafenib",
        "vandetanib",
        "sorafenib",
        "pazopanib",
        "axitinib",
        "lenvatinib",
        "bevacizumab",
        "ramucirumab",
        "tivozanib",
        "cediranib",
        "nintedanib",
        "apatinib",
        "fruquintinib",
    ],
    "mtor_transcript_safe": ["everolimus", "temsirolimus", "sirolimus"],
    "plk1_mitotic": ["volasertib", "onvansertib"],
    "alkylator_low_specificity": [
        "altretamine",
        "cyclophosphamide",
        "temozolomide",
        "dacarbazine",
        "melphalan",
    ],
    "hormone_receptor_modulator": [
        "mifepristone",
        "fulvestrant",
        "tamoxifen",
        "letrozole",
        "anastrozole",
        "exemestane",
        "amcenestrant",
    ],
    "cdk4_6_cell_cycle": ["abemaciclib", "palbociclib", "ribociclib"],
    "hif2a_hypoxia": ["belzutifan"],
    "androgen_receptor_axis": ["abiraterone", "enzalutamide", "apalutamide", "darolutamide"],
}

MOA_TO_THERAPY_FAMILY = {
    "proteasome": "targeted_therapy",
    "taxane": "chemotherapy",
    "topo2_anthracycline": "chemotherapy",
    "egfr_her2_mapk": "targeted_therapy",
    "gemcitabine_nucleoside": "chemotherapy",
    "fluoropyrimidine_tyms": "chemotherapy",
    "platinum_dna_damage": "chemotherapy",
    "topo1": "chemotherapy",
    "antifolate_tyms": "chemotherapy",
    "vegf_multikinase": "targeted_therapy",
    "mtor_transcript_safe": "targeted_therapy",
    "plk1_mitotic": "targeted_therapy",
    "alkylator_low_specificity": "chemotherapy",
    "hormone_receptor_modulator": "endocrine_hormonal",
    "cdk4_6_cell_cycle": "targeted_therapy",
    "hif2a_hypoxia": "targeted_therapy",
    "androgen_receptor_axis": "endocrine_hormonal",
}

EXACT_DRUG_ALIASES = {
    "5_fluorouracil": ["fluorouracil", "5 fluorouracil", "5-fu", "5 fu"],
    "cabozantinib": ["cabozantinib"],
    "doxorubicin": ["doxorubicin", "adriamycin"],
    "lapatinib": ["lapatinib"],
    "mitoxantrone": ["mitoxantrone"],
    "topotecan": ["topotecan"],
}

ATLAS_TEXT_COLUMNS = (
    "brief_title",
    "conditions",
    "arm_title",
    "arm_description",
    "interventions",
    "regimen",
    "treatment_regimen",
)

PRIMARY_SCORE_COL = "atlas_mono_disease_therapy_shrink_k8"
LEGACY_PRIMARY_SCORE_COL = "atlas_mono_allcomer_hierarchical_prior_therapy_first_orr"
SHRINKAGE_K_VALUES = (8,)
CTGOV_AUDIT_EXCEPTION_ATLAS_ROW_INDICES = (
    582,
    1519,
    2448,
    2568,
    3862,
    9268,
    10228,
    12033,
    14965,
    14966,
    17451,
)
STRICT_NON_ORR_ATLAS_ROW_INDICES = (4782, 11729)
OPTIONAL_UNCONFIRMED_ORR_ATLAS_ROW_INDICES = (7251,)
STRICT_RELEASE_EXCLUDED_ATLAS_ROW_INDICES = tuple(
    sorted((*CTGOV_AUDIT_EXCEPTION_ATLAS_ROW_INDICES, *STRICT_NON_ORR_ATLAS_ROW_INDICES))
)

def norm_text(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def norm_drug(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    parts = [part for part in text.split("_") if part and part not in SALT_WORDS]
    key = "_".join(parts)
    aliases = {
        "fluorouracil": "5_fluorouracil",
        "5_fu": "5_fluorouracil",
        "doxorubicin_hydrochloride": "doxorubicin",
        "lapatinib_ditosylate": "lapatinib",
        "topotecan_hydrochloride": "topotecan",
        "mitoxantrone_dihydrochloride": "mitoxantrone",
        "cabozantinib_s_malate": "cabozantinib",
    }
    return aliases.get(key, key)


def contains_norm_term(normalized_text: str, term: str) -> bool:
    return bool(term) and f"_{term}_" in f"_{normalized_text}_"


def target_aliases(drug: Any, drug_norm: Any) -> set[str]:
    aliases = {norm_text(drug_norm), norm_drug(drug)}
    key = norm_drug(drug_norm) or norm_drug(drug)
    aliases.update(norm_text(value) for value in EXACT_DRUG_ALIASES.get(key, []))
    return {alias for alias in aliases if alias and len(alias) >= 4}


def line_bucket(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text == "1l":
        return "1L"
    if text in {"2l", "2l+", "3l+"}:
        return "2L+"
    if text in {"adjuvant", "neoadjuvant", "maintenance", "localized_or_definitive"}:
        return text
    if text in {"advanced_or_metastatic_line_unspecified", "line_not_reported"}:
        return "advanced_unspecified"
    return text or "unknown"


def therapy_families(value: Any) -> set[str]:
    text = str(value or "").lower()
    out: set[str] = set()
    if "chemotherapy" in text:
        out.add("chemotherapy")
    if "targeted_therapy" in text or "adc" in text:
        out.add("targeted_therapy")
    if "immunotherapy_checkpoint" in text:
        out.add("immunotherapy_checkpoint")
    if "endocrine_hormonal" in text:
        out.add("endocrine_hormonal")
    if "radiation" in text:
        out.add("radiation")
    if "vaccine_oncolytic_cellular" in text:
        out.add("vaccine_oncolytic_cellular")
    if "supportive_care_or_symptom_control" in text:
        out.add("supportive_care_or_symptom_control")
    if not out and text:
        out.add(text)
    return out


def infer_moa_components(normalized_text: str) -> set[str]:
    components: set[str] = set()
    for component, terms in MOA_KEYWORDS.items():
        if any(contains_norm_term(normalized_text, norm_text(term)) for term in terms):
            components.add(component)
    return components


def is_real_therapy(therapy_set: set[str]) -> bool:
    return not (
        therapy_set <= {"supportive_care_or_symptom_control"}
        or therapy_set <= {"radiation"}
    )


def load_atlas_rows(
    path: str | Path,
    *,
    excluded_raw_row_indices: set[int] | None = None,
) -> list[dict[str, Any]]:
    """Load the small subset of atlas columns needed for ORR priors."""

    atlas_rows: list[dict[str, Any]] = []
    excluded_raw_row_indices = excluded_raw_row_indices or set()
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw_idx, raw in enumerate(reader):
            if raw_idx in excluded_raw_row_indices:
                continue
            orr = finite_float(raw.get("model_orr_pct"))
            if not math.isfinite(orr) or orr < 0.0 or orr > 100.0:
                continue
            text_norm = norm_text(" | ".join(str(raw.get(col) or "") for col in ATLAS_TEXT_COLUMNS))
            therapy_set = therapy_families(raw.get("therapy_class"))
            if not is_real_therapy(therapy_set):
                continue
            weight = finite_float(raw.get("orr_denom"))
            atlas_rows.append(
                {
                    "atlas_raw_row_index": raw_idx,
                    "nct_id": raw.get("nct_id", ""),
                    "tissue_type": raw.get("tissue_type", ""),
                    "line_bucket": line_bucket(raw.get("line_of_therapy")),
                    "biomarker": str(raw.get("biomarker") or "").lower(),
                    "is_combination": str(raw.get("is_combination") or "").lower() == "true",
                    "model_orr_pct_source": raw.get("model_orr_pct_source") or "unknown",
                    "atlas_orr_pct": orr,
                    "atlas_weight": weight if math.isfinite(weight) and weight > 0 else 1.0,
                    "atlas_text_norm": text_norm,
                    "atlas_moa_set": infer_moa_components(text_norm),
                    "atlas_therapy_set": therapy_set,
                }
            )
    return atlas_rows


def load_target_rows(
    path: str | Path,
    *,
    surface_score_col: str | None = "default_score",
    orr_col: str = "orr_pct",
) -> list[dict[str, Any]]:
    rows = read_csv_rows(path)
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        observed = finite_float(row.get(orr_col))
        if not math.isfinite(observed):
            continue
        if surface_score_col and surface_score_col in row:
            score = finite_float(row.get(surface_score_col))
            if not math.isfinite(score):
                continue
        cohort = str(
            row.get("cohort") or row.get("disease") or row.get("benchmark_disease_key") or ""
        )
        drug = str(row.get("drug") or row.get("drug_surface") or "")
        drug_norm_clean = norm_drug(row.get("drug_norm") or row.get("drug_norm_surface") or drug)
        moa = str(row.get("moa_component") or row.get("current_default_moa_component") or "")
        out.append(
            {
                **row,
                "surface_pair_id": row.get("surface_pair_id")
                or f"{cohort}::{drug_norm_clean}::{idx}",
                "cohort": cohort,
                "drug": drug,
                "drug_norm_clean": drug_norm_clean,
                "moa_component": moa,
                "target_therapy_family": row.get("target_therapy_family")
                or MOA_TO_THERAPY_FAMILY.get(moa, ""),
                "observed_orr_pct": observed,
            }
        )
    return out


def summarize_subset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "prior_orr_pct": math.nan,
            "arm_mean_orr_pct": math.nan,
            "median_orr_pct": math.nan,
            "n_arms": 0,
            "n_trials": 0,
            "weight_sum": 0.0,
            "source_mix": "",
        }
    weights = [finite_float(row.get("atlas_weight"), 1.0) for row in rows]
    orrs = [finite_float(row.get("atlas_orr_pct")) for row in rows]
    weight_sum = sum(weights)
    sorted_orrs = sorted(orrs)
    mid = len(sorted_orrs) // 2
    median = (
        sorted_orrs[mid]
        if len(sorted_orrs) % 2
        else (sorted_orrs[mid - 1] + sorted_orrs[mid]) / 2.0
    )
    source_mix = Counter(str(row.get("model_orr_pct_source") or "unknown") for row in rows)
    return {
        "prior_orr_pct": sum(
            orr * weight for orr, weight in zip(orrs, weights, strict=True)
        )
        / weight_sum,
        "arm_mean_orr_pct": sum(orrs) / len(orrs),
        "median_orr_pct": median,
        "n_arms": len(rows),
        "n_trials": len({str(row.get("nct_id") or "") for row in rows}),
        "weight_sum": weight_sum,
        "source_mix": ";".join(f"{key}:{source_mix[key]}" for key in sorted(source_mix)),
    }


def atlas_row_mentions_target_drug(row: dict[str, Any], aliases: set[str]) -> bool:
    text = str(row.get("atlas_text_norm") or "")
    return any(contains_norm_term(text, alias) for alias in aliases)


def build_row_priors(
    atlas_rows: list[dict[str, Any]],
    target: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    disease = str(target.get("cohort") or "")
    target_moa = str(target.get("moa_component") or "")
    target_family = str(target.get("target_therapy_family") or "")
    tissues = DISEASE_TO_ATLAS_TISSUES.get(disease, set())
    aliases = target_aliases(target.get("drug"), target.get("drug_norm_clean"))
    eligible = [row for row in atlas_rows if not atlas_row_mentions_target_drug(row, aliases)]

    row_out: dict[str, Any] = {
        "excluded_exact_drug_atlas_arms": len(atlas_rows) - len(eligible),
        "target_atlas_tissues": ";".join(sorted(tissues)),
        "target_therapy_family": target_family,
    }
    support_rows: list[dict[str, Any]] = []

    def add_hierarchy(
        pool: list[dict[str, Any]],
        prefix: str,
        hierarchy_prefix: str,
        eligibility: str,
    ) -> None:
        def disease_match(row: dict[str, Any]) -> bool:
            return bool(tissues) and str(row.get("tissue_type") or "") in tissues

        def moa_match(row: dict[str, Any]) -> bool:
            return bool(target_moa) and target_moa in row.get("atlas_moa_set", set())

        def therapy_match(row: dict[str, Any]) -> bool:
            return bool(target_family) and target_family in row.get("atlas_therapy_set", set())

        cell_defs = [
            ("disease_moa", lambda row: disease_match(row) and moa_match(row), 3),
            (
                "disease_1l_moa",
                lambda row: disease_match(row) and moa_match(row) and row["line_bucket"] == "1L",
                3,
            ),
            (
                "disease_2l_plus_moa",
                lambda row: disease_match(row) and moa_match(row) and row["line_bucket"] == "2L+",
                3,
            ),
            ("disease_therapy", lambda row: disease_match(row) and therapy_match(row), 8),
            (
                "disease_1l_therapy",
                lambda row: disease_match(row)
                and therapy_match(row)
                and row["line_bucket"] == "1L",
                5,
            ),
            (
                "disease_2l_plus_therapy",
                lambda row: disease_match(row)
                and therapy_match(row)
                and row["line_bucket"] == "2L+",
                5,
            ),
            ("disease_baseline", disease_match, 15),
            ("global_moa", moa_match, 5),
            ("global_therapy", therapy_match, 25),
            ("global_baseline", lambda row: True, 25),
        ]
        summaries: dict[str, dict[str, Any]] = {}
        for cell_name, predicate, min_arms in cell_defs:
            subset = [atlas_row for atlas_row in pool if predicate(atlas_row)]
            summary = summarize_subset(subset)
            summaries[cell_name] = summary
            row_out[f"{prefix}_{cell_name}_orr"] = summary["prior_orr_pct"]
            row_out[f"{prefix}_{cell_name}_n_arms"] = summary["n_arms"]
            row_out[f"{prefix}_{cell_name}_n_trials"] = summary["n_trials"]
            row_out[f"{prefix}_{cell_name}_weight_sum"] = summary["weight_sum"]
            support_rows.append(
                {
                    "surface_pair_id": target.get("surface_pair_id"),
                    "cohort": disease,
                    "drug": target.get("drug"),
                    "drug_norm": target.get("drug_norm_clean"),
                    "moa_component": target_moa,
                    "eligibility": eligibility,
                    "cell_name": cell_name,
                    "min_arms_for_hierarchy": min_arms,
                    **summary,
                }
            )
        select_hierarchy(
            row_out,
            summaries,
            output_prefix=hierarchy_prefix,
            hierarchy=[
                ("disease_moa", 3),
                ("disease_therapy", 8),
                ("disease_baseline", 15),
                ("global_moa", 5),
                ("global_therapy", 25),
                ("global_baseline", 25),
            ],
        )
        select_hierarchy(
            row_out,
            summaries,
            output_prefix=f"{hierarchy_prefix}_therapy_first",
            hierarchy=[
                ("disease_therapy", 8),
                ("disease_baseline", 15),
                ("global_therapy", 25),
                ("global_moa", 5),
                ("global_baseline", 25),
            ],
        )

    add_hierarchy(eligible, "atlas_prior", "atlas_hierarchical_prior", "all_real_therapy")
    mono_allcomer = [
        row for row in eligible if not row["is_combination"] and row["biomarker"] != "yes"
    ]
    add_hierarchy(
        mono_allcomer,
        "atlas_mono_allcomer_prior",
        "atlas_mono_allcomer_hierarchical_prior",
        "non_combination_biomarker_no",
    )
    return row_out, support_rows


def select_hierarchy(
    row_out: dict[str, Any],
    summaries: dict[str, dict[str, Any]],
    *,
    output_prefix: str,
    hierarchy: list[tuple[str, int]],
) -> None:
    selected_name = ""
    selected = math.nan
    for cell_name, min_arms in hierarchy:
        summary = summaries[cell_name]
        prior = finite_float(summary["prior_orr_pct"])
        if summary["n_arms"] >= min_arms and math.isfinite(prior):
            selected_name = cell_name
            selected = prior
            break
    row_out[f"{output_prefix}_orr"] = selected
    row_out[f"{output_prefix}_source"] = selected_name
    row_out[f"{output_prefix}_n_arms"] = summaries.get(selected_name, {}).get("n_arms", 0)
    row_out[f"{output_prefix}_n_trials"] = summaries.get(selected_name, {}).get("n_trials", 0)
    row_out[f"{output_prefix}_weight_sum"] = summaries.get(selected_name, {}).get("weight_sum", 0.0)


def build_baseline_cells(
    atlas_rows: list[dict[str, Any]],
    eligibility: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for disease, tissues in DISEASE_TO_ATLAS_TISSUES.items():
        disease_rows = [row for row in atlas_rows if str(row.get("tissue_type") or "") in tissues]
        for line in ["1L", "2L+", "advanced_unspecified", "maintenance"]:
            for family in [
                "chemotherapy",
                "targeted_therapy",
                "immunotherapy_checkpoint",
                "endocrine_hormonal",
            ]:
                subset = [
                    row
                    for row in disease_rows
                    if row["line_bucket"] == line and family in row.get("atlas_therapy_set", set())
                ]
                rows.append(
                    {
                        "eligibility": eligibility,
                        "cohort": disease,
                        "line_bucket": line,
                        "therapy_family": family,
                        **summarize_subset(subset),
                    }
                )
    return sorted(rows, key=lambda row: (row["cohort"], row["line_bucket"], row["therapy_family"]))


def pairwise_within_disease_correlation(
    rows: list[dict[str, Any]],
    *,
    score_col: str,
    method: str,
) -> tuple[float, int]:
    pair_rows: list[dict[str, float]] = []
    for disease in sorted({str(row.get("cohort") or "") for row in rows}):
        group = [
            row
            for row in rows
            if str(row.get("cohort") or "") == disease
            and math.isfinite(finite_float(row.get(score_col)))
            and math.isfinite(finite_float(row.get("observed_orr_pct")))
        ]
        for left_idx, left in enumerate(group):
            for right in group[left_idx + 1 :]:
                pair_rows.append(
                    {
                        "score_delta": finite_float(left[score_col])
                        - finite_float(right[score_col]),
                        "orr_delta": finite_float(left["observed_orr_pct"])
                        - finite_float(right["observed_orr_pct"]),
                    }
                )
    corr = spearman if method == "spearman" else pearson
    return (
        corr(
            [row["score_delta"] for row in pair_rows],
            [row["orr_delta"] for row in pair_rows],
        ),
        len(pair_rows),
    )


def metric_row(
    rows: list[dict[str, Any]],
    *,
    score_col: str,
    label: str,
    is_orr_scale: bool = True,
) -> dict[str, Any]:
    scored = [
        row
        for row in rows
        if math.isfinite(finite_float(row.get(score_col)))
        and math.isfinite(finite_float(row.get("observed_orr_pct")))
    ]
    errors = [
        finite_float(row.get(score_col)) - finite_float(row.get("observed_orr_pct"))
        for row in scored
    ]
    pair_pearson, n_pairs = pairwise_within_disease_correlation(
        scored,
        score_col=score_col,
        method="pearson",
    )
    pair_spearman, _ = pairwise_within_disease_correlation(
        scored,
        score_col=score_col,
        method="spearman",
    )
    observed = [row["observed_orr_pct"] for row in scored]
    scores = [row[score_col] for row in scored]
    return {
        "label": label,
        "score_col": score_col,
        "n_rows": len(scored),
        "pearson": pearson(observed, scores),
        "spearman": spearman(observed, scores),
        "within_disease_pair_pearson": pair_pearson,
        "within_disease_pair_spearman": pair_spearman,
        "within_disease_pairs": n_pairs,
        "auc_above_disease_median": auc_above_group_median(
            scored,
            group_col="cohort",
            value_col="observed_orr_pct",
            score_col=score_col,
        ),
        "mae_orr_pct": (
            sum(abs(error) for error in errors) / len(errors)
            if is_orr_scale and errors
            else math.nan
        ),
        "rmse_orr_pct": (
            math.sqrt(sum(error * error for error in errors) / len(errors))
            if is_orr_scale and errors
            else math.nan
        ),
        "mean_prediction": (
            sum(finite_float(row[score_col]) for row in scored) / len(scored)
            if scored
            else math.nan
        ),
        "mean_observed_orr": (
            sum(finite_float(row["observed_orr_pct"]) for row in scored) / len(scored)
            if scored
            else math.nan
        ),
    }


def add_atlas_shrinkage_priors(
    predictions: list[dict[str, Any]],
    *,
    k_values: tuple[int, ...] = SHRINKAGE_K_VALUES,
) -> None:
    """Add support-shrunk all-comer monotherapy disease+therapy priors in-place."""

    for row in predictions:
        raw = finite_float(row.get("atlas_mono_allcomer_prior_disease_therapy_orr"))
        n_arms = finite_float(row.get("atlas_mono_allcomer_prior_disease_therapy_n_arms"), 0.0)
        global_therapy = finite_float(row.get("atlas_mono_allcomer_prior_global_therapy_orr"))
        legacy_primary = finite_float(row.get(LEGACY_PRIMARY_SCORE_COL))
        row["atlas_mono_disease_therapy_raw_or_primary"] = (
            raw if math.isfinite(raw) else legacy_primary
        )
        for k in k_values:
            if math.isfinite(raw) and math.isfinite(global_therapy):
                weight = max(0.0, n_arms) / (max(0.0, n_arms) + float(k))
                row[f"atlas_mono_disease_therapy_shrink_k{k}"] = (
                    weight * raw + (1.0 - weight) * global_therapy
                )
            else:
                row[f"atlas_mono_disease_therapy_shrink_k{k}"] = legacy_primary


def baseline_metrics(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        metric_row(
            predictions,
            score_col=PRIMARY_SCORE_COL,
            label=PRIMARY_SCORE_COL,
            is_orr_scale=True,
        )
    ]


def calculate_atlas_orr_baseline(
    *,
    atlas_csv: str | Path,
    cohort_predictions_csv: str | Path,
    surface_score_col: str | None = "default_score",
    excluded_raw_atlas_row_indices: set[int] | None = None,
) -> dict[str, Any]:
    excluded_raw_atlas_row_indices = excluded_raw_atlas_row_indices or set()
    atlas_rows = load_atlas_rows(
        atlas_csv,
        excluded_raw_row_indices=excluded_raw_atlas_row_indices,
    )
    target_rows = load_target_rows(cohort_predictions_csv, surface_score_col=surface_score_col)
    predictions: list[dict[str, Any]] = []
    support_cells: list[dict[str, Any]] = []
    for target in target_rows:
        row_priors, row_support = build_row_priors(atlas_rows, target)
        predictions.append({**target, **row_priors})
        support_cells.extend(row_support)
    add_atlas_shrinkage_priors(predictions)

    baseline_cells = build_baseline_cells(atlas_rows, "all_real_therapy")
    mono_allcomer_rows = [
        row for row in atlas_rows if not row["is_combination"] and row["biomarker"] != "yes"
    ]
    mono_baseline_cells = build_baseline_cells(
        mono_allcomer_rows,
        "non_combination_biomarker_no",
    )
    metrics = baseline_metrics(predictions)
    primary_metric = next(row for row in metrics if row["score_col"] == PRIMARY_SCORE_COL)
    source_counts = Counter(
        str(row.get("atlas_mono_allcomer_hierarchical_prior_therapy_first_source") or "")
        for row in predictions
    )
    summary = {
        "atlas_rows_with_model_orr_after_real_therapy_filter": len(atlas_rows),
        "excluded_raw_atlas_row_indices": sorted(excluded_raw_atlas_row_indices),
        "excluded_raw_atlas_row_count": len(excluded_raw_atlas_row_indices),
        "target_eval_rows": len(target_rows),
        "surface_score_col": surface_score_col or "",
        "primary_baseline": primary_metric,
        "primary_source_counts": dict(sorted(source_counts.items())),
        "methodology": {
            "endpoint": "model_orr_pct",
            "exact_drug_exclusion": (
                "atlas arms mentioning the target drug or alias are removed per target row"
            ),
            "primary_filter": "all-comer monotherapy: is_combination != true and biomarker != yes",
            "primary_formula": (
                "n/(n+8) * disease_therapy_ORR + 8/(n+8) * global_therapy_ORR; "
                "falls back to the predefined hierarchy when either cell is unavailable"
            ),
            "weighting": "weighted mean ORR by orr_denom when available; otherwise weight 1",
            "prediction_inputs_used": [
                "target disease/cohort key",
                "target therapy family derived from broad MOA",
                "historical Atlas model_orr_pct",
                "Atlas orr_denom weights when available",
                "Atlas tissue, therapy class, monotherapy flag, biomarker flag, "
                "line bucket, and arm text for filtering",
            ],
            "prediction_inputs_not_used": [
                "target observed ORR label",
                "Gaia score",
                "tumor biology or patient-level features",
                "exact target drug Atlas arms",
                "DepMap features",
                "fitted model over the target rows",
            ],
            "overfit_boundary": (
                "primary k=8 is fixed and not optimized on target labels; "
                "observed ORR is used only for evaluation metrics"
            ),
        },
    }
    return {
        "predictions": predictions,
        "support_cells": support_cells,
        "metrics": metrics,
        "baseline_cells": baseline_cells,
        "mono_allcomer_baseline_cells": mono_baseline_cells,
        "summary": summary,
    }


def write_atlas_orr_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    write_csv_rows(output / "atlas_orr_predictions.csv", result["predictions"])
    write_csv_rows(output / "atlas_orr_support_cells.csv", result["support_cells"])
    write_csv_rows(output / "atlas_orr_metrics.csv", result["metrics"])
    write_csv_rows(output / "atlas_orr_baseline_cells.csv", result["baseline_cells"])
    write_csv_rows(
        output / "atlas_orr_mono_allcomer_baseline_cells.csv",
        result["mono_allcomer_baseline_cells"],
    )
    write_json(output / "atlas_orr_summary.json", result["summary"])
    write_methodology_report(output / "atlas_orr_methodology.md", result)


def write_methodology_report(path: str | Path, result: dict[str, Any]) -> None:
    primary = result["summary"]["primary_baseline"]
    source_counts = result["summary"]["primary_source_counts"]
    excluded = result["summary"].get("excluded_raw_atlas_row_indices", [])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        "\n".join(
            [
                "# Atlas ORR Baseline Methodology",
                "",
                "This baseline estimates cohort-drug ORR from prior trial context in the atlas.",
                "It does not use the exact target drug as a predictive feature.",
                "",
                "## Primary Baseline",
                "",
                (
                    "The Atlas prior asks what similar trials have historically achieved. "
                    "It uses historical Atlas ORR by disease and therapy family, "
                    "excluding the exact target drug, with no tumor biology."
                ),
                "",
                "- Endpoint: atlas `model_orr_pct`.",
                (
                    "- Strict-release Atlas row exclusions: "
                    f"{', '.join(str(idx) for idx in excluded) if excluded else 'none'}."
                ),
                "- Exclusion: remove atlas arms whose text mentions the target drug or alias.",
                (
                    "- Eligibility: all-comer monotherapy atlas arms, defined as "
                    "`is_combination != true` and `biomarker != yes`."
                ),
                (
                    "- Score: support-shrunk disease + therapy-family ORR, "
                    "`n / (n + 8) * disease_therapy_ORR + 8 / (n + 8) * global_therapy_ORR`."
                ),
                (
                    "- Aggregation: weighted mean ORR using `orr_denom` when "
                    "available, otherwise weight 1."
                ),
                (
                    "- Fallback: use the predefined all-comer monotherapy therapy-first hierarchy "
                    "when either shrinkage cell is unavailable."
                ),
                "",
                "## Prediction Inputs",
                "",
                "Used:",
                "",
                "- Target disease/cohort key.",
                "- Target therapy family derived from broad MOA.",
                "- Historical Atlas `model_orr_pct`.",
                "- Atlas `orr_denom` weights when available.",
                (
                    "- Atlas tissue, therapy class, monotherapy flag, biomarker flag, "
                    "line bucket, and arm text for filtering."
                ),
                "",
                "Not used:",
                "",
                "- Target observed ORR label, except for post hoc evaluation metrics.",
                "- Gaia score.",
                "- Tumor biology or patient-level features.",
                "- Exact target drug Atlas arms.",
                "- DepMap features.",
                "- Any fitted model over the target rows.",
                "",
                "## Overfit Boundary",
                "",
                (
                    "- Primary `k=8` is fixed from the disease + therapy-family support "
                    "threshold; it is not selected by optimizing target labels."
                ),
                (
                    "- The Atlas prior is deterministic once Atlas and target disease/"
                    "therapy family are known."
                ),
                "- Observed ORR is used only after prediction to compute metrics.",
                "",
                "## Primary Metric",
                "",
                f"- Rows: {primary['n_rows']}",
                f"- Pearson: {primary['pearson']}",
                f"- Spearman: {primary['spearman']}",
                f"- AUC above disease median: {primary['auc_above_disease_median']}",
                f"- MAE ORR pct: {primary['mae_orr_pct']}",
                "",
                "## Primary Fallback Counts",
                "",
                *[f"- {key or 'missing'}: {value}" for key, value in sorted(source_counts.items())],
                "",
            ]
        ),
        encoding="utf-8",
    )
