# Atlas ORR Support Reasonableness Audit

This audit checks the Atlas support rows behind the fixed `k=8` Atlas ORR baseline on the 63 cohort benchmark v2 evaluation rows.

## Verdict

The Atlas support set is broadly reasonable as a transparent historical-trial prior:

- 191 unique support arms remain after removing the 11 ClinicalTrials.gov/literature audit exceptions.
- These 191 arms span 116 unique NCT records.
- Every remaining support arm is `ctgov_verified_match` under the checked-in ClinicalTrials.gov audit.
- Exact target-drug leakage hits: 0.
- All remaining support arms are non-combination and biomarker-unselected under the Atlas filters.
- Every one of the 63 target rows has verified Atlas support.
- The strict release baseline additionally removes two endpoint-caveat rows, leaving 189 support arms across 114 NCT records.

The main caveat is endpoint strictness. Two CT.gov-verified rows are numerically verified but are not strict CR/PR ORR endpoints:

- Atlas row 4782, NCT01121562, sunitinib, Clinical Benefit Response Rate.
- Atlas row 11729, NCT00201838, control group, 6-month progression-free endpoint.

One additional row is response-like but unconfirmed:

- Atlas row 7251, NCT00872989, vandetanib, unconfirmed partial response.

## Support Coverage

- Target rows: 63
- Verified support rows before endpoint-caveat removal: 191
- Strict release support rows: 189
- Strict release support NCTs: 114
- Strict release per-target support rows: min 16, mean 95.0, max 160
- Strict release per-target support NCTs: min 12, mean 57.9, max 94

## Sensitivity

| Support rule | Removed raw Atlas rows | Pearson | Spearman | AUC above disease median | MAE ORR pct |
| --- | ---: | ---: | ---: | ---: | ---: |
| CTGov/literature-cleaned support | 11 | 0.397 | 0.448 | 0.744 | 11.695 |
| Strict release: also remove two obvious non-ORR endpoint rows | 13 | 0.409 | 0.464 | 0.742 | 11.586 |
| Also remove the unconfirmed-PR row | 14 | 0.409 | 0.474 | 0.740 | 11.632 |

The strict release uses the 13-row removal rule. The signal is not dependent on the questionable rows; removing the two obvious non-ORR rows slightly improves Pearson and Spearman. Removing the unconfirmed response row improves Spearman further with a small MAE tradeoff, so that row is documented as optional sensitivity rather than removed from the default release.

## Files

- `atlas_orr_support_reasonableness_support_rows.csv`: all 191 CTGov-verified support arms with audit classification.
- `atlas_orr_support_reasonableness_flags.csv`: the small endpoint-caveat subset.
- `atlas_orr_support_reasonableness_target_summary.csv`: target-level support coverage for the 63 evaluation rows, including strict release counts.
- `atlas_orr_support_reasonableness_summary.json`: machine-readable summary.
