"""Conservative artifact exporter from the source monorepo."""

from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

from .io import read_csv_rows, read_json, sha256_file, write_csv_rows, write_json
from .patient_crc import filter_crc_rows

COHORT_SAFE_FILES = (
    "README.md",
    "manifest.json",
    "policy.json",
    "metrics.csv",
    "by_disease_metrics.csv",
    "gene_shuffle_summary.csv",
    "hard_donor_summary.csv",
    "susceptibility_policy.json",
)

COHORT_CLINICAL_COLUMNS = (
    "surface_pair_id",
    "cohort_surface",
    "drug_surface",
    "drug_norm_surface",
    "orr_pct",
    "patient_denominator",
    "label_source",
    "label_priority",
    "label_scope",
    "orr_missing",
    "benchmark_disease_key",
    "current_default_moa_component",
    "default_score_column",
    "cohort",
    "drug",
    "drug_norm",
    "moa_component",
    "n_enrolled",
    "n_patients_scored",
)

COHORT_ROW_RESULT_FILES = (
    "predictions.csv",
    "patient_probabilities.csv",
)

PATIENT_SAFE_FILES = (
    "universal_patient_response_axes_policy_20260525.json",
    "universal_patient_response_axes_metrics_20260525.csv",
    "crc_patient_moa_tailored_calibrated_response_distribution_policy_20260525.json",
    "crc_patient_moa_tailored_calibrated_response_distribution_metrics_20260525.csv",
    "crc_patient_moa_tailored_response_distribution_policy_20260525.json",
    "crc_patient_moa_tailored_response_distribution_metrics_20260525.csv",
    "crc_patient_cell_level_heterogeneity_adapter_policy_20260525.json",
    "crc_patient_cell_level_heterogeneity_adapter_metrics_20260525.csv",
    "crc_moa_delta_risk_probability_summary_20260516.csv",
    "crc_moa_delta_risk_reason_summary_20260516.csv",
)

PATIENT_UNIVERSAL_CLINICAL_COLUMNS = (
    "benchmark_level",
    "benchmark_id",
    "benchmark_slice",
    "cohort",
    "analysis_unit",
    "item_id",
    "success_label",
    "protocol",
    "therapy_context",
    "score_policy",
    "primary_warning_family",
    "axis_contract_version",
    "axis_policy",
    "axis_notes",
)

PATIENT_CRC_CLINICAL_COLUMNS = (
    "source_sample_id",
    "source_patient_id",
    "regimen",
    "clinical_outcome",
    "observed_responder",
    "observed_non_responder",
    "moa_component",
    "selected_variant",
    "selection_source",
)

PATIENT_CRC_ROW_FILES = (
    "universal_patient_response_axes_scores_20260525.csv",
    "crc_patient_moa_tailored_calibrated_response_distribution_scores_20260525.csv",
    "crc_patient_moa_tailored_response_distribution_scores_20260525.csv",
    "crc_moa_delta_risk_probability_primary_calls_20260516.csv",
    "crc_patient_level_primary_calls_compact.csv",
)


def export_public_bundle(
    *,
    source_root: str | Path,
    output_root: str | Path,
    include_row_results: bool = False,
) -> dict[str, Any]:
    """Copy a reviewed benchmark bundle from `spatial-fun`.

    By default this excludes row-level prediction and patient-score tables.
    When `include_row_results` is enabled, patient tables are filtered to CRC.
    """

    source = Path(source_root)
    output = Path(output_root)
    manifest: dict[str, Any] = {
        "source_root": str(source),
        "include_row_results": include_row_results,
        "artifacts": {},
        "notes": [
            "Default export excludes raw data, per-cell caches, model checkpoints, "
            "Modal/S3 runtime code, and generated figures.",
            "Full CRC patient score row files are filtered to CRC rows only when "
            "include_row_results is enabled.",
        ],
    }

    cohort_files = [*COHORT_SAFE_FILES, *(COHORT_ROW_RESULT_FILES if include_row_results else ())]
    export_group(
        source / "production/full_benchmark/cohort_benchmark_v2",
        output / "cohort_benchmark_v2",
        cohort_files,
        manifest=manifest,
        group="cohort_benchmark_v2",
    )
    export_cohort_clinical_rows(
        source / "production/full_benchmark/cohort_benchmark_v2",
        output / "cohort_benchmark_v2/clinical_rows",
        manifest=manifest,
    )
    export_group(
        source / "production/full_benchmark/patient_level",
        output / "patient_crc",
        PATIENT_SAFE_FILES,
        manifest=manifest,
        group="patient_crc",
    )
    export_patient_clinical_rows(
        source / "production/full_benchmark/patient_level",
        output / "patient_crc/clinical_rows",
        manifest=manifest,
    )
    if include_row_results:
        export_crc_patient_rows(
            source / "production/full_benchmark/patient_level",
            output / "patient_crc",
            manifest=manifest,
        )

    write_json(output / "export_manifest.json", manifest)
    write_data_policy(output / "DATA_POLICY.md", include_row_results=include_row_results)
    return manifest


