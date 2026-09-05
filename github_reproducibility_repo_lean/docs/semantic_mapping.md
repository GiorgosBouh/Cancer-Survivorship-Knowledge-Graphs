# Semantic Mapping for the First Knowledge Graph Skeleton

**Purpose:** Map the current processed NHANES data layer to the first cancer survivorship accelerometry knowledge graph skeleton.

**Machine-readable mapping:** `data/processed/semantic_mapping.csv`

---

## 1. Scope

This mapping covers the current processed outputs:

```text
participants.csv
cancer_diagnoses.csv
pam_days.csv
pam_minutes.csv
pam_minute_features.csv
protocol_definitions.csv
valid_day_protocol_results.csv
cohort_flow.csv
```

The goal is not to finish the full ontology yet. The goal is to define a clean first semantic bridge from the working data pipeline to a pilot RDF knowledge graph.

---

## 2. Main Knowledge Graph Entities

| Data output | KG entity | Meaning |
|---|---|---|
| `participants.csv` | `cskg:Participant` | Retained NHANES adult participant with self-reported cancer history |
| `cancer_diagnoses.csv` | `cskg:CancerDiagnosis` | Cancer diagnosis slot extracted from NHANES MCQ variables |
| `pam_days.csv` | `cskg:DailyMovementSummary` | Daily NHANES physical activity monitor summary |
| `pam_minutes.csv` | `sosa:Observation` | Minute-level accelerometer observation |
| `pam_minute_features.csv` | `cskg:DerivedMovementFeatureSet` | Daily features derived from minute-level observations |
| `protocol_definitions.csv` | `cskg:ProcessingProtocol` | Candidate processing/valid-day protocol |
| `valid_day_protocol_results.csv` | `cskg:ProtocolApplicationResult` | Participant-level result after applying a protocol |
| `cohort_flow.csv` | `cskg:CohortFlowStage` | Reproducibility counts for cohort construction |

---

## 3. Candidate External Resources

| Prefix | Resource | Planned role |
|---|---|---|
| `sosa:` | SOSA/SSN | Sensor observations, sensors, procedures |
| `prov:` | PROV-O | Provenance, derivation, software execution |
| `time:` | OWL-Time | Days, intervals, temporal positions |
| `qudt:` / `unit:` | QUDT | Quantities and units where suitable |
| `ucum:` | UCUM | Unit representation where QUDT is not enough |
| `dct:` | Dublin Core Terms | Identifiers, source metadata, labels |
| `dcat:` | DCAT | Dataset and distribution metadata |
| `ncit:` | NCI Thesaurus | Cancer terminology after codebook mapping |
| `cskg:` | Project ontology | Operational accelerometry definitions not covered cleanly elsewhere |

Important: project-specific terms should only be added after checking reuse options. The current `cskg:` terms are working names for the pilot skeleton.

---

## 4. Core Modeling Pattern

The pilot KG should follow this chain:

```text
Participant
  -> CancerHistoryAssertion / CancerDiagnosis
  -> Sensor / DevicePlacement
  -> Minute-level SOSA Observation
  -> DailyMovementSummary
  -> DerivedMovementFeatureSet
  -> ProcessingProtocol
  -> ProtocolApplicationResult
```

Each derived result should point back to:

```text
raw NHANES source file
processed CSV table
pipeline script
protocol definition
execution timestamp / manifest
```

This provenance pattern should use `prov:wasDerivedFrom`, `prov:wasGeneratedBy`, and a project-level software execution entity.

---

## 5. Ready Mappings

These fields are ready for the first pilot KG because they have already been generated and validated:

| Source | Meaning |
|---|---|
| `SEQN` + `cycle` | Participant URI key |
| `MCQ220` | Cancer history assertion source |
| `cancer_diagnoses.csv` | Diagnosis slots and age-at-diagnosis source structure |
| `PAXTMD` | Total recorded minutes |
| `PAXVMD` | Valid minutes |
| `PAXMTSD` | Daily total MIMS |
| `PAXWWMD` | Valid wake wear minutes |
| `PAXSWMD` | Valid sleep wear minutes |
| `PAXNWMD` | Valid non-wear minutes |
| `PAXUMD` | Valid unknown-status minutes |
| `PAXQFD` | Daily quality flag score |
| `PAXMTSM` | Minute-level triaxial MIMS observation |
| `PAXQFM` | Minute-level quality flag score |
| `daily_total_valid_mims_from_minutes` | Derived and validated daily total MIMS |
| `peak_30_valid_mims` | Derived peak-30 MIMS feature |
| `protocol_id` | Processing protocol identifier |
| `eligible_under_protocol` | Operational eligibility assertion |

---

## 6. Important Validation Result

The PAXDAY/PAXMIN validation passed:

```text
matched participant-days: 7785
failed rows: 0
```

The validation confirmed that `PAXDAY` agrees with minute-derived `PAXMIN` values for:

- total recorded minutes,
- valid minutes,
- daily total MIMS,
- wake wear minutes,
- sleep wear minutes,
- non-wear minutes,
- unknown minutes,
- quality flag score.

Important detail:

`PAXQFD` should be modeled as a daily quality flag score. It matches the sum of minute-level `PAXQFM` values. It is not simply the count of flagged minutes.

---

## 7. Mappings That Need Codebook Work

These are not blocked technically, but they need NHANES codebook interpretation before strong semantic claims:

| Field/group | Needed work |
|---|---|
| `RIAGENDR` | Map gender codes to labels/concepts |
| `RIDRETH1`, `RIDRETH3` | Map race/ethnicity codes to labels/concepts |
| `MCQ230*` / `cancer_type_code` | Map NHANES cancer type codes to NCIt concepts |
| `PAXDAYWD`, `PAXDAYWM` | Map day-of-week codes |
| `PAXPREDM` | Confirm official labels for wake/sleep/non-wear/unknown |
| `PAXFLGSM` | Interpret minute-level quality flag labels |
| other raw `DEMO` / `MCQ` fields | Select which clinical/covariate fields belong in first KG |

---

## 8. Proposed URI Pattern

For the pilot graph, use deterministic local URIs.

Examples:

```text
cskg:participant/{cycle}/{SEQN}
cskg:cancer-diagnosis/{cycle}/{SEQN}/{diagnosis_slot}
cskg:pam-day/{cycle}/{SEQN}/{PAXDAYD}
cskg:pam-minute/{cycle}/{SEQN}/{PAXDAYM}/{PAXSSNMP}
cskg:feature-set/{cycle}/{SEQN}/{PAXDAYM}
cskg:protocol/{protocol_id}
cskg:protocol-result/{cycle}/{SEQN}/{protocol_id}
```

Keep `SEQN` as the source identifier but do not expose it as a global real-world person identifier outside the local NHANES graph context.

---

## 9. Next Step

Build a small pilot RDF graph for 10-20 participants using this mapping.

The pilot graph should answer:

1. Which participants have self-reported cancer history?
2. What diagnosis code slots were reported?
3. Which days have valid accelerometry summaries?
4. What minute-derived features were generated?
5. Which protocol was applied?
6. Why was a participant eligible or not under each protocol?
7. Which source files and scripts generated the result?

After that, add SHACL checks for:

- missing unit,
- missing provenance,
- missing device placement,
- incompatible metric/device/placement,
- missing protocol source,
- protocol result without valid supporting days.
