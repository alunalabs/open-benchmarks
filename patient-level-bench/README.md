# Patient-Level Bench

The patient-level benchmark evaluates whether pretreatment spatial sections can
predict later clinical response for the same patient.

`benchmark_summary.csv` is the patient-level benchmark index. It includes CRC
and cSCC model-score metrics, the CRC observed readout, and formula-control
rows with real metric, null p95, and empirical p-value fields.

This folder includes compact clinical-row manifests under `clinical_rows/`.
They contain benchmark identifiers and labels/metadata only; model score and
probability columns are intentionally omitted from those row files.

Reviewed model-score artifacts live under `model_scores/`.
Observed readout artifacts live under `observed_readouts/`; these use measured
on-treatment tissue deltas and are not pretreatment prediction benchmarks.
Formula controls live under `baseline/formula_controls_20260605/`.

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

## cSCC Checkpoint Compartment Score

`model_scores/cscc_checkpoint_compartment_20260604/` contains the public cSCC
patient-level checkpoint response artifact:

- 12 cSCC checkpoint-treated patient rows.
- Default score: `relative_response_probability`.
- Default metrics: AUC response high `0.944`, Spearman response high `0.772`.

The score keeps the universal response-axis product shape used by the CRC
patient and cohort benchmarks, but routes checkpoint biology to the validated
compartments: immune-primary cells for engagement, response conversion,
coverage, and escape/refuge control; epithelial cells for resistant-tail
control. This is a relative p_response ranking score, not a calibrated clinical
ORR probability.

## CRC Module Mean Cosine Readout

`observed_readouts/crc_module_mean_cosine_20260604/` contains a compact
module-cosine artifact for 11 CRC patients:

- Primary readout: `module_mean_cosine`.
- Best mean step: `4`.
- Step 1 mean: `-0.106`.
- Step 4 mean: `0.304`.

The calculation averages predicted and observed gene deltas within each scoring
module, then computes cosine similarity across the resulting module-mean
vectors. This is a program-alignment readout, not a direct responder classifier.

## Formula Controls

`baseline/formula_controls_20260605/` contains deterministic controls that
recompute the released patient formulas after corrupting alignment:

- CRC label shuffle and CRC support-vector shuffle.
- cSCC label shuffle and cSCC axis-vector shuffle.

These are exact public formula controls for the checked-in axis/module score
tables. They are not private hard-donor controls, because donor/context
reruns are not part of the released patient score artifacts.
