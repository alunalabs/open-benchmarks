# Atlas ORR Leave-Disease-Out Tuning

This is an anti-overfit sensitivity check for the Atlas shrinkage prior.
It is not the primary release baseline.

## Procedure

- Start from exact-drug-excluded Atlas shrinkage scores for each fixed `k`.
- Hold out one disease/cohort at a time.
- Select `k` using only all non-held-out diseases.
- Apply the selected `k` to every row in the held-out disease.
- Concatenate held-out predictions across diseases and evaluate once.

## Label Boundary

- Observed ORR is used in training diseases to choose `k`, but never in the held-out disease being predicted.
- No tumor biology, production spatial score, or exact target drug arms are used.
- Strict-release Atlas row exclusions: 582, 1519, 2448, 2568, 3862, 4782, 9268, 10228, 11729, 12033, 14965, 14966, 17451.

## Primary LODO Sensitivity Metric

- Score column: `atlas_mono_disease_therapy_shrink_lodo_tuned_spearman`
- Rows: 63
- Pearson: 0.2922530219385001
- Spearman: 0.41904800475244997
- AUC above disease median: 0.6962474645030426
- MAE ORR pct: 12.571540827002169
