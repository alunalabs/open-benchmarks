# Atlas ORR Strict Release Recalculation

This recalculation removes reviewed Atlas support-arm issues from the raw Atlas
source pool, then reruns the same exact-drug-excluded fixed `k=8` Atlas ORR
prior on the 63 cohort benchmark v2 ORR rows.

Removed rows:

- 3 `ctgov_value_mismatch` support rows.
- 8 `ctgov_no_matching_orr_measurement` support rows.
- 2 CTGov-verified endpoint caveat rows that are not strict CR/PR ORR.

This leaves 189 audited support rows represented in the strict release support
pool. The large filtered Atlas CSV used for local regeneration was generated
under `artifacts/` and is intentionally not checked in.

## Primary Fixed k=8 Result

| Run | Pearson | Spearman | AUC above disease median | MAE ORR pct | RMSE ORR pct |
| --- | ---: | ---: | ---: | ---: | ---: |
| Strict release fixed `k=8` | 0.409 | 0.464 | 0.742 | 11.586 | 13.193 |

This is the public Atlas ORR baseline score for the release.

## LODO Sensitivity

Leave-disease-out Spearman-tuned shrinkage on the strict Atlas pool reached:

- Pearson: 0.292
- Spearman: 0.419
- AUC above disease median: 0.696
- MAE ORR pct: 12.572

This is an anti-overfit sensitivity check, not the primary release baseline.
The primary baseline remains fixed `k=8`, with no tuning on the 63 target
labels.

## Reproduce

The strict release run drops raw Atlas row indices:

```text
582, 1519, 2448, 2568, 3862, 4782, 9268, 10228, 11729, 12033, 14965, 14966, 17451
```

Run from the repo root with the unfiltered raw Atlas CSV:

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_strict_release/baseline \
  --surface-score-column default_score \
  --strict-release-cleaning
```

