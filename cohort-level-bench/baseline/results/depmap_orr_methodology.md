# DepMap ORR Baseline Methodology

This baseline estimates cohort-drug ORR from DepMap drug-sensitivity screens.
It uses the target drug but not trial outcomes beyond the evaluation labels.

## Primary Baseline

- Inputs: GDSC1, GDSC2, and PRISM AUC matrices plus `Model.csv` lineages.
- Drug matching: normalized compound name with a small salt/prodrug synonym map.
- Disease matching: cohort disease is mapped to DepMap `OncotreeLineage`.
- Score: `1 - mean(percentile_rank(AUC))` over matched-lineage cell lines; higher means more sensitive.

## Primary Metric

- Rows covered: 40
- Pearson: -0.013645548168619076
- Spearman: -0.04384043636775361
- AUC above disease median: 0.47368421052631576

## Covered Screen Counts

- GDSC1: 5
- GDSC2: 29
- PRISM: 6
