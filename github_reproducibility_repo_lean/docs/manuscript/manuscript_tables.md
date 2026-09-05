# Manuscript Tables and Figure Data

**Purpose:** deterministic manuscript/proposal assets generated from the current pipeline outputs.

These tables are downstream summaries. Reviewed NCIt mappings are qualified self-reported source-code mappings only; the tables do not reinterpret wrist MIMS as MVPA, sedentary, active/inactive, or clinical physical-activity classification.

## Generated Artifacts

| Artifact | Role |
|---|---|
| `docs/manuscript/table1_cohort_construction.csv` | Manuscript table: table1_cohort_construction |
| `docs/manuscript/table2_protocol_definitions.csv` | Manuscript table: table2_protocol_definitions |
| `docs/manuscript/table3_protocol_outcome_sensitivity.csv` | Manuscript table: table3_protocol_outcome_sensitivity |
| `docs/manuscript/table3_pairwise_protocol_discordance.csv` | Manuscript table: table3_pairwise_protocol_discordance |
| `docs/manuscript/table4_kg_validation.csv` | Manuscript table: table4_kg_validation |
| `docs/manuscript/table5_harmonisation_compatibility.csv` | Manuscript table: table5_harmonisation_compatibility |
| `docs/manuscript/table5_harmonisation_status_counts.csv` | Manuscript table: table5_harmonisation_status_counts |
| `docs/manuscript/table6_protocol_citation_evidence.csv` | Manuscript table: table6_protocol_citation_evidence |
| `docs/manuscript/table6_protocol_citation_counts.csv` | Manuscript table: table6_protocol_citation_counts |
| `docs/manuscript/table7_competency_questions.csv` | Manuscript table: table7_competency_questions |
| `docs/manuscript/figure1_pipeline_counts.csv` | Figure data: figure1_pipeline_counts |
| `docs/manuscript/figure2_harmonisation_status_counts.csv` | Figure data: figure2_harmonisation_status_counts |
| `docs/manuscript/figure3_protocol_sensitivity.csv` | Figure data: figure3_protocol_sensitivity |
| `docs/manuscript/manuscript_tables.md` | Human-readable manuscript table package |

## Claim Boundary

MIMS values are movement-summary metrics only; no MVPA, sedentary, active/inactive, or clinical physical activity classification is made.

NCIt review status: `review_completed_qualified_assertions_allowed`; qualified NCIt assertion count: `19`.


## Table 1. Cohort Construction

| Stage | NHANES 2011-2012 | NHANES 2013-2014 | Total |
| --- | --- | --- | --- |
| All NHANES participants | 9756 | 10175 | 19931 |
| Age 20 or older | 5560 | 5769 | 11329 |
| Self-reported cancer history, MCQ220 = 1 | 488 | 547 | 1035 |
| Physical activity monitor header available | 462 | 530 | 992 |
| Daily physical activity monitor summary available | 406 | 472 | 878 |
| Minute-level physical activity monitor data available | 406 | 472 | 878 |

## Table 2. Protocol Definitions and Interpretation Limits

| Protocol | Definition | Expression | Minimum valid days | Review status | Classification type | Interpretation limit |
| --- | --- | --- | --- | --- | --- | --- |
| wake_wear_10h_min4 | At least 10 hours valid wake wear on at least 4 days | PAXWWMD >= 600 | 4 | approved_completeness_rule | candidate completeness rule | Completeness/sensitivity rule only; not an activity classification. |
| wake_wear_12h_min4 | At least 12 hours valid wake wear on at least 4 days | PAXWWMD >= 720 | 4 | approved_sensitivity_rule | sensitivity completeness rule | Completeness/sensitivity rule only; not an activity classification. |
| valid_minutes_20h_min4 | At least 20 hours valid data on at least 4 days | PAXVMD >= 1200 | 4 | approved_24h_completeness_rule | 24-hour completeness rule | Completeness/sensitivity rule only; not an activity classification. |

## Table 3. Protocol Outcome Sensitivity

