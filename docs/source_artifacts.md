# Source Artifacts

This repo was extracted from the internal `spatial-fun` monorepo.

## Included Benchmark Scope

| Layer | Source surface | Intended public contents |
| --- | --- | --- |
| Patient benchmark | Patient-level production exports | CRC clinical rows, compact CRC rank-score table, cSCC checkpoint score table, metrics, policy summaries |
| Patient observed readout | CRC measured on-treatment delta audit | Compact module mean cosine trajectory, patient-step scores, and module vectors |
| Cohort benchmark | Strict ORR cohort rows | 44-row clinical manifest, 44-row Gaia predicted ORR table, metrics |
| Atlas ORR baseline | Atlas trial-arm CSV | Code, methodology, compact 44-row baseline prediction table, and result summaries; raw Atlas remains external |
| DepMap ORR baseline | DepMap model/drug matrices | Code, methodology, 44-row feature table, and baseline result summaries; raw matrices remain external |

BioBench is not part of this public release. The public cohort surface is the
strict 44-row ORR set.

## Excluded By Default

- Raw `h5ad`, per-cell, per-gene, and per-patient spatial data.
- Model checkpoints, training code, Modal apps, S3 paths, and runtime caches.
- Broad experiment folders and one-off analysis scripts.
- Full patient-level model-score rows outside the reviewed compact CRC
  rank-score table and cSCC checkpoint compartment table checked into
  `patient-level-bench/model_scores/`.
- Full cohort-level production prediction/probability rows outside the reviewed
  44-row score table checked into `cohort-level-bench/model_scores/gaia/`.
- Raw Atlas curation tables.
- Raw DepMap drug-sensitivity matrices.

## Canonical Public Source Files

Methodology:

- `docs/methodology.md`
- `notebooks/README.md`
- `scripts/reproduce_release_scores.py`

Patient-level CRC:

- `patient-level-bench/clinical_rows/crc_patient_clinical_rows_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_rank_scores_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/crc_patient_moa_tailored_metrics_20260525.csv`
- `patient-level-bench/model_scores/crc_moa_tailored_20260525/reproduce_crc_moa_tailored_rank_score.py`

Patient-level cSCC:

- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_patient_scores_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/cscc_checkpoint_compartment_metrics_20260604.csv`
- `patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/reproduce_cscc_checkpoint_compartment.py`

Patient-level CRC module mean cosine readout:

- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_step_summary.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_patient_steps.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/crc_module_mean_cosine_module_vectors.csv`
- `patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/reproduce_crc_module_mean_cosine.py`

Cohort-level strict ORR:

- [cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv](../cohort-level-bench/clinical_rows/cohort_benchmark_strict44_clinical_rows.csv)
- [cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv](../cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv)
- [cohort-level-bench/model_scores/gaia/gaia_metrics.csv](../cohort-level-bench/model_scores/gaia/gaia_metrics.csv)
- [cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json](../cohort-level-bench/model_scores/gaia/gaia_model_score_summary.json)
- [cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py](../cohort-level-bench/model_scores/gaia/reproduce_gaia_metrics.py)

Atlas ORR baseline:

- `atlas/results/ctgov_phase2_solid_tumor_atlas_cohorts_pubmed_supplement.csv`
  as the external Atlas input.
- `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`
  as the target row file.
- `cohort-level-bench/baseline/reproduce_atlas_orr_results.py`
- `cohort-level-bench/baseline/results/atlas_orr_predictions.csv`
- `cohort-level-bench/baseline/results/atlas_orr_metrics.csv`
- `cohort-level-bench/baseline/results/atlas_orr_summary.json`

DepMap ORR baseline:

- `data/depmap/Model.csv` as external model-lineage metadata.
- `data/depmap/drug/GDSC2AUCMatrix.csv`
- `data/depmap/drug/GDSC1AUCMatrix.csv`
- `data/depmap/drug/REPURPOSINGAUCMatrix.csv`
- `data/depmap/drug/GDSC2Log2ViabilityCollapsedConditions.csv`
- `data/depmap/drug/GDSC1Log2ViabilityCollapsedConditions.csv`
- `data/depmap/drug/REPURPOSINGLog2ViabilityCollapsedConditions.csv`
- `cohort-level-bench/model_scores/gaia/gaia_44_strict_orr_model_scores.csv`
  as the target row file.
- `cohort-level-bench/baseline/reproduce_depmap_orr_results.py`
- `cohort-level-bench/baseline/results/depmap_orr_features.csv`
- `cohort-level-bench/baseline/results/depmap_orr_metrics.csv`
- `cohort-level-bench/baseline/results/depmap_orr_summary.json`
