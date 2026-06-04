# Patient-Level Bench

The patient-level benchmark evaluates whether pretreatment spatial sections can
predict later clinical response for the same patient.

This folder includes compact clinical-row manifests under `clinical_rows/`.
They contain benchmark identifiers and labels/metadata only; model score and
probability columns are intentionally omitted from those row files.

Reviewed model-score artifacts live under `model_scores/`.
Observed readout artifacts live under `observed_readouts/`; these use measured
on-treatment state and are not pretreatment prediction benchmarks.

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

See `docs/universal_softmin_crc_patient_rank_score.md` and
`docs/methodology.md` for the full formula and release boundary.

## CRC Observed On-Treatment p_response Readout

`observed_readouts/crc_on_treatment_p_response_20260604/` contains a compact
observed-state readout artifact for 11 CRC on-treatment samples:

- Primary readout: observed absolute-state p_response.
- AUC PR-high: `0.867`.
- Fixed 0.5 balanced accuracy: `0.917`.
- Calls all `5/5` PR patients correctly and `5/6` SD patients correctly; the
  miss is `P11`.

The observed delta p_response comparator is weaker: AUC `0.600`, balanced
accuracy `0.533`. This supports the interpretation that the panel works best as
an on-treatment state readout rather than a pre-to-on delta readout.
