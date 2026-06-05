#!/usr/bin/env python3
"""Regenerate benchmark-level summary CSVs from checked-in artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.benchmark_index import write_benchmark_summary_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=REPO_ROOT, type=Path)
    args = parser.parse_args()

    result = write_benchmark_summary_artifacts(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
