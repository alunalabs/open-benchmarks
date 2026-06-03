# Atlas ORR Literature Review of CTGov Audit Exceptions

This is a second-pass literature audit for the 11 Atlas support-arm rows that
were not directly verified by the conservative ClinicalTrials.gov matcher in
`atlas_orr_ctgov_audit.csv`.

The search used trial NCT IDs, drug names, trial titles, PubMed/NCBI records,
ClinicalTrials.gov publication links, and targeted web searches. Search date:
2026-06-03.

## Summary

- Peer-reviewed trial publications were found for 7 of 11 exception rows.
- One PubMed-sourced Atlas row was traceable to a predecessor avasopasem/SBRT
  publication, but not to results from the listed GRECO-2 NCT.
- Three rows had no peer-reviewed result publication found; their best evidence
  remains the posted ClinicalTrials.gov result record.
- Most exceptions do not rescue the original Atlas value as strict CR/PR ORR.
  The literature usually supports correction to CTGov ORR, correction to zero,
  or exclusion because the Atlas value is stable disease, progression, tumor
  burden reduction, or disease-control-like response.

## Row-Level Interpretation

| NCT ID | Arm | Atlas ORR | Literature/registry finding | Recommended strict-ORR handling |
| --- | --- | ---: | --- | --- |
| [NCT00453310](https://clinicaltrials.gov/study/NCT00453310) | sunitinib malate | 30 | PubMed [19547919](https://pubmed.ncbi.nlm.nih.gov/19547919/) reports no objective responses among 10 enrolled patients. | Set to 0 or exclude. |
| [NCT00661609](https://clinicaltrials.gov/study/NCT00661609) | AZD4877 | 6.66667 | PubMed [23329066](https://pubmed.ncbi.nlm.nih.gov/23329066/) reports 1 confirmed PR among 39 efficacy-evaluable patients, matching CTGov 2.6%. | Correct to 2.6. |
| [NCT01259375](https://clinicaltrials.gov/study/NCT01259375) | All Groups | 33.3333 | PubMed [26897615](https://pubmed.ncbi.nlm.nih.gov/26897615/) reports overall response rate 13% in 23 evaluable patients. | Correct to 13 or exclude subtype endpoint. |
| [NCT00470275](https://clinicaltrials.gov/study/NCT00470275) | Cytarabine | 100 | PubMed [18989890](https://pubmed.ncbi.nlm.nih.gov/18989890/) reports no objective responses among 10 treated patients. | Correct to 0. |
| [NCT00866320](https://clinicaltrials.gov/study/NCT00866320) | Sorafenib | 30 | PubMed [20806321](https://pubmed.ncbi.nlm.nih.gov/20806321/) confirms 30% tumor burden reduction rate, with one unconfirmed PR. | Exclude from strict confirmed ORR. |
| [NCT00409292](https://clinicaltrials.gov/study/NCT00409292) | RAD001 | 24.1379 | PubMed [19047305](https://pubmed.ncbi.nlm.nih.gov/19047305/) reports no complete or partial responses; seven patients had stable disease. | Set to 0 or exclude. |
| [NCT04698915](https://clinicaltrials.gov/study/NCT04698915) | Arm A Active GC4711 | 88 | PubMed [38039992](https://pubmed.ncbi.nlm.nih.gov/38039992/) reports an earlier avasopasem/SBRT study, not GRECO-2 results; the 88% value is stable disease or better at 90 days. PubMed [38264869](https://pubmed.ncbi.nlm.nih.gov/38264869/) is the GRECO-2 study design record. | Exclude from CTGov-verified strict ORR or relabel as predecessor disease-control-like evidence. |
| [NCT00454194](https://clinicaltrials.gov/study/NCT00454194) | Arm II (Pemetrexed) | 19.2157 | No peer-reviewed result publication found; CTGov reports 9.8% partial response for the pemetrexed-only arm. | Correct to CTGov 9.8. |
| [NCT00706628](https://clinicaltrials.gov/study/NCT00706628) | BIBF 1120 Monotherapy | 8.3 | No peer-reviewed result publication found; CTGov reports 8.3% RECIST objective response at 12 weeks, but Atlas labels the endpoint as tumor progression rate. | Keep 8.3 only after endpoint-title curation. |
| [NCT00706628](https://clinicaltrials.gov/study/NCT00706628) | BIBW 2992 Monotherapy | 50 | No peer-reviewed result publication found; CTGov reports 0% RECIST objective response, while 50% matches tumor progression rate. | Correct to 0 or exclude. |
| [NCT01453595](https://clinicaltrials.gov/study/NCT01453595) | Cohort -1: BEZ235 200mg | 60 | PubMed [27286790](https://pubmed.ncbi.nlm.nih.gov/27286790/) reports no objective responses among five response-evaluable patients. | Set to 0 or exclude. |

## Release Guidance

The original Atlas baseline remains reproducible from the raw Atlas snapshot.
For a cleaned strict-ORR release, these exception rows should not be silently
treated as verified Atlas ORR. The safest public benchmark policy is:

1. Keep `atlas_orr_ctgov_audit.csv` as the provenance audit.
2. Use `atlas_orr_literature_review.csv` for exception-level manual curation.
3. For strict CR/PR ORR analyses, correct rows where CTGov and literature agree
   on a value, and exclude rows where the available endpoint is not objective
   response.
