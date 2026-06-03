# Atlas ORR Baseline

This repo includes a reproducible calculator for atlas-derived ORR priors on
cohort benchmark v2. The raw atlas is not checked into this code repo; it is a
large external source artifact.

## Source Inputs

- Atlas CSV: `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv`
- Cohort v2 predictions CSV: `production/full_benchmark/cohort_benchmark_v2/predictions.csv`
- Atlas endpoint: `model_orr_pct`

The local Atlas snapshot used for the June 2026 experiment had 21,035 raw rows.
The public strict score removes 13 reviewed raw Atlas row indices before
calculation, leaving 21,022 raw Atlas rows and 9,638 real-therapy rows eligible
after the numeric-ORR and real-therapy filters.

## Primary Baseline

The primary benchmark baseline is an exact-drug-excluded, all-comer
monotherapy support-shrunk atlas prior.

In plain terms, the Atlas prior asks what similar trials have historically
achieved. It uses a curated atlas of trial arms to build a disease x
therapy-family historical ORR, excludes the exact target drug, and shrinks the
disease-specific rate toward the global therapy-family rate. It uses no tumor
biology and no production spatial-model score.

For each target cohort-drug row:

1. Remove the reviewed strict-release raw Atlas row indices.
2. Normalize the target drug name and known aliases.
3. Remove atlas arms whose title, regimen, intervention, or description text
   mentions the exact target drug or alias.
4. Keep all-comer monotherapy atlas arms:
   `is_combination != true` and `biomarker != yes`.
5. Map the target disease to atlas tissue type.
6. Map broad MOA to therapy family, such as chemotherapy or targeted therapy.
7. Compute the disease + therapy-family ORR cell and the global
   therapy-family ORR cell.
8. Shrink the disease + therapy-family cell toward the global therapy-family
   cell:

```text
shrunk ORR = n / (n + 8) * disease_therapy_ORR
           + 8 / (n + 8) * global_therapy_ORR
```

9. Fall back to the legacy all-comer monotherapy therapy-first hierarchy if
   either shrinkage cell is unavailable.
10. Aggregate ORR as a weighted mean using `orr_denom` when available;
   otherwise each atlas arm receives weight 1.

This baseline intentionally does not use the exact drug identity as a
predictive feature.

## What Is Used

For prediction on each of the 63 cohort-level ORR rows, the Atlas prior uses:

- Target disease or cohort key, mapped to Atlas tissue type.
- Target broad MOA only to derive therapy family, such as chemotherapy,
  targeted therapy, immunotherapy, or endocrine therapy.
- Historical Atlas arm ORR, `model_orr_pct`.
- Historical Atlas arm denominator, `orr_denom`, as the aggregation weight when
  available.
- Atlas arm metadata needed for filtering: tissue, therapy class,
  monotherapy/combination status, biomarker status, line, and arm text.

It does not use:

- The observed ORR label for the target row, except when computing evaluation
  metrics after predictions are already made.
- The production spatial model score or patient-level tumor biology features.
- The exact target drug as a predictive feature.
- DepMap features or any fitted model over the 63 rows.

The exact target drug exclusion is text-based: Atlas arms whose title,
intervention, regimen, or description mentions the target drug or a known alias
are removed before computing the historical prior for that target row.

## Overfit Controls

The release Atlas baseline is not fit to the 63 target ORR labels.

- The primary score is fixed as `atlas_mono_disease_therapy_shrink_k8`.
- `k=8` is fixed from the original support threshold for the disease +
  therapy-family cell, not selected by maximizing performance on the 63 rows.
- The formula is deterministic once Atlas and the target row disease/therapy
  family are known:

```text
shrunk ORR = n / (n + 8) * disease_therapy_ORR
           + 8 / (n + 8) * global_therapy_ORR
```

- A unit test changes a target row's observed ORR and production score while
  holding disease and therapy family fixed; the Atlas prior score is unchanged.
- A leave-disease-out sensitivity analysis selected `k` inside training
  diseases only. On the strict Atlas pool, this reaches Pearson 0.292 and
  Spearman 0.419, which is weaker than fixed `k=8` and is reported only as an
  overfit sensitivity check.

This should be reported as a strong transparent baseline on these 63 cohorts,
not as a learned predictive model.

## June 2026 Result

On the 63 ORR-scored cohort benchmark v2 rows, the strict release
fixed `k=8` shrinkage prior reached:

- Pearson: 0.409
- Spearman: 0.464
- AUC above disease median: 0.742
- MAE: 11.59 ORR percentage points

The strict score removes 13 reviewed raw Atlas row indices from the Atlas
source pool before recomputing the prior:

- 3 ClinicalTrials.gov value mismatches.
- 8 rows with no matching ClinicalTrials.gov ORR measurement.
- 2 CTGov-verified endpoint caveat rows that are not strict CR/PR ORR.

