# Atlas ORR Baseline Methodology

This baseline estimates cohort-drug ORR from prior trial context in the atlas.
It does not use the exact target drug as a predictive feature.

## Primary Baseline

The Atlas prior asks what similar trials have historically achieved. It uses historical Atlas ORR by disease and therapy family, excluding the exact target drug, with no tumor biology.

- Endpoint: atlas `model_orr_pct`.
- Strict-release Atlas row exclusions: 582, 1519, 2448, 2568, 3862, 4782, 9268, 10228, 11729, 12033, 14965, 14966, 17451.
- Exclusion: remove atlas arms whose text mentions the target drug or alias.
- Eligibility: all-comer monotherapy atlas arms, defined as `is_combination != true` and `biomarker != yes`.
- Score: support-shrunk disease + therapy-family ORR, `n / (n + 8) * disease_therapy_ORR + 8 / (n + 8) * global_therapy_ORR`.
- Aggregation: weighted mean ORR using `orr_denom` when available, otherwise weight 1.
- Fallback: use the predefined all-comer monotherapy therapy-first hierarchy when either shrinkage cell is unavailable.

## Prediction Inputs

Used:

- Target disease/cohort key.
- Target therapy family derived from broad MOA.
- Historical Atlas `model_orr_pct`.
- Atlas `orr_denom` weights when available.
- Atlas tissue, therapy class, monotherapy flag, biomarker flag, line bucket, and arm text for filtering.

Not used:

- Target observed ORR label, except for post hoc evaluation metrics.
- Gaia score.
- Tumor biology or patient-level features.
- Exact target drug Atlas arms.
- DepMap features.
- Any fitted model over the target rows.

## Overfit Boundary

- Primary `k=8` is fixed from the disease + therapy-family support threshold; it is not selected by optimizing target labels.
- The Atlas prior is deterministic once Atlas and target disease/therapy family are known.
- Observed ORR is used only after prediction to compute metrics.

## Primary Metric

- Rows: 44
- Pearson: 0.46491446729880376
- Spearman: 0.4602344791806983
- AUC above disease median: 0.7283057851239669
- MAE ORR pct: 11.260271723775242

## Primary Fallback Counts

- disease_baseline: 24
- disease_therapy: 7
- global_therapy: 13
