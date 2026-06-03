# Active Default Apples-To-Apples Audit

## Verdict

The active default no-prior apoptosis-prevalence score is **formula-consistent and semantically comparable, but not strict raw-source apples-to-apples**.

It is apples-to-apples for the score we are actually using when these checks pass:

- all `1078` patient rows have the required score inputs;
- patient score equals `coverage_support * apoptosis_step4_pred_fraction * resistant_tail_control` for every row;
- cohort score equals the mean of patient scores for every cohort-drug row with patient scores.
- prevalence rows resolve to one generation semantic: `single_cell_marker_panel_matched_null_step4`.

Important diagnostics:

- explicit `ct_hetero_moa_mean` exists for `559/1078` active patient rows, but it is not an input to `apoptosis_prevalence_no_prior_score`;
- provenance can still carry multiple source labels by cache generation date: `default_cache_20260521; ge5_backfill_cache_20260527_prevalence_marker_panel`;
- active-axis policy labels for coverage/tail are: `moa_tailored_available_axis_product_v1; moa_tailored_moa_conversion_control_axis_product_v1`;
- `0` active rows do not have a matching row in the available prevalence provenance artifact.

## Formula Checks

| check | result |
| --- | --- |
| required input completeness | PASS |
| patient formula exact within 1e-12 | PASS |
| max patient formula abs diff | 9.964e-17 |
| cohort score equals patient mean within 1e-12 | PASS |
| max cohort-vs-patient abs diff | 9.714e-17 |
| prevalence generation semantic comparable | PASS |
| single prevalence extraction source | MIXED |
| single coverage/tail axis policy | MIXED |
| strict raw-source apples-to-apples | MIXED |

## Active Metric

| score_col | n_orr | pearson | spearman | within_disease_pair_weighted_pearson | within_disease_pair_weighted_spearman | auc_success_above_disease_median |
| --- | --- | --- | --- | --- | --- | --- |
| apoptosis_prevalence_no_prior_score | 63 | 0.5110 | 0.5202 | 0.4214 | 0.3975 | 0.7647 |

## Required Inputs

| input | nonnull | missing | mean | min | max |
| --- | --- | --- | --- | --- | --- |
| coverage_support | 1078 | 0 | 0.4853 | 0.0000 | 1.0000 |
| apoptosis_step4_pred_fraction | 1078 | 0 | 0.1585 | 0.0000 | 0.5206 |
| resistant_tail_control | 1078 | 0 | 0.5595 | 0.0000 | 1.0000 |
| apoptosis_prevalence_no_prior_score | 1078 | 0 | 0.0680 | 0.0000 | 0.5076 |

## Axis Policy Split

| cohort | prediction_source | axis_policy | moa_conversion_control_applied | n_patient_rows | score_mean | engagement_mean | coverage_mean | tail_mean | apoptosis_pred_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breast | current_production_default | moa_tailored_available_axis_product_v1 | False | 104 | 0.1224 | 1.0000 | 0.6990 | 0.7706 | 0.1840 |
| crc | current_production_default | moa_tailored_available_axis_product_v1 | False | 120 | 0.0424 | 1.0000 | 0.2381 | 0.4598 | 0.1858 |
| crc | ge5_missing_backfill | moa_tailored_available_axis_product_v1 | False | 60 | 0.0114 | 1.0000 | 0.0500 | 0.0833 | 0.1132 |
| crc | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 20 | 0.0314 | 0.1800 | 0.4883 | 0.2922 | 0.1424 |
| gastric | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 350 | 0.0601 | 0.2186 | 0.6292 | 0.5558 | 0.1345 |
| hnscc | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 7 | 0.0649 | 0.1200 | 0.9811 | 0.7153 | 0.0924 |
| nsclc | current_production_default | moa_tailored_available_axis_product_v1 | False | 195 | 0.0942 | 1.0000 | 0.4771 | 0.7543 | 0.1864 |
| nsclc | ge5_missing_backfill | moa_tailored_available_axis_product_v1 | False | 21 | 0.0108 | 1.0000 | 0.0476 | 0.2857 | 0.1078 |
| nsclc | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 42 | 0.0305 | 0.5500 | 0.3295 | 0.2968 | 0.1374 |
| ovarian | current_production_default | moa_tailored_available_axis_product_v1 | False | 48 | 0.1116 | 1.0000 | 0.6033 | 0.7353 | 0.1933 |
| ovarian | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 12 | 0.1572 | 0.1150 | 0.9055 | 0.8643 | 0.1877 |
| pdac | current_production_default | moa_tailored_available_axis_product_v1 | False | 52 | 0.0715 | 1.0000 | 0.3846 | 0.4442 | 0.1772 |
| pdac | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 13 | 0.0065 | 0.1200 | 0.0975 | 0.1309 | 0.1040 |
| prostate | ge5_missing_backfill | moa_tailored_available_axis_product_v1 | False | 8 | 0.0000 | 1.0000 | 0.0000 | 0.8750 | 0.2076 |
| prostate | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 8 | 0.1442 | 0.9000 | 0.7572 | 0.7178 | 0.2040 |
| rcc | ge5_missing_backfill | moa_tailored_moa_conversion_control_axis_product_v1 | True | 18 | 0.0310 | 0.8167 | 0.3895 | 0.4849 | 0.1241 |

