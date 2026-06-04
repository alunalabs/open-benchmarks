# CRC Observed On-Treatment p_response Readout

This folder contains a public observed-state validation artifact for the CRC
p_response/module panel. It asks whether the p_response panel separates actual
measured on-treatment CRC samples when scored as absolute on-treatment state.

This is not the public pretreatment CRC prediction benchmark and not the
rank-calibrated CRC score. It uses measured on-treatment state and is included
as a readout sanity check and P2/P12 explainer support.

## Included

- [crc_on_treatment_p_response_readout_metrics.csv](crc_on_treatment_p_response_readout_metrics.csv):
  headline metrics for observed absolute-state p_response, observed delta
  p_response, and the secondary signed MOA-risk adapter.
- [crc_on_treatment_p_response_patient_scores.csv](crc_on_treatment_p_response_patient_scores.csv):
  11 CRC patient rows with observed absolute-state p_response and observed
  delta p_response.
- [crc_on_treatment_p2_p12_module_reference.csv](crc_on_treatment_p2_p12_module_reference.csv):
  P2/P12 module-support reference used by the p_response explainer panel.
- [crc_on_treatment_p_response_summary.json](crc_on_treatment_p_response_summary.json):
  machine-readable summary and boundary.
- [MANIFEST.json](MANIFEST.json): checksums for this folder.

## Headline

Observed absolute-state p_response on 11 CRC patients:

- AUC PR-high: `0.8667`
- Balanced accuracy at `p_response >= 0.5`: `0.9167`
- PR mean: `0.6128`
- SD mean: `0.3545`
- Fixed-threshold calls: all `5/5` PR patients correctly and `5/6` SD
  patients correctly; the miss is `P11`.

Observed delta p_response is weaker:

- AUC PR-high: `0.6000`
- Balanced accuracy at `p_response >= 0.5`: `0.5333`

The signed CRC MOA-risk adapter is also strong in aggregate:

- SD-high AUC: `0.9000`
- Balanced accuracy at risk threshold `0`: `0.8167`

It is not the same object as the p_response explainer. In particular, it
derisks P12 and calls it responder-like, so it should not be used as the
explanation for the P2/P12 p_response panel.

## P2/P12

Observed absolute-state p_response:

- P2: `0.6180`, correctly responder-like.
- P12: `0.3428`, correctly SD-like.

The module reference is directionally consistent: P2 has positive KRAS/MAPK,
EGFR, kill-conversion, and cytostasis support; P12 has weak or negative target
axes and strong negative escape/resistance support.

## Boundary

- Uses measured on-treatment tissue state.
- Does not evaluate pretreatment prediction.
- Does not replace `response_score_rank_calibrated`.
- Best interpreted as an observed-state module-panel validation and explainer
  artifact.
