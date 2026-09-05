# Real Accelerometry Source Selection

**Decision:** select PhysioNet NHANES-derived step/activity-count data version 1.0.2 as the near-term real non-synthetic source extension.

This is not an NCIt task. NCIt expert review remains pending and no NCIt disease IRIs should be asserted because of this source selection.

## Selected Source

| Field | Value |
|---|---|
| source_id | physionet_nhanes_steps_activity_counts_v1_0_2 |
| source_name | Minute level step counts and physical activity data from NHANES 2011-2014 |
| repository | PhysioNet |
| version | 1.0.2 |
| published | 2026-08-06 |
| doi | 10.13026/d7sw-f662 |
| landing_page | https://physionet.org/content/minute-level-step-count-nhanes/1.0.2/ |
| download_root | https://physionet.org/files/minute-level-step-count-nhanes/1.0.2/ |
| access | open access under PhysioNet terms |
| license | Creative Commons Zero 1.0 Universal Public Domain Dedication |
| size_uncompressed | 2.7 GB |
| selection_decision | selected_for_near_term_real_source_extension |
| selection_reason | Real non-synthetic derived accelerometry source with step-count algorithms, ActiGraph activity counts, MIMS, wear prediction, and quality flags. It can link to the existing NHANES cohort by SEQN and day. |
| top_tier_limitation | It is not an independent external cohort; it is a real derived source from the same NHANES wrist accelerometry population. CAPTURE-24 remains the stronger external open validation candidate. |

## Why This Source

The source is open, current, real, and directly linkable to the existing NHANES cancer-history cohort through `SEQN` and measurement day. It adds derived step-count and ActiGraph activity-count variables, enabling a real naive-vs-semantic harmonisation experiment without inventing a synthetic second source.

It is still not the final strongest top-tier validation because it is derived from the same NHANES wrist accelerometry population. CAPTURE-24 and NCI IDATA remain external-source candidates.

## Required Files

| file_group | file_name | priority | purpose | expected_size | integration_use |
| --- | --- | --- | --- | --- | --- |
| metadata | subject-info.csv | required_first | Confirm SEQN linkage and coverage against the current cancer-history cohort. | 926.3 KB | cohort overlap and source manifest |
| documentation | data_README.md | required_first | Record source-variable definitions, file layout, and version-specific notes. | 2.9 KB | provenance and citation evidence |
| checksums | SHA256SUMS.txt | required_first | Verify downloaded files and support reproducibility. | 3.0 KB | source manifest checksums |
| activity_counts | csv/nhanes_1440_AC.csv.xz | required_for_first_metric_experiment | Add ActiGraph activity counts as a real derived source variable. | large | daily and valid-minute activity-count summaries |
| step_counts | csv/nhanes_1440_actisteps.csv.xz | required_for_first_step_experiment | Add ActiLife step-count estimates for naive-vs-semantic comparison. | large | daily step-count summaries |
| wear_prediction | csv/nhanes_1440_PAXPREDM.csv.xz | recommended | Compare source-provided wear prediction to existing PAXMIN/PAXDAY protocol variables. | large | valid-day protocol compatibility checks |
| quality_flags | csv/nhanes_1440_PAXFLGSM.csv.xz | recommended | Preserve data-quality context for derived metrics. | small_to_medium | quality/provenance safeguards |

## Candidate Comparison

| candidate_id | decision | is_real_source | is_external_cohort | access | linkage_to_current_cohort | primary_value | main_limitation | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| physionet_nhanes_steps_activity_counts_v1_0_2 | selected_now | True | False | open | direct SEQN/day linkage | real derived metrics: step counts, ActiGraph activity counts, Troiano wear, MIMS | same NHANES wrist accelerometry population | download metadata/checksums first, then selected compressed metric files |
| capture24 | external_validation_candidate | True | True | open large download | no participant linkage; semantic comparison only | external free-living wrist accelerometry with activity annotations | not cancer-specific and large download | use after PhysioNet extension or if external-cohort validation becomes required |
| nci_idata_actigraph | best_cancer_relevant_candidate_after_access | True | True | approval required | no direct linkage expected | cancer-relevant ActiGraph epoch data | requires CDAS project approval and data transfer | prepare project proposal if cancer-specific external validation is required |

## Integration Plan

1. Download `subject-info.csv`, `data_README.md`, `SHA256SUMS.txt`, and `LICENSE.txt` first.
2. Confirm overlap between PhysioNet `SEQN` values and the current cancer-history cohort.
3. Download one metric file first, preferably `csv/nhanes_1440_AC.csv.xz` or `csv/nhanes_1440_actisteps.csv.xz`.
4. Build daily summaries for the current cohort only to avoid unnecessary full-dataset expansion.
5. Add source-variable mappings for activity counts and step-count outputs.
6. Repeat naive-vs-semantic risk evaluation using this real source.

## Current Status

Selection status: `selected_metadata_downloaded`

Selected source id: `physionet_nhanes_steps_activity_counts_v1_0_2`
