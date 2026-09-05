# Protocol Outcome Sensitivity

**Generated:** 2026-08-11 Europe/Athens  
**Script:** `src/cskg_pipeline/build_protocol_outcome_sensitivity.py`

This analysis answers the methodological review point that the valid-day rules must be treated as a sensitivity grid, not as arbitrary filters.

The analysis reports MIMS only as a movement-summary metric. It does not create MVPA, sedentary, active/inactive, or clinical physical activity labels.

## Inputs

- `data/processed/pam_days.csv`
- `data/processed/pam_minute_features.csv`
- `data/processed/protocol_definitions.csv`
- `data/processed/valid_day_protocol_results.csv`
- `docs/protocols/protocol_review_sheet.csv`

## Outputs

- `data/processed/protocol_outcome_sensitivity_summary.csv`
- `data/processed/protocol_outcome_sensitivity_participants.csv`
- `data/processed/protocol_pairwise_inclusion_comparison.csv`
- `reports/protocol_outcome_sensitivity_summary.json`

## Headline Results

| Protocol | Eligible participants | Eligible % | Valid day rows | Mean participant daily MIMS |
|---|---:|---:|---:|---:|
| `wake_wear_10h_min4` | 807 | 91.91344 | 5553 | 11567.603003 |
| `wake_wear_12h_min4` | 722 | 82.232346 | 4824 | 12201.537613 |
| `valid_minutes_20h_min4` | 862 | 98.177677 | 6111 | 10827.114119 |

## Pairwise Inclusion Discordance

| Protocol A | Protocol B | Both eligible | A only | B only | Neither | Discordant participants |
|---|---:|---:|---:|---:|---:|---:|
| `wake_wear_10h_min4` | `wake_wear_12h_min4` | 722 | 85 | 0 | 71 | 85 |
| `wake_wear_10h_min4` | `valid_minutes_20h_min4` | 806 | 1 | 56 | 15 | 57 |
| `wake_wear_12h_min4` | `valid_minutes_20h_min4` | 721 | 1 | 141 | 15 | 142 |

## Interpretation

Protocol choice changes both participant inclusion and the movement-summary distribution. The strict 12-hour wake-wear rule excludes 85 participants who are included by the 10-hour wake-wear rule. The 20-hour valid-minutes rule includes 141 participants excluded by the 12-hour wake-wear rule.

This gives the project a concrete sensitivity result: the valid-day protocol is not just metadata; it changes the analytic cohort and the summary movement estimates.

## Limits

These results are descriptive only. They do not validate any rule as clinically superior, and they do not establish cancer-specific physical activity inference.

The cohort label remains: adults with a self-reported history of cancer in NHANES, not an EHR-verified cancer survivorship cohort.