## Explicit MOA Completeness

| cohort | prediction_source | n_patient_rows | ct_hetero_moa_mean_nonnull | ct_hetero_moa_mean_complete_rate | ct_hetero_joint_p10_nonnull |
| --- | --- | --- | --- | --- | --- |
| breast | current_production_default | 104 | 0 | 0.0000 | 0 |
| crc | current_production_default | 120 | 0 | 0.0000 | 0 |
| crc | ge5_missing_backfill | 80 | 80 | 1.0000 | 80 |
| gastric | ge5_missing_backfill | 350 | 350 | 1.0000 | 350 |
| hnscc | ge5_missing_backfill | 7 | 7 | 1.0000 | 7 |
| nsclc | current_production_default | 195 | 0 | 0.0000 | 0 |
| nsclc | ge5_missing_backfill | 63 | 63 | 1.0000 | 63 |
| ovarian | current_production_default | 48 | 0 | 0.0000 | 0 |
| ovarian | ge5_missing_backfill | 12 | 12 | 1.0000 | 12 |
| pdac | current_production_default | 52 | 0 | 0.0000 | 0 |
| pdac | ge5_missing_backfill | 13 | 13 | 1.0000 | 13 |
| prostate | ge5_missing_backfill | 16 | 16 | 1.0000 | 16 |
| rcc | ge5_missing_backfill | 18 | 18 | 1.0000 | 18 |

## Prevalence Source Split

