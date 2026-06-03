# Patient-Level Bench

The patient-level benchmark evaluates whether pretreatment spatial sections can
predict later clinical response for the same patient.

This folder includes compact clinical-row manifests under `clinical_rows/`.
They contain benchmark identifiers and labels/metadata only; model score and
probability columns are intentionally omitted from those row files.

Reviewed model-score artifacts live under `model_scores/`.

## CRC MOA-Tailored Probability

`model_scores/crc_moa_tailored_20260525/` contains the public CRC patient-level
MOA-tailored probability artifact:

- 11 CRC patient rows.
- Default score: `response_probability_module_calibrated`.
- Default metrics: AUC response high `0.800`, fixed 0.5 balanced accuracy
  `0.617`.

The score starts from broad module supports for KRAS/MAPK, EGFR, cytostasis,
escape control, and kill conversion. Those are summarized into coverage, mean
support, and p10 support, then passed through a soft-min over sigmoid response
gates. The default probability uses a label-free coverage rescale for the
five-module patient surface.

See `docs/universal_softmin_crc_patient_probability.md` for the full formula
and the relationship to the cohort universal softmin sidecar.
