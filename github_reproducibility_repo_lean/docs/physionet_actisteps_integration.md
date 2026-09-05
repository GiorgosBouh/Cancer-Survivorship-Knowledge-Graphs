# PhysioNet ActiLife Steps Integration

**Purpose:** integrate one real non-synthetic PhysioNet accelerometry-derived metric for the current cancer-history cohort.

## Source

| Field | Value |
|---|---|
| source_id | physionet_nhanes_steps_activity_counts_v1_0_2 |
| metric_id | actilife_steps |
| input | `data/raw/physionet-minute-level-step-count-nhanes-1.0.2/csv/nhanes_1440_actisteps.csv.xz` |

## Generated Outputs

| Artifact | Role |
|---|---|
| `data/processed/physionet_actisteps_daily_summary.csv` | Cohort-restricted day-level ActiLife step summaries |
| `data/processed/physionet_actisteps_participant_summary.csv` | Participant-level ActiLife step summaries |
| `reports/physionet_actisteps_summary.json` | Machine-readable integration summary |

## Summary

| Measure | Value |
|---|---:|
| Rows scanned from source | 130186 |
| Project participants | 1035 |
| Daily summary rows | 7785 |
| Participant summary rows | 878 |
| Participants with ActiLife steps | 878 |
| Mean daily ActiLife steps over participants | 7940.529821 |

## Interpretation Limit

ActiLife step counts are real derived step-count metrics from the PhysioNet NHANES source. They are not MIMS, MVPA, sedentary, or clinical physical-activity classifications.

## Next Step

Add this real source to the harmonisation source-variable map and rerun the naive-vs-semantic risk evaluation using real ActiLife step counts rather than relying only on the synthetic hip-counts demonstration.