As an anti-overfit sensitivity check, strict leave-disease-out Spearman-tuned
shrinkage selected `k` using all diseases except the held-out disease and
reached Pearson 0.292, Spearman 0.419, AUC 0.696, MAE 12.57. The release
baseline uses fixed `k=8`, not an outcome-fitted `k`.

The LODO tuning procedure is reproducible with:

```bash
python cohort-level-bench/baseline/atlas_orr_lodo_tuning.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_lodo_tuning \
  --surface-score-column default_score \
  --strict-release-cleaning
```

This command writes per-held-out-disease selected `k` records, LODO metrics,
LODO predictions, and a methodology file.

## ClinicalTrials.gov ORR Audit

The fixed `k=8` Atlas score uses 202 unique Atlas support-arm rows across the
63 cohort targets. The checked-in ClinicalTrials.gov audit is here:

- `cohort-level-bench/baseline/results/atlas_orr_ctgov_audit.csv`
- `cohort-level-bench/baseline/results/atlas_orr_ctgov_audit_exceptions.csv`
- `cohort-level-bench/baseline/results/atlas_orr_ctgov_exception_review.csv`
- `cohort-level-bench/baseline/results/atlas_orr_literature_review.csv`
- `cohort-level-bench/baseline/results/atlas_orr_literature_review.md`
- `cohort-level-bench/baseline/results/atlas_orr_support_reasonableness.md`
- `cohort-level-bench/baseline/results/atlas_orr_support_reasonableness_summary.json`
- `cohort-level-bench/baseline/results/atlas_orr_support_reasonableness_support_rows.csv`
- `cohort-level-bench/baseline/results/atlas_orr_support_reasonableness_flags.csv`
- `cohort-level-bench/baseline/results/atlas_orr_support_reasonableness_target_summary.csv`
- `cohort-level-bench/baseline/results/atlas_orr_cleaned_verified_support.md`
- `cohort-level-bench/baseline/results/atlas_orr_ctgov_manual_review.md`
- `cohort-level-bench/baseline/results/atlas_orr_ctgov_audit_summary.json`

Each audit row includes the Atlas ORR, ClinicalTrials.gov study URL, v2 API URL,
matched outcome title, matched result group, raw CTGov measurement, denominator
where available, derived CTGov ORR percentage, and audit status.

Checked-in audit status:

- 191 support rows verified directly against ClinicalTrials.gov within 0.5 ORR
  percentage points.
- 3 support rows had a CTGov value mismatch.
- 8 support rows had no matching CTGov ORR measurement under the conservative
  group/title/category matcher.

A second-pass literature review of those 11 exception rows is included in
`atlas_orr_literature_review.csv`. It found peer-reviewed result publications
for 7 rows, identified the PubMed-sourced GC4711 row as predecessor
disease-control-like evidence rather than GRECO-2 strict ORR, and left three
rows as registry-only curation cases.

Removing all 11 audit exceptions from the Atlas source pool leaves 191
CTGov-verified support rows. A support-row reasonableness audit of those rows
found no exact-drug leakage and no biomarker-selected or combination support
rows. Two additional CTGov-verified rows have endpoint-title caveats that are
not strict CR/PR ORR (`Clinical Benefit Response Rate` and a 6-month
progression-free endpoint).

The strict release baseline removes those two endpoint-caveat rows as well,
leaving 189 audited support rows. Rerunning the same fixed `k=8` prior gives
Pearson 0.409, Spearman 0.464, AUC above disease median 0.742, and MAE 11.59
ORR percentage points. Removing those plus one unconfirmed-PR support row gives
Pearson 0.409 and Spearman 0.474, but the unconfirmed response row remains in
the default release baseline as an explicitly documented optional sensitivity.

Regenerate with:

```bash
python cohort-level-bench/baseline/atlas_orr_ctgov_audit.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_ctgov_audit \
  --cache-dir artifacts/ctgov_api_cache \
  --surface-score-column default_score
```

Fitted atlas-feature models were also explored in the source experiment, but
they are not included as the benchmark baseline because row-level random forest
fits overfit the 63-row disease mix. The reusable benchmark baseline here is
the prior-only atlas calculator.

## Reproduce

From this repo:

```bash
open-benchmarks atlas-orr-baseline \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column default_score \
  --strict-release-cleaning
```

The strict release run uses the raw Atlas source plus
`--strict-release-cleaning`, which removes the 13 reviewed raw row indices
listed in `cohort-level-bench/baseline/results/atlas_orr_summary.json`.

Outputs:

- `atlas_prior_predictions.csv`
- `atlas_prior_support_cells.csv`
- `atlas_prior_metrics.csv`
- `atlas_baseline_cells.csv`
- `atlas_mono_allcomer_baseline_cells.csv`
- `atlas_prior_summary.json`
- `atlas_prior_methodology.md`
