# Atlas ORR Baseline

This repo includes a reproducible calculator for Atlas-derived ORR priors on
the 44-row strict cohort benchmark. The raw Atlas CSV is an external source
artifact and is not checked into this repository.

## Source Inputs

- Atlas CSV: `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv`
- Target rows: `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`
- Atlas endpoint: `model_orr_pct`

The public strict score removes 13 reviewed raw Atlas row indices before
calculation. After numeric-ORR and real-therapy filtering, the scoring pool has
9,638 eligible Atlas rows.

## Primary Baseline

The primary benchmark baseline is an exact-drug-excluded, all-comer monotherapy
support-shrunk Atlas prior.

For each target cohort-drug row:

1. Remove the reviewed strict-release raw Atlas row indices.
2. Normalize the target drug name and known aliases.
3. Remove Atlas arms whose text mentions the exact target drug or alias.
4. Keep all-comer monotherapy Atlas arms:
   `is_combination != true` and `biomarker != yes`.
5. Map the target disease to Atlas tissue type.
6. Map broad MOA to therapy family.
7. Compute the disease + therapy-family ORR cell and the global
   therapy-family ORR cell.
8. Shrink the disease + therapy-family cell toward the global therapy-family
   cell:

```text
shrunk ORR = n / (n + 8) * disease_therapy_ORR
           + 8 / (n + 8) * global_therapy_ORR
```

9. Fall back to the predefined all-comer monotherapy therapy-first hierarchy if
   either shrinkage cell is unavailable.
10. Aggregate ORR as a weighted mean using `orr_denom` when available;
    otherwise each Atlas arm receives weight 1.

## What Is Used

For prediction on each of the 44 target rows, the Atlas prior uses:

- Target disease or cohort key.
- Target broad MOA only to derive therapy family.
- Historical Atlas arm ORR, `model_orr_pct`.
- Historical Atlas arm denominator, `orr_denom`, as aggregation weight when
  available.
- Atlas metadata needed for filtering: tissue, therapy class,
  monotherapy/combination status, biomarker status, line, and arm text.

It does not use:

- The observed ORR label for the target row, except when computing evaluation
  metrics after predictions are already made.
- Gaia score or patient-level tumor biology features.
- The exact target drug as a predictive feature.
- DepMap features or any fitted model over the 44 rows.

## Overfit Controls

The release Atlas baseline is not fit to the 44 target ORR labels.

- The primary score is fixed as `atlas_mono_disease_therapy_shrink_k8`.
- `k=8` is fixed and is not selected by maximizing performance on the 44 rows.
- The formula is deterministic once Atlas and target disease/therapy family
  are known.
- Observed ORR is used only after prediction to compute metrics.

## Released Result

On the 44 strict ORR rows, fixed `k=8` shrinkage reached:

- Pearson r: `0.465`
- Spearman rho: `0.460`
- AUC above disease median: `0.728`
- MAE: `11.3` ORR percentage points

The release baseline is fixed `k=8`; no fitted Atlas model or label-selected
Atlas score is included.

## Reproduce

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct \
  --strict-release-cleaning
```

Outputs:

- `atlas_orr_predictions.csv`
- `atlas_orr_support_cells.csv`
- `atlas_orr_metrics.csv`
- `atlas_orr_baseline_cells.csv`
- `atlas_orr_mono_allcomer_baseline_cells.csv`
- `atlas_orr_summary.json`
- `atlas_orr_methodology.md`
