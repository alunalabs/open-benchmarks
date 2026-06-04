# CRC Patient Rank Score

This note documents the public CRC patient-level rank score included in
`patient-level-bench/model_scores/crc_moa_tailored_20260525/`.

The public score is `response_score_rank_calibrated`. It is a label-free
within-panel rank score, not an absolute response probability.

## Inputs

The score starts from five broad module support values:

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

## Soft-Min Intermediate

The rank source intermediate uses a label-free coverage rescale because the CRC
patient adapter has five module supports:

```text
effective_coverage = min(1, coverage / 0.80)

module_calibrated_intermediate =
  min(
    sigmoid(effective_coverage, center=0.90, scale=0.05),
    sigmoid(mean_support, center=0.0, scale=0.015),
    sigmoid(p10_support, center=-0.02, scale=0.015)
  )
```

## Public Rank Score

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
z-scores, or a drug prior to assign rank scores. Non-default raw/probability
score columns and label-aware isotonic apparent calibration columns from the
source artifact are intentionally excluded from the public rank-score table.

Released 11-row CRC metric for `response_score_rank_calibrated`:

- AUC response high: `0.800`
- Fixed 0.5 balanced accuracy: `0.733`
- Predicted responders at 0.5: `6`
- Responders/non-responders: `5` / `6`