| cohort | prediction_source | prevalence_extraction_source | prevalence_granularity | prevalence_generation_semantics | source_row_id_status | n_patient_rows | score_mean | apoptosis_null_mean | apoptosis_pred_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| breast | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 80 | 0.1202 | 0.2003 | 0.1789 |
| breast | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 24 | 0.1296 | 0.2004 | 0.2012 |
| crc | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 18 | 0.0937 | 0.2003 | 0.1982 |
| crc | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 96 | 0.0269 | 0.2002 | 0.1834 |
| crc | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | source_specific_offset:cosmx_crc_6k | 6 | 0.1370 | 0.2002 | 0.1869 |
| crc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 12 | 0.0397 | 0.2002 | 0.2156 |
| crc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 64 | 0.0098 | 0.2002 | 0.1008 |
| crc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | source_specific_offset:cosmx_crc_6k | 4 | 0.0527 | 0.2001 | 0.1503 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_100_108 | 7 | 0.0506 | 0.2012 | 0.0964 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_104_1762 | 7 | 0.0257 | 0.2000 | 0.0989 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_111_1055 | 7 | 0.0508 | 0.2031 | 0.1440 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_114_252 | 7 | 0.0769 | 0.2005 | 0.1638 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_120_1016 | 7 | 0.0867 | 0.2005 | 0.1852 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_124_1042 | 7 | 0.0542 | 0.2014 | 0.1059 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_126_442 | 7 | 0.0894 | 0.2007 | 0.1748 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_130_318 | 7 | 0.0174 | 0.2000 | 0.0870 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_135_1125 | 7 | 0.0608 | 0.2015 | 0.1333 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_138_1007 | 7 | 0.0731 | 0.2014 | 0.1449 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_140_105 | 7 | 0.0890 | 0.2010 | 0.1637 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_144_1214 | 7 | 0.0646 | 0.2015 | 0.1248 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_148_1042 | 7 | 0.0983 | 0.2019 | 0.1845 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_151_1006 | 7 | 0.0182 | 0.2002 | 0.0551 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_156_1022 | 7 | 0.0549 | 0.2003 | 0.1174 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_160_110 | 7 | 0.0081 | 0.2005 | 0.0296 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_166_1024 | 7 | 0.0608 | 0.2007 | 0.1528 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_169_1478 | 7 | 0.0848 | 0.2006 | 0.1444 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_175_1449 | 7 | 0.0358 | 0.2008 | 0.1072 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_179_1012 | 7 | 0.0683 | 0.2003 | 0.1236 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_17_1038 | 7 | 0.0357 | 0.2000 | 0.0742 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_183_1055 | 7 | 0.0481 | 0.2013 | 0.1167 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_185_1001 | 7 | 0.0961 | 0.2009 | 0.1619 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_186_1262 | 7 | 0.0219 | 0.2011 | 0.1133 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_190_1037 | 7 | 0.0345 | 0.2000 | 0.1224 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_192_1154 | 7 | 0.0404 | 0.2015 | 0.1528 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_197_1040 | 7 | 0.0702 | 0.2019 | 0.1411 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_198_1027 | 7 | 0.0525 | 0.2009 | 0.0969 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_205_1007 | 7 | 0.0745 | 0.2013 | 0.1488 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_21_1048 | 7 | 0.0451 | 0.2007 | 0.0962 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_229_1097 | 7 | 0.0579 | 0.2000 | 0.1022 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_23_1156 | 7 | 0.0707 | 0.2008 | 0.1485 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_3_1000 | 7 | 0.0565 | 0.2067 | 0.1388 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_41_1311 | 7 | 0.0689 | 0.2023 | 0.1676 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_44_1276 | 7 | 0.0414 | 0.2042 | 0.1268 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_48_1042 | 7 | 0.0965 | 0.2003 | 0.1925 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_52_1113 | 7 | 0.0084 | 0.2007 | 0.0503 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_56_1020 | 7 | 0.0210 | 0.2013 | 0.0545 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_5_120 | 7 | 0.0164 | 0.2008 | 0.0827 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_60_1027 | 7 | 0.0729 | 0.2000 | 0.1345 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_66_1018 | 7 | 0.0756 | 0.2007 | 0.1320 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_68_1029 | 7 | 0.1255 | 0.2010 | 0.2423 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_72_1401 | 7 | 0.1721 | 0.2004 | 0.3202 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_76_645 | 7 | 0.0387 | 0.2000 | 0.0803 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_80_1 | 7 | 0.1137 | 0.2007 | 0.2487 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_84_144 | 7 | 0.0139 | 0.2008 | 0.0538 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_89_1527 | 7 | 0.0952 | 0.2016 | 0.2366 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_93_2695 | 7 | 0.0464 | 0.2018 | 0.1450 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_97_1055 | 7 | 0.0732 | 0.2027 | 0.1834 |
| gastric | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | unsupported_source_obs_id:c_1_9_1056 | 7 | 0.0539 | 0.2006 | 0.1243 |
| hnscc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 7 | 0.0649 | 0.2003 | 0.0924 |
| nsclc | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 104 | 0.0962 | 0.2003 | 0.1927 |
| nsclc | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 91 | 0.0918 | 0.2002 | 0.1792 |
| nsclc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 42 | 0.0242 | 0.2022 | 0.1305 |
| nsclc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 21 | 0.0234 | 0.2002 | 0.1216 |
| ovarian | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 24 | 0.0804 | 0.2003 | 0.1762 |
| ovarian | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 24 | 0.1428 | 0.2004 | 0.2105 |
| ovarian | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | cell_prefix | 6 | 0.1532 | 0.2002 | 0.1927 |
| ovarian | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 6 | 0.1612 | 0.2004 | 0.1827 |
| pdac | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 32 | 0.0512 | 0.2001 | 0.1672 |
| pdac | current_production_default | default_cache_20260521 | single_cell | single_cell_marker_panel_matched_null_step4 | source_specific_offset:cosmx_pdac_6k | 20 | 0.1039 | 0.2004 | 0.1930 |
| pdac | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 8 | 0.0105 | 0.2001 | 0.0778 |
| pdac | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | source_specific_offset:cosmx_pdac_6k | 5 | 0.0000 | 0.2001 | 0.1458 |
| prostate | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 16 | 0.0721 | 0.2004 | 0.2058 |
| rcc | ge5_missing_backfill | ge5_backfill_cache_20260527_prevalence_marker_panel | single_cell | single_cell_marker_panel_matched_null_step4 | numeric | 18 | 0.0310 | 0.2006 | 0.1241 |
