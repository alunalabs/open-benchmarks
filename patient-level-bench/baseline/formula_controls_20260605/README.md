# Patient Formula Controls

These controls recompute the same public patient-level formulas after
deterministic, seeded alignment corruption.

CRC controls:

- Real formula: compute the CRC module soft-min intermediate from KRAS/MAPK,
  EGFR, cytostasis, escape-control, and kill-conversion supports; convert the
  intermediate to a within-panel rank score.
- `crc_label_shuffle`: keeps the released module supports and recomputed rank
  scores fixed, then permutes response labels.
- `crc_support_vector_shuffle`: permutes complete five-module support vectors
  across patient labels, then recomputes the same CRC rank formula.

cSCC controls:

- Real formula: multiply engagement, response-conversion, coverage,
  resistant-tail, and escape/refuge supports.
- `cscc_label_shuffle`: keeps the recomputed product scores fixed, then
  permutes response labels.
- `cscc_axis_vector_shuffle`: permutes complete five-axis vectors across
  patient labels, then recomputes the same product formula.

Headline results:

- CRC real AUC: `0.800`
- CRC support-vector-shuffle AUC null p95: `0.800`
- CRC support-vector-shuffle empirical p(null AUC >= real): `0.062`
- CRC real fixed 0.5 balanced accuracy: `0.733`
- cSCC real AUC: `0.944`
- cSCC axis-vector-shuffle AUC null p95: `0.806`
- cSCC axis-vector-shuffle empirical p(null AUC >= real): `0.003`

Boundary:

- These are exact controls for the public released patient formulas and
  released axis/module columns.
- They are not private hard-donor controls. A hard-donor patient control would
  require rerunning the upstream model with mismatched donor/context inputs,
  which is not part of the public score artifact.

Files:

- `patient_formula_control_real_metrics.csv`: real CRC and cSCC metrics.
- `patient_formula_control_metrics.csv`: per-iteration control metrics.
- `patient_formula_control_summary.csv`: null summaries and empirical p-values.
