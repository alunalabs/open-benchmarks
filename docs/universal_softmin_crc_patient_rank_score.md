# Universal Softmin And CRC Patient Rank Score

This note documents the relationship between the cohort universal softmin
sidecar and the public CRC patient-level calibrated rank score.

Short answer: they use the same soft-min response-gate idea, but they are not
the same calculation.

## Cohort Universal Softmin

`universal_axis_softmin_response_probability_mean` is a cohort-level score in
`cohort-level-bench/model_scores/v13_1b/`.

It is computed in two steps:

```text
per_patient_universal_softmin = min(final axis support values)
cohort_score = mean(per_patient_universal_softmin across patients)
```

The per-patient score is `universal_axis_softmin_response_probability`. The
cohort score is the mean of that patient probability within each cohort-drug
row. In the source production tables, the mean recalculates
`universal_axis_softmin_response_probability_mean` to floating-point precision.

The final axis support values are:

- coverage support
- response-conversion support
- resistant-tail/refuge control
- sometimes MOA/context engagement control

If the MOA-aware conversion-control axis is active, the soft-min is taken over
context engagement, coverage, MOA engagement, and resistant-tail control. If it
is not active, the soft-min is taken over the available selected-variant gates.

Code references:

- `src/spatial_benchmarks/universal_axes.py`, `moa_tailored_patient_axis_row`
- `src/spatial_benchmarks/metrics.py`, `softmin`

Released 63-row metric:

- score column: `universal_axis_softmin_response_probability_mean`
- Pearson: `0.6457167802588868`
- Spearman: `0.5187919517683375`
- AUC above disease median: `0.7753549695740365`

## CRC Patient Rank Score

The CRC patient-level rank score is included in
`patient-level-bench/model_scores/crc_moa_tailored_20260525/`.

It starts from five broad module support values:

- `kras_mapk_support`
- `egfr_support`
- `cytostasis_support`
- `escape_control_support`
- `kill_conversion_support`

Those supports are summarized as:

```text
coverage = fraction of module supports greater than 0
mean_support = mean(module supports)
p10_support = 10th percentile(module supports)
```

The rank source intermediate uses a label-free coverage rescale because the CRC
patient adapter has only five module supports:

```text
effective_coverage = min(1, coverage / 0.80)

module_calibrated_intermediate =
  min(
    sigmoid(effective_coverage, center=0.90, scale=0.05),
    sigmoid(mean_support, center=0.0, scale=0.015),
    sigmoid(p10_support, center=-0.02, scale=0.015)
  )
```

The public default score is the within-panel rank of that intermediate:

```text
response_score_rank_calibrated =
  rank(module_calibrated_intermediate within the 11-patient CRC panel) / 11
```

The fixed classifier is:

```text
predicted responder = response_score_rank_calibrated >= 0.5
```

This default score does not use patient labels, observed ORR calibration,
z-scores, or a drug prior to assign rank scores. It is panel-relative, not an
absolute response probability. Non-default raw/probability score columns and
label-aware isotonic apparent calibration columns from the source artifact are
intentionally excluded from the public rank-score table.

Released 11-row CRC metric for `response_score_rank_calibrated`:

- AUC response high: `0.8`
- fixed 0.5 balanced accuracy: `0.7333333333333334`
- predicted responders at 0.5: `6`
- responders/non-responders: `5` / `6`

## Relationship

`universal_axis_softmin_response_probability_mean` is a cohort-level mean of
patient universal-axis softmin probabilities. It uses the same broad "all
response gates must pass" soft-min principle as the CRC MOA-tailored patient
module score, but it is not identical to the CRC patient rank score and not the
warning-pressure patient-level score.
