# Pilot Knowledge Graph

**Output:** `data/processed/pilot_kg.ttl`  
**Summary:** `reports/pilot_kg_summary.json`  
**Generator:** `src/cskg_pipeline/build_pilot_kg.py`

---

## Purpose

This is the first small RDF/Turtle pilot graph created from the processed NHANES accelerometry data layer for adults with self-reported cancer history.

It is intentionally small so the modeling pattern can be inspected before generating a full graph. It is a representation pilot, not yet a cross-study harmonisation demonstration.

---

## Current Pilot Size

```text
participants: 20
diagnoses: 25
cancer history assertions: 20
daily movement summaries: 60
derived feature sets: 60
minute observations: 300
processing protocols: 3
protocol application results: 60
activity data sources: 2
harmonisation source-variable mappings: 7
harmonised activity definitions: 4
synthetic daily activity summaries: 60
protocol citation evidence nodes: 12
triples: 8648
code mapping rows loaded: 96
code labels enriched: true
protocol review rows loaded: 3
protocol review enriched: true
protocol citation evidence rows: 12
protocol citation enriched: true
synthetic harmonisation enriched: true
```

Selection strategy:

```text
participants with protocol-discordant inclusion results first, then cycle and SEQN order
```

Limits used:

```text
max participants: 20
max days per participant: 3
max minute observations per day: 5
```

---

## Regenerate

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_pilot_kg --participants 20 --max-days 3 --max-minutes-per-day 5
```

---

## Code Label Enrichment

The pilot graph is now enriched with CDC/NHANES source labels from:

```text
data/processed/code_mappings.csv
```

Examples of added labels:

```text
cskg:genderLabel
cskg:raceEthnicityLabel
cskg:cancerHistoryLabel
cskg:cancerTypeLabel
cskg:cancerTypeMappingStatus
cskg:devicePlacementLabel
cskg:deviceOrientationLabel
cskg:dayOfWeekLabel
cskg:predictedWearStateLabel
cskg:qualityFlagScoreLabel
cskg:qualityFlagLabelDescription
```

The original source codes are still preserved. The labels are added beside them, not instead of them.

---

## Protocol Review Enrichment

The pilot graph is now enriched with approved protocol review metadata from:

```text
docs/protocols/protocol_review_sheet.csv
```

Examples of added protocol metadata:

```text
cskg:protocolReviewDecision
cskg:protocolApprovedStatus
cskg:protocolApprovedExpression
cskg:protocolApprovedMinValidDays
cskg:protocolReviewerComment
cskg:protocolInterpretationLimit
```

The graph explicitly records that accepted protocols are data completeness/sensitivity rules only, not MVPA, sedentary, active/inactive, or clinical physical activity classifications.

## Protocol Citation Provenance

The pilot graph now includes citation evidence nodes for the three valid-day protocols. These nodes distinguish official NHANES source-variable documentation, literature context, and local project review decisions. The citation evidence is scoped: it supports source-variable meaning and completeness/sensitivity rationale, not MVPA, sedentary, active/inactive, or clinical physical-activity classification.

Current RDF citation count:

```text
protocol citation evidence nodes: 12
```

## Synthetic Harmonisation Enrichment

The pilot graph now includes the synthetic contrasting source as RDF, not only as CSV documentation. The enrichment adds:

```text
cskg:ActivityDataSource
cskg:HarmonisedSourceVariableMapping
cskg:HarmonisedActivityDefinition
cskg:SyntheticDailyActivitySummary
```

Current RDF enrichment counts:

```text
activity data sources: 2
harmonisation source-variable mappings: 7
harmonised activity definitions: 4
synthetic daily activity summaries: 60
```

The synthetic daily summaries are limited to the same selected participant-days as the pilot graph. They are linked back to their seed NHANES day with `cskg:seededFromNhanesDay` and carry explicit interpretation limits stating that the synthetic source is not measured hip accelerometry and not a conversion from wrist MIMS.

---

## Competency Questions

Query-ready competency questions were added in:

```text
docs/competency_questions.md
queries/competency/
```

They cover protocol discordance, protocol review status, reviewed NCIt mappings, provenance traversal, minute measurement context, and self-reported cancer history.

## Validation

SHACL shapes were added for the pilot graph:

```text
shapes/pilot_kg_shapes.ttl
```

A lightweight local validator was also added:

```text
src/cskg_pipeline/validate_pilot_kg.py
```

Run validation with:

```bash
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg
```

Current validation result:

```text
passed: true
total checks: 5071
failed checks: 0
failed policy checks: 0
triple count: 9324
pySHACL conforms: true
```

The local validator mirrors required-property checks from the SHACL shapes. Full `pyshacl` validation has been added as the standards-compliant gate; run with `--require-pyshacl` for paper/proposal claims.

Additional policy guard:

```text
NCItReviewPendingGuard: passed
NCIt review status: review_completed_qualified_assertions_allowed
Qualified NCIt assertion count in RDF graph: 19
```

This guard now allows reviewed NCIt IRIs as qualified mapping metadata from self-reported NHANES cancer-type codes; these are not confirmed diagnosis, histology, stage, treatment, recurrence, or current disease-status assertions.

---

## Included Pattern

The graph connects:

```text
Participant
  -> CancerDiagnosis
  -> Sensor
  -> DailyMovementSummary
  -> Minute-level SOSA Observation
  -> DerivedMovementFeatureSet
  -> ProcessingProtocol
  -> ProtocolApplicationResult
```

It also includes provenance links to source tables and the graph-building software execution.

---

## Main Prefixes

```text
cskg: project ontology working namespace
sosa: sensor observations
prov: provenance
dct: identifiers and source metadata
time: temporal positions
qudt: quantity modeling placeholder
```

---

## Protocol Outcome Sensitivity

Protocol outcome sensitivity has also been computed in `docs/protocols/outcome_sensitivity.md`. The three accepted completeness/sensitivity rules change both participant inclusion and movement-summary estimates.

## Important Caveat

This pilot graph does not yet include finalized external ontology alignment for all fields.

Some values remain source-code values, especially:

- NHANES demographic codes,
- cancer type codes,
- quality flag labels,
- device placement codes,
- protocol citation metadata.

These are intentionally preserved as source-coded values until codebook mapping and expert review are completed.

---

## Next Step

Use the validated pilot graph to review the modeling pattern, then expand toward a fuller KG.

Immediate follow-up items:

- run full `pyshacl` validation when `rdflib` and `pyshacl` are installed,
- map source code values to controlled ontology terms,
- add citation-level protocol justification,
- keep wrist MIMS definitions separate from incompatible hip-count thresholds.
