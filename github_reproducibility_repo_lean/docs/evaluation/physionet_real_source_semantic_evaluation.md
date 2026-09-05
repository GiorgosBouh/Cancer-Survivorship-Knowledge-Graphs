# PhysioNet Real Source Semantic Evaluation

**Purpose:** repeat the naive-vs-semantic harmonisation logic with a real non-synthetic derived step-count source.

## Summary

| Measure | Value |
|---|---:|
| Paired daily rows | 7785 |
| Paired participants | 878 |
| Pearson correlation, MIMS vs ActiLife steps | 0.957383 |
| Spearman correlation, MIMS vs ActiLife steps | 0.96414 |
| High semantic risk rows | 1 |

## Semantic Risk Register

| risk_id | risk_type | harmonised_construct | left_source | left_variable | left_unit | right_source | right_variable | right_unit | naive_harmonisation_risk | kg_guarded_decision | risk_level | interpretation_limit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| real_source_mims_vs_actilife_steps | real_source_construct_pair | daily movement volume | nhanes_2011_2014_wrist_mims | PAXMTSD | MIMS | physionet_nhanes_steps_activity_counts_v1_0_2 | daily_total_actilife_steps | step | naive movement-volume matching could imply MIMS-to-steps numeric comparability | block numeric equivalence; preserve source-specific metrics | high | ActiLife steps and MIMS are real but different source-specific metrics. |

## Interpretation Limit

Correlation between MIMS and ActiLife steps may be descriptively reported, but it does not establish numeric conversion, MVPA, sedentary classification, or clinical physical-activity status.

## Main Meaning

The project now has a real derived step-count source linked to the same cohort. The KG-compatible interpretation is construct-level alignment under daily movement volume, while explicitly blocking numeric equivalence between MIMS and steps.
