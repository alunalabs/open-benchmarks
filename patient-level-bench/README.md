# Patient-Level Bench

The patient-level benchmark evaluates whether pretreatment spatial sections can
predict later clinical response for the same patient.

This folder includes compact clinical-row manifests under `clinical_rows/`.
They contain benchmark identifiers and labels/metadata only; model score and
probability columns are intentionally omitted from those row files.

Reviewed model-score artifacts live under `model_scores/`.

## CRC MOA-Tailored Rank Score

`model_scores/crc_moa_tailored_20260525/` contains the public CRC patient-level
MOA-tailored rank-score artifact:

- 11 CRC patient rows.
- Default score: `response_score_rank_calibrated`.
- Default metrics: AUC response high `0.800`, fixed 0.5 balanced accuracy
  `0.733`.

The score starts from broad module supports for KRAS/MAPK, EGFR, cytostasis,
escape control, and kill conversion. Those are summarized into coverage, mean
support, and p10 support, then passed through a soft-min over sigmoid response
gates to produce a label-free intermediate. The public default converts that
intermediate into a within-panel rank score and classifies rank >= 0.5 as a
responder. This score is panel-relative, not an absolute response probability.

See `docs/universal_softmin_crc_patient_rank_score.md` for the full formula
and the relationship to the cohort universal softmin sidecar.
