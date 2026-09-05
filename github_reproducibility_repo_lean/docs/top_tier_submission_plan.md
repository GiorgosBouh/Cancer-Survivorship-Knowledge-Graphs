# Top-Tier Submission Plan

**Target contribution:** semantic validation framework for preventing invalid harmonisation of accelerometry-derived physical-activity definitions in cancer-survivorship research.

## Recommended Scope

Do not frame the paper as a completed cancer-survivorship KG. Frame it as a reproducible semantic validation and compatibility-checking framework, with NHANES cancer-history accelerometry as the primary use case.

## Dataset Strategy

| candidate_id | source | url | access_status | why_it_matters | top_tier_use | limitation | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nhanes_2003_2006_hip_actigraph_pam | NHANES 2003-2006 Physical Activity Monitor PAXRAW_C/PAXRAW_D | https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&Cycle= | open integrated | Adds an independent public accelerometry cohort: different participants, survey cycles, hip-worn ActiGraph AM-7164, and 1-minute activity-count/step epochs. | main independent-source semantic validation case for cross-device and cross-cohort compatibility safeguards | Still NHANES and self-reported cancer history; not an independent clinical cancer-survivorship cohort. | 1 |
| physionet_nhanes_steps_activity_counts_v1_0_2 | PhysioNet minute-level step counts and physical activity data from NHANES 2011-2014, version 1.0.2 | https://physionet.org/content/minute-level-step-count-nhanes/1.0.2/ | open | Adds real algorithmic step-count and ActiGraph activity-count outputs derived from NHANES raw wrist data. | near-term real derived-source extension; not a fully independent cohort | Same NHANES monitoring population, so it tests metric/algorithm harmonisation more than cross-cohort generalisation. | 2 |
| capture24 | CAPTURE-24 wrist accelerometry with activity annotations | https://ora.ox.ac.uk/objects/uuid:99d7c092-d865-4a19-b096-cc16440cd001 | open large download | Adds a real external wrist accelerometry dataset with ground-truth activity labels and MET-linked annotations. | strong external semantic compatibility case for activity-label and intensity-definition modelling | Not cancer-survivorship specific and full download is large. | 3 |
| nci_idata_actigraph | NCI IDATA ActiGraph 60-second and 10-second epoch datasets | https://cdas.cancer.gov/datasets/idata/140/ | approval required | Cancer-relevant ActiGraph epoch data with public dictionaries and controlled access to records. | best fit for a cancer-focused top-tier extension if access is approved | Requires CDAS project approval and data-transfer process before experiments can be run. | 4 |

## Readiness Checklist

| criterion | status | evidence | top_tier_action |
| --- | --- | --- | --- |
| Reproducible NHANES data foundation | complete | cohort, day, minute, feature, protocol, manifest, and quality artifacts exist | keep one-command rebuild documented |
| Standards-compliant KG validation | complete | pySHACL conforms=True; failed_policy_checks=0 | use --require-pyshacl as mandatory validation gate |
| Protocol sensitivity evaluation | complete | protocol-discordance risk register quantifies participant inclusion changes | make protocol discordance a main result |
| Naive-vs-semantic harmonisation evaluation | complete | semantic risk registers and competency queries now cover synthetic, PhysioNet, and independent PAM sources; CQ9 exposes PAM source safeguards | keep interpretation limits prominent in manuscript tables and figures |
| Second real accelerometry data source | complete | PhysioNet v1.0.2 ActiLife steps integrated for 878 participants as a real derived same-cohort source | keep wording precise: real derived same-cohort source, not independent validation |
| Independent public accelerometry source | complete | NHANES 2003-2006 PAM integrated: participants_with_paxraw=768; daily_rows=5367; retained_minute_rows=7724170; kg_nodes=20 | use as the main independent-source harmonisation validation; do not claim independent clinical survivorship cohort |
| NCIt cancer-type expert review | complete_with_caveat | NCIt review status=review_completed_qualified_assertions_allowed; assertion_count=19 | use reviewed mappings only as qualified self-report code mappings; keep clinical caveats visible |
| External ontology/domain expert review | prepared_pending_review | review packet prepared: items=6; status=prepared_pending_external_review | obtain completed external reviewer decisions before claiming independent expert approval |
| Public reproducibility archive | prepared_pending_deposit | reproducibility archive plan generated; no DOI/archive deposit yet | prepare Zenodo/OSF archive with code, generated non-sensitive outputs, and environment lock |
| Reporting checklists | partial_complete | STROBE-style and FAIR/resource checklist draft generated | complete target-journal-specific reporting checklist during manuscript finalization |
| Journal-specific manuscript package | partial_complete | manuscript tables and figure inputs generated | create target-journal cover story and final figures |

## Blocking Items Before Top-Tier Submission

1. Keep reviewed NCIt mappings qualified as self-reported source-code mappings, not confirmed disease diagnoses.
2. Obtain completed independent domain/ontology review of compatibility statuses and interpretation limits.
3. Archive code and generated reusable artifacts with a DOI.
4. Complete target-journal reporting checklist and final figure drafts.

## Near-Term Experiment Order

1. Use CQ9 and the IndependentPAMDailySummary SHACL shape as the KG-level evidence for the independent public accelerometry source.
2. Report PhysioNet ActiLife steps as a real same-cohort derived metric source, not as independent validation.
3. Send `docs/review/domain_ontology_review_sheet.csv` for external domain/ontology review.
4. Deposit the reproducibility package and complete journal-specific figures/checklists.
