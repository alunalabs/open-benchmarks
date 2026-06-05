# Benchmark Methodology

This document is the public methodology contract for the current
`open-benchmarks` release.

## Release Scope

This release includes:

- Patient-level CRC response benchmark: 11 pretreatment CRC patient rows.
- Patient-level cSCC checkpoint response benchmark: 12 pretreatment cSCC
  patient rows.
- Patient-level CRC module mean cosine readout: 11 CRC patients across
  cascade steps 1-8.
- Patient-level CRC hard-donor and gene-swap control baselines: 11 CRC
  patients across baseline, gene-shuffled, and hard-donor control surfaces.
- Cohort-level ORR benchmark: 44 strict observed ORR cohort-drug rows.
- Cohort-level baselines: Atlas fixed `k=8` ORR prior and DepMap lineage
  sensitivity on the same 44 target rows.
- Cohort-level hard-donor and gene-swap robustness controls for the 44-row
  heterogeneity-magnitude readout.

This release excludes BioBench, full production prediction tables,
patient-probability tables, raw spatial data, raw Atlas curation tables, and
raw DepMap matrices.

The public model artifacts in this repository are checked-in score CSVs and
baseline feature/prediction CSVs. Private model checkpoints, raw per-cell
outputs, and source raw Atlas/DepMap matrices are external. Folder-local
`reproduce_*.py` scripts and notebooks under `notebooks/` recompute the public
metrics from the checked-in release artifacts.

## Shared Metrics

Cohort-level scores are evaluated against observed ORR percentage points:

```text
y_true = orr_pct
y_score = model or baseline score
```

Metrics:

- Pearson r: ordinary Pearson correlation on finite `(y_true, y_score)` pairs.
- Spearman rho: Pearson correlation of average ranks, with ties averaged.
- MAE: mean absolute error in ORR percentage points, when the score is on the
  ORR percentage scale.
- AUC above disease median: within each disease, mark rows above that disease's
  median observed ORR as positive, then compute AUC from the score.

Patient-level CRC metrics are evaluated against `observed_responder`:

- AUC response high: AUC of `response_score_rank_calibrated` against responder
  label.
- Fixed 0.5 balanced accuracy: balanced accuracy of
  `response_score_rank_calibrated >= 0.5`.

CRC prior-control baseline metrics use the same AUC and balanced-accuracy
definitions, but are audit controls rather than promoted predictors. Risk-sum
surfaces are oriented as lower risk is more responder-like for AUC and use
`risk <= 0` for the thresholded call.

## Patient-Level CRC Benchmark

Artifacts:

- `patient-level-bench/clinical_rows/crc_patient_clinical_rows_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_rank_scores_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_metrics_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/reproduce_crc_moa_tailored_rank_score.py`

Rows:

- 11 pretreatment CRC patient rows.
- Labels: `observed_responder` and `observed_non_responder`.
- Public score: `response_score_rank_calibrated`.

The score starts from five broad module supports:

```text
kras_mapk_support
egfr_support
cytostasis_support
escape_control_support
kill_conversion_support
```

For each patient:

```text
coverage = fraction of module supports greater than 0
mean_support = mean(module supports)
p10_support = 10th percentile(module supports)
effective_coverage = min(1, coverage / 0.80)
```

Then compute the label-free intermediate:

```text
module_calibrated_intermediate =
  min(
    sigmoid(effective_coverage, center=0.90, scale=0.05),
    sigmoid(mean_support, center=0.0, scale=0.015),
    sigmoid(p10_support, center=-0.02, scale=0.015)
  )
```

The public score is the panel-relative rank:

```text
response_score_rank_calibrated =
  rank(module_calibrated_intermediate within the 11-patient CRC panel) / 11
```

The fixed classifier is:

```text
predicted responder = response_score_rank_calibrated >= 0.5
```

Boundary:

- The score does not use patient labels to assign scores.
- It does not use observed ORR calibration, z-scores, or drug priors.
- It is panel-relative, not an absolute probability.
- Non-default probability and apparent-calibration columns are excluded.

Released metrics:

- Rows: 11
- AUC response high: 0.800
- Fixed 0.5 balanced accuracy: 0.733

## Patient-Level cSCC Checkpoint Benchmark

