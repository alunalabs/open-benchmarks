# Patient-Level Clinical Rows

This folder contains compact patient-level clinical-row manifests.

Files:

- `universal_patient_response_axes_clinical_rows_20260525.csv`: 23 public
  clinical label rows from the universal patient response axes surface
  (`11` CRC and `12` cSCC).
- `crc_patient_clinical_rows_20260525.csv`: 11 CRC regimen/outcome rows with
  responder/non-responder labels.

These files include row identifiers and clinical labels/metadata only. They do
not include model score, probability, or per-cell output columns.

Reviewed CRC patient-level probability rows are published separately under
`patient-level-bench/model_scores/crc_moa_tailored_20260525/`.