| Protocol | Eligible participants | Eligible % | Valid day rows | Mean participant daily MIMS | Mean participant peak-30 valid MIMS | Interpretation limit |
| --- | --- | --- | --- | --- | --- | --- |
| wake_wear_10h_min4 | 807 | 91.91344 | 5553 | 11567.603003 | 814.698825 | Movement-summary sensitivity only; not MVPA, sedentary, active/inactive, or clinical physical activity classification. |
| wake_wear_12h_min4 | 722 | 82.232346 | 4824 | 12201.537613 | 836.718342 | Movement-summary sensitivity only; not MVPA, sedentary, active/inactive, or clinical physical activity classification. |
| valid_minutes_20h_min4 | 862 | 98.177677 | 6111 | 10827.114119 | 781.146019 | Movement-summary sensitivity only; not MVPA, sedentary, active/inactive, or clinical physical activity classification. |

## Table 3b. Pairwise Protocol Discordance

| Left protocol | Right protocol | Both eligible | Left only | Right only | Neither | Discordant participants |
| --- | --- | --- | --- | --- | --- | --- |
| wake_wear_10h_min4 | wake_wear_12h_min4 | 722 | 85 | 0 | 71 | 85 |
| wake_wear_10h_min4 | valid_minutes_20h_min4 | 806 | 1 | 56 | 15 | 57 |
| wake_wear_12h_min4 | valid_minutes_20h_min4 | 721 | 1 | 141 | 15 | 142 |

## Table 4. Pilot KG Summary and Validation

| Measure | Value |
| --- | --- |
| Participants | 20 |
| Cancer diagnoses | 25 |
| Cancer history assertions | 20 |
| Daily movement summaries | 60 |
| Minute observations | 300 |
| Derived feature sets | 60 |
| Processing protocols | 3 |
| Protocol application results | 60 |
| Protocol citation evidence nodes | 12 |
| Activity data sources | 4 |
| Harmonisation source-variable mappings | 9 |
| Independent PAM daily summaries | 20 |
| Harmonised activity definitions | 4 |
| Synthetic daily activity summaries | 60 |
| RDF triples | 9324 |
| pySHACL conforms | True |
| Validation failed checks | 0 |
| Failed policy checks | 0 |
| NCIt review status | review_completed_qualified_assertions_allowed |
| NCIt assertion count while pending | 19 |

## Table 5. Harmonisation Compatibility

| Source | Variable | Label | Device location | Unit | Harmonised construct | Compatibility status | Interpretation limit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nhanes_2011_2014_wrist_mims | PAXMTSD | Daily total MIMS | wrist | MIMS | daily movement volume | source-specific metric; not directly convertible | Do not apply hip counts/minute intensity thresholds to MIMS. |
| nhanes_2011_2014_wrist_mims | PAXWWMD | Valid wake wear minutes | wrist | minute | valid wear completeness | compatible after protocol abstraction | Completeness rule only; not an activity classification. |
| nhanes_2011_2014_wrist_mims | PAXVMD | Valid minutes | wrist | minute | valid data completeness | compatible after protocol abstraction | Does not encode intensity. |
| synthetic_hip_counts_demo | daily_total_vertical_axis_counts | Daily total vertical-axis counts | hip | count | daily movement volume | source-specific metric; not directly convertible | Not comparable as a numeric equivalent of MIMS. |
| synthetic_hip_counts_demo | valid_wear_minutes | Valid wear minutes | hip | minute | valid wear completeness | compatible after protocol abstraction | Completeness rule only; not an activity classification. |
| synthetic_hip_counts_demo | mvpa_minutes_1952_cpm | MVPA minutes by 1952 counts/minute cut point | hip | minute | source-defined activity intensity | not harmonisable with NHANES wrist MIMS in current KG | Requires hip counts/minute protocol context. |
| synthetic_hip_counts_demo | sedentary_minutes_100_cpm | Sedentary minutes by 100 counts/minute cut point | hip | minute | source-defined sedentary classification | not harmonisable with NHANES wrist MIMS in current KG | Requires hip counts/minute protocol context. |
| nhanes_2003_2006_hip_actigraph_pam | PAXINTEN | ActiGraph AM-7164 hip-worn activity counts per 1-minute epoch | hip | device-specific activity counts/minute | daily movement volume | broad construct only; numeric equivalence blocked | Do not convert hip ActiGraph counts to wrist MIMS. Do not treat cut-points, MVPA, sedentary time, or total volume as numerically equivalent without protocol-specific validation. |
| nhanes_2005_2006_hip_actigraph_pam | PAXSTEP | ActiGraph AM-7164 hip-worn step count per 1-minute epoch | hip | steps/minute | daily ambulatory volume | source-specific step metric; no conversion from/to MIMS | Steps can be summarized as a real ambulatory metric, but cannot be inferred from NHANES 2011-2014 wrist MIMS and cannot validate MIMS-to-steps conversion. |

