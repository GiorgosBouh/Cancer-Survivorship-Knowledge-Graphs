# Paper / Proposal Package

**Project:** Automated Semantic Harmonisation of Accelerometry-Based Physical Activity Definitions for Cancer-Survivorship Knowledge Graphs

**Status:** paper/proposal-ready technical package for the current pilot implementation.

This document consolidates the current contribution, methods, results, validation evidence, figures/tables, and claim boundaries. It is intended for manuscript drafting, proposal text, supervisor review, and reviewer-response preparation.

## 1. Contribution Statement

This project develops a reproducible semantic representation layer for accelerometry-derived physical activity definitions in adults with self-reported cancer history in NHANES 2011-2014. The pilot links processed NHANES wrist accelerometry data, source-code labels, valid-day completeness protocols, protocol review metadata, citation evidence, provenance, SHACL validation, and competency queries in a cancer-survivorship knowledge graph scaffold.

The current implementation also includes a deterministic synthetic hip-worn counts/minute source, a real same-cohort PhysioNet ActiLife step-derived source, and an independent public NHANES 2003-2006 hip-worn ActiGraph PAM source. The harmonisation layer aligns source-specific variables at the construct and protocol level while preserving explicit warnings that wrist MIMS, ActiLife steps, and hip ActiGraph counts/minute are not numerically interchangeable.

## 2. Core Claim

Defensible claim:

```text
We demonstrate a validated pilot knowledge graph that represents source-specific accelerometry variables, valid-day completeness protocols, protocol citation evidence, provenance, review status, and harmonisation compatibility constraints for adults with self-reported cancer history in NHANES 2011-2014.
```

Claim boundary:

```text
The current graph does not validate MVPA, sedentary, active/inactive, or clinical physical-activity classifications for NHANES wrist MIMS. Reviewed NCIt cancer-type mappings are asserted only as qualified mappings from self-reported NHANES source codes, not as confirmed diagnosis or histology assertions.
```

## 3. Methods Summary

### Data Source

The data layer uses NHANES 2011-2012 and 2013-2014:

- `DEMO`
- `MCQ`
- `PAXHD`
- `PAXDAY`
- `PAXMIN`

The cohort is restricted to adults aged 20+ with `MCQ220 = 1`. This is represented as self-reported cancer history, not clinically verified survivorship.

### Processing Outputs

The reproducible pipeline produces:

- `participants.csv`
- `cancer_diagnoses.csv`
- `pam_days.csv`
- `pam_minutes.csv`
- `pam_minute_features.csv`
- `protocol_definitions.csv`
- `valid_day_protocol_results.csv`
- semantic mapping, code mapping, protocol review, harmonisation, citation, and validation reports.

### Protocols

Three valid-day protocols are represented as completeness/sensitivity rules:

| Protocol | Expression | Minimum valid days | Interpretation |
|---|---|---:|---|
| `wake_wear_10h_min4` | `PAXWWMD >= 600` | 4 | baseline wake-wear completeness rule |
| `wake_wear_12h_min4` | `PAXWWMD >= 720` | 4 | stricter sensitivity completeness rule |
| `valid_minutes_20h_min4` | `PAXVMD >= 1200` | 4 | 24-hour valid-minutes completeness rule |

These are not activity-intensity thresholds.

### Knowledge Graph Pattern

The pilot RDF graph connects:

```text
Participant
  -> CancerHistoryAssertion
  -> CancerDiagnosis
  -> Sensor
  -> DailyMovementSummary
  -> Minute-level SOSA Observation
  -> DerivedMovementFeatureSet
  -> ProcessingProtocol
  -> ProtocolApplicationResult
  -> ProtocolCitationEvidence
  -> HarmonisedSourceVariableMapping
  -> HarmonisedActivityDefinition
  -> SyntheticDailyActivitySummary
```

The graph uses PROV-O for derivation/generation links, SOSA for observations/sensors, Dublin Core Terms for identifiers and citations, and a project ontology for accelerometry-specific terms and safeguards.

## 4. Results Snapshot

### Cohort and Data Foundation

Current cohort counts from the completed pipeline:

| Measure | Count |
|---|---:|
| Adult self-reported cancer-history participants | 1035 |
| Participants with PAXDAY | 878 |
| Participants with PAXMIN | 878 |
| Retained minute-level rows | 9949908 |
| Minute-derived feature rows | 7785 |

### Protocol Sensitivity

Protocol choice changes participant inclusion and movement-summary estimates:

