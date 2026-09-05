# Domain/Ontology Review Instructions

Purpose: obtain independent review of the semantic compatibility claims used in the accelerometry harmonisation KG.

The reviewer should inspect `domain_ontology_review_sheet.csv` and mark each row as `accept`, `revise`, or `reject`, with a short reviewer comment. This review is separate from NCIt cancer-type review.

## Review Scope

1. Whether the NHANES 2003-2006 PAM source is correctly described as an independent public accelerometry source.
2. Whether hip ActiGraph counts/minute, hip steps, wrist MIMS, and PhysioNet ActiLife steps are represented with appropriate non-conversion safeguards.
3. Whether valid-day rules are correctly limited to completeness/sensitivity interpretation.
4. Whether the RDF pattern avoids false identity linkage between independent NHANES cycles.
5. Whether competency query `cq9_independent_pam_source_validation.rq` exposes the independent-source evidence and interpretation limits clearly.

## Out of Scope

NCIt cancer-type IRI approval is out of scope here and remains pending in the separate NCIt review sheet.
