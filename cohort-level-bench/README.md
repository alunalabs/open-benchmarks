# Cohort-Level Bench

The cohort-level benchmark evaluates drug response at the drug-by-disease
level. A row represents a strict observed ORR cohort-drug pair with a Gaia
predicted ORR percentage.

The current public cohort target is the 44-row strict ORR set:

- [clinical_rows/cohort_benchmark_strict44_clinical_rows.csv](clinical_rows/cohort_benchmark_strict44_clinical_rows.csv)
- [model_scores/gaia/gaia_44_strict_orr_model_scores.csv](model_scores/gaia/gaia_44_strict_orr_model_scores.csv)

## Clinical Rows

The clinical-row manifest includes row identifiers, disease/drug metadata,
broad MOA, therapy family, observed ORR, and evidence links. It excludes Gaia
score columns.

## Model Scores

The Gaia score artifact includes the same 44 rows plus:

- `gaia_predicted_orr_pct`
- `default_score`
- `expected_response_pct`
- `expected_orr_pct`

For this release these are continuity aliases for the same predicted ORR
percentage.

Released metric for `gaia_predicted_orr_pct`:

- Rows: `44`
- Pearson r: `0.650`
- Spearman rho: `0.594`
- Mean absolute ORR gap: `10.2` percentage points
- AUC above disease median: `0.752`

Only this strict 44-row cohort target is linked in the public release. See
`../docs/methodology.md` for row construction, metric definitions, and score
boundaries.

## Baselines

The `baseline/` folder contains external-data baselines recomputed on the same
44 target rows:

- Atlas ORR prior: exact-drug-excluded, support-shrunk historical ORR from
  previous Atlas trial arms.
- DepMap ORR sensitivity: GDSC/PRISM drug-sensitivity rank in matched cancer
  lineages.

The baseline scripts expect raw Atlas and DepMap source tables as local
external inputs. The checked-in result summaries are small release artifacts.
