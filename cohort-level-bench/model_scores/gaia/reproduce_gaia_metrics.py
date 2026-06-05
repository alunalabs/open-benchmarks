#!/usr/bin/env python3
"""Recompute Gaia strict-44 cohort ORR metrics from the released score CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.reproduce import (  # noqa: E402
    raise_if_drift,
    reproduce_gaia_cohort_orr,
)


def main() -> int:
    base = Path(__file__).resolve().parent
    report = reproduce_gaia_cohort_orr(
        scores_csv=base / "gaia_44_strict_orr_model_scores.csv",
        metrics_csv=base / "gaia_metrics.csv",
        by_disease_csv=base / "gaia_by_disease_metrics.csv",
    )
    raise_if_drift(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
