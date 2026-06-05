# CRC Module Mean Cosine Readout

This folder contains the public CRC module mean cosine artifact. It asks whether the v13.1b visible-persistent cascade predicted tumor program delta aligns with the measured tumor on-treatment minus pretreatment delta.

This is the public cosine readout for the CRC cascade alignment surface. It is not the public pretreatment CRC rank-score benchmark and does not replace `response_score_rank_calibrated`.

## Calculation

For each patient and cascade step:

1. Start with predicted gene deltas from the cascade and observed tumor deltas from paired on-treatment minus pretreatment samples.
2. Average genes within each scoring module to form a six-dimensional predicted module vector and a six-dimensional observed module vector.
3. Compute cosine similarity between those two module-mean vectors.

```text
module_mean_cosine = cosine(mean_gene_delta_by_module_predicted,
                            mean_gene_delta_by_module_observed)
```

The readout uses 41 scoring-panel genes present in the CRC panel and six modules.

## Included

- [crc_module_mean_cosine_step_summary.csv](crc_module_mean_cosine_step_summary.csv): mean module cosine trajectory across cascade steps 1-8.
- [crc_module_mean_cosine_patient_steps.csv](crc_module_mean_cosine_patient_steps.csv): per-patient module mean cosine at each cascade step.
- [crc_module_mean_cosine_module_vectors.csv](crc_module_mean_cosine_module_vectors.csv): predicted and observed module-mean vectors used by the cosine calculation.
- [crc_module_mean_cosine_summary.json](crc_module_mean_cosine_summary.json): machine-readable summary and boundary.
- [reproduce_crc_module_mean_cosine.py](reproduce_crc_module_mean_cosine.py): recompute
  per-patient module cosine and step summary from the released module vectors.
- [MANIFEST.json](MANIFEST.json): checksums for this folder.

## Headline

Mean module mean cosine across 11 CRC patients:

- Step 1 mean: `-0.106`
- Step 4 mean: `0.304`
- Step 4 median: `0.561`
- Step 4 PR mean: `0.522`
- Step 4 SD mean: `0.123`

Step 4 is the best step by cohort mean. Later steps decline in mean similarity.

## Boundary

- Uses measured tumor on-treatment minus pretreatment delta as the observed target.
- Uses v13.1b `visible_persistent` cascade predicted deltas.
- Reports program-level module alignment, not exact within-module gene reconstruction.
- Does not evaluate pretreatment clinical response labels directly.
- Does not replace the public CRC `response_score_rank_calibrated` prediction benchmark.

## Reproduce

```bash
python patient-level-bench/observed_readouts/crc_module_mean_cosine_20260604/reproduce_crc_module_mean_cosine.py
```