Artifacts:

- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_patient_scores_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_metrics_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_summary.json`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/reproduce_cscc_checkpoint_compartment.py`

Rows:

- 12 pretreatment cSCC patient rows.
- Labels: `response_label`, where `1` is pCR/mPR responder and `0` is
  Non-mPR/pCR non-responder.
- Public score: `relative_response_probability`.

The score uses the same universal response-axis product shape as the CRC
patient and cohort-level benchmarks, but routes cSCC checkpoint axes to their
validated compartments:

```text
relative_response_probability =
  immune_primary.engagement_support
  * immune_primary.response_conversion_support
  * immune_primary.coverage_support
  * epithelial.resistant_tail_control
  * immune_primary.escape_refuge_control
```

Boundary:

- The score does not use patient labels to assign scores.
- It does not use observed ORR calibration, z-scores, or drug priors.
- It is a relative p_response ranking score, not an absolute clinical ORR
  probability.
- The public table contains only the promoted compartment map, not the full
  exploratory all-combination axis-source screen.

Released metrics:

- Rows: 12
- AUC response high: 0.944
- Spearman response high: 0.772

## Patient-Level CRC Module Mean Cosine Readout

Artifacts:

- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_step_summary.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_patient_steps.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_module_vectors.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_summary.json`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/reproduce_crc_module_mean_cosine.py`

Rows:

- 11 CRC patients.
- Cascade steps 1-8.
- Primary readout: `module_mean_cosine`.

Calculation:

```text
for each patient and cascade step:
  predicted_module_delta[module] =
    mean(predicted_delta_logcp10k[genes in module])

  observed_module_delta[module] =
    mean(observed_tumor_on_minus_pre_delta_logcp10k[genes in module])

  module_mean_cosine =
    cosine(predicted_module_delta, observed_module_delta)
```

The readout uses 41 scoring-panel genes present in the CRC panel and six
response/resistance modules.

Released module mean cosine metrics:

- Patients: 11
- Best mean step: 4
- Step 1 mean: -0.106
- Step 4 mean: 0.304
- Step 4 median: 0.561
- Step 4 PR mean: 0.522
- Step 4 SD mean: 0.123

Boundary:

- This readout uses measured tumor on-treatment minus pretreatment delta as
  the observed target.
- It is not a pretreatment prediction benchmark.
- It does not replace the public pretreatment `response_score_rank_calibrated`
  score.
- It reports broad program-level alignment, not exact within-module
  gene-by-gene reconstruction.

## Patient-Level CRC Prior-Control Baselines

Artifacts:

- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_patient_prior_control_patient_scores.csv`
- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_patient_prior_control_metrics.csv`
- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_patient_prior_control_vs_baseline.csv`
- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_hard_donor_gene_delta_step_summary.csv`

Rows:

- 33 sanitized patient-control rows.
- 11 CRC patients under each control: baseline, `gene_shuffled`, and
  `hard_donor`.
- Labels: `is_response`.

Controls:

- `gene_shuffled`: shuffles gene identity in the prior cascade while keeping
  the patient rows and labels fixed. This tests whether the surface depends on
  gene/module semantics.
- `hard_donor`: replaces the intended donor context with a hard mismatched
  donor context. This tests whether the ranked patient surface changes when the
  donor/context is wrong.

Primary audit surface:

```text
predicted_delta_moa_gate_response_probability
```

Metrics are recomputed from the sanitized patient-control table:

```text
AUC response high = AUC(is_response, p_response)
balanced accuracy = BA(is_response, p_response >= 0.5)
movement = mean(abs(control_patient_score - baseline_patient_score))
```

Released audit metrics on the primary surface:

- Baseline AUC: 0.633
- Gene-shuffled AUC: 0.567
- Gene-shuffled mean absolute movement vs baseline: 0.297
- Hard-donor AUC: 0.633
- Hard-donor mean absolute movement vs baseline: 0.014

Boundary:

- This is a robustness/control audit, not the promoted CRC response benchmark.
- The hard-donor step-4 surface barely moves from baseline, so this control is
  a cautionary result rather than a specificity pass.
- The promoted CRC patient benchmark remains
  `response_score_rank_calibrated`.

## Cohort-Level Gaia ORR Benchmark

