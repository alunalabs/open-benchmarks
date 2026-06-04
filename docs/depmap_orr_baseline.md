# DepMap ORR Baseline

This repo includes a reproducible calculator for DepMap drug-sensitivity
baselines on the 44-row strict cohort benchmark. The raw DepMap matrices are
external source artifacts and are not checked into this repository.

## Source Inputs

- DepMap model metadata: `data/depmap/Model.csv`
- DepMap drug matrices: `data/depmap/drug/{GDSC2,GDSC1,REPURPOSING}AUCMatrix.csv`
- DepMap compound indexes: `data/depmap/drug/*CollapsedConditions.csv`
- Target rows: `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`

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

This is an external-data baseline. It uses drug identity through DepMap
sensitivity, but it does not fit a model to ORR labels.

## Released Result

On the 44 strict ORR rows, DepMap covered 40 rows. The primary
lineage-sensitivity-rank baseline reached:

- Pearson r: `-0.014`
- Spearman rho: `-0.044`
- AUC above disease median: `0.474`

The result is effectively null on this cohort-level ORR surface. It is included
as a negative baseline on the same target rows as Gaia and Atlas.

## Reproduce

```bash
python cohort-level-bench/baseline/depmap_orr_baseline.py \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct
```

Outputs:

- `depmap_orr_features.csv`
- `depmap_orr_metrics.csv`
- `depmap_orr_summary.json`
- `depmap_orr_methodology.md`
