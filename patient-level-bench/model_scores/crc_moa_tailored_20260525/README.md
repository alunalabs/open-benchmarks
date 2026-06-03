# CRC MOA-Tailored Patient Probability

This folder contains a compact public CRC patient-level score artifact for the
2026-05-25 MOA-tailored module-calibrated response distribution.

## Included

- `crc_patient_moa_tailored_probabilities_20260525.csv`: 11 CRC patient rows
  with clinical labels, broad module supports, raw transfer probability, and
  the default module-calibrated response probability.
- `crc_patient_moa_tailored_metrics_20260525.csv`: label-free metrics for the
  raw transfer probability and the default module-calibrated probability.
- `crc_patient_moa_tailored_summary.json`: machine-readable calculation and
  release summary.
- `MANIFEST.json`: byte sizes and SHA-256 checksums for this folder.

## Default Score

The default score is `response_probability_module_calibrated`.

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

Then:

```text
response_probability_module_calibrated =
  min(
    sigmoid(effective_coverage, center=0.90, scale=0.05),
    sigmoid(mean_support, center=0.0, scale=0.015),
    sigmoid(p10_support, center=-0.02, scale=0.015)
  )
```

The companion raw transfer score, `response_probability_uncalibrated`, uses the
same formula with raw `coverage` instead of `effective_coverage`.

## Metrics

For `response_probability_module_calibrated` on 11 CRC patient rows:

- AUC response high: `0.800`
- fixed 0.5 balanced accuracy: `0.617`
- predicted responders at 0.5: `3`
- responders/non-responders: `5` / `6`

The probability assignment is label-free: it uses no patient labels, observed
ORR calibration, z-scores, or drug prior. Source isotonic apparent calibration
columns are label-aware audit columns and are excluded from this public table.

See `docs/universal_softmin_crc_patient_probability.md` for the relationship
between this patient probability and the cohort universal softmin sidecar.
