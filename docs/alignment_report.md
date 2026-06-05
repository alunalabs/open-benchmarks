# Benchmark Alignment Report

Checked on 2026-06-03.

This report records the public numbers that should be kept aligned across the
Gaia blog/Tahoe writeup language and this `open-benchmarks` release.

## Canonical Release Numbers

Patient-level CRC benchmark:

- Rows: 11 pretreatment CRC patients.
- Public score: `response_score_rank_calibrated`.
- AUC response high: 0.800.
- Fixed 0.5 balanced accuracy: 0.733.

Patient-level CRC module mean cosine readout:

- Public cosine metric: `module_mean_cosine`.
- Best mean step: 4.
- Step 1 mean: -0.106.
- Step 4 mean: 0.304.

Cohort-level ORR benchmark:

- Rows: 44 strict observed ORR cohort-drug pairs.
- Public score: `gaia_predicted_orr_pct`.
- Pearson r: 0.650.
- Spearman rho: 0.594.
- Mean absolute ORR gap: 10.2 percentage points.
- AUC above disease median: 0.752.

Atlas baseline:

- Target rows: same 44 strict ORR rows.
- Public score: `atlas_mono_disease_therapy_shrink_k8`.
- Fixed shrinkage: `k=8`.
- Pearson r: 0.465.
- Spearman rho: 0.460.
- Mean absolute ORR gap: 11.3 percentage points.
- AUC above disease median: 0.728.

DepMap baseline:

- Target rows: same 44 strict ORR rows.
- Covered rows for primary DepMap score: 40.
- Public score: `depmap_lineage_sensitivity_rank`.
- Pearson r: -0.014.
- Spearman rho: -0.044.
- AUC above disease median: 0.474.

## Alignment Notes

The cohort headline values match the Tahoe cohort row data: 44 strict ORR pairs,
Pearson 0.650, Spearman 0.594, and 10.2 percentage-point mean absolute ORR gap.

The patient headline values match the Tahoe patient-level language: 11 CRC
patients, AUC 0.800, fixed-threshold balanced accuracy 0.733, and step-4
module mean cosine 0.304.

For this release, DepMap must be reported on the same strict 44-row target set
as Gaia and Atlas.

## Source Of Truth

The canonical release methodology is `docs/methodology.md`.

The canonical checked-in metrics are:

- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_metrics_20260525.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_step_summary.csv`
- `cohort-level-bench/model_scores/gaia/gaia_metrics.csv`
- `cohort-level-bench/baseline/results/atlas_orr_metrics.csv`
- `cohort-level-bench/baseline/results/depmap_orr_metrics.csv`
