# Reproducibility Notebooks

These notebooks recompute public benchmark metrics and regenerate the release
figures from checked-in artifacts. The benchmark math is written directly in
the notebooks so readers can inspect how each score and metric is computed.

They are intentionally lightweight:

- Public model-score artifacts are the checked-in CSVs under
  `patient-level-bench/` and `cohort-level-bench/`.
- Raw spatial data, private checkpoints, per-cell inference outputs, raw Atlas
  tables, and raw DepMap matrices are external source artifacts.
- The notebooks reproduce the published scores from released rows and score
  columns by explicitly computing the metrics and score formulas in notebook
  cells.
- They write generated SVG figures to `artifacts/notebook_figures/`.
- Atlas and DepMap source-data regeneration remains available through the
  baseline scripts under `cohort-level-bench/baseline/`.

Run from the repository root after installing the package:

```bash
python -m pip install -e ".[dev]"
jupyter lab notebooks/
```

Notebook index:

- `01_cohort_benchmarks.ipynb`: Gaia cohort ORR, Atlas fixed-k baseline, and
  DepMap baseline numbers, the negative marker-cache hard-donor/gene-shuffle
  audit, and cohort-level figures.
- `02_patient_benchmarks.ipynb`: CRC rank score, cSCC checkpoint compartment
  score, and CRC module mean cosine numbers plus patient-level figures.
