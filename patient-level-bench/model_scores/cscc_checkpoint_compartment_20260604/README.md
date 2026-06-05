# cSCC Checkpoint Compartment Patient Score

This folder contains the compact public cSCC patient-level checkpoint response
artifact for the 2026-06-04 compartment-specific checkpoint scorer.

## Included

- `cscc_checkpoint_compartment_patient_scores_20260604.csv`: 12 cSCC patient
  rows at the promoted visible-persistent step-4 checkpoint policy.
- `cscc_checkpoint_compartment_metrics_20260604.csv`: primary response-label
  audit metrics for the promoted score.
- `cscc_checkpoint_compartment_summary.json`: machine-readable calculation and
  release summary.
- `reproduce_cscc_checkpoint_compartment.py`: recompute the released score and
  metrics from the checked-in score CSV.
- `MANIFEST.json`: byte sizes and SHA-256 checksums for this folder.

## Default Score

The default score is `relative_response_probability`.

It uses the same universal response-axis product philosophy as the CRC patient
and cohort-level benchmarks, but routes cSCC checkpoint biology to the
validated compartments:

```text
relative_response_probability =
  immune_primary.engagement_support
  * immune_primary.response_conversion_support
  * immune_primary.coverage_support
  * epithelial.resistant_tail_control
  * immune_primary.escape_refuge_control
```

The fixed compartment map is:

```text
engagement_support -> immune_primary_cells
response_conversion_support -> immune_primary_cells
coverage_support -> immune_primary_cells
resistant_tail_control -> epithelial
escape_refuge_control -> immune_primary_cells
```

## Metrics

For `relative_response_probability` on 12 cSCC checkpoint patients:

- AUC response high: `0.944`
- Spearman response high: `0.772`
- responders/non-responders: `6` / `6`
- mean score in responders: `0.0408`
- mean score in non-responders: `0.0050`

The score is label-free and relative. It uses no patient labels, observed ORR
calibration, z-scores, or drug prior to assign scores. It should be read as a
relative p_response ranking score, not as a calibrated clinical ORR
probability. The larger all-combination axis-source screen is excluded from the
public table; this folder contains only the promoted compartment map.

## Reproduce

```bash
python patient-level-bench/model_scores/cscc_checkpoint_compartment_20260604/reproduce_cscc_checkpoint_compartment.py
```
