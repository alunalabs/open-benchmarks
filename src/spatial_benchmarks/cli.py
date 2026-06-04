"""Command-line entry points for benchmark inspection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .atlas_orr import (
    STRICT_RELEASE_EXCLUDED_ATLAS_ROW_INDICES,
    calculate_atlas_orr_baseline,
    write_atlas_orr_outputs,
)
from .atlas_ctgov_audit import audit_atlas_ctgov_support, write_atlas_ctgov_audit_outputs
from .depmap_orr import calculate_depmap_orr_baseline, write_depmap_orr_outputs
from .export import export_public_bundle
from .io import read_csv_rows
from .patient_crc import patient_metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="open-benchmarks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    atlas = subparsers.add_parser(
        "atlas-orr-baseline",
        help="Compute exact-drug-excluded Atlas ORR baselines for the strict cohort rows.",
    )
    atlas.add_argument("--atlas-csv", required=True, type=Path)
    atlas.add_argument("--cohort-predictions", required=True, type=Path)
    atlas.add_argument("--output-dir", required=True, type=Path)
    atlas.add_argument("--surface-score-column", default="default_score")
    atlas.add_argument(
        "--strict-release-cleaning",
        action="store_true",
        help=(
            "Drop the reviewed strict-release raw Atlas row indices. "
            "Use with the unfiltered raw Atlas CSV."
        ),
    )
    atlas.add_argument(
        "--exclude-raw-atlas-row-index",
        action="append",
        default=[],
        type=int,
        help="Additional zero-based raw Atlas CSV row index to exclude before scoring.",
    )

    atlas_audit = subparsers.add_parser(
        "atlas-orr-ctgov-audit",
        help="Audit Atlas ORR support rows against ClinicalTrials.gov outcomes.",
    )
    atlas_audit.add_argument("--atlas-csv", required=True, type=Path)
    atlas_audit.add_argument("--cohort-predictions", required=True, type=Path)
    atlas_audit.add_argument("--output-dir", required=True, type=Path)
    atlas_audit.add_argument("--surface-score-column", default="default_score")
    atlas_audit.add_argument("--cache-dir", default=None, type=Path)
    atlas_audit.add_argument("--sleep-seconds", default=0.0, type=float)

    depmap = subparsers.add_parser(
        "depmap-orr-baseline",
        help="Compute DepMap drug-sensitivity ORR baselines for the strict cohort rows.",
    )
    depmap.add_argument("--depmap-drug-dir", required=True, type=Path)
    depmap.add_argument("--model-csv", required=True, type=Path)
    depmap.add_argument("--cohort-predictions", required=True, type=Path)
    depmap.add_argument("--output-dir", required=True, type=Path)
    depmap.add_argument("--surface-score-column", default="default_score")

    patient = subparsers.add_parser(
        "patient-crc-metrics",
        help="Compute CRC-only patient benchmark metrics.",
    )
    patient.add_argument("--scores", required=True, type=Path)
    patient.add_argument("--score-column", default="relative_response_probability")
    patient.add_argument("--label-column", default="success_label")
    patient.add_argument("--threshold", default=0.5, type=float)

    export = subparsers.add_parser(
        "export-public-bundle",
        help="Export a conservative public artifact bundle.",
    )
    export.add_argument("--source-root", required=True, type=Path)
    export.add_argument("--output-root", required=True, type=Path)
    export.add_argument("--include-row-results", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "atlas-orr-baseline":
        excluded_indices = set(args.exclude_raw_atlas_row_index)
        if args.strict_release_cleaning:
            excluded_indices.update(STRICT_RELEASE_EXCLUDED_ATLAS_ROW_INDICES)
        result = calculate_atlas_orr_baseline(
            atlas_csv=args.atlas_csv,
            cohort_predictions_csv=args.cohort_predictions,
            surface_score_col=args.surface_score_column,
            excluded_raw_atlas_row_indices=excluded_indices,
        )
        write_atlas_orr_outputs(result, args.output_dir)
        result = result["summary"]
    elif args.command == "atlas-orr-ctgov-audit":
        result = audit_atlas_ctgov_support(
            atlas_csv=args.atlas_csv,
            cohort_predictions_csv=args.cohort_predictions,
            surface_score_col=args.surface_score_column,
            cache_dir=args.cache_dir,
            sleep_seconds=args.sleep_seconds,
        )
        write_atlas_ctgov_audit_outputs(result, args.output_dir)
        result = result["summary"]
    elif args.command == "depmap-orr-baseline":
        result = calculate_depmap_orr_baseline(
            depmap_drug_dir=args.depmap_drug_dir,
            model_csv=args.model_csv,
            cohort_predictions_csv=args.cohort_predictions,
            surface_score_col=args.surface_score_column,
        )
        write_depmap_orr_outputs(result, args.output_dir)
        result = result["summary"]
    elif args.command == "patient-crc-metrics":
        result = patient_metrics(
            read_csv_rows(args.scores),
            score_col=args.score_column,
            label_col=args.label_column,
            threshold=args.threshold,
        )
    elif args.command == "export-public-bundle":
        result = export_public_bundle(
            source_root=args.source_root,
            output_root=args.output_root,
            include_row_results=args.include_row_results,
        )
    else:
        parser.error(f"unhandled command: {args.command}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
