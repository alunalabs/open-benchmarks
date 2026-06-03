# Source Artifacts

This repo was extracted from the internal `spatial-fun` monorepo.

## Included Benchmark Scope

| Layer | Source surface | Intended public contents |
| --- | --- | --- |
| BioBench v3 | `production/biobench_v3` | manifests, ligand modules, row indexes, summaries, README |
| BioBench v2 legacy | `production/biobench_v2` | older clean and audit-inclusive row manifests, ligand modules, summary |
| Cohort benchmark v2 | `production/full_benchmark/cohort_benchmark_v2` | README, manifest, policy, aggregate metrics, compact clinical-row manifests, reviewed Gaia 63-row score tables, compact audits |
| Patient benchmark | `production/full_benchmark/patient_level` | policies, aggregate metrics, compact clinical-row manifests, reviewed CRC patient rank-score table |
| Atlas ORR baseline | `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv` | code and methodology for exact-drug-excluded ORR priors; raw atlas remains external |
| Atlas CTGov ORR audit | ClinicalTrials.gov v2 API study JSON | checked-in support-row audit CSVs with ClinicalTrials.gov citations; raw API cache remains external/ignored |
| DepMap ORR baseline | `data/depmap/Model.csv`, `data/depmap/drug/*AUCMatrix.csv`, `data/depmap/drug/*CollapsedConditions.csv` | code and methodology for GDSC/PRISM drug-sensitivity baselines; raw matrices remain external |

## Excluded By Default

- Raw `h5ad`, per-cell, per-gene, and per-patient spatial data.
- Model checkpoints, training code, Modal apps, S3 paths, and runtime caches.
- Generated figures and PDFs outside the small local README figures in
  `docs/figures/`.
- Broad experiment folders and one-off analysis scripts.
- Full patient-level model-score rows outside the reviewed compact CRC
  rank-score table checked into `patient-level-bench/model_scores/`.
- Full cohort-level prediction/probability rows outside the reviewed 63-row
  model-score tables checked into `cohort-level-bench/model_scores/gaia/`.
- The full working `atlas/` directory. It is large and contains curation/intermediate artifacts; keep it as an external source artifact.
- Raw DepMap drug-sensitivity matrices. Keep them as external source artifacts with their own data provenance and license notes.

## Review Before Publishing Row Results

Patient-level score tables can contain de-identified patient IDs, regimens,
response labels, and per-patient model outputs. This repo includes compact
clinical-row manifests with score/probability columns omitted. Full score tables
should stay out of default source control unless the data owner has approved
publication. If published, use a separate data release with a clear data
license and stable checksums.

## Canonical Source Files

BioBench v3:

- `production/biobench_v3/README.md`
- `production/biobench_v3/biobench_v3_curated_manifest.csv`
- `production/biobench_v3/biobench_v3_curated_ligand_modules.csv`
- `production/biobench_v3/biobench_v3_curated_all_rows_index.csv`
- `production/biobench_v3/biobench_v3_curated_summary.json`

BioBench v2 legacy:

- `production/biobench_v2/biobench_v2_manifest_clean.csv`
- `production/biobench_v2/biobench_v2_manifest_unfiltered.csv`
- `production/biobench_v2/biobench_v2_ligand_modules.csv`
- `production/biobench_v2/biobench_v2_summary.json`

Cohort benchmark v2:

- `production/full_benchmark/cohort_benchmark_v2/README.md`
- `production/full_benchmark/cohort_benchmark_v2/manifest.json`
- `production/full_benchmark/cohort_benchmark_v2/policy.json`
- `production/full_benchmark/cohort_benchmark_v2/metrics.csv`
- `production/full_benchmark/cohort_benchmark_v2/by_disease_metrics.csv`
- `production/full_benchmark/cohort_benchmark_v2/predictions.csv` as the source
  for compact checked-in clinical row manifests and the reviewed 63-row Gaia
  model-score tables
- `production/full_benchmark/cohort_benchmark_v2/patient_probabilities.csv` is
  not included in this repo
- `production/full_benchmark/cohort_level/*active_default_input_comparability_*.csv`
  as compact audit-log sources

CRC patient benchmark:

- `production/full_benchmark/patient_level/universal_patient_response_axes_policy_20260525.json`
- `production/full_benchmark/patient_level/universal_patient_response_axes_metrics_20260525.csv`
- `production/full_benchmark/patient_level/universal_patient_response_axes_scores_20260525.csv`
  as the source for compact checked-in clinical row labels with score columns
  omitted
- `production/full_benchmark/patient_level/crc_patient_moa_tailored_calibrated_response_distribution_policy_20260525.json`
- `production/full_benchmark/patient_level/crc_patient_moa_tailored_calibrated_response_distribution_metrics_20260525.csv`
- `production/full_benchmark/patient_level/crc_patient_moa_tailored_calibrated_response_distribution_scores_20260525.csv`
  as the source for compact checked-in CRC regimen/outcome rows and the
  reviewed CRC patient rank-score table
- `production/full_benchmark/patient_level/crc_moa_delta_risk_probability_summary_20260516.csv`

Atlas ORR baseline:

- `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv` as the external atlas input
- `production/full_benchmark/cohort_benchmark_v2/predictions.csv` as the target cohort-drug ORR surface when row results are approved
- `experiments/2026-06-02_atlas_depmap_v2_63_baselines/results/report.md` as the source experiment report for the June 2026 baseline numbers
- `experiments/2026-06-02_atlas_depmap_v2_63_baselines/results/overfit_diagnostics_report.md` as the overfit-sensitivity report
- ClinicalTrials.gov v2 API URLs, one per NCT ID, as the audit citation source for checked-in `cohort-level-bench/baseline/results/atlas_orr_ctgov_audit.csv`

DepMap ORR baseline:

- `data/depmap/Model.csv` as the external model-lineage metadata
- `data/depmap/drug/GDSC2AUCMatrix.csv`
- `data/depmap/drug/GDSC1AUCMatrix.csv`
- `data/depmap/drug/REPURPOSINGAUCMatrix.csv`
- `data/depmap/drug/GDSC2Log2ViabilityCollapsedConditions.csv`
- `data/depmap/drug/GDSC1Log2ViabilityCollapsedConditions.csv`
- `data/depmap/drug/REPURPOSINGLog2ViabilityCollapsedConditions.csv`
- `production/full_benchmark/cohort_benchmark_v2/predictions.csv` as the target cohort-drug ORR surface when row results are approved
