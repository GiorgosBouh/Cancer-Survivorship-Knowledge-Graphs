# Naive vs Semantic Harmonisation Evaluation

**Purpose:** show what a naive harmonisation would incorrectly permit and how the KG blocks or qualifies those claims.

## Main Finding

The current KG does not merely store activity variables. It records whether variables and definitions are compatible, source-specific, or not harmonisable with NHANES wrist MIMS. This turns hidden preprocessing and definition choices into queryable validation evidence.

## Semantic Harmonisation Risk Register

| risk_id | risk_type | harmonised_construct | left_source | left_variable | left_unit | left_compatibility | right_source | right_variable | right_unit | right_compatibility | naive_harmonisation_risk | kg_guarded_decision | risk_level | interpretation_limit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| construct_pair_1 | cross_source_construct_pair | daily movement volume | nhanes_2011_2014_wrist_mims | PAXMTSD | MIMS | source-specific metric; not directly convertible | synthetic_hip_counts_demo | daily_total_vertical_axis_counts | count | source-specific metric; not directly convertible | naive construct matching could imply invalid numeric comparability | block numeric equivalence; retain source-specific metrics | high | Do not apply hip counts/minute intensity thresholds to MIMS. Not comparable as a numeric equivalent of MIMS. |
| construct_pair_2 | cross_source_construct_pair | valid wear completeness | nhanes_2011_2014_wrist_mims | PAXWWMD | minute | compatible after protocol abstraction | synthetic_hip_counts_demo | valid_wear_minutes | minute | compatible after protocol abstraction | low if protocol and interpretation limits are retained | allow construct-level protocol abstraction only | controlled | Completeness rule only; not an activity classification. Completeness rule only; not an activity classification. |
| unsupported_claim_3 | unsupported_back_mapping | source-defined activity intensity | synthetic_hip_counts_demo | mvpa_minutes_1952_cpm | minute | not harmonisable with NHANES wrist MIMS in current KG | nhanes_2011_2014_wrist_mims | no compatible NHANES wrist MIMS variable | not applicable | not supported | naive activity-label harmonisation could back-map hip-counts intensity classification to wrist MIMS | block back-mapping to NHANES wrist MIMS | high | Requires hip counts/minute protocol context. |
| unsupported_claim_4 | unsupported_back_mapping | source-defined sedentary classification | synthetic_hip_counts_demo | sedentary_minutes_100_cpm | minute | not harmonisable with NHANES wrist MIMS in current KG | nhanes_2011_2014_wrist_mims | no compatible NHANES wrist MIMS variable | not applicable | not supported | naive activity-label harmonisation could back-map hip-counts intensity classification to wrist MIMS | block back-mapping to NHANES wrist MIMS | high | Requires hip counts/minute protocol context. |

## Protocol Discordance Risk Register

| risk_id | left_protocol | right_protocol | participants_evaluated | discordant_participants | discordant_percent | naive_harmonisation_risk | kg_guarded_decision | risk_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wake_wear_10h_min4__vs__wake_wear_12h_min4 | wake_wear_10h_min4 | wake_wear_12h_min4 | 878 | 85 | 9.681093 | treating valid-day protocols as interchangeable changes analytic inclusion | represent each protocol and query discordant eligibility explicitly | high |
| wake_wear_10h_min4__vs__valid_minutes_20h_min4 | wake_wear_10h_min4 | valid_minutes_20h_min4 | 878 | 57 | 6.492027 | treating valid-day protocols as interchangeable changes analytic inclusion | represent each protocol and query discordant eligibility explicitly | high |
| wake_wear_12h_min4__vs__valid_minutes_20h_min4 | wake_wear_12h_min4 | valid_minutes_20h_min4 | 878 | 142 | 16.173121 | treating valid-day protocols as interchangeable changes analytic inclusion | represent each protocol and query discordant eligibility explicitly | high |

## Interpretation

A naive workflow could match variables by broad labels such as movement volume, MVPA, sedentary time, or valid wear. The KG-guarded workflow allows only reviewed construct-level abstraction and blocks numeric equivalence or back-mapping where source metrics are incompatible.