def export_group(
    source_dir: Path,
    output_dir: Path,
    names: tuple[str, ...] | list[str],
    *,
    manifest: dict[str, Any],
    group: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    group_manifest: dict[str, Any] = {}
    for name in names:
        source_path = source_dir / name
        if not source_path.exists():
            continue
        output_path = output_dir / name
        shutil.copy2(source_path, output_path)
        group_manifest[name] = artifact_record(output_path, source_path)
    manifest["artifacts"][group] = group_manifest


def export_crc_patient_rows(
    source_dir: Path,
    output_dir: Path,
    *,
    manifest: dict[str, Any],
) -> None:
    group_manifest = manifest["artifacts"].setdefault("patient_crc", {})
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in PATIENT_CRC_ROW_FILES:
        source_path = source_dir / name
        if not source_path.exists():
            continue
        rows = filter_crc_rows(read_csv_rows(source_path))
        output_path = output_dir / name
        write_csv_rows(output_path, rows)
        group_manifest[name] = artifact_record(output_path, source_path)
        group_manifest[name]["crc_rows"] = len(rows)


def export_patient_clinical_rows(
    source_dir: Path,
    output_dir: Path,
    *,
    manifest: dict[str, Any],
) -> None:
    group_manifest = manifest["artifacts"].setdefault("patient_crc_clinical_rows", {})
    output_dir.mkdir(parents=True, exist_ok=True)

    universal_source = source_dir / "universal_patient_response_axes_scores_20260525.csv"
    if universal_source.exists():
        rows = select_columns(read_csv_rows(universal_source), PATIENT_UNIVERSAL_CLINICAL_COLUMNS)
        output_path = output_dir / "universal_patient_response_axes_clinical_rows_20260525.csv"
        write_csv_rows(output_path, rows, fieldnames=PATIENT_UNIVERSAL_CLINICAL_COLUMNS)
        group_manifest[output_path.name] = artifact_record(output_path, universal_source)
        group_manifest[output_path.name]["rows"] = len(rows)

    crc_source = (
        source_dir
        / "crc_patient_moa_tailored_calibrated_response_distribution_scores_20260525.csv"
    )
    if crc_source.exists():
        rows = select_columns(read_csv_rows(crc_source), PATIENT_CRC_CLINICAL_COLUMNS)
        output_path = output_dir / "crc_patient_clinical_rows_20260525.csv"
        write_csv_rows(output_path, rows, fieldnames=PATIENT_CRC_CLINICAL_COLUMNS)
        group_manifest[output_path.name] = artifact_record(output_path, crc_source)
        group_manifest[output_path.name]["rows"] = len(rows)


def export_cohort_clinical_rows(
    source_dir: Path,
    output_dir: Path,
    *,
    manifest: dict[str, Any],
) -> None:
    source_path = source_dir / "predictions.csv"
    if not source_path.exists():
        return

    group_manifest = manifest["artifacts"].setdefault("cohort_benchmark_v2_clinical_rows", {})
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rows = read_csv_rows(source_path)
    row_sets = {
        "cohort_benchmark_v2_clinical_rows.csv": source_rows,
        "cohort_benchmark_v2_orr_labeled_clinical_rows.csv": [
            row for row in source_rows if is_finite(row.get("orr_pct"))
        ],
        "cohort_benchmark_v2_eval_clinical_rows.csv": [
            row
            for row in source_rows
            if is_finite(row.get("orr_pct"))
            and is_finite(row.get(str(row.get("default_score_column") or "default_score")))
        ],
    }
    for name, rows in row_sets.items():
        selected = select_columns(rows, COHORT_CLINICAL_COLUMNS)
        output_path = output_dir / name
        write_csv_rows(output_path, selected, fieldnames=COHORT_CLINICAL_COLUMNS)
        group_manifest[name] = artifact_record(output_path, source_path)
        group_manifest[name]["rows"] = len(selected)


def select_columns(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{column: row.get(column, "") for column in columns} for row in rows]


def is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def artifact_record(output_path: Path, source_path: Path) -> dict[str, Any]:
    return {
        "path": str(output_path),
        "source_path": str(source_path),
        "bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
    }


def write_data_policy(path: Path, *, include_row_results: bool) -> None:
    status = (
        "includes reviewed row-level results"
        if include_row_results
        else "definitions and aggregate metrics only"
    )
    path.write_text(
        "\n".join(
            [
                "# Data Policy",
                "",
                f"This artifact bundle status: **{status}**.",
                "",
                "The code repository should not include raw spatial data, model checkpoints, "
                "per-cell caches, or private runtime paths.",
                "Patient-level row results require separate approval before publication, "
                "even when de-identified.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def load_export_manifest(path: str | Path) -> dict[str, Any]:
    return read_json(path)
