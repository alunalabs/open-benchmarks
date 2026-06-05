# Cohort Formula Controls

These controls are exact public controls for the released 44-row Gaia cohort
score table.

The public cohort artifact contains the final score
`gaia_predicted_orr_pct`, not the private per-patient axis/probability rows
used upstream to build it. Therefore these controls keep the released score and
the released metric path fixed, then corrupt score-to-label alignment.

Controls:

- `label_shuffle_global`: permutes observed ORR labels across all 44 cohort
  rows.
- `label_shuffle_within_disease`: permutes observed ORR labels only within each
  disease, preserving disease-specific ORR distributions.

Both controls recompute the same released metrics:

```text
Pearson r
Spearman rho
AUC above disease median
```

Headline results:

- Real Gaia 44 Pearson r: `0.650`
- Global label-shuffle Pearson null p95: `0.275`
- Within-disease label-shuffle Pearson null p95: `0.421`
- Real Gaia 44 Spearman rho: `0.594`
- Within-disease label-shuffle Spearman null p95: `0.379`
- Real Gaia 44 AUC above disease median: `0.752`
- Within-disease label-shuffle AUC null p95: `0.633`

Boundary:

- These are exact controls for the released public score/metric artifact.
- They are not hard-donor or gene-shuffle controls, because the released 44-row
  artifact does not include the private donor/gene-level inputs needed to
  recompute those controls.
- If we release per-patient cohort axis/probability rows later, the correct
  next control is to rerun the cohort formula after donor/context and
  gene-identity corruption.

Files:

- `cohort_formula_control_real_metrics.csv`: real 44-row Gaia metrics.
- `cohort_formula_control_metrics.csv`: per-iteration control metrics.
- `cohort_formula_control_summary.csv`: null summaries and empirical p-values.