## Table 5b. Harmonisation Compatibility Counts

| Source | Compatibility status | Rows |
| --- | --- | --- |
| nhanes_2003_2006_hip_actigraph_pam | broad construct only; numeric equivalence blocked | 1 |
| nhanes_2005_2006_hip_actigraph_pam | source-specific step metric; no conversion from/to MIMS | 1 |
| nhanes_2011_2014_wrist_mims | compatible after protocol abstraction | 2 |
| nhanes_2011_2014_wrist_mims | source-specific metric; not directly convertible | 1 |
| synthetic_hip_counts_demo | compatible after protocol abstraction | 1 |
| synthetic_hip_counts_demo | not harmonisable with NHANES wrist MIMS in current KG | 2 |
| synthetic_hip_counts_demo | source-specific metric; not directly convertible | 1 |

## Table 6. Protocol Citation Evidence

| Protocol | Evidence role | Support level | Source title | Supported component | Interpretation limit |
| --- | --- | --- | --- | --- | --- |
| wake_wear_10h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | source variable PAXWWMD | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| wake_wear_10h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | source variable PAXWWMD | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| wake_wear_10h_min4 | literature_context | context_only_not_wrist_mims_validation | Catalog of NHANES accelerometer rules, variables, and definitions | 10h/day and min4-days context | Use only to justify why 10h/min4 is a reasonable sensitivity/completeness candidate to represent and test. |
| wake_wear_10h_min4 | project_review_decision | local_project_review_support | Project protocol review sheet | project approval status | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |
| wake_wear_12h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | source variable PAXWWMD | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| wake_wear_12h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | source variable PAXWWMD | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| wake_wear_12h_min4 | literature_context | context_only_not_wrist_mims_validation | Catalog of NHANES accelerometer rules, variables, and definitions | 12h/day sensitivity context | Use only as rationale for retaining a stricter sensitivity rule. |
| wake_wear_12h_min4 | project_review_decision | local_project_review_support | Project protocol review sheet | project approval status | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |
| valid_minutes_20h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | source variable PAXVMD | Use PAXVMD only as a valid minutes completeness input in this project. |
| valid_minutes_20h_min4 | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | source variable PAXVMD | Use PAXVMD only as a valid minutes completeness input in this project. |
| valid_minutes_20h_min4 | literature_context | context_only_not_threshold_validation | Minute-level step counts and physical activity data from NHANES 2011-2014 | 24-hour wrist accelerometry context | Use only as context for representing a 24-hour completeness sensitivity rule. |
| valid_minutes_20h_min4 | project_review_decision | local_project_review_support | Project protocol review sheet | project approval status | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |

## Table 6b. Protocol Citation Evidence Counts

| Evidence role | Support level | Rows |
| --- | --- | --- |
| literature_context | context_only_not_threshold_validation | 1 |
| literature_context | context_only_not_wrist_mims_validation | 2 |
| project_review_decision | local_project_review_support | 3 |
| source_variable_definition | direct_source_variable_support | 6 |