| Protocol | Eligible participants | Eligible % | Valid day rows | Mean participant daily MIMS |
|---|---:|---:|---:|---:|
| `wake_wear_10h_min4` | 807 | 91.91344 | 5553 | 11567.603003 |
| `wake_wear_12h_min4` | 722 | 82.232346 | 4824 | 12201.537613 |
| `valid_minutes_20h_min4` | 862 | 98.177677 | 6111 | 10827.114119 |

Pairwise discordance:

| Comparison | Discordant participants |
|---|---:|
| `wake_wear_10h_min4` vs `wake_wear_12h_min4` | 85 |
| `wake_wear_10h_min4` vs `valid_minutes_20h_min4` | 57 |
| `wake_wear_12h_min4` vs `valid_minutes_20h_min4` | 142 |

Interpretation: valid-day definitions materially affect the analytic cohort. Therefore, protocols must be represented as first-class semantic objects rather than undocumented preprocessing choices.

### Pilot KG Size

Current rebuilt pilot graph:

| Entity/result | Count |
|---|---:|
| Participants | 20 |
| Cancer diagnoses | 25 |
| Cancer history assertions | 20 |
| Daily movement summaries | 60 |
| Derived feature sets | 60 |
| Minute observations | 300 |
| Processing protocols | 3 |
| Protocol application results | 60 |
| Protocol citation evidence nodes | 12 |
| Activity data sources | 4 |
| Harmonisation source-variable mappings | 9 |
| Harmonised activity definitions | 4 |
| Synthetic daily activity summaries | 60 |
| Independent PAM daily summaries | 20 |
| RDF triples | 9185 |

### Synthetic Harmonisation

The synthetic source is represented in the RDF graph as a second accelerometry source pattern:

| Component | Count |
|---|---:|
| Activity data sources | 4 |
| Harmonisation source-variable mappings | 9 |
| Harmonised activity definitions | 4 |
| Synthetic daily activity summaries in pilot KG | 60 |

Compatibility statuses in the harmonisation bridge:

| Compatibility status | Rows |
|---|---:|
| compatible after protocol abstraction | 3 |
| source-specific metric; not directly convertible | 2 |
| not harmonisable with NHANES wrist MIMS in current KG | 2 |

Interpretation: harmonisation is represented as construct-level alignment with explicit incompatibility status, not numeric conversion.

### Real PhysioNet ActiLife Step Source

A real non-synthetic derived accelerometry source has now been integrated:

| Measure | Value |
|---|---:|
| Source | PhysioNet NHANES-derived ActiLife steps v1.0.2 |
| DOI | 10.13026/d7sw-f662 |
| Source rows scanned | 130186 |
| Cohort daily summary rows | 7785 |
| Participants with ActiLife steps | 878 |
| Mean daily ActiLife steps over participants | 7940.529821 |

Paired real-source semantic evaluation:

| Measure | Value |
|---|---:|
| Paired MIMS-step daily rows | 7785 |
| Paired participants | 878 |
| Pearson correlation, MIMS vs ActiLife steps | 0.957383 |
| Spearman correlation, MIMS vs ActiLife steps | 0.96414 |
| High semantic risk rows | 1 |

Interpretation: PhysioNet ActiLife steps provide a real derived step-count source for semantic evaluation. The correlation with MIMS can be reported descriptively, but it does not establish numeric conversion, MVPA, sedentary classification, or clinical physical-activity status.


### Independent NHANES 2003-2006 PAM Source

An independent public accelerometry source has now been integrated for semantic validation:

| Measure | Value |
|---|---:|
| Source | NHANES 2003-2006 Physical Activity Monitor PAXRAW_C/PAXRAW_D |
| Device/setup | hip-worn ActiGraph AM-7164, 1-minute epochs |
| Cancer-history adults before PAM filtering | 892 |
| Participants with PAM minute records | 768 |
| Daily PAM summary rows | 5367 |
| Retained PAM minute rows | 7724170 |
| 2003-2004 participants with PAM | 410 |
| 2005-2006 participants with PAM | 358 |

Interpretation: this source is independent from the 2011-2014 wrist/MIMS source by participant, survey cycle, device placement, and metric. It supports a stronger cross-source semantic validation case than PhysioNet alone. It still does not support numeric conversion between hip ActiGraph counts, steps, and wrist MIMS, and it is not an independent clinical cancer-survivorship cohort.

### Protocol Citation Evidence

Citation/provenance layer:

| Evidence role | Rows |
|---|---:|
| source-variable documentation | 6 |
| literature context | 3 |
| project-review decision | 3 |
| total citation evidence rows | 12 |

The citation layer separates source-variable support, literature context, and local review decisions. It does not validate MVPA or sedentary classification for NHANES wrist MIMS.

## 5. Validation

