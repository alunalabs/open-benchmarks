# CRC Prior-Control Baselines

This folder contains compact CRC hard-donor and gene-shuffle control summaries
for the 11-patient CRC prior-control audit.

These controls are included to show what each perturbation is testing:

- Hard donor: run the same-regimen surface after replacing the intended donor
  context with a hard mismatched donor context. This checks whether a ranked
  patient surface is genuinely donor/context specific.
- Gene shuffle: run the surface after shuffling gene identity in the prior
  cascade. This checks whether the surface depends on gene/module semantics.

Interpretation boundary:

- The step-4 CRC hard-donor control is a cautionary result. On the public
  `predicted_delta_moa_gate_response_probability` surface, hard donor remains
  almost identical to baseline (`mean_abs_movement = 0.0137`,
  `Pearson vs baseline = 0.999`).
- Gene-shuffle changes the same surface more (`mean_abs_movement = 0.297`,
  `Pearson vs baseline = 0.792`), but this control is still an audit artifact,
  not the promoted CRC patient-level benchmark.
- The promoted CRC patient-level benchmark remains the label-free
  `response_score_rank_calibrated` artifact under `model_scores/`.

Files:

- `crc_patient_prior_control_patient_scores.csv`: sanitized 33-row patient
  score table for baseline, gene-shuffled, and hard-donor controls.
- `crc_patient_prior_control_metrics.csv`: AUC and balanced accuracy by
  control and surface.
- `crc_patient_prior_control_vs_baseline.csv`: step-4 movement versus the
  baseline surface.
- `crc_hard_donor_gene_delta_step_summary.csv`: hard-donor gene-delta
  convergence by cascade step.
- `crc_signed_gate_actual_hard_donor_movement.csv`: signed-gate movement under
  actual gene-shuffled and hard-donor cascades.
