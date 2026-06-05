# Patient-Level Model Scores

Reviewed public patient-level score artifacts.

- `crc_moa_tailored_20260525/`: compact CRC patient-level MOA-tailored rank
  score table and metrics for 11 CRC patients.
- `cscc_checkpoint_compartment_20260604/`: compact cSCC patient-level
  checkpoint compartment score table and metrics for 12 cSCC patients.

Each model-score folder includes a `reproduce_*.py` script that recomputes the
published metrics from the checked-in score CSV. The public model artifacts are
the released score tables; private checkpoints, raw spatial data, and per-cell
inference outputs are external to this repository.

Clinical-row manifests remain under `patient-level-bench/clinical_rows/` and
are metadata-only.

Observed on-treatment readout artifacts are not model-score artifacts; they are
under `patient-level-bench/observed_readouts/`.
