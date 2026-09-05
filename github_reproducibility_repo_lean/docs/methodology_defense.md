# Methodology Defense

**Project:** Automated Semantic Harmonisation of Accelerometry-Based Physical Activity Definitions for Cancer-Survivorship Knowledge Graphs

**Purpose:** provide a reviewer-facing defense of the current pilot methodology, its safeguards, and its claim boundaries.

This document deliberately separates what the project now demonstrates from what remains pending. It should be used as the basis for proposal, paper, and reviewer-response text.

## 1. Defensible Current Claim

The current implementation demonstrates a reproducible semantic representation layer for accelerometry-derived physical activity definitions in adults with self-reported cancer history in NHANES 2011-2014. It also demonstrates harmonisation mechanics inside the RDF pilot graph using a deterministic synthetic contrasting source.

The defensible claim is:

```text
The project can represent source-specific accelerometry variables, valid-day completeness protocols, provenance, review status, and interpretation limits in a knowledge graph and associated harmonisation tables, while preventing incompatible activity-intensity claims.
```

The current implementation should not be described as a fully validated clinical survivorship knowledge graph or as a cross-study epidemiologic analysis.

## 2. Main Reviewer Risks and Responses

| Reviewer risk | Methodological response | Evidence artifact |
|---|---|---|
| The work is only a data pipeline, not semantic harmonisation. | A synthetic hip-worn counts/minute source was added to the RDF pilot graph to contrast with NHANES wrist MIMS. Source variables are mapped to harmonised constructs with explicit compatibility status. | `docs/semantic_harmonisation_demo.md`, `data/processed/harmonisation_source_variable_map.csv`, `data/processed/pilot_kg.ttl` |
| Wrist MIMS might be incorrectly treated like hip counts/minute. | MIMS and counts/minute are preserved as source-specific metrics. The harmonisation bridge aligns them only at construct level, not as numeric equivalents. | `data/processed/harmonisation_source_variable_map.csv`, `docs/ontology.md` |
| MVPA or sedentary thresholds might be overclaimed. | Hip counts/minute cut points are represented only as source-defined synthetic classifications. No MVPA, sedentary, active/inactive, or clinical physical-activity classification is inferred for NHANES wrist MIMS. | `data/processed/harmonised_activity_definitions.csv`, `docs/semantic_harmonisation_demo.md` |
| Valid-day rules may be arbitrary filters. | Protocols are modeled as reviewed completeness/sensitivity rules; citation evidence now separates source-variable support, literature context, and local review decisions. Outcome sensitivity quantifies how protocol choice changes eligibility and movement summaries. | `docs/protocols/protocol_citations.md`, `docs/protocols/outcome_sensitivity.md`, `data/processed/protocol_pairwise_inclusion_comparison.csv` |
| The cohort may be overdescribed as clinically verified cancer survivorship. | `MCQ220` is modeled as self-reported cancer-history evidence only, not registry-confirmed diagnosis, treatment, stage, recurrence, or current disease status. | `docs/pilot_kg.md`, `ontology/cskg.ttl`, `queries/competency/cq6_self_reported_cancer_history.rq` |
| Candidate NCIt mappings may be overinterpreted. | NCIt expert review is complete with caveats. The validation policy guard permits reviewed NCIt IRIs only as qualified mappings from self-reported source codes. | `reports/pilot_kg_shacl_validation_summary.json`, `docs/review/ncit_mapping_review_status.md` |
| The graph may lack structural validation. | The pilot RDF graph passes the local required-property validator and the standards-compliant pySHACL gate. | `reports/pilot_kg_shacl_validation_summary.json`, `shapes/pilot_kg_shapes.ttl` |
| The graph may not answer meaningful questions. | Six competency questions were implemented and executed against the pilot graph. | `docs/competency_questions.md`, `reports/competency_question_results.json` |

## 3. Data Foundation

The current data foundation uses NHANES 2011-2012 and 2013-2014:

- `DEMO`
- `MCQ`
- `PAXHD`
- `PAXDAY`
- `PAXMIN`

The retained population is adults age 20+ with `MCQ220 = 1`, described as adults with a self-reported history of cancer. This is intentionally not called an EHR-confirmed, registry-confirmed, or clinically verified cancer survivorship cohort.

Current processed data include:

- `data/processed/participants.csv`
- `data/processed/cancer_diagnoses.csv`
- `data/processed/pam_days.csv`
- `data/processed/pam_minutes.csv`
- `data/processed/pam_minute_features.csv`
- `data/processed/protocol_definitions.csv`
- `data/processed/valid_day_protocol_results.csv`

Data quality checks pass:

```text
reports/data_quality_report.json: passed true
```

The PAXDAY/PAXMIN consistency validation also passes, confirming that daily summaries agree with minute-derived values for the checked fields.

## 4. Protocol Sensitivity Defense

The current protocols are completeness and sensitivity rules only:

| Protocol | Rule | Minimum valid days |
|---|---|---:|
| `wake_wear_10h_min4` | `PAXWWMD >= 600` | 4 |
| `wake_wear_12h_min4` | `PAXWWMD >= 720` | 4 |
| `valid_minutes_20h_min4` | `PAXVMD >= 1200` | 4 |

They are not MVPA, sedentary, active/inactive, or clinical activity classifications.

Outcome sensitivity shows that protocol choice materially changes the analytic cohort:

