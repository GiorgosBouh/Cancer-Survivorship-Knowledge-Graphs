# Data Sources

This reproducibility bundle does not include raw public accelerometry files because they are large. The pipeline expects them under `data/raw/` using the folder layout below.

## NHANES 2011-2014 Wrist Accelerometry / MIMS

Primary source used for the main cancer-history cohort and wrist MIMS processing:

- NHANES 2011-2012
- NHANES 2013-2014
- Demographics: `DEMO`
- Medical conditions questionnaire: `MCQ`
- Physical activity monitor day-level files: `PAXDAY`
- Physical activity monitor header files: `PAXHD`
- Large minute-level files: `PAXMIN_G.xpt`, `PAXMIN_H.xpt`

Expected local layout:

```text
data/raw/2011-2012/
data/raw/2013-2014/
```

The large `PAXMIN` files were obtained from:

```text
https://ftp.cdc.gov/pub/NHANES/LargeDataFiles/
```

## PhysioNet Derived ActiLife Steps

Real derived-source comparison:

```text
Minute level step counts and physical activity data from NHANES 2011-2014
Version: 1.0.2
DOI: 10.13026/d7sw-f662
```

Expected local layout:

```text
data/raw/physionet-minute-level-step-count-nhanes-1.0.2/
```

The integrated metric file was:

```text
csv/nhanes_1440_actisteps.csv.xz
```

## NHANES 2003-2006 Hip-Worn ActiGraph PAM

Independent public accelerometry source used for cross-cycle, cross-device semantic validation:

- NHANES 2003-2004: `DEMO_C.XPT`, `MCQ_C.XPT`, `PAXRAW_C.zip`, `paxraw_c.xpt`
- NHANES 2005-2006: `DEMO_D.XPT`, `MCQ_D.XPT`, `PAXRAW_D.zip`, `paxraw_d.xpt`

Expected local layout:

```text
data/raw/2003-2004/
data/raw/2005-2006/
```

## Included Derived Outputs

The repository includes compact derived outputs needed to inspect the manuscript tables, figures, KG validation, competency queries, and review status. The very large derived minute table `data/processed/pam_minutes.csv` is excluded and should be regenerated from raw `PAXMIN` when a full rebuild is needed.

