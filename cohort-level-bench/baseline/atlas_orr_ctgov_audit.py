#!/usr/bin/env python3
"""Audit Atlas ORR support rows against ClinicalTrials.gov."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["atlas-orr-ctgov-audit", *sys.argv[1:]]))
