# Gaia Cohort Model Scores

This folder contains the public cohort-level Gaia score artifacts for the
44-row strict ORR benchmark.

See `docs/methodology.md` for row construction and metric definitions.

## Included

- [gaia_44_strict_orr_model_scores.csv](gaia_44_strict_orr_model_scores.csv):
  one row per strict observed ORR
  cohort-drug pair, with observed ORR and Gaia predicted ORR percentage.
- [gaia_metrics.csv](gaia_metrics.csv): global metrics for `gaia_predicted_orr_pct`.
- [gaia_by_disease_metrics.csv](gaia_by_disease_metrics.csv): by-disease metrics for
  `gaia_predicted_orr_pct`.
- [gaia_model_score_summary.json](gaia_model_score_summary.json): machine-readable summary of the public
  score and calculation boundary.
- [reproduce_gaia_metrics.py](reproduce_gaia_metrics.py): recompute the public
  global and by-disease metrics from the released score CSV.
- [MANIFEST.json](MANIFEST.json): checksums for this folder.

## Public Score

The public score column is `gaia_predicted_orr_pct`.

It is evaluated directly against `orr_pct`:

- Rows: `44`
- Pearson r: `0.650`
- Spearman rho: `0.594`
- Mean absolute ORR gap: `10.2` percentage points
- AUC above disease median: `0.752`

The table also includes `default_score`, `expected_response_pct`, and
`expected_orr_pct` as continuity aliases for `gaia_predicted_orr_pct`.

## Scope Boundary

This folder links only the strict 44-row public cohort score table and its
summary metrics. Full production prediction tables, patient-probability tables,
and internal model audit logs are not included.

The public model artifact in this folder is the score CSV. Gaia checkpoint
weights and per-cell inference outputs are external to this release.

## Reproduce

```bash
python cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py
```