Artifacts:

- `cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv`
- `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`
- `cohort-level-bench/model_scores/gaia/gaia_metrics.csv`
- `cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json`
- `cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py`

Rows:

- 44 strict observed ORR cohort-drug pairs.
- Disease counts: breast 8, CRC 10, NSCLC 14, ovarian 8, PDAC 4.
- Observed label: `orr_pct`.
- Public score: `gaia_predicted_orr_pct`.

The score table also includes `default_score`, `expected_response_pct`, and
`expected_orr_pct` as continuity aliases for `gaia_predicted_orr_pct`.

Calculation:

```text
metric_input_rows = rows with finite orr_pct and finite gaia_predicted_orr_pct
y_true = orr_pct
y_score = gaia_predicted_orr_pct
```

Boundary:

- The public cohort score table contains only the selected strict 44-row ORR
  benchmark.
- It does not include patient-probability tables or full production prediction
  tables.
- Metrics are direct correlations and errors against observed ORR; no row is
  reweighted for the headline Pearson/Spearman.

Released metrics:

- Rows: 44
- Pearson r: 0.650
- Spearman rho: 0.594
- MAE: 10.2 ORR percentage points
- AUC above disease median: 0.752

## Atlas Fixed `k=8` ORR Baseline

Artifacts:

- `cohort-level-bench/baseline/atlas_orr_baseline.py`
- `cohort-level-bench/baseline/reproduce_atlas_orr_results.py`
- `cohort-level-bench/baseline/results/atlas_orr_predictions.csv`
- `cohort-level-bench/baseline/results/atlas_orr_metrics.csv`
- `cohort-level-bench/baseline/results/atlas_orr_summary.json`
- `cohort-level-bench/baseline/results/atlas_orr_methodology.md`

Target rows:

- Same 44 strict ORR rows as the Gaia cohort benchmark.

External input:

- `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv`

Prediction inputs used:

- Target disease/cohort key.
- Target therapy family derived from broad MOA.
- Historical Atlas `model_orr_pct`.
- Atlas `orr_denom` weights when available.
- Atlas tissue, therapy class, monotherapy flag, biomarker flag, line bucket,
  and arm text for filtering.

Prediction inputs not used:

- Target observed ORR labels.
- Gaia scores.
- Tumor biology or patient-level features.
- Exact target-drug Atlas arms.
- DepMap features.
- Any fitted model over the 44 target rows.

Per target row:

1. Remove reviewed strict-release raw Atlas row exclusions.
2. Remove Atlas arms whose text mentions the exact target drug or alias.
3. Keep all-comer monotherapy Atlas arms:
   `is_combination != true` and `biomarker != yes`.
4. Map disease to Atlas tissue and broad MOA to therapy family.
5. Compute disease + therapy-family ORR and global therapy-family ORR.
6. Apply fixed support shrinkage:

```text
atlas_mono_disease_therapy_shrink_k8 =
  n / (n + 8) * disease_therapy_ORR
  + 8 / (n + 8) * global_therapy_ORR
```

If either shrinkage cell is unavailable, the scorer falls back to the predefined
all-comer monotherapy therapy-first hierarchy.

Boundary:

- `k=8` is fixed and not selected by optimizing target labels.
- Observed ORR is used only after predictions are made, for evaluation.
- No fitted Atlas-feature model is included in this release.

Released metrics:

- Rows: 44
- Pearson r: 0.465
- Spearman rho: 0.460
- MAE: 11.3 ORR percentage points
- AUC above disease median: 0.728

## DepMap ORR Baseline

Artifacts:

- `cohort-level-bench/baseline/depmap_orr_baseline.py`
- `cohort-level-bench/baseline/reproduce_depmap_orr_results.py`
- `cohort-level-bench/baseline/results/depmap_orr_features.csv`
- `cohort-level-bench/baseline/results/depmap_orr_metrics.csv`
- `cohort-level-bench/baseline/results/depmap_orr_summary.json`
- `cohort-level-bench/baseline/results/depmap_orr_methodology.md`

Target rows:

- Same 44 strict ORR rows as the Gaia cohort benchmark.
- DepMap covers 40 of the 44 rows with the primary score.

External inputs:

- `data/depmap/Model.csv`
- `data/depmap/drug/GDSC2AUCMatrix.csv`
- `data/depmap/drug/GDSC1AUCMatrix.csv`
- `data/depmap/drug/REPURPOSINGAUCMatrix.csv`
- Matching `*CollapsedConditions.csv` compound index files.

Per target row:

1. Match disease to DepMap `OncotreeLineage`.
2. Match drug to a GDSC2, GDSC1, or PRISM compound by normalized name and a
   small synonym table.
3. Read the compound AUC column from the matched screen.
4. Compute percentile rank of AUC within that drug/screen.
5. Average percentile rank over matched-lineage cell lines.
6. Orient as sensitivity:

```text
depmap_lineage_sensitivity_rank = 1 - mean(percentile_rank(AUC))
```

Higher values mean matched-lineage cell lines are more sensitive.

Boundary:

- DepMap uses target drug identity through drug-sensitivity screens.
- It does not fit a model to ORR labels.
- It does not use Gaia scores or Atlas priors.

Released metrics:

- Target rows: 44
- Covered rows: 40
- Pearson r: -0.014
- Spearman rho: -0.044
- AUC above disease median: 0.474

## Cohort-Level Hard-Donor and Gene-Swap Controls

Artifacts:

- `cohort-level-bench/baseline/robustness_controls_20260525/heterogeneity_hard_donor_controls.csv`
- `cohort-level-bench/baseline/robustness_controls_20260525/heterogeneity_hard_donor_random_summary.csv`
- `cohort-level-bench/baseline/robustness_controls_20260525/heterogeneity_gene_shuffle_controls.csv`
- `cohort-level-bench/baseline/robustness_controls_20260525/heterogeneity_gene_shuffle_random_summary.csv`
- `cohort-level-bench/baseline/robustness_controls_20260525/heterogeneity_gene_shuffle_hard_readout_controls.csv`

Rows:

- 44 strict cohort ORR target rows are used in each real/control metric row.
- The public CSVs are metric-level control rows and null summaries, not raw
  patient-level or per-cell predictions.

Controls:

- Hard donor: same-patient wrong-drug donor contexts. This tests whether the
  readout remains context-specific when the donor/drug context is deliberately
  mismatched.
- Gene-swap/gene-shuffle: preserves random-control sizes and signs while
  shuffling gene identity. This tests whether the signal depends on correct
  gene/module semantics.

Primary variant:

```text
signed_mag_tail_soft_primary
```

Primary metric:

```text
within_disease_pair_weighted_spearman
```

Null summaries are recomputed as:

```text
null_mean = mean(random-control within-disease Spearman)
null_p95 = 95th percentile(random-control within-disease Spearman)
empirical_p = fraction(random controls >= real within-disease Spearman)
```

Released primary-control results:

- Real within-disease Spearman: 0.439
- Random same-patient wrong-drug donor null n: 20
- Hard-donor null mean: -0.101
- Hard-donor null p95: 0.232
- Hard-donor empirical p >= real: 0.000
- Gene-swap null n: 100
- Gene-swap null mean: 0.009
- Gene-swap null p95: 0.371
- Gene-swap empirical p >= real: 0.010

Boundary:

- These controls are robustness baselines, not the Gaia, Atlas, or DepMap
  headline predictors.
- They are included to show whether a response readout remains above
  deliberately corrupted donor/context and gene/module nulls.

## Reproduction Commands

Verify every checked-in release metric without external raw data:

```bash
python scripts/reproduce_release_scores.py
```

Verify individual checked-in score artifacts:

```bash
python cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py
python cohort-level-bench/baseline/reproduce_atlas_orr_results.py
python cohort-level-bench/baseline/reproduce_depmap_orr_results.py
python patient-level-bench/model_scores/crc_moa_tailored_20260525/reproduce_crc_moa_tailored_rank_score.py
python patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/reproduce_cscc_checkpoint_compartment.py
python patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/reproduce_crc_module_mean_cosine.py
```

Regenerate Atlas/DepMap baseline feature rows from external source data:

Atlas:

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct \
  --strict-release-cleaning
```

DepMap:

```bash
python cohort-level-bench/baseline/depmap_orr_baseline.py \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct
```