| Comparison | Discordant participants |
|---|---:|
| `wake_wear_10h_min4` vs `wake_wear_12h_min4` | 85 |
| `wake_wear_10h_min4` vs `valid_minutes_20h_min4` | 57 |
| `wake_wear_12h_min4` vs `valid_minutes_20h_min4` | 142 |

This supports the methodological argument that protocol definitions need to be first-class semantic objects rather than undocumented preprocessing choices.

## 5. Harmonisation Defense

The synthetic contrasting source adds a hip-worn counts/minute pattern with:

- synthetic daily vertical-axis counts,
- valid wear minutes,
- source-defined MVPA minutes by 1952 counts/minute,
- source-defined sedentary minutes by 100 counts/minute.

Current synthetic harmonisation summary:

| Measure | Count |
|---|---:|
| Synthetic participant-day rows | 7785 |
| Synthetic participants | 878 |
| Source variable mappings | 7 |
| Activity/protocol definitions | 4 |
| Pairwise completeness comparison rows | 878 |
| Eligibility agreement rows | 868 |
| Eligibility disagreement rows | 10 |

Compatibility statuses in the source-variable map:

| Compatibility status | Rows |
|---|---:|
| compatible after protocol abstraction | 3 |
| not harmonisable with NHANES wrist MIMS in current KG | 2 |
| source-specific metric; not directly convertible | 2 |

This demonstrates the intended semantic pattern:

```text
source-specific variables -> harmonised construct -> compatibility status -> interpretation limit
```

The key defense is not that wrist MIMS and hip counts/minute become directly comparable. The key defense is that the KG can represent why they are not directly comparable while still aligning them under broader constructs such as valid wear completeness or daily movement volume.

## 6. Knowledge Graph Defense

The pilot graph is intentionally small for inspection and validation:

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
| Activity data sources | 2 |
| Harmonisation source-variable mappings | 7 |
| Harmonised activity definitions | 4 |
| Synthetic daily activity summaries | 60 |
| Protocol citation evidence nodes | 12 |
| Triples | 8648 |

The graph includes:

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
```

It also includes provenance links to source tables and software execution. This is the core reason the graph is methodologically useful: it represents not only values, but also how values were produced, reviewed, constrained, and interpreted.

## 7. Validation Defense

The current pilot RDF graph passes the validation gate:

```text
pySHACL available: true
pySHACL conforms: true
passed: true
triple count: 9324
total checks: 5071
failed checks: 0
failed policy checks: 0
```

The NCIt policy guard also passes:

```text
NCIt review status: review_completed_qualified_assertions_allowed
Qualified NCIt assertion count in RDF graph: 19
```

This means the current graph is structurally valid under the current pilot shapes and asserts reviewed NCIt identifiers only as qualified mappings from self-reported source codes.

## 8. Competency Question Defense

The six competency questions show that the graph answers reviewer-relevant questions beyond a flat CSV export:

| Query | Rows returned | Defense role |
|---|---:|---|
| CQ1 protocol discordance | 40 | Shows protocol-dependent inclusion differences in the pilot graph |
| CQ2 protocol review status | 3 | Shows protocol review decisions and interpretation limits |
| CQ3 reviewed cancer type mappings | 25 | Shows reviewed NCIt mappings are qualified rather than overinterpreted |
| CQ4 daily feature provenance | 60 | Shows source/provenance traversal for movement features |
| CQ5 minute measurement context | 300 | Shows minute observations with measurement context |
| CQ6 self-reported cancer history | 20 | Shows the cohort is represented as self-reported cancer history |
| CQ7 harmonisation compatibility | 11 | Shows compatible, source-specific, and non-harmonisable mappings/definitions |
| CQ8 protocol citation provenance | 12 | Shows scoped citation evidence and support levels for valid-day protocols |

This supports the claim that the KG is queryable around definitions, provenance, review status, and interpretation limits.

## 9. What We Should Not Claim Yet

Do not claim:

- clinically verified cancer survivorship,
- validated MVPA or sedentary classification for NHANES wrist MIMS,
- numeric conversion between MIMS and counts/minute,
- completed NCIt cancer-type ontology alignment,
- full cross-study empirical harmonisation using two real cohorts,
- validated clinical outcome inference.

The current contribution is a reproducible semantic harmonisation scaffold with a validated pilot graph and a synthetic contrasting-source demonstration.

## 10. Recommended Paper/Proposal Wording

Use wording like:

```text
We developed a reproducible semantic representation layer for NHANES wrist accelerometry data among adults with self-reported cancer history and demonstrated the harmonisation pattern using a deterministic synthetic contrasting source. The graph represents accelerometry variables, valid-day completeness protocols, provenance, review status, and interpretation limits. It explicitly prevents incompatible claims such as applying hip-worn counts/minute MVPA or sedentary thresholds to wrist MIMS.
```

Avoid wording like:

```text
We harmonised physical activity intensity across wrist MIMS and hip counts/minute data.
```

Better replacement:

```text
We harmonised source-specific accelerometry definitions at the semantic construct and protocol level while preserving metric incompatibilities and source-specific interpretation limits.
```

## 11. Remaining Work

The next methodological hardening steps are:

1. Keep reviewed NHANES cancer type to NCIt mappings qualified as self-reported source-code mappings, not confirmed disease or histology assertions.
2. Decide whether to expand synthetic harmonisation beyond the selected pilot participant-days.
3. Harden controlled-term mappings for demographic, device, wear-state, and quality-flag codes.
4. Expand the graph only after ontology pattern and review gates are accepted.