The current pilot graph passes both local required-property validation and the standards-compliant pySHACL gate:

```text
pySHACL conforms: true
triple count: 9324
total local checks: 5071
failed checks: 0
failed policy checks: 0
```

NCIt guard:

```text
NCIt review status: review_completed_qualified_assertions_allowed
Qualified NCIt assertion count: 19
```

This means the graph is structurally valid under the current pilot shapes and asserts reviewed NCIt identifiers only as qualified mappings from self-reported source codes.

## 6. Competency Questions

The graph answers eight reviewer-relevant competency questions:

| Query | Rows returned | Reviewer risk addressed |
|---|---:|---|
| CQ1 protocol discordance | 40 | protocol choice changes inclusion |
| CQ2 protocol review status | 3 | protocols are reviewed completeness/sensitivity rules |
| CQ3 reviewed cancer type mappings | 25 | Reviewed NCIt mappings are qualified and not overinterpreted |
| CQ4 daily feature provenance | 60 | movement features expose provenance |
| CQ5 minute measurement context | 300 | MIMS/wear-state/quality context is queryable |
| CQ6 self-reported cancer history | 20 | cohort is not overclaimed as clinically verified survivorship |
| CQ7 harmonisation compatibility | 11 | compatibility/incompatibility is queryable |
| CQ8 protocol citation provenance | 12 | protocol evidence and support level are queryable |
| CQ9 independent PAM source validation | 20 | independent source evidence and non-conversion limits are queryable |

### Domain/Ontology Review and Reproducibility Status

Prepared artifacts:

| Artifact | Status |
|---|---|
| `docs/review/domain_ontology_review_sheet.csv` | prepared, pending external review |
| `docs/review/domain_ontology_review_instructions.md` | prepared |
| `reports/domain_ontology_review_status.json` | `prepared_pending_external_review` |
| `docs/reproducibility_archive_plan.md` | prepared, DOI deposit pending |
| `docs/reporting_checklists.md` | draft checklist prepared |

Interpretation: the project is ready to send for independent domain/ontology review, but it must not claim completed external expert approval yet.

## 7. Main Tables for Manuscript / Proposal

Recommended tables:

| Table | Source artifact | Purpose |
|---|---|---|
| Table 1: cohort construction | `data/processed/cohort_flow.csv` | show reproducible cohort filtering and accelerometry availability |
| Table 2: protocol definitions and interpretation limits | `data/processed/protocol_definitions.csv`, `docs/protocols/protocol_review_sheet.csv` | show rules are completeness/sensitivity definitions only |
| Table 3: protocol outcome sensitivity | `docs/protocols/outcome_sensitivity.md` | show protocol-dependent inclusion and movement summaries |
| Table 4: KG summary and validation | `reports/pilot_kg_summary.json`, `reports/pilot_kg_shacl_validation_summary.json` | show graph content and validation status |
| Table 5: harmonisation compatibility | `data/processed/harmonisation_source_variable_map.csv` | show compatible/source-specific/non-harmonisable constructs |
| Table 6: protocol citation evidence | `docs/protocols/protocol_citation_evidence.csv` | show scoped support levels for protocol components |
| Table 7: competency query results | `reports/competency_question_results.json` | show query behavior beyond flat CSVs |

## 8. Figure Plan

### Figure 1: Reproducible Data-to-KG Pipeline

Suggested content:

```text
NHANES DEMO/MCQ/PAXHD/PAXDAY/PAXMIN
  -> processed participant/day/minute/features tables
  -> protocol definitions and protocol results
  -> RDF graph + ontology + SHACL validation
```

Purpose: show that the KG is generated from reproducible data artifacts, not manually assembled.

### Figure 2: Semantic Harmonisation Pattern

Suggested content:

```text
NHANES wrist MIMS source
  -> PAXMTSD/PAXWWMD/PAXVMD
  -> harmonised constructs
  -> compatibility status

Synthetic hip counts/minute source
  -> counts/minute, valid wear, source-defined MVPA/sedentary
  -> harmonised constructs
  -> compatibility status
```

Purpose: show that harmonisation preserves incompatibility warnings rather than hiding them.

### Figure 3: Protocol Sensitivity and Review Gates

Suggested content:

```text
valid-day protocol definitions
  -> protocol review status
  -> citation evidence
  -> participant inclusion differences
  -> SHACL + policy guard
```

Purpose: show why protocol definitions are represented as first-class semantic objects.

## 9. Recommended Manuscript Wording

Use:

