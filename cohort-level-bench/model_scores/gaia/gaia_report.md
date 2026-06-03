# Universal Response-Axis Cohort Default V2

## Summary

This snapshot promotes `apoptosis_prevalence_no_prior_score` as the active v2 cohort default on the
retained GE5 cohort surface. The previous engagement-weighted apoptosis score,
`apoptosis_prevalence_basic_score`, and the previous active-axis product,
`relative_response_probability_mean`, remain in the artifacts as sidecars for
comparison.

The default score is:

```text
coverage_support * apoptosis_step4_pred_fraction * resistant_tail_control
```

CRC ORR labels for bortezomib, 5-fluorouracil, irinotecan, and oxaliplatin are
sourced from the 2026-05-27 curation artifact and remain part of the v2 default.

Key behavior:

- Cohort rows: `69`
- ORR-scored rows with default predictions: `63`
- Pearson r: `0.5110`
- Spearman rho: `0.5202`
- Within-disease Pearson: `0.4214`
- Within-disease Spearman: `0.3975`
- Disease-median AUC: `0.7647`

## Prediction Sources

| prediction_source | rows |
| --- | --- |
| current_production_default | 39 |
| ge5_missing_backfill | 26 |
| missing_prediction | 4 |

## Default Versus Sidecars

| score | pearson | spearman | within_disease_spearman | auc | mean_score |
| --- | --- | --- | --- | --- | --- |
| apoptosis_prevalence_no_prior_score | 0.511 | 0.5202 | 0.3975 | 0.7647 | 0.07538 |
| apoptosis_prevalence_basic_score | 0.5527 | 0.4905 | 0.5185 | 0.7799 | 0.0641 |
| prob_apoptosis_prevalence_orr_gt_20pct | 0.6504 | 0.5638 | 0.4717 | 0.7353 | 0.1102 |
| universal_axis_softmin_response_probability_mean | 0.6457 | 0.5188 | 0.4822 | 0.7754 | 0.3173 |
| legacy_relative_response_probability_mean | 0.6434 | 0.5022 | 0.4932 | 0.7784 | 0.2705 |

`prob_apoptosis_prevalence_orr_gt_20pct` is the best packaged 63-row Pearson
sidecar. `universal_axis_softmin_response_probability_mean` is the universal
softmin sidecar and the second-best packaged Pearson sidecar. Both are included
for leaderboard transparency; the active/default score remains
`apoptosis_prevalence_no_prior_score`.

## Global Metrics

| scope | disease | score_policy | readout | score_col | label | n_orr | pearson | spearman | within_disease_pair_weighted_pearson | within_disease_pair_weighted_spearman | auc_success_above_disease_median | mean_response_probability | mean_expected_response_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | all | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 63 | 0.511 | 0.5202 | 0.4214 | 0.3975 | 0.7647 | 0.07538 | 7.538 |
| global | all | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptosis_prevalence_no_prior_response_count_distribution | prob_apoptosis_prevalence_no_prior_orr_gt_20pct | prob_apoptosis_prevalence_no_prior_orr_gt_20pct | 63 | 0.5591 | 0.5599 | 0.4474 | 0.3826 | 0.7363 | 0.1021 | 10.21 |
| global | all | apoptosis_prevalence_axis_v1 | patient_apoptotic_fraction_axis_substitution_with_engagement_prior | apoptosis_prevalence_basic_score | apoptosis_prevalence_basic_score | 63 | 0.5527 | 0.4905 | 0.4818 | 0.5185 | 0.7799 | 0.0641 | 6.41 |
| global | all | apoptosis_prevalence_axis_v1 | patient_apoptosis_prevalence_response_count_distribution_with_engagement_prior | prob_apoptosis_prevalence_orr_gt_20pct | prob_apoptosis_prevalence_orr_gt_20pct | 63 | 0.6504 | 0.5638 | 0.5048 | 0.4717 | 0.7353 | 0.1102 | 11.02 |
| global | all | legacy_universal_response_axes_v1 | legacy_patient_response_axis_probability_distribution | relative_response_probability_mean | legacy_universal_axis_product_probability_mean | 63 | 0.6434 | 0.5022 | 0.4554 | 0.4932 | 0.7784 | 0.2705 | 27.05 |
| global | all | legacy_universal_response_axes_v1 | legacy_patient_response_axis_probability_distribution | universal_axis_softmin_response_probability_mean | legacy_universal_axis_softmin_probability_mean | 63 | 0.6457 | 0.5188 | 0.4182 | 0.4822 | 0.7754 | 0.3173 | 31.73 |
| global | all | legacy_universal_response_axes_v1 | legacy_patient_response_axis_probability_distribution | universal_axis_geomean_response_probability_mean | legacy_universal_axis_geomean_probability_mean | 63 | 0.6138 | 0.58 | 0.3748 | 0.4554 | 0.7561 | 0.4099 | 40.99 |
| global | all | legacy_universal_response_axes_v1 | legacy_patient_response_axis_probability_distribution | prob_universal_axis_orr_gt_20pct | legacy_prob_universal_axis_orr_gt_20pct | 63 | 0.5563 | 0.5 | 0.3788 | 0.4954 | 0.7267 | 0.4013 | 40.13 |
| global | all | legacy_moa_tailored_response_distribution | legacy_source_moa_tailored_response_probability | response_probability_mean | legacy_source_moa_tailored_response_probability_mean | 63 | 0.4294 | 0.2892 | 0.263 | 0.3178 | 0.6668 | 0.2686 | 26.86 |

