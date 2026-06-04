# Benchmark Methodology

This document is the public methodology contract for the current
`open-benchmarks` release.

## Release Scope

This release includes:

- Patient-level CRC response benchmark: 11 pretreatment CRC patient rows.
- Patient-level CRC observed on-treatment p_response readout: 11 measured
  on-treatment CRC patient rows.
- Cohort-level ORR benchmark: 44 strict observed ORR cohort-drug rows.
- Cohort-level baselines: Atlas fixed `k=8` ORR prior and DepMap lineage
  sensitivity on the same 44 target rows.

This release excludes BioBench, full production prediction tables,
patient-probability tables, raw spatial data, raw Atlas curation tables, and
raw DepMap matrices.

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

## Patient-Level CRC Benchmark

Artifacts:

- `patient-level-bench/clinical_rows/crc_patient_clinical_rows_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_rank_scores_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_metrics_20260525.csv`

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

## Patient-Level CRC Observed On-Treatment p_response Readout

Artifacts:

- `patient-level-bench/observed_readouts/crc_on_treatment_p_response_20260604/crc_on_treatment_p_response_readout_metrics.csv`
- `patient-level-bench/observed_readouts/crc_on_treatment_p_response_20260604/crc_on_treatment_p_response_patient_scores.csv`
- `patient-level-bench/observed_readouts/crc_on_treatment_p_response_20260604/crc_on_treatment_p2_p12_module_reference.csv`
- `patient-level-bench/observed_readouts/crc_on_treatment_p_response_20260604/crc_on_treatment_p_response_summary.json`

Rows:

- 11 measured on-treatment CRC patient rows.
- Labels: partial response vs stable disease.
- Primary readout: `observed_absolute_state_p_response`.

Calculation:

```text
observed_absolute_state_p_response =
  p_response gate scored on measured on-treatment tissue state
```

The fixed classifier is:

```text
predicted responder = observed_absolute_state_p_response >= 0.5
```

Boundary:

- This readout uses measured on-treatment state.
- It is not a pretreatment prediction benchmark.
- It does not replace the public pretreatment `response_score_rank_calibrated`
  score.
- It is included as observed-state validation for the p_response/module panel
  and as P2/P12 explainer support.

Released observed absolute-state p_response metrics:

- Rows: 11
- AUC PR-high: 0.867
- Fixed 0.5 balanced accuracy: 0.917
- PR mean: 0.6128
- SD mean: 0.3545
- Fixed-threshold calls: 5/5 PR and 5/6 SD; missed patient P11.

Important comparator:

- Observed delta p_response AUC PR-high: 0.600
- Observed delta p_response fixed 0.5 balanced accuracy: 0.533

Secondary readout:

- The observed signed MOA-risk adapter reaches SD-high AUC 0.900, but it is not
  the same object as the p_response explainer and calls P12 responder-like.

## Cohort-Level Gaia ORR Benchmark

Artifacts:

- `cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv`
- `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`
- `cohort-level-bench/model_scores/gaia/gaia_metrics.csv`
- `cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json`

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

## Reproduction Commands

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
