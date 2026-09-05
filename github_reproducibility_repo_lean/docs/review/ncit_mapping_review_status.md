# NCIt Mapping Review Status

**Status:** review completed; qualified NCIt mapping assertions allowed

## Scope

This status applies to NHANES `cancer_type_code` values mapped to NCI Thesaurus candidates.

## Evidence Received

- `docs/review/evidence/expert review of cancer codes 1.xlsx`
- `docs/review/evidence/expert review of cancer codes 2.rtf`

## Current Decision

The review is no longer pending. Reviewed NCIt IRIs may be asserted only as qualified mapping metadata from self-reported NHANES source codes.

They must not be interpreted as registry-confirmed diagnoses, histology confirmations, stage, treatment, recurrence, or current disease status.

## Generated Files

- `docs/review/ncit_cancer_type_review_sheet_completed.csv`
- `data/processed/approved_cancer_type_ncit_mapping.csv`
- `reports/ncit_expert_review_import_summary.json`

## Import Summary

- Review rows: `33`
- Graph-assertable qualified mappings: `25`
- Not asserted rows: `8`

## Policy

NCIt IRIs are reviewed mappings from self-reported NHANES cancer-type codes. They are not registry-confirmed diagnoses, histology confirmations, staging, treatment, recurrence, or current disease-status assertions. The second oncologist review recommends preserving source-level site information and not inferring histology from prevalence.

## Acknowledgement Names

- Christos Kazazis, MD, specialist doctor in Internal Medicine and Diabetology, Department of History of Medicine and Medical Ethics, National and Kapodistrian University of Athens, Athens, Greece.
- Helena Linardou, MD PhD, Medical Oncologist, Director, 4th Oncology Dept. & Clinical Trials Center, Metropolitan Hospital, Athens, Greece.