```text
We developed a reproducible semantic representation layer for NHANES 2011-2014 wrist accelerometry data among adults with self-reported cancer history. The pilot knowledge graph represents source variables, daily and minute-level movement summaries, valid-day completeness protocols, protocol citation evidence, provenance, review status, and harmonisation compatibility constraints. A deterministic synthetic hip-worn counts/minute source demonstrates how incompatible source patterns can be aligned at the construct and protocol level without asserting numeric equivalence.
```

Use:

```text
Protocol definitions were represented as data completeness and sensitivity rules. Outcome sensitivity analysis showed that protocol choice changed participant inclusion and movement-summary distributions, supporting the need to encode protocol definitions explicitly rather than treating them as hidden preprocessing choices.
```

Use:

```text
The graph passed a pySHACL validation gate and a policy guard that now permits reviewed NCIt IRIs only as qualified mappings from self-reported source codes.
```

## 10. Claims To Avoid

Do not claim:

- clinically verified cancer survivorship,
- validated MVPA/sedentary classification for NHANES wrist MIMS,
- numeric conversion between MIMS and counts/minute,
- completed NCIt cancer-type ontology alignment,
- validated cross-study epidemiologic harmonisation using two real measured cohorts,
- clinical outcome inference.

## 11. Top-Tier Readiness Status

Current top-tier status:

```text
not_ready_blocking_gaps_remain
```

The project is now stronger as a top-tier candidate because it includes reviewer-facing risk registers and a real PhysioNet ActiLife step-count source showing where naive harmonisation would be unsafe. The current evaluation identifies:

```text
semantic risk rows: 4
high semantic risk rows: 3
real-source semantic risk rows: 1
protocol risk rows: 3
maximum protocol-discordant participants: 16.173121 percent
```

The main contribution should be framed as:

```text
A semantic validation framework for preventing invalid harmonisation of accelerometry-derived physical-activity definitions in cancer-survivorship research.
```

Not as:

```text
A completed cancer-survivorship knowledge graph or completed cross-study epidemiologic harmonisation.
```

New real-source artifacts:

```text
docs/real_accelerometry_source_selection.md
docs/physionet_real_source_overlap.md
data/processed/real_source_required_files.csv
data/processed/real_accelerometry_source_selection.csv
data/processed/physionet_source_cohort_overlap.csv
data/processed/physionet_source_cohort_overlap_by_cycle.csv
reports/real_accelerometry_source_selection_summary.json
reports/physionet_source_overlap_summary.json
```

Selected source:

```text
PhysioNet Minute level step counts and physical activity data from NHANES 2011-2014
version: 1.0.2
DOI: 10.13026/d7sw-f662
metadata status: downloaded and checksum-verified
cohort overlap: 1035/1035 project cancer-history participants present in PhysioNet metadata
```

New top-tier planning artifacts:

```text
docs/top_tier_submission_plan.md
docs/evaluation/naive_vs_semantic_harmonisation.md
data/processed/semantic_harmonisation_risk_register.csv
data/processed/protocol_discordance_risk_register.csv
data/processed/top_tier_dataset_candidates.csv
data/processed/top_tier_readiness_checklist.csv
reports/top_tier_readiness_summary.json
```

## 12. Current Limitations

Current limitations:

- Cancer history is self-reported via NHANES `MCQ220`.
- Cancer type to NCIt mapping expert review is complete with caveats; reviewed NCIt IRIs remain qualified source-code mappings, not confirmed disease or histology assertions.
- Synthetic hip counts/minute data are demonstration artifacts, not measured data. A real PhysioNet derived ActiLife step-count source has now been downloaded, checksum-verified, cohort-linked, and semantically evaluated, but it is derived from the same NHANES wrist source rather than an independent external cohort.
- Protocol citations provide scoped evidence and context, not clinical validation.
- The RDF graph is a pilot subset for inspection and validation, not a full-scale graph export.
- External controlled-term mappings for demographics, device placement, wear state, and quality flags remain incomplete.

## 13. Next Work Package

Recommended next steps for a stronger top-tier submission:

1. Keep reviewed NCIt cancer-type IRIs qualified as self-reported source-code mappings. CAPTURE-24 remains the stronger open external validation candidate; NCI IDATA ActiGraph remains the best cancer-relevant candidate but requires access approval.
2. Extend the real-source semantic evaluation to ActiGraph activity counts (`csv/nhanes_1440_AC.csv.xz`) or an independent external source if top-tier target requires external-cohort validation.
3. Add independent ontology/domain review of compatibility statuses and interpretation limits.
4. Generate final figure drafts from `docs/manuscript/figure*_*.csv` and the risk-register outputs.
5. Prepare a public reproducibility archive with code, generated reusable artifacts, environment details, and DOI.
6. Add reporting checklists, including observational-reporting and FAIR/data-resource readiness materials.
