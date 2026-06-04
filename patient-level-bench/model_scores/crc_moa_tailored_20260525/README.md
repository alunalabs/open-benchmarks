# CRC MOA-Tailored Patient Rank Score

This folder contains the compact public CRC patient-level rank-score artifact
for the 2026-05-25 MOA-tailored response distribution.

## Included

- `crc_patient_moa_tailored_rank_scores_20260525.csv`: 11 CRC patient rows
  with clinical labels, broad module supports, and the default calibrated rank
  score.
- `crc_patient_moa_tailored_metrics_20260525.csv`: label-free metrics for the
  default calibrated rank score.
- `crc_patient_moa_tailored_summary.json`: machine-readable calculation and
  release summary.
- `MANIFEST.json`: byte sizes and SHA-256 checksums for this folder.

## Default Score

The default score is `response_score_rank_calibrated`.

It starts from five broad module supports:

```text
kras_mapk_support
egfr_support
cytostasis_support
escape_control_support
kill_conversion_support
```

The supports are summarized as:

```text
coverage = fraction of module supports greater than 0
mean_support = mean(module supports)
p10_support = 10th percentile(module supports)
effective_coverage = min(1, coverage / 0.80)
```

First, compute the label-free module-calibrated intermediate:

```text
module_calibrated_intermediate =
  min(
    sigmoid(effective_coverage, center=0.90, scale=0.05),
    sigmoid(mean_support, center=0.0, scale=0.015),
    sigmoid(p10_support, center=-0.02, scale=0.015)
  )
```

Then convert that intermediate into a panel-relative rank:

```text
response_score_rank_calibrated =
  rank(module_calibrated_intermediate within the 11-patient CRC panel) / 11
```

The fixed classifier is:

```text
predicted responder = response_score_rank_calibrated >= 0.5
```

## Metrics

For `response_score_rank_calibrated` on 11 CRC patient rows:

- AUC response high: `0.800`
- fixed 0.5 balanced accuracy: `0.733`
- predicted responders at 0.5: `6`
- responders/non-responders: `5` / `6`

The score is label-free and panel-relative: it uses no patient labels, observed
ORR calibration, z-scores, or drug prior to assign the rank score, but the value
depends on the other patients in this 11-patient CRC panel. Non-default
raw/probability score columns and source isotonic apparent calibration columns
are excluded from this public table.

See `docs/universal_softmin_crc_patient_rank_score.md` and
`docs/methodology.md` for the calculation and release boundary.
