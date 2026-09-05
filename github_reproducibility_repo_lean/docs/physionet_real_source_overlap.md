# PhysioNet Real Source Cohort Overlap

**Source:** PhysioNet minute-level step counts and physical activity data from NHANES 2011-2014, version 1.0.2.

This is the first real non-synthetic source integration check. It uses downloaded PhysioNet metadata only and does not yet process the large activity-count or step-count metric files.

## Summary

| Measure | Value |
|---|---:|
| PhysioNet subjects | 19931 |
| Project cancer-history participants | 1035 |
| Present in PhysioNet metadata | 1035 |
| Missing from PhysioNet metadata | 0 |
| Overall overlap percent | 100.0 |

## By Cycle

| cycle | project_cancer_history_participants | present_in_physionet | overlap_percent |
| --- | --- | --- | --- |
| 2011-2012 | 488 | 488 | 100.0 |
| 2013-2014 | 547 | 547 | 100.0 |

## Interpretation

The selected PhysioNet source can be linked to the existing NHANES cancer-history cohort by `SEQN` and cycle. This supports the next experiment: add a real derived accelerometry metric such as ActiGraph activity counts or step counts and rerun semantic compatibility checks without using the synthetic hip-counts demo as the only contrasting source.

## Next Step

Download one compressed metric file, preferably csv/nhanes_1440_AC.csv.xz or csv/nhanes_1440_actisteps.csv.xz, and build cohort-restricted daily summaries.