## Table 7. Competency Questions

| Query | Rows returned | Reviewer risk addressed | Source query |
| --- | --- | --- | --- |
| CQ1_PROTOCOL_DISCORDANCE | 40 | Protocol choice changes inclusion | queries/competency/cq1_protocol_discordance.rq |
| CQ2_PROTOCOL_REVIEW_STATUS | 3 | Protocols are reviewed completeness/sensitivity rules | queries/competency/cq2_protocol_review_status.rq |
| CQ3_PENDING_CANCER_TYPE_MAPPINGS | 25 | NCIt candidates are not overasserted | queries/competency/cq3_pending_cancer_type_mappings.rq |
| CQ4_DAILY_FEATURE_PROVENANCE | 60 | Movement features expose provenance | queries/competency/cq4_daily_feature_provenance.rq |
| CQ5_MINUTE_MEASUREMENT_CONTEXT | 300 | MIMS/wear-state/quality context is queryable | queries/competency/cq5_minute_measurement_context.rq |
| CQ6_SELF_REPORTED_CANCER_HISTORY | 20 | Cohort is not overclaimed as clinically verified survivorship | queries/competency/cq6_self_reported_cancer_history.rq |
| CQ7_HARMONISATION_COMPATIBILITY | 13 | Compatibility and incompatibility are queryable | queries/competency/cq7_harmonisation_compatibility.rq |
| CQ8_PROTOCOL_CITATION_PROVENANCE | 12 | Protocol evidence and support levels are queryable | queries/competency/cq8_protocol_citation_provenance.rq |
| CQ9_INDEPENDENT_PAM_SOURCE_VALIDATION | 20 | Independent PAM source evidence and non-conversion limits are queryable | queries/competency/cq9_independent_pam_source_validation.rq |

## Figure Data 1. Pipeline Counts

| Pipeline stage | NHANES 2011-2012 | NHANES 2013-2014 | Total |
| --- | --- | --- | --- |
| All NHANES participants | 9756 | 10175 | 19931 |
| Age 20 or older | 5560 | 5769 | 11329 |
| Self-reported cancer history, MCQ220 = 1 | 488 | 547 | 1035 |
| Physical activity monitor header available | 462 | 530 | 992 |
| Daily physical activity monitor summary available | 406 | 472 | 878 |
| Minute-level physical activity monitor data available | 406 | 472 | 878 |

## Figure Data 2. Harmonisation Status Counts

| Source | Compatibility status | Rows |
| --- | --- | --- |
| nhanes_2003_2006_hip_actigraph_pam | broad construct only; numeric equivalence blocked | 1 |
| nhanes_2005_2006_hip_actigraph_pam | source-specific step metric; no conversion from/to MIMS | 1 |
| nhanes_2011_2014_wrist_mims | compatible after protocol abstraction | 2 |
| nhanes_2011_2014_wrist_mims | source-specific metric; not directly convertible | 1 |
| synthetic_hip_counts_demo | compatible after protocol abstraction | 1 |
| synthetic_hip_counts_demo | not harmonisable with NHANES wrist MIMS in current KG | 2 |
| synthetic_hip_counts_demo | source-specific metric; not directly convertible | 1 |

## Figure Data 3. Protocol Sensitivity

| Protocol | Eligible participants | Eligible % | Valid day rows | Mean participant daily MIMS |
| --- | --- | --- | --- | --- |
| wake_wear_10h_min4 | 807 | 91.91344 | 5553 | 11567.603003 |
| wake_wear_12h_min4 | 722 | 82.232346 | 4824 | 12201.537613 |
| valid_minutes_20h_min4 | 862 | 98.177677 | 6111 | 10827.114119 |

## Recommended Use

- Use the CSV files for manuscript tables, plotting, and supervisor review.
- Use `figure*_*.csv` as plotting inputs for the three figure concepts in `docs/paper_package.md`.
- Keep reviewed NCIt mappings qualified as source-code mappings, not confirmed disease or histology assertions.
