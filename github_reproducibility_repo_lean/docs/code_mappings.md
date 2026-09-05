# NHANES Code Mappings

**Machine-readable mapping:** `data/processed/code_mappings.csv`  
**Summary report:** `reports/code_mapping_summary.json`  
**Generator:** `src/cskg_pipeline/build_code_mappings.py`

---

## Purpose

This file documents the first source-code mapping layer for the cancer survivorship accelerometry KG.

The goal is to replace opaque source codes such as `1`, `2`, `14`, or `P` with CDC/NHANES source labels, while keeping external ontology mappings conservative.

---

## Current Result

```text
mapping rows: 96
rows observed in current processed data: 87
```

Status breakdown:

| mapping_status                                   | rows |
| ------------------------------------------------ | ---- |
| source label ready                               | 63   |
| source label ready; NCIt pending                 | 28   |
| source label ready; needs expert/ontology review | 5    |

Variable coverage:

| source_variable  | rows |
| ---------------- | ---- |
| MCQ220           | 4    |
| PAXDAYWD         | 7    |
| PAXFLGSM         | 26   |
| PAXHAND          | 4    |
| PAXORENT         | 3    |
| PAXPREDM         | 4    |
| PAXQFM           | 2    |
| RIAGENDR         | 2    |
| RIDRETH1         | 5    |
| RIDRETH3         | 6    |
| cancer_type_code | 33   |

---

## Variables Covered

The mapping currently covers:

- `RIAGENDR` gender codes,
- `RIDRETH1` race/Hispanic origin codes,
- `RIDRETH3` race/Hispanic origin with Non-Hispanic Asian category,
- `MCQ220` self-reported cancer/malignancy history,
- `cancer_type_code` from normalized `MCQ230*` cancer type slots,
- `PAXHAND` wrist/non-dominant-hand placement metadata,
- `PAXORENT` wrist PAM orientation,
- `PAXDAYWD` day-of-week codes,
- `PAXPREDM` minute-level wake/sleep/non-wear status,
- `PAXQFM` minute-level quality flag score,
- `PAXFLGSM` minute-level quality flag labels.

---

## Important Cancer Mapping Note

NHANES cancer type labels are now attached to the local `cancer_type_code` values.

However, exact NCIt concept IDs are not filled yet. This is deliberate. Some NHANES categories are broad or ambiguous, for example:

- `Skin (don't know what kind)`,
- `Other`,
- `More than 3 kinds`,
- `Refused`,
- `Don't know`.

These should not be forced into precise NCIt cancer concepts without expert/ontology review.

Most common observed cancer source labels in the current cohort:

| code_value | source_label                | observed_count | mapping_status                                   |
| ---------- | --------------------------- | -------------- | ------------------------------------------------ |
| 14         | Breast                      | 168            | source label ready; NCIt pending                 |
| 32         | Skin (non-melanoma)         | 166            | source label ready; NCIt pending                 |
| 30         | Prostate                    | 157            | source label ready; NCIt pending                 |
| 33         | Skin (don't know what kind) | 95             | source label ready; needs expert/ontology review |
| 25         | Melanoma                    | 75             | source label ready; NCIt pending                 |
| 15         | Cervix (cervical)           | 70             | source label ready; NCIt pending                 |
| 16         | Colon                       | 68             | source label ready; NCIt pending                 |
| 39         | Other                       | 62             | source label ready; needs expert/ontology review |
| 38         | Uterus (uterine)            | 40             | source label ready; NCIt pending                 |
| 23         | Lung                        | 35             | source label ready; NCIt pending                 |
| 24         | Lymphoma/ Hodgkin's disease | 26             | source label ready; NCIt pending                 |
| 37         | Thyroid                     | 26             | source label ready; NCIt pending                 |

---

## Accelerometry Wear-State Mapping

`PAXPREDM` is now mapped to CDC/NHANES source labels:

| code_value | source_label | observed_count |
| ---------- | ------------ | -------------- |
| 1          | Wake wear    | 5426442        |
| 2          | Sleep wear   | 3393430        |
| 3          | Non wear     | 705022         |
| 4          | Unknown      | 425014         |

These are algorithm-estimated states for each minute, not participant-level behavior classifications.

---

## Quality Flag Mapping

`PAXQFM` is modeled as a quality flag score:

| code_value | source_label                            | observed_count | notes                                                                                                                            |
| ---------- | --------------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 0          | No data quality flags occurred          | 9943858        | Zero-like NHANES floating values are normalized to 0 in this mapping.                                                            |
| >0         | One or more data quality flags occurred | 6050           | Values greater than zero indicate invalid minute under QC review; this is a score, not simply invalid-minute count at day level. |

Important: `PAXQFD`/`PAXQFM` are scores. Since multiple flags can occur in the same minute, daily quality flag score should not be interpreted as a simple count of invalid minutes.

`PAXFLGSM` is also mapped at the individual flag-letter level. If a minute contains multiple letters, the observed count for each letter counts rows containing that letter.

---

## Sources

CDC/NHANES sources used:

- DEMO_G: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/demo_g.htm
- DEMO_H: https://wwwn.cdc.gov/nchs/Data/Nhanes/Public/2013/DataFiles/DEMO_H.htm
- MCQ_G: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/MCQ_G.htm
- MCQ_H: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/MCQ_H.htm
- PAXHD_G: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXHD_G.htm
- PAXDAY_G: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXDAY_G.htm
- PAXMIN_G: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXMIN_G.htm

---

## Regenerate

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_code_mappings
```

---

## Current Use in the Pilot Graph

`data/processed/code_mappings.csv` is now used by `src/cskg_pipeline/build_pilot_kg.py` to enrich `data/processed/pilot_kg.ttl` with source labels.

The original source codes remain in the graph, and labels are added beside them. For example, `cskg:hasCancerTypeCode` remains available, and `cskg:cancerTypeLabel` is added as a readable source label.

## Next Step

Perform a separate NCIt mapping review for cancer types, then add exact concept IRIs only where the mapping is defensible.
