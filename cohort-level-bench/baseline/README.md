# Cohort-Level Baselines

This folder contains baseline scripts and result summaries for the cohort-level
ORR benchmark.

## Scripts

- `atlas_orr_baseline.py`: runs the exact-drug-excluded Atlas ORR prior
  calculator. The primary score is `atlas_mono_disease_therapy_shrink_k8`.
- `atlas_orr_lodo_tuning.py`: runs leave-disease-out tuning over the fixed
  `k` grid as an anti-overfit sensitivity check.
- `atlas_orr_ctgov_audit.py`: audits the Atlas support-arm ORRs against
  ClinicalTrials.gov outcome measurements and writes ClinicalTrials.gov
  citations.
- `depmap_orr_baseline.py`: runs the DepMap GDSC/PRISM lineage-sensitivity
  calculator. The primary score is `depmap_lineage_sensitivity_rank`.

Both scripts are thin wrappers around the package implementation under
`src/spatial_benchmarks/`.

## Results

Release summaries are under `results/`:

- `atlas_orr_metrics.csv`
- `atlas_orr_summary.json`
- `atlas_orr_lodo_fit_records.csv`
- `atlas_orr_lodo_metrics.csv`
- `atlas_orr_lodo_summary.json`
- `atlas_orr_lodo_methodology.md`
- `atlas_orr_ctgov_audit.csv`
- `atlas_orr_ctgov_audit_exceptions.csv`
- `atlas_orr_ctgov_exception_review.csv`
- `atlas_orr_literature_review.csv`
- `atlas_orr_literature_review.md`
- `atlas_orr_support_reasonableness.md`
- `atlas_orr_support_reasonableness_summary.json`
- `atlas_orr_support_reasonableness_support_rows.csv`
- `atlas_orr_support_reasonableness_flags.csv`
- `atlas_orr_support_reasonableness_target_summary.csv`
- `atlas_orr_cleaned_verified_support.md`
- `atlas_orr_ctgov_manual_review.md`
- `atlas_orr_ctgov_audit_summary.json`
- `depmap_orr_metrics.csv`
- `depmap_orr_summary.json`

Row-level generated outputs are intentionally not committed. Regenerate them
into `artifacts/` with the commands below.

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
- Production spatial-model score.
- Tumor biology or patient-level features.
- Exact target drug Atlas arms.
- DepMap features.
- Any fitted model over the 63 target rows.

The primary score is fixed as `atlas_mono_disease_therapy_shrink_k8`:

```text
shrunk ORR = n / (n + 8) * disease_therapy_ORR
           + 8 / (n + 8) * global_therapy_ORR
```

`k=8` is the original support threshold for the disease x therapy-family cell;
it is not selected by optimizing the 63 target ORR labels. The strict release
result is Pearson `0.409` and Spearman `0.464` on 63 rows. A
leave-disease-out sensitivity analysis that selects `k` using all
non-held-out diseases reaches Pearson `0.292` and Spearman `0.419`; this is
reported as an overfit check, not as the primary baseline.

## Leave-Disease-Out Tuning

LODO tuning is run only as a sensitivity check:

1. Compute Atlas shrinkage predictions for each fixed `k` in
   `1, 3, 5, 8, 10, 15, 25, 50, 100`.
2. Hold out one disease.
3. Select `k` using all other diseases by the requested objective, primarily
   Spearman.
4. Apply that selected `k` to the held-out disease.
5. Concatenate held-out predictions across diseases and evaluate once.

The held-out disease labels are never used to choose that disease's `k`.

## ClinicalTrials.gov ORR Audit

The Atlas score on the 63 cohorts is supported by 202 unique Atlas arm rows
from 125 ClinicalTrials.gov NCT records. The audit file cites the
ClinicalTrials.gov study page and v2 API URL for each support row, records the
matched outcome title/group/value, and compares the derived CTGov ORR
percentage with the Atlas `model_orr_pct`.

Audit status on the checked-in results:

- `ctgov_verified_match`: 191 support rows.
- `ctgov_value_mismatch`: 3 support rows.
- `ctgov_no_matching_orr_measurement`: 8 support rows.

The exceptions are intentionally preserved in
`atlas_orr_ctgov_audit_exceptions.csv` for manual review. One exception is an
Atlas row whose model ORR came from PubMed rather than CTGov.

`atlas_orr_literature_review.csv` and `.md` are the second-pass literature
audit for those 11 exceptions. They record PubMed/DOI evidence when available,
registry-only gaps when no publication was found, and a recommended strict-ORR
handling decision for each exception.

The intermediate cleaned verified-support recalculation removes those 11
exceptions from the Atlas source pool. The release baseline additionally
removes two CTGov-verified endpoint caveat rows that are not strict CR/PR ORR
endpoints, then reruns the same fixed `k=8` prior. It reaches Pearson `0.409`
and Spearman `0.464` on the same 63 ORR rows.

`atlas_orr_support_reasonableness.md` audits the 191 CTGov-verified support
arms before endpoint-caveat removal. It finds no exact-drug leakage and
confirms all support arms are biomarker-unselected and non-combination. The
strict release score uses 189 audited support arms after removing the two
endpoint caveats.

## Reproduce Atlas

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column default_score \
  --strict-release-cleaning
```

The public strict score uses the raw Atlas CSV plus `--strict-release-cleaning`,
which removes the 13 reviewed raw Atlas row indices listed in
`results/atlas_orr_summary.json`.

## Reproduce Atlas LODO Tuning

```bash
python cohort-level-bench/baseline/atlas_orr_lodo_tuning.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_lodo_tuning \
  --surface-score-column default_score \
  --strict-release-cleaning
```

## Reproduce Atlas CTGov Audit

```bash
python cohort-level-bench/baseline/atlas_orr_ctgov_audit.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/atlas_orr_ctgov_audit \
  --cache-dir artifacts/ctgov_api_cache \
  --surface-score-column default_score
```

## Reproduce DepMap

```bash
python cohort-level-bench/baseline/depmap_orr_baseline.py \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions /path/to/spatial-fun/production/full_benchmark/cohort_benchmark_v2/predictions.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column default_score
```
