# Protocol Citation Evidence

**Purpose:** record citation-level provenance for valid-day completeness/sensitivity protocols.

This layer separates source-variable evidence, literature context, and local review decisions. It does not convert completeness rules into MVPA, sedentary, active/inactive, or clinical physical-activity definitions.

## Generated Artifacts

| Artifact | Role |
|---|---|
| `docs/protocols/protocol_citation_evidence.csv` | Machine-readable citation evidence rows |
| `reports/protocol_citation_summary.json` | Citation summary report |
| `docs/protocols/protocol_citations.md` | Human-readable citation summary |

## Summary

- Protocols covered: 3
- Citation evidence rows: 12

## Evidence Roles

| Role | Rows |
|---|---:|
| literature_context | 3 |
| project_review_decision | 3 |
| source_variable_definition | 6 |

## Protocol Evidence

| Protocol | Role | Support level | Source | Interpretation limit |
|---|---|---|---|---|
| `wake_wear_10h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| `wake_wear_10h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| `wake_wear_10h_min4` | literature_context | context_only_not_wrist_mims_validation | Catalog of NHANES accelerometer rules, variables, and definitions | Use only to justify why 10h/min4 is a reasonable sensitivity/completeness candidate to represent and test. |
| `wake_wear_10h_min4` | project_review_decision | local_project_review_support | Project protocol review sheet | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |
| `wake_wear_12h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| `wake_wear_12h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | Use PAXWWMD only as a valid wake wear minutes completeness input in this project. |
| `wake_wear_12h_min4` | literature_context | context_only_not_wrist_mims_validation | Catalog of NHANES accelerometer rules, variables, and definitions | Use only as rationale for retaining a stricter sensitivity rule. |
| `wake_wear_12h_min4` | project_review_decision | local_project_review_support | Project protocol review sheet | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |
| `valid_minutes_20h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2011-2012 Physical Activity Monitor documentation | Use PAXVMD only as a valid minutes completeness input in this project. |
| `valid_minutes_20h_min4` | source_variable_definition | direct_source_variable_support | NHANES 2013-2014 Physical Activity Monitor documentation | Use PAXVMD only as a valid minutes completeness input in this project. |
| `valid_minutes_20h_min4` | literature_context | context_only_not_threshold_validation | Minute-level step counts and physical activity data from NHANES 2011-2014 | Use only as context for representing a 24-hour completeness sensitivity rule. |
| `valid_minutes_20h_min4` | project_review_decision | local_project_review_support | Project protocol review sheet | Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification. |

## Guardrail

Citation support is intentionally scoped. Official NHANES documentation supports the meaning of source variables such as `PAXWWMD` and `PAXVMD`; literature-context rows support why these candidate completeness thresholds are worth representing and testing. None of these rows validates wrist MIMS MVPA or sedentary classification.
