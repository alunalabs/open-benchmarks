#!/usr/bin/env python3
"""Recompute cSCC checkpoint-compartment metrics from the released CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.reproduce import (  # noqa: E402
    raise_if_drift,
    reproduce_cscc_checkpoint_compartment,
)


def main() -> int:
    base = Path(__file__).resolve().parent
    report = reproduce_cscc_checkpoint_compartment(
        scores_csv=base / "cscc_checkpoint_compartment_patient_scores_20260604.csv",
        metrics_csv=base / "cscc_checkpoint_compartment_metrics_20260604.csv",
    )
    raise_if_drift(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
