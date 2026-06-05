# Marker-Cache Control Audit

This folder contains a negative hard-donor and gene-shuffle audit for a
non-promoted full-cache spreadsheet-marker scorer.

This is not the promoted cohort ORR benchmark and it is not an Atlas or DepMap
baseline. It is included as an audit showing that a direct spreadsheet marker
scorer over cached gene deltas did not validate gene identity.

Rows:

- Real full-cache marker rows with continuous ORR: `45`.
- Real full-cache marker rows with binary success labels: `39`.
- Gene-shuffle null iterations in the metric table: `200`.

Primary audit score:

```text
full_marker_score_coverage_weighted_mean
```

Headline audit result:

- Real standalone marker binary AUC: `0.366`.
- Real standalone marker binary Spearman: `-0.232`.
- Real standalone marker continuous-ORR Pearson: `-0.018`.
- Gene-shuffle AUC null p95: `0.611`.
- Gene-shuffle empirical p(null AUC >= real AUC): `0.765`.
- Hard-donor marker-swap AUC: `0.655`.

Interpretation:

- The standalone marker scorer fails as a direct response benchmark.
- The hard-donor marker swap beats the real marker score.
- The real marker score sits inside or below the gene-shuffle null
  distribution.
- Therefore this audit is a cautionary negative control, not a release-grade
  predictive baseline.

Files:

- `marker_full_cache_real_scores.csv`: sanitized real marker-score rows.
- `marker_full_cache_hard_donor_scores.csv`: sanitized hard-donor marker-swap
  score rows.
- `marker_full_cache_gene_shuffle_sample_scores.csv`: sampled shuffled
  row-level scores for inspection.
- `marker_full_cache_metrics.csv`: real metric rows.
- `marker_full_cache_hard_donor_metrics.csv`: hard-donor metric rows.
- `marker_full_cache_gene_shuffle_metrics.csv`: per-iteration gene-shuffle
  metric rows.
- `marker_full_cache_gene_shuffle_null_summary.csv`: checked-in null summary.
- `marker_full_cache_summary.json`: compact headline metric summary.
