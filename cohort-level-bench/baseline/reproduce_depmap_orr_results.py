#!/usr/bin/env python3
"""Recompute DepMap ORR metrics from the released DepMap feature CSV."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.reproduce import (  # noqa: E402
    raise_if_drift,
    reproduce_depmap_orr_features,
)


def main() -> int:
    base = Path(__file__).resolve().parent / "results"
    report = reproduce_depmap_orr_features(
        features_csv=base / "depmap_orr_features.csv",
        metrics_csv=base / "depmap_orr_metrics.csv",
    )
    raise_if_drift(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
