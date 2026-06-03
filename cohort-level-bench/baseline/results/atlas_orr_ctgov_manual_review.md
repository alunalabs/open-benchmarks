# Atlas ORR ClinicalTrials.gov Manual Review

This file summarizes the 11 non-verified rows from
`atlas_orr_ctgov_audit.csv`. All are Atlas support-arm rows used by the fixed
`atlas_mono_disease_therapy_shrink_k8` score on the 63 cohort-level ORR rows.

The full audit cites ClinicalTrials.gov study URLs and v2 API URLs for every
support row. Status counts:

- Verified directly against ClinicalTrials.gov: 191 / 202 rows.
- CTGov value mismatch: 3 / 202 rows.
- No matching CTGov ORR measurement under the conservative matcher: 8 / 202
  rows.

## Value Mismatches

| NCT ID | Arm | Atlas ORR | CTGov evidence | Review note |
| --- | --- | ---: | --- | --- |
| [NCT00661609](https://clinicaltrials.gov/study/NCT00661609) | AZD4877 | 6.66667 | CTGov ORR outcome reports 2.6% for OG000. | Atlas value does not match posted CTGov percentage. |
| [NCT00470275](https://clinicaltrials.gov/study/NCT00470275) | Cytarabine | 100 | CTGov `Response` outcome reports 0 responders / 10 participants. | Atlas appears to have used the non-responder count rather than responder count. |
| [NCT00454194](https://clinicaltrials.gov/study/NCT00454194) | Arm II (Pemetrexed) | 19.2157 | CTGov confirmed response rate reports 9.8% partial response for OG001. | Atlas value does not match posted CTGov response percentage. |

## No Matching CTGov ORR Measurement

| NCT ID | Arm | Atlas ORR | Review note |
| --- | --- | ---: | --- |
| [NCT00453310](https://clinicaltrials.gov/study/NCT00453310) | sunitinib malate | 30 | Posted outcome title is ORR-like, but categories are stable disease and progression of disease, not CR/PR responders. |
| [NCT01259375](https://clinicaltrials.gov/study/NCT01259375) | All Groups | 33.3333 | CTGov has a 13% partial-response endpoint and a histology-subtype count endpoint; neither matches Atlas ORR under group/title/category rules. |
| [NCT00866320](https://clinicaltrials.gov/study/NCT00866320) | Sorafenib | 30 | Atlas endpoint is tumor-burden reduction, not standard ORR. |
| [NCT00409292](https://clinicaltrials.gov/study/NCT00409292) | RAD001 | 24.1379 | Posted endpoint has stable disease and progressive disease categories only. |
| [NCT04698915](https://clinicaltrials.gov/study/NCT04698915) | Arm A Active GC4711 | 88 | Atlas ORR source is PubMed PMID 38039992; no matching CTGov ORR measurement was found. |
| [NCT00706628](https://clinicaltrials.gov/study/NCT00706628) | BIBF 1120 Monotherapy | 8.3 | Atlas endpoint is RECIST tumor progression rate; CTGov also has an objective-response endpoint, but that is not the Atlas endpoint title for this row. |
| [NCT00706628](https://clinicaltrials.gov/study/NCT00706628) | BIBW 2992 Monotherapy | 50 | Atlas endpoint is RECIST tumor progression rate; CTGov objective response for this arm is 0% at listed time points. |
| [NCT01453595](https://clinicaltrials.gov/study/NCT01453595) | Cohort -1: BEZ235 200mg | 60 | Posted ORR outcome categories are progression of disease and stable disease only, not CR/PR responders. |

## Interpretation

The checked-in Atlas prior results remain reproducible from the original Atlas
CSV, but this audit identifies 11 support rows that should be manually curated
before treating every support ORR as independently re-verified from
ClinicalTrials.gov. The audit files preserve these exceptions rather than
silently correcting or dropping them.
