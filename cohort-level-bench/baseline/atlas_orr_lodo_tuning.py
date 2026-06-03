#!/usr/bin/env python3
"""Run leave-disease-out tuning for the cohort-level Atlas ORR baseline."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["atlas-orr-lodo-tuning", *sys.argv[1:]]))
