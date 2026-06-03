# DepMap ORR Baseline

This repo includes a reproducible calculator for DepMap drug-sensitivity
baselines on cohort benchmark v2. The raw DepMap matrices are not checked into
this code repo; they are large external source artifacts.

## Source Inputs

- DepMap model metadata: `data/depmap/Model.csv`
- DepMap drug matrices: `data/depmap/drug/{GDSC2,GDSC1,REPURPOSING}AUCMatrix.csv`
- DepMap compound indexes: `data/depmap/drug/*CollapsedConditions.csv`
- Cohort v2 predictions CSV: `production/full_benchmark/cohort_benchmark_v2/predictions.csv`

## Primary Baseline

For each target cohort-drug row:

1. Match the disease to a DepMap `OncotreeLineage`.
2. Match the drug to a GDSC2, GDSC1, or PRISM compound using normalized names
   and a small salt/prodrug synonym table.
3. Read that compound's AUC column from the matched screen.
4. Rank-normalize AUC within the drug and screen. Lower AUC means greater
   sensitivity, so lower percentile rank means more sensitive.
5. Average percentile rank over matched-lineage cell lines.
6. Use `depmap_lineage_sensitivity_rank = 1 - lineage_rank` as the score, so
   higher means the lineage is more sensitive.

This is an intentionally simple external-data baseline. It uses drug identity
through DepMap sensitivity, unlike the Atlas prior, but it does not fit a model
to the 63 cohort labels.

## June 2026 Result

On the 63 ORR-scored cohort benchmark v2 rows, DepMap covered 55 rows. The
primary lineage-sensitivity-rank baseline reached:

- Pearson: -0.067
- Spearman: -0.062
- AUC above disease median: 0.475

The result is effectively null and slightly wrong-sign on this cohort-level
monotherapy surface. It is included as a useful negative baseline.

## Reproduce

From this repo:

```bash
open-benchmarks depmap-orr-baseline \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column default_score
```

Outputs:

- `depmap_v2_63_features.csv`
- `depmap_v2_63_metrics.csv`
- `depmap_v2_63_summary.json`
- `depmap_v2_63_methodology.md`
