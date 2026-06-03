# Cohort-Level Clinical Rows

This folder contains compact cohort-level clinical-row manifests for cohort
benchmark v2.

Files:

- `cohort_benchmark_v2_clinical_rows.csv`: all 69 cohort-drug rows in the
  production v2 surface.
- `cohort_benchmark_v2_orr_labeled_clinical_rows.csv`: 66 rows with finite ORR
  labels.
- `cohort_benchmark_v2_eval_clinical_rows.csv`: 63 rows with finite ORR labels
  and finite default scores; this is the evaluation surface used for the
  reported cohort-level ORR correlations and Atlas/DepMap baselines.

These files include clinical label and row metadata only. They do not include
model score, patient-probability, or full prediction columns.
