# v13.1b Cohort Model Scores

This folder contains the public cohort-level v13.1b model score artifacts for
the 63 ORR-scored cohort benchmark v2 rows.

## Included

- `v13_1b_63_model_scores.csv`: one row per ORR-scored cohort-drug pair with
  clinical label metadata, the active/default v13.1b score, and the candidate
  score columns reported in the production metrics table.
- `v13_1b_best_63_model_scores.csv`: focused 63-row table with the active
  default score plus the best packaged Pearson/Spearman sidecars and the
  universal softmin sidecar.
- `v13_1b_metrics.csv`: global metrics for the active score and candidate
  sidecar scores.
- `v13_1b_by_disease_metrics.csv`: by-disease metrics for the active/default
  score.
- `v13_1b_model_score_summary.json`: machine-readable summary of the active
  score, candidate best metrics, and audit status.
- `v13_1b_report.md`: production report for the v13.1b cohort default.
- `audit_logs/`: compact audit and susceptibility artifacts.

## Active Release Score

The active/default v13.1b score is `apoptosis_prevalence_no_prior_score`.

It is computed as:

```text
coverage_support * apoptosis_step4_pred_fraction * resistant_tail_control
```

On the 63 ORR-scored rows:

- Pearson: `0.511`
- Spearman: `0.520`
- Within-disease weighted Pearson: `0.421`
- Within-disease weighted Spearman: `0.397`
- AUC above disease median: `0.765`

This score uses no drug prior and no z-scores. It is not calibrated as a
clinical ORR probability; `expected_response_pct` and `expected_orr_pct` are
continuity aliases for `100 * score`.

## Best Packaged Sidecars

The row file also includes candidate score columns from `v13_1b_metrics.csv`.
These are included for transparency and auditability. The release default is
not reselected per disease or per row.

The best packaged 63-row Pearson sidecar is
`prob_apoptosis_prevalence_orr_gt_20pct`:

- Pearson: `0.650`
- Spearman: `0.564`
- AUC above disease median: `0.735`

The universal softmin response-probability sidecar is
`universal_axis_softmin_response_probability_mean`:

- Pearson: `0.646`
- Spearman: `0.519`
- AUC above disease median: `0.775`

It is the cohort-level mean of per-patient
`universal_axis_softmin_response_probability`, where each patient score is:

```text
min(final axis support values)
```

The final axis support values are coverage, response-conversion,
resistant-tail/refuge, and sometimes MOA/context engagement control. This uses
the same soft-min response-gate idea as the CRC patient module probability, but
it is not the same calculation. See
`docs/universal_softmin_crc_patient_probability.md`.

The best packaged 63-row Spearman sidecar is
`universal_axis_geomean_response_probability_mean`:

- Pearson: `0.614`
- Spearman: `0.580`
- AUC above disease median: `0.756`

These are global leaderboard summaries over nine precomputed sidecar columns.
They are not fitted per row or disease, but choosing the top Pearson or
Spearman sidecar is label-aware candidate selection, so the active/default
score remains reported separately.

An internal coverage-threshold sensitivity sweep reached Pearson `0.659` on the
same 63 rows (`hard_generic_keep_moa`, threshold `0.90`), but that sweep is
label-aware retuning and is not a public release score.

## Excluded

The public folder intentionally excludes:

- The full 190-column production `predictions.csv`.
- The 1,078-row `patient_probabilities.csv`.
- The raw nominal-sample audit table with patient identifiers.
