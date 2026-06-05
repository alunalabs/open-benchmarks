# Cohort-Level Baselines

This folder contains baseline scripts and result summaries for the 44-row
strict cohort-level ORR benchmark.

See `docs/methodology.md` for the shared row set, metric definitions, and
baseline boundaries.

## Scripts

- `atlas_orr_baseline.py`: exact-drug-excluded Atlas ORR prior. The primary
  score is `atlas_mono_disease_therapy_shrink_k8`.
- `atlas_orr_ctgov_audit.py`: optional support-arm audit against
  ClinicalTrials.gov outcome measurements.
- `reproduce_atlas_orr_results.py`: recompute Atlas release metrics from the
  checked-in 44-row `results/atlas_orr_predictions.csv`.
- `depmap_orr_baseline.py`: DepMap GDSC/PRISM lineage-sensitivity baseline.
  The primary score is `depmap_lineage_sensitivity_rank`.
- `reproduce_depmap_orr_results.py`: recompute DepMap release metrics from the
  checked-in 44-row `results/depmap_orr_features.csv`.

## Checked-In Results

Release summaries are under `results/`:

- `atlas_orr_metrics.csv`
- `atlas_orr_predictions.csv`
- `atlas_orr_summary.json`
- `atlas_orr_methodology.md`
- `depmap_orr_features.csv`
- `depmap_orr_metrics.csv`
- `depmap_orr_summary.json`
- `depmap_orr_methodology.md`

Formula controls are under `formula_controls_20260605/`. They keep the released
44-row Gaia score and metric path fixed, then corrupt ORR-label alignment.
These are exact public controls for the checked-in score artifact, not
donor/gene controls.

## Atlas Overfit Boundary

The Atlas prior asks what similar trials have historically achieved. For each
target row, it builds a disease x therapy-family historical ORR from the Atlas,
excludes Atlas arms that mention the exact target drug, and support-shrinks that
rate toward the global therapy-family rate.

Prediction inputs:

- Target disease/cohort key.
- Target therapy family derived from broad MOA.
- Historical Atlas `model_orr_pct`.
- Atlas arm support, denominator, tissue, therapy class, monotherapy flag,
  biomarker flag, line bucket, and text for exact-drug exclusion.

Not prediction inputs:

- Target observed ORR label.
- Gaia score.
- Tumor biology or patient-level features.
- Exact target drug Atlas arms.
- DepMap features.
- Any fitted model over the 44 target rows.

The primary score is fixed as `atlas_mono_disease_therapy_shrink_k8`:

```text
shrunk ORR = n / (n + 8) * disease_therapy_ORR
           + 8 / (n + 8) * global_therapy_ORR
```

`k=8` is fixed and is not selected by optimizing the 44 target ORR labels.
Observed ORR is used only after prediction to compute metrics.

The checked-in `results/atlas_orr_predictions.csv` is a compact public
prediction table. It includes target metadata, observed ORR for evaluation, the
Atlas primary score, source cell, and support counts. It excludes Gaia score
columns.

Fixed Atlas result on the 44 target rows:

- Pearson r: `0.465`
- Spearman rho: `0.460`
- AUC above disease median: `0.728`
- MAE: `11.3` ORR percentage points

## DepMap

DepMap matches the target drug to GDSC/PRISM screens and the target disease to
DepMap `OncotreeLineage`. The primary score is:

```text
depmap_lineage_sensitivity_rank = 1 - mean(percentile_rank(AUC))
```

Higher values mean matched-lineage cell lines are more sensitive to the drug.
This baseline uses the target drug through DepMap but does not fit a model to
the ORR labels.

DepMap result on the same 44 target rows:

- Covered rows: `40`
- Pearson r: `-0.014`
- Spearman rho: `-0.044`
- AUC above disease median: `0.474`

## Formula Controls

`formula_controls_20260605/` contains deterministic controls for the released
44-row Gaia score table.

Controls:

- `label_shuffle_global`: permutes observed ORR labels across all 44 rows.
- `label_shuffle_within_disease`: permutes observed ORR labels only within each
  disease.

Headline result:

- Real Gaia 44 Pearson r: `0.650`
- Global label-shuffle Pearson null p95: `0.275`
- Within-disease label-shuffle Pearson null p95: `0.421`
- Real Gaia 44 AUC above disease median: `0.752`
- Within-disease label-shuffle AUC null p95: `0.633`

Boundary: the public 44-row artifact contains final cohort scores, not the
private per-patient axis/probability rows needed to recompute donor/gene
controls. These are exact controls for the public score/metric artifact.

## Reproduce Atlas

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct \
  --strict-release-cleaning
```

Verify the checked-in Atlas release metrics without external raw data:

```bash
python cohort-level-bench/baseline/reproduce_atlas_orr_results.py
```

## Reproduce DepMap

```bash
python cohort-level-bench/baseline/depmap_orr_baseline.py \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct
```

Verify the checked-in DepMap release metrics without external raw data:

```bash
python cohort-level-bench/baseline/reproduce_depmap_orr_results.py
```
