#!/usr/bin/env python3
"""Regenerate public formula-control artifacts from checked-in score tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spatial_benchmarks.formula_controls import (
    CONTROL_ITERATIONS,
    CONTROL_SEED,
    write_formula_control_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--iterations", default=CONTROL_ITERATIONS, type=int)
    parser.add_argument("--seed", default=CONTROL_SEED, type=int)
    args = parser.parse_args()

    result = write_formula_control_artifacts(
        root=args.root,
        n_iter=args.iterations,
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "cohort_dir": result["cohort_dir"],
                "patient_dir": result["patient_dir"],
                "iterations": args.iterations,
                "seed": args.seed,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