## Disease Metrics

| scope | disease | score_policy | readout | score_col | label | n_orr | pearson | spearman | within_disease_pair_weighted_pearson | within_disease_pair_weighted_spearman | auc_success_above_disease_median | mean_response_probability | mean_expected_response_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| disease | breast | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 8 | 0.4955 | 0.5952 | 0.4955 | 0.5952 | 0.9375 | 0.1224 | 12.24 |
| disease | crc | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 10 | -0.3804 | -0.04573 | -0.3804 | -0.04573 | 0.5 | 0.03203 | 3.203 |
| disease | gastric | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 7 | 0.8584 | 0.6071 | 0.8584 | 0.6071 | 0.9167 | 0.06012 | 6.012 |
| disease | hnscc | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 1 |  |  |  |  |  | 0.06493 | 6.493 |
| disease | nsclc | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 15 | 0.5298 | 0.4613 | 0.5298 | 0.4613 | 0.8929 | 0.08521 | 8.521 |
| disease | ovarian | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 10 | 0.5126 | 0.2727 | 0.5126 | 0.2727 | 0.68 | 0.1207 | 12.07 |
| disease | pdac | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 5 | 0.6966 | 0.9 | 0.6966 | 0.9 | 0.8333 | 0.05845 | 5.845 |
| disease | prostate | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 1 |  |  |  |  |  | 0 | 0 |
| disease | rcc | apoptosis_prevalence_no_prior_axis_v1 | patient_apoptotic_fraction_no_prior_axis_substitution | apoptosis_prevalence_no_prior_score | apoptosis_prevalence_no_prior_score | 6 | 0.8599 | 0.6571 | 0.8599 | 0.6571 | 0.7778 | 0.03095 | 3.095 |

## Rows Without Default Predictions

| cohort | drug_surface | drug_norm | orr_pct | label_source |
| --- | --- | --- | --- | --- |
| gastric | Docetaxel | docetaxel | 9 | v2_external_manual_seed |
| gastric | Paclitaxel | paclitaxel | 3.8 | v2_external_manual_seed |
| hnscc | Docetaxel | docetaxel | 10 | v2_external_manual_seed |
| prostate | Docetaxel | docetaxel |  | v2_manual_seed |

## Interpretation

The promoted default removes the non-cascade engagement/context prior from the
apoptosis-prevalence score. It uses coverage support, the fraction of tumor-like
cells called apoptotic at step 4, and resistant-tail control. The score is not
fitted to clinical ORR and its mean scale is lower than the legacy active-axis
probability; `expected_response_pct` / `expected_orr_pct` are therefore
continuity aliases for `100 * apoptosis_prevalence_no_prior_score`, not calibrated clinical response
rates.

All prevalence rows in the promoted combined raw table are true single-cell marker-panel fractions.

The existing gene-shuffle and hard-donor susceptibility artifacts are retained
as legacy active-axis controls for `relative_response_probability_mean`; they
were not recomputed for the apoptosis-prevalence default in this promotion.
