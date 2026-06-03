#!/usr/bin/env python3
"""Export reviewed benchmark artifacts from the source monorepo."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from spatial_benchmarks.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["export-public-bundle", *sys.argv[1:]]))
