# Cohort Robustness Controls

This folder contains compact hard-donor and gene-shuffle control summaries for
the 44-row cohort-level heterogeneity-magnitude readout.

These files are not the main Gaia, Atlas, or DepMap predictors. They are
specificity checks:

- Hard donor: replace the matched context with same-patient wrong-drug donor
  contexts. This should reduce within-disease correlation if the readout is
  context-specific.
- Gene shuffle: preserve random-control sizes and signs while shuffling gene
  identity. This should reduce within-disease correlation if the readout depends
  on the correct gene/module semantics.

Primary signed-mag-tail-soft summary:

- Real within-disease Spearman: `0.439`
- Random same-patient wrong-drug donor null p95: `0.232`
- Gene-shuffle null p95: `0.371`
- Empirical p for gene-shuffle null >= real: `0.01`

Files:

- `heterogeneity_hard_donor_controls.csv`: real and deterministic wrong-drug
  hard-donor control metrics by variant.
- `heterogeneity_hard_donor_random_summary.csv`: random same-patient
  wrong-drug donor null summaries.
- `heterogeneity_gene_shuffle_controls.csv`: per-shuffle control metrics used
  to recompute the gene-shuffle null summary.
- `heterogeneity_gene_shuffle_random_summary.csv`: random gene-shuffle null
  summaries.
- `heterogeneity_gene_shuffle_hard_readout_controls.csv`: per-shuffle control
  metrics for the harder readout.
- `heterogeneity_gene_shuffle_hard_readout_summary.csv`: gene-shuffle null
  summaries for the harder readout.
