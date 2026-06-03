# Cohort-Level Bench

The cohort-level benchmark evaluates drug response at the trial-arm or
drug-by-disease level. A row represents a production cohort-drug pair with an
observed objective response rate (ORR) and a model-predicted ORR derived from
aggregating patient-section response probabilities.

This benchmark is noisier than patient-level response because it trades
individual matched outcomes for broader coverage across drugs and diseases. It
is still useful because it tests whether spatial rollout scores recover
meaningful differences in response across clinical settings without fitting to
observed ORR labels.

## Baselines

The `baseline/` folder contains external-data baselines for the same
cohort-level ORR surface:

- Atlas ORR prior: exact-drug-excluded, support-shrunk prior response rate from
  previous trial arms.
- DepMap ORR sensitivity: GDSC/PRISM drug-sensitivity rank in matched cancer
  lineages.

The baseline scripts expect raw Atlas and DepMap source tables as local external
inputs. The tracked result summaries are small release artifacts.

## Clinical Rows

The `clinical_rows/` folder contains compact cohort benchmark v2 row manifests:

- `cohort_benchmark_v2_clinical_rows.csv`: all 69 cohort-drug rows.
- `cohort_benchmark_v2_orr_labeled_clinical_rows.csv`: 66 rows with finite ORR
  labels.
- `cohort_benchmark_v2_eval_clinical_rows.csv`: 63 evaluation rows with finite
  ORR labels and finite default scores.

These files preserve clinical labels and row metadata without carrying the full
model prediction table.

## Model Scores

The `model_scores/v13_1b/` folder contains the reviewed public v13.1b
cohort-model score artifacts:

- `v13_1b_63_model_scores.csv`: all 63 ORR-scored evaluation rows with the
  active/default v13.1b score and candidate score sidecars.
- `v13_1b_best_63_model_scores.csv`: focused 63-row table with the active
  default score, the best packaged Pearson/Spearman sidecars, and the universal
  softmin sidecar.
- `v13_1b_metrics.csv`: global active/candidate metrics.
- `v13_1b_by_disease_metrics.csv`: by-disease active/default metrics.
- `audit_logs/`: compact input-comparability and susceptibility audits.

The active/default v13.1b score is `apoptosis_prevalence_no_prior_score`
with Pearson `0.511` and Spearman `0.520` on the 63 ORR-scored rows.
The best packaged 63-row Pearson sidecar is
`prob_apoptosis_prevalence_orr_gt_20pct`, with Pearson `0.650` and Spearman
`0.564`. The universal softmin sidecar
`universal_axis_softmin_response_probability_mean` is also included explicitly,
with Pearson `0.646` and Spearman `0.519`. These are label-aware leaderboard
summaries across precomputed sidecars, not the active/default release score.
The softmin sidecar is the cohort-level mean of per-patient
`min(final axis support values)` probabilities; see
`docs/universal_softmin_crc_patient_rank_score.md`.
The full 190-column production prediction table and 1,078-row patient
probability table are intentionally not included.
