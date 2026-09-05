# Draft NCIt Mapping for NHANES Cancer Types

**Machine-readable draft:** `data/processed/cancer_type_ncit_mapping.csv`  
**Summary report:** `reports/cancer_type_ncit_mapping_summary.json`  
**Generator:** `src/cskg_pipeline/build_ncit_mapping.py`

---

## Purpose

This is a conservative draft mapping from NHANES cancer type source labels to candidate NCI Thesaurus concepts.

It is a review artifact only. The NCIt IRIs are not yet asserted in the RDF graph.

---

## Current Result

```text
mapping rows: 33
rows with NCIt candidate: 24
rows without NCIt candidate: 9
observed rows with NCIt candidate: 23
observed rows without NCIt candidate: 6
```

Status and relation breakdown:

| mapping_status       | mapping_relation | rows |
| -------------------- | ---------------- | ---- |
| draft_candidate      | broadMatch       | 7    |
| draft_candidate      | closeMatch       | 15   |
| draft_candidate      | exactMatch       | 2    |
| manual_review_needed | reviewNeeded     | 4    |
| not_mapped           | notMapped        | 5    |

---

## High-Confidence Draft Candidates

These are still draft candidates, but they were clean EVS search results and are good starting points for review:

| nhanes_code | nhanes_label           | observed_count | ncit_code | ncit_preferred_label    | mapping_relation |
| ----------- | ---------------------- | -------------- | --------- | ----------------------- | ---------------- |
| 14          | Breast                 | 168            | C4872     | Breast Carcinoma        | closeMatch       |
| 15          | Cervix (cervical)      | 70             | C9039     | Cervical Carcinoma      | closeMatch       |
| 16          | Colon                  | 68             | C4910     | Colon Carcinoma         | closeMatch       |
| 17          | Esophagus (esophageal) | 8              | C3513     | Esophageal Carcinoma    | closeMatch       |
| 18          | Gallbladder            | 0              | C3844     | Gallbladder Carcinoma   | closeMatch       |
| 19          | Kidney                 | 22             | C9384     | Kidney Carcinoma        | closeMatch       |
| 21          | Leukemia               | 7              | C3161     | Leukemia                | exactMatch       |
| 22          | Liver                  | 6              | C7927     | Liver Carcinoma         | closeMatch       |
| 23          | Lung                   | 35             | C4878     | Lung Carcinoma          | closeMatch       |
| 25          | Melanoma               | 75             | C3224     | Melanoma                | exactMatch       |
| 28          | Ovary (ovarian)        | 22             | C4908     | Ovarian Carcinoma       | closeMatch       |
| 29          | Pancreas (pancreatic)  | 7              | C207229   | Pancreatic Carcinoma    | closeMatch       |
| 30          | Prostate               | 157            | C4863     | Prostate Carcinoma      | closeMatch       |
| 31          | Rectum (rectal)        | 6              | C9382     | Rectal Carcinoma        | closeMatch       |
| 35          | Stomach                | 12             | C4911     | Gastric Carcinoma       | closeMatch       |
| 37          | Thyroid                | 26             | C4815     | Thyroid Gland Carcinoma | closeMatch       |

---

## Medium-Confidence / Broad Candidates

These mappings are intentionally marked as broad or medium confidence because the NHANES label is broader than the candidate concept or the histology is unknown:

| nhanes_code | nhanes_label                | observed_count | ncit_code | ncit_preferred_label       | mapping_relation | review_note                                                                                                           |
| ----------- | --------------------------- | -------------- | --------- | -------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| 10          | Bladder                     | 26             | C9334     | Malignant Bladder Neoplasm | broadMatch       | EVS search also returned Bladder Carcinoma C4912; malignant neoplasm is broader and better matches unknown histology. |
| 12          | Bone                        | 8              | C4016     | Malignant Bone Neoplasm    | broadMatch       | Broad anatomic cancer label; histology unknown.                                                                       |
| 13          | Brain                       | 6              | C3568     | Malignant Brain Neoplasm   | broadMatch       | Broad anatomic cancer label; histology unknown.                                                                       |
| 20          | Larynx/ windpipe            | 10             | C4855     | Laryngeal Carcinoma        | closeMatch       | NHANES label includes larynx/windpipe; laryngeal candidate needs review for windpipe/trachea ambiguity.               |
| 24          | Lymphoma/ Hodgkin's disease | 26             | C3208     | Lymphoma                   | broadMatch       | NHANES label combines lymphoma/Hodgkin disease; broad lymphoma candidate needs review.                                |
| 26          | Mouth/tongue/lip            | 5              | C8990     | Oral Cavity Carcinoma      | broadMatch       | NHANES label mouth/tongue/lip is broader than oral cavity carcinoma; needs review.                                    |
| 34          | Soft tissue (muscle or fat) | 4              | C9306     | Soft Tissue Sarcoma        | broadMatch       | NHANES label is soft tissue muscle/fat; sarcoma candidate likely but needs review.                                    |
| 38          | Uterus (uterine)            | 40             | C3552     | Malignant Uterine Neoplasm | broadMatch       | EVS search returned Malignant Uterine Neoplasm C3552; broad anatomic label.                                           |

---

## Observed Codes Without NCIt Candidate

These observed categories should not be asserted as NCIt disease concepts yet:

| nhanes_code | nhanes_label                | observed_count | mapping_status       | review_note                                                                                                    |
| ----------- | --------------------------- | -------------- | -------------------- | -------------------------------------------------------------------------------------------------------------- |
| 11          | Blood                       | 5              | manual_review_needed | NHANES label is broad. EVS returned Liquid Tumor C116915, but this is too broad to assert without review.      |
| 32          | Skin (non-melanoma)         | 166            | manual_review_needed | Needs review: source label says non-melanoma skin, but exact NCIt concept should be selected carefully.        |
| 33          | Skin (don't know what kind) | 95             | not_mapped           | Ambiguous NHANES category; do not map to a precise cancer concept.                                             |
| 36          | Testis (testicular)         | 8              | manual_review_needed | EVS phrase search did not return a clean general testicular carcinoma/neoplasm candidate in the first results. |
| 39          | Other                       | 62             | not_mapped           | Ambiguous NHANES category; do not map to a precise cancer concept.                                             |
| 66          | More than 3 kinds           | 2              | not_mapped           | Aggregate response category; not a disease concept.                                                            |

---

## Mapping Relations Used

- `exactMatch`: NHANES label and NCIt candidate are effectively the same broad disease concept.
- `closeMatch`: candidate is a close disease concept, but source label lacks histology/detail.
- `broadMatch`: candidate is useful but broader/narrower ambiguity needs review.
- `reviewNeeded`: no candidate is asserted yet.
- `notMapped`: source value is ambiguous or not a disease concept.

---

## Sources

Primary source for candidate concepts:

```text
https://api-evsrest.nci.nih.gov/api/v1/concept/ncit
```

NCI describes NCIt as its reference terminology and biomedical ontology, and EVS REST API as the backend service used by EVS Explore.

Related NCI page:

```text
https://www.cancer.gov/about-nci/organization/cbiit/vocabulary
```

---

## Regenerate

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_ncit_mapping
```

---

## Next Step

Review `data/processed/cancer_type_ncit_mapping.csv` manually. After approval, add NCIt IRIs only for accepted `exactMatch` or accepted `closeMatch` rows.
