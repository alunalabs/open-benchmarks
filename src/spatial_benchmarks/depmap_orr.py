"""DepMap drug-sensitivity baselines for the strict 44-row cohort benchmark."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .atlas_orr import load_target_rows, metric_row
from .io import write_csv_rows, write_json
from .metrics import finite_float


DISEASE_TO_DEPMAP_LINEAGE = {
    "breast": "Breast",
    "crc": "Bowel",
    "gastric": "Esophagus/Stomach",
    "hnscc": "Head and Neck",
    "nsclc": "Lung",
    "ovarian": "Ovary/Fallopian Tube",
    "pdac": "Pancreas",
    "prostate": "Prostate",
    "rcc": "Kidney",
}

SCREEN_FILES = {
    "GDSC2": (
        "GDSC2Log2ViabilityCollapsedConditions.csv",
        "GDSC2AUCMatrix.csv",
    ),
    "GDSC1": (
        "GDSC1Log2ViabilityCollapsedConditions.csv",
        "GDSC1AUCMatrix.csv",
    ),
    "PRISM": (
        "REPURPOSINGLog2ViabilityCollapsedConditions.csv",
        "REPURPOSINGAUCMatrix.csv",
    ),
}

SYNONYMS = {
    "5-fluorouracil": "fluorouracil",
    "5-fu": "fluorouracil",
    "gemcitabine hydrochloride": "gemcitabine",
    "erlotinib hydrochloride": "erlotinib",
    "nab-paclitaxel": "paclitaxel",
    "doxorubicin hcl liposome": "doxorubicin",
    "doxorubicin (hydrochloride)": "doxorubicin",
    "trifluridine/tipiracil": "trifluridine",
}

PRIMARY_DEPMAP_SCORE_COL = "depmap_lineage_sensitivity_rank"
PUBLIC_DEPMAP_FEATURE_COLUMNS = (
    "surface_pair_id",
    "benchmark_row_id",
    "cohort",
    "disease",
    "drug",
    "drug_norm_clean",
    "moa_component",
    "target_therapy_family",
    "observed_orr_pct",
    "depmap_lineage",
    "depmap_screen",
    "depmap_compound_id",
    "depmap_lineage_n",
    "depmap_abs_lineage_auc",
    "depmap_abs_global_auc",
    "depmap_lineage_rank",
    "depmap_lineage_sensitivity_rank",
    "depmap_lineage_auc_sensitivity",
    "depmap_global_auc_sensitivity",
)


def norm(value: Any) -> str:
    """Normalize drug strings the same way as the source DepMap experiment."""

    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def load_compound_index(depmap_drug_dir: str | Path) -> dict[str, tuple[str, str]]:
    """Return norm(CompoundName) -> (screen, CompoundID), preferring GDSC2 then GDSC1."""

    drug_dir = Path(depmap_drug_dir)
    index: dict[str, tuple[str, str]] = {}
    for screen, (condition_file, _) in SCREEN_FILES.items():
        path = drug_dir / condition_file
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = row.get("CompoundName")
                compound_id = row.get("CompoundID")
                if name and compound_id:
                    index.setdefault(norm(name), (screen, str(compound_id)))
    return index


def load_model_lineages(model_csv: str | Path) -> dict[str, str]:
    with Path(model_csv).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {
            str(row.get("ModelID") or ""): str(row.get("OncotreeLineage") or "")
            for row in reader
            if row.get("ModelID") and row.get("OncotreeLineage")
        }


def read_auc_column(matrix_csv: str | Path, compound_id: str) -> dict[str, float]:
    """Read one compound AUC column from a DepMap matrix."""

    path = Path(matrix_csv)
    if not path.exists():
        return {}
    values: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or compound_id not in reader.fieldnames:
            return {}
        id_column = reader.fieldnames[0]
        for row in reader:
            model_id = str(row.get(id_column) or row.get("ModelID") or "")
            value = finite_float(row.get(compound_id))
            if model_id and math.isfinite(value):
                values[model_id] = value
    return values


def percentile_ranks(values_by_model: dict[str, float]) -> dict[str, float]:
    """Average percentile ranks, matching pandas `rank(pct=True)` for finite values."""

    items = sorted(values_by_model.items(), key=lambda item: item[1])
    ranks: dict[str, float] = {}
    start = 0
    n_items = len(items)
    while start < n_items:
        end = start
        while end + 1 < n_items and items[end + 1][1] == items[start][1]:
            end += 1
        rank = (start + 1 + end + 1) / 2.0 / n_items
        for idx in range(start, end + 1):
            ranks[items[idx][0]] = rank
        start = end + 1
    return ranks


def mean(values: list[float], *, min_count: int) -> float:
    clean = [value for value in values if math.isfinite(value)]
    return sum(clean) / len(clean) if len(clean) >= min_count else math.nan


def drug_candidates(row: dict[str, Any]) -> list[str]:
    candidates = [
        row.get("drug_norm_surface"),
        row.get("drug_norm"),
        row.get("drug_norm_clean"),
        row.get("drug"),
    ]
    out: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def resolve_compound(
    row: dict[str, Any],
    compound_index: dict[str, tuple[str, str]],
) -> tuple[str, str] | None:
    for candidate in drug_candidates(row):
        canonical = SYNONYMS.get(candidate.lower(), candidate)
        hit = compound_index.get(norm(canonical))
        if hit:
            return hit
    return None


def build_lineage_index(model_lineages: dict[str, str]) -> dict[str, list[str]]:
    lineages: dict[str, list[str]] = {}
    for model_id, lineage in model_lineages.items():
        lineages.setdefault(lineage, []).append(model_id)
    return lineages


def build_depmap_features(
    target_rows: list[dict[str, Any]],
    *,
    depmap_drug_dir: str | Path,
    model_csv: str | Path,
    min_rank_lines: int = 10,
    min_lineage_lines: int = 2,
    min_global_lines: int = 5,
) -> list[dict[str, Any]]:
    compound_index = load_compound_index(depmap_drug_dir)
    model_lineages = load_model_lineages(model_csv)
    lineage_index = build_lineage_index(model_lineages)
    column_cache: dict[tuple[str, str], dict[str, float]] = {}
    rank_cache: dict[tuple[str, str], dict[str, float]] = {}

    def values_for(screen: str, compound_id: str) -> dict[str, float]:
        key = (screen, compound_id)
        if key not in column_cache:
            _, matrix_file = SCREEN_FILES[screen]
            column_cache[key] = read_auc_column(Path(depmap_drug_dir) / matrix_file, compound_id)
        return column_cache[key]

    def ranks_for(screen: str, compound_id: str) -> dict[str, float]:
        key = (screen, compound_id)
        if key not in rank_cache:
            values = values_for(screen, compound_id)
            rank_cache[key] = percentile_ranks(values) if len(values) >= min_rank_lines else {}
        return rank_cache[key]

    feature_rows: list[dict[str, Any]] = []
    all_model_ids = set(model_lineages)
    for row in target_rows:
        disease = str(row.get("cohort") or row.get("disease") or "")
        lineage = DISEASE_TO_DEPMAP_LINEAGE.get(disease, "")
        lineage_models = lineage_index.get(lineage, [])
        hit = resolve_compound(row, compound_index)

        base = {
            **row,
            "depmap_lineage": lineage,
            "depmap_screen": "",
            "depmap_compound_id": "",
            "depmap_lineage_n": 0,
            "depmap_abs_lineage_auc": math.nan,
            "depmap_abs_global_auc": math.nan,
            "depmap_lineage_rank": math.nan,
            "depmap_lineage_sensitivity_rank": math.nan,
            "depmap_lineage_auc_sensitivity": math.nan,
            "depmap_global_auc_sensitivity": math.nan,
        }
        if not lineage or hit is None:
            feature_rows.append(base)
            continue

        screen, compound_id = hit
        values = values_for(screen, compound_id)
        ranks = ranks_for(screen, compound_id)
        lineage_auc_values = [values[model_id] for model_id in lineage_models if model_id in values]
        global_auc_values = [values[model_id] for model_id in all_model_ids if model_id in values]
        lineage_rank_values = [ranks[model_id] for model_id in lineage_models if model_id in ranks]

        lineage_auc = mean(lineage_auc_values, min_count=min_lineage_lines)
        global_auc = mean(global_auc_values, min_count=min_global_lines)
        lineage_rank = mean(lineage_rank_values, min_count=min_lineage_lines)

        base.update(
            {
                "depmap_screen": screen,
                "depmap_compound_id": compound_id,
                "depmap_lineage_n": len(lineage_rank_values),
                "depmap_abs_lineage_auc": lineage_auc,
                "depmap_abs_global_auc": global_auc,
                "depmap_lineage_rank": lineage_rank,
                "depmap_lineage_sensitivity_rank": (
                    1.0 - lineage_rank if math.isfinite(lineage_rank) else math.nan
                ),
                "depmap_lineage_auc_sensitivity": (
                    -lineage_auc if math.isfinite(lineage_auc) else math.nan
                ),
                "depmap_global_auc_sensitivity": (
                    -global_auc if math.isfinite(global_auc) else math.nan
                ),
            }
        )
        feature_rows.append(base)
    return feature_rows


def depmap_metrics(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    score_specs = [
        (
            "depmap_lineage_sensitivity_rank",
            "depmap_lineage_sensitivity_rank",
        ),
        (
            "depmap_lineage_auc_sensitivity",
            "depmap_lineage_auc_sensitivity",
        ),
        (
            "depmap_global_auc_sensitivity",
            "depmap_global_auc_sensitivity",
        ),
    ]
    return [
        metric_row(features, score_col=score_col, label=label, is_orr_scale=False)
        for score_col, label in score_specs
    ]


def calculate_depmap_orr_baseline(
    *,
    depmap_drug_dir: str | Path,
    model_csv: str | Path,
    cohort_predictions_csv: str | Path,
    surface_score_col: str | None = "default_score",
    min_rank_lines: int = 10,
    min_lineage_lines: int = 2,
    min_global_lines: int = 5,
) -> dict[str, Any]:
    target_rows = load_target_rows(cohort_predictions_csv, surface_score_col=surface_score_col)
    features = build_depmap_features(
        target_rows,
        depmap_drug_dir=depmap_drug_dir,
        model_csv=model_csv,
        min_rank_lines=min_rank_lines,
        min_lineage_lines=min_lineage_lines,
        min_global_lines=min_global_lines,
    )
    metrics = depmap_metrics(features)
    primary_metric = next(row for row in metrics if row["score_col"] == PRIMARY_DEPMAP_SCORE_COL)
    covered = [
        row for row in features if math.isfinite(finite_float(row.get(PRIMARY_DEPMAP_SCORE_COL)))
    ]
    summary = {
        "target_eval_rows": len(target_rows),
        "depmap_covered_rows": len(covered),
        "surface_score_col": surface_score_col or "",
        "primary_baseline": primary_metric,
        "screen_counts": dict(
            sorted(Counter(str(row.get("depmap_screen") or "") for row in covered).items())
        ),
        "methodology": {
            "endpoint": "DepMap GDSC/PRISM AUC matrix",
            "orientation": "higher depmap_lineage_sensitivity_rank means more lineage-sensitive",
            "rank_normalization": "per-drug percentile rank of AUC within screen",
            "lineage_score": "1 - mean percentile AUC rank over matched lineage cell lines",
            "min_rank_lines": min_rank_lines,
            "min_lineage_lines": min_lineage_lines,
            "min_global_lines": min_global_lines,
        },
    }
    return {"features": features, "metrics": metrics, "summary": summary}


def write_depmap_orr_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    output = Path(output_dir)
    public_features = [
        {column: row.get(column, "") for column in PUBLIC_DEPMAP_FEATURE_COLUMNS}
        for row in result["features"]
    ]
    write_csv_rows(output / "depmap_orr_features.csv", public_features)
    write_csv_rows(output / "depmap_orr_metrics.csv", result["metrics"])
    write_json(output / "depmap_orr_summary.json", result["summary"])
    write_methodology_report(output / "depmap_orr_methodology.md", result)


def write_methodology_report(path: str | Path, result: dict[str, Any]) -> None:
    primary = result["summary"]["primary_baseline"]
    screen_counts = result["summary"]["screen_counts"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        "\n".join(
            [
                "# DepMap ORR Baseline Methodology",
                "",
                "This baseline estimates cohort-drug ORR from DepMap drug-sensitivity screens.",
                "It uses the target drug but not trial outcomes beyond the evaluation labels.",
                "",
                "## Primary Baseline",
                "",
                "- Inputs: GDSC1, GDSC2, and PRISM AUC matrices plus `Model.csv` lineages.",
                "- Drug matching: normalized compound name with a small salt/prodrug synonym map.",
                "- Disease matching: cohort disease is mapped to DepMap `OncotreeLineage`.",
                (
                    "- Score: `1 - mean(percentile_rank(AUC))` over matched-lineage cell lines; "
                    "higher means more sensitive."
                ),
                "",
                "## Primary Metric",
                "",
                f"- Rows covered: {primary['n_rows']}",
                f"- Pearson: {primary['pearson']}",
                f"- Spearman: {primary['spearman']}",
                f"- AUC above disease median: {primary['auc_above_disease_median']}",
                "",
                "## Covered Screen Counts",
                "",
                *[f"- {key}: {value}" for key, value in sorted(screen_counts.items())],
                "",
            ]
        ),
        encoding="utf-8",
    )
