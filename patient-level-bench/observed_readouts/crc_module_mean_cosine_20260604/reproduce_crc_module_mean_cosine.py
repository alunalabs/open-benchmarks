#!/usr/bin/env python3
"""Recompute CRC module-mean cosine readout metrics from released vectors."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.reproduce import (  # noqa: E402
    raise_if_drift,
    reproduce_crc_module_mean_cosine,
)


def main() -> int:
    base = Path(__file__).resolve().parent
    report = reproduce_crc_module_mean_cosine(
        module_vectors_csv=base / "crc_module_mean_cosine_module_vectors.csv",
        patient_steps_csv=base / "crc_module_mean_cosine_patient_steps.csv",
        step_summary_csv=base / "crc_module_mean_cosine_step_summary.csv",
    )
    raise_if_drift(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
