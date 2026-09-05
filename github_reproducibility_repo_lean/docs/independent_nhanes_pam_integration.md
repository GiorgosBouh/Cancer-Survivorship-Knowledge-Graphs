# Independent NHANES 2003-2006 PAM Integration

**Decision:** use NHANES 2003-2006 Physical Activity Monitor data as the first independent public accelerometry validation source.

This source is independent from the existing NHANES 2011-2014 wrist/MIMS source at the participant, survey-cycle, device-placement, and metric level. It is still from the NHANES program, so it should not be described as an independent clinical cancer-survivorship cohort.

## Source

- 2003-2004 PAXRAW_C: hip-worn ActiGraph AM-7164, 1-minute `PAXINTEN` activity-count epochs.
- 2005-2006 PAXRAW_D: hip-worn ActiGraph AM-7164, 1-minute `PAXINTEN` and `PAXSTEP` epochs.
- Cancer-history cohort definition is the same conservative survey definition used in the main pipeline: adults aged 20+ with `MCQ220=1`.

## Current Counts

| Metric | Value |
|---|---|
| cancer-history adults before PAM filtering | 892 |
| participants with PAM minute records | 768 |
| daily PAM summary rows | 5367 |
| retained PAM minute rows | 7724170 |

## Per-Cycle Processing

| cycle | rows_scanned | chunks_scanned | retained_minute_rows | participants_requested | participants_with_paxraw | daily_rows | has_step_column |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2003-2004 | 72250027 | 145 | 4123017 | 478 | 410 | 2864 | False |
| 2005-2006 | 74874095 | 150 | 3601153 | 414 | 358 | 2503 | True |

## Semantic Map

| source_id | source_variable | source_label | source_unit | harmonised_construct | compatibility_status | compatible_with_current_mims | interpretation_limit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nhanes_2003_2006_hip_actigraph_pam | PAXINTEN | ActiGraph AM-7164 hip-worn activity counts per 1-minute epoch | device-specific activity counts/minute | daily movement volume | broad construct only; numeric equivalence blocked | False | Do not convert hip ActiGraph counts to wrist MIMS. Do not treat cut-points, MVPA, sedentary time, or total volume as numerically equivalent without protocol-specific validation. |
| nhanes_2005_2006_hip_actigraph_pam | PAXSTEP | ActiGraph AM-7164 hip-worn step count per 1-minute epoch | steps/minute | daily ambulatory volume | source-specific step metric; no conversion from/to MIMS | False | Steps can be summarized as a real ambulatory metric, but cannot be inferred from NHANES 2011-2014 wrist MIMS and cannot validate MIMS-to-steps conversion. |

## Risk Register

| risk_id | risk_type | risk_level | naive_claim | kg_guarded_decision | why_it_matters |
| --- | --- | --- | --- | --- | --- |
| independent_pam_vs_wrist_mims_numeric_equivalence | cross_cohort_cross_device_metric | high | Treat NHANES 2003-2006 hip ActiGraph counts and NHANES 2011-2014 wrist MIMS as the same physical activity variable. | Permit only broad construct-level grouping under movement volume; block numeric conversion/equivalence. | The source differs by participants, cycle, device placement, device generation, and metric definition. |
| independent_pam_cutpoint_back_mapping | unsupported_threshold_transfer | high | Apply hip-count cut-points or step cadence interpretations to wrist MIMS outputs. | Require source-specific protocol nodes and explicit validation before threshold transfer. | A semantic match on activity labels is not enough to support MVPA/sedentary claims across devices. |

## Interpretation

This closes the practical independent-dataset gap better than PhysioNet because the participants and raw accelerometry collection are not the same as the 2011-2014 wrist/MIMS source.

It does not permit conversion between hip ActiGraph counts, steps, and wrist MIMS. The KG should represent these as source-specific metrics that can be grouped only under broad constructs unless a validated conversion or protocol-specific threshold mapping is provided.
