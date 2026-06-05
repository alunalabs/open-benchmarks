# Open Benchmarks

Open benchmark code and release summaries for the Gaia oncology benchmark suite
described in the [AlunaData blog](https://blog.alunadata.com/).

This release contains two benchmark layers:

- **Patient-level bench**: pretreatment patient-section response prediction.
- **Cohort-level bench**: drug-by-disease objective response rate (ORR)
  prediction.

BioBench is intentionally not included in this repository yet.

The detailed row, score, metric, and baseline methodology is in
`docs/methodology.md`; the blog/Tahoe number cross-check is in
`docs/alignment_report.md`.

## Patient-Level Bench

The patient-level benchmark asks whether a pretreatment spatial section can
predict later clinical response for the same patient. The current public score
artifact focuses on 11 metastatic CRC patients treated with KRAS-axis plus
EGFR-axis regimens.

<p align="center">
  <img src="docs/figures/blog-presponse-flow.png" alt="Patient-level response score flow" width="820">
</p>

Public artifacts:

- `patient-level-bench/clinical_rows/crc_patient_clinical_rows_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_rank_scores_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_metrics_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/reproduce_crc_moa_tailored_rank_score.py`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_patient_scores_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_metrics_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/reproduce_cscc_checkpoint_compartment.py`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_step_summary.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/reproduce_crc_module_mean_cosine.py`
- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_patient_prior_control_patient_scores.csv`
- `patient-level-bench/baseline/crc_prior_controls_20260525/crc_patient_prior_control_vs_baseline.csv`

The public CRC score is `response_score_rank_calibrated`. It summarizes
KRAS/MAPK, EGFR, cytostasis, escape-control, and kill-conversion module
supports into a label-free soft-min response intermediate, then converts that
intermediate into a within-panel rank score. It is a benchmark rank score, not
an absolute response probability.

Released CRC metrics:

- Rows: `11`
- AUC response high: `0.800`
- Fixed 0.5 balanced accuracy: `0.733`

See `docs/methodology.md` and
`docs/universal_softmin_crc_patient_rank_score.md` for the calculation.

cSCC checkpoint compartment score:

- Rows: `12`
- AUC response high: `0.944`
- Spearman rho: `0.772`
- Boundary: relative p_response ranking score over compartment-specific
  checkpoint axes; not a calibrated clinical ORR probability.

Module mean cosine readout:

- Rows: `11`
- Best mean step: `4`
- Step 1 mean: `-0.106`
- Step 4 mean: `0.304`
- Boundary: compares cascade predicted tumor program deltas against measured
  tumor on-treatment minus pretreatment deltas; not a pretreatment prediction
  benchmark.

CRC prior-control baselines:

- Gene-swap control: `0.567` AUC on the predicted-delta p_response surface
  with `0.297` mean absolute movement versus baseline.
- Hard-donor control: `0.633` AUC on the same surface with only `0.014` mean
  absolute movement versus baseline.
- Boundary: these are donor/context and gene/module specificity audits, not
  promoted patient response predictors.

## Cohort-Level Bench

The cohort-level benchmark asks the same response question at trial-arm scale.
Each row is a strict observed ORR cohort-drug pair with a Gaia predicted ORR
percentage. The public target is the 44-row strict ORR set used by the Tahoe
cohort figure.

<p align="center">
  <img src="docs/figures/blog-cohort-orr.png" alt="Observed vs predicted ORR" width="520">
</p>

Public artifacts:

- [cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv](cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv)
- [cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv](cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv)
- [cohort-level-bench/model_scores/gaia/gaia_metrics.csv](cohort-level-bench/model_scores/gaia/gaia_metrics.csv)
- [cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json](cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json)
- [cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py](cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py)

The public cohort score is `gaia_predicted_orr_pct`, evaluated directly against
`orr_pct`.

Released cohort metrics:

- Strict ORR pairs: `44`
- Pearson r: `0.650`
- Spearman rho: `0.594`
- Mean absolute ORR gap: `10.2` percentage points
- AUC above disease median: `0.752`

Only the strict 44-row cohort target is linked in this release. See
`docs/methodology.md` for row construction, metric definitions, and score
boundaries.

## Cohort-Level Baselines

Baseline scripts and checked-in 44-row results live under
`cohort-level-bench/baseline/`.

Atlas ORR prior:

- Script: `cohort-level-bench/baseline/atlas_orr_baseline.py`
- Reproduction script: `cohort-level-bench/baseline/reproduce_atlas_orr_results.py`
- Row predictions: `cohort-level-bench/baseline/results/atlas_orr_predictions.csv`
- Results: `cohort-level-bench/baseline/results/atlas_orr_metrics.csv`
- Primary score: `atlas_mono_disease_therapy_shrink_k8`
- Target rows: `44`
- Pearson r: `0.465`
- Spearman rho: `0.460`
- MAE: `11.3` ORR percentage points

The Atlas prior uses target disease, broad therapy family, historical Atlas
trial-arm ORR, and exact-drug exclusion. It does not use target observed ORR,
Gaia scores, tumor biology, exact target drug Atlas arms, DepMap, or a fitted
model over the target rows.

DepMap drug sensitivity:

- Script: `cohort-level-bench/baseline/depmap_orr_baseline.py`
- Reproduction script: `cohort-level-bench/baseline/reproduce_depmap_orr_results.py`
- Results: `cohort-level-bench/baseline/results/depmap_orr_metrics.csv`
- Primary score: `depmap_lineage_sensitivity_rank`
- Target rows: `44`
- Covered rows: `40`
- Pearson r: `-0.014`
- Spearman rho: `-0.044`

DepMap is included as a negative external-data baseline on the same 44-row ORR
surface.

Robustness controls:

- Folder: `cohort-level-bench/baseline/robustness_controls_20260525/`
- Hard-donor baseline: same-patient wrong-drug donor contexts.
- Gene-swap baseline: gene-shuffled controls preserving sizes and signs.
- Primary 44-row within-disease Spearman: real `0.439`, hard-donor null p95
  `0.232`, gene-swap null p95 `0.371`.

## Install

```bash
python -m pip install -e ".[dev]"
```

The package uses only the Python standard library at runtime. Development
checks use `pytest` and `ruff`.

## Recompute

Run the Atlas baseline:

```bash
python cohort-level-bench/baseline/atlas_orr_baseline.py \
  --atlas-csv /path/to/spatial-fun/atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/atlas_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct \
  --strict-release-cleaning
```

Run every no-external-data release metric reproduction check:

```bash
python scripts/reproduce_release_scores.py
```

The reproducibility notebooks are under `notebooks/`. They load the same
checked-in score artifacts and recompute the displayed metrics.

Run the DepMap baseline:

```bash
python cohort-level-bench/baseline/depmap_orr_baseline.py \
  --depmap-drug-dir /path/to/spatial-fun/data/depmap/drug \
  --model-csv /path/to/spatial-fun/data/depmap/Model.csv \
  --cohort-predictions cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv \
  --output-dir artifacts/depmap_orr_baseline \
  --surface-score-column gaia_predicted_orr_pct
```

## Artifact Policy

This repo is code-and-summary oriented. Raw spatial data, model checkpoints,
per-cell outputs, raw Atlas curation tables, and raw DepMap matrices remain
external source artifacts.
