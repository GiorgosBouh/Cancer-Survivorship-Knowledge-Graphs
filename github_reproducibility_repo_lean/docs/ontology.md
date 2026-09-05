# Project Ontology

**Ontology file:** `ontology/cskg.ttl`  
**Namespace:** `https://w3id.org/cskg/ontology/`  
**Version:** `0.1.0-pilot`

---

## Purpose

This is the first working ontology for the NHANES accelerometry graph for adults with self-reported cancer history.

It defines the project terms currently used by the pilot RDF graph and SHACL validation layer. It is intentionally conservative: it models generated data structures, provenance, review gates, and interpretation limits while marking codebook-dependent terms as provisional. It should be described as a representation and synthetic harmonisation pilot until a second real dataset demonstrates empirical cross-study harmonisation.

---

## What It Covers

The ontology currently defines classes for:

- `cskg:Participant`
- `cskg:CancerHistoryAssertion`
- `cskg:SelfReportedCancerHistory`
- `cskg:CancerDiagnosis`
- `cskg:DailyMovementSummary`
- `cskg:DerivedMovementFeatureSet`
- `cskg:ProcessingProtocol`
- `cskg:ProtocolApplicationResult`
- `cskg:CohortFlowStage`
- device placement/orientation placeholders
- quality flag and wear-state placeholders
- survey design variables

It also defines source-code label enrichment properties such as `cskg:genderLabel`, `cskg:cancerTypeLabel`, `cskg:predictedWearStateLabel`, and `cskg:qualityFlagLabelDescription`.

It also defines protocol review enrichment properties such as `cskg:protocolReviewDecision`, `cskg:protocolApprovedStatus`, and `cskg:protocolInterpretationLimit`.

It also defines object and datatype properties used to connect:

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

---

## Reused Ontologies

The pilot ontology reuses established vocabularies where suitable:

| Vocabulary | Role |
|---|---|
| RDF/RDFS/OWL | ontology structure |
| Dublin Core Terms | identifiers and metadata |
| PROV-O | provenance, derivation, software execution |
| SOSA/SSN | sensors and observations |
| OWL-Time | planned temporal modeling |
| QUDT/UCUM | planned quantity/unit hardening |
| NCIt | planned cancer type mapping |

---

## Important Modeling Decisions

`MCQ220` is represented as a source cancer-history assertion. It is not treated as a registry-confirmed cancer diagnosis.

`PAXQFD` is modeled as a quality flag score. It matches the sum of minute-level `PAXQFM` values, not simply a count of flagged minutes.

Wrist MIMS values are kept separate from hip-worn counts/minute thresholds. The ontology includes compatibility warnings to avoid claiming MVPA or sedentary behavior classification from incompatible thresholds.

---


## Review-Driven Safeguards

The ontology now includes explicit safeguards requested by methodological review:

- `cskg:SelfReportedCancerHistory` separates NHANES MCQ220 self-report from clinically verified diagnosis.
- `cskg:MIMSUnit` declares MIMS as a custom movement-summary unit.
- MIMS properties include notes preventing MVPA, sedentary, active/inactive, or clinical physical activity interpretation without a validated protocol.
- `ontology/cskg_alignment_candidates.ttl` records candidate alignment to external standards without using premature `owl:equivalentClass` assertions.

## Protocol Citation Terms

The ontology now includes citation/provenance terms for protocol evidence:

- `cskg:ProtocolCitationEvidence`
- `cskg:hasProtocolCitationEvidence`
- `cskg:citationRole`
- `cskg:supportLevel`
- `cskg:citedClaim`
- `cskg:evidenceStatus`

These terms let the graph distinguish source-variable documentation, literature context, and project review decisions. They are intentionally scoped and do not assert clinical validity for the completeness thresholds.

## Synthetic Harmonisation Terms

The ontology now includes a synthetic harmonisation extension used by the pilot RDF graph:

- `cskg:ActivityDataSource`
- `cskg:HarmonisedSourceVariableMapping`
- `cskg:HarmonisedActivityDefinition`
- `cskg:SyntheticDailyActivitySummary`
- `cskg:CountsPerMinuteUnit`

These terms let the graph represent NHANES wrist MIMS and synthetic hip counts/minute as separate source patterns, align their variables at construct level, and preserve compatibility warnings. The ontology does not assert that MIMS and counts/minute are convertible.

## Still Provisional

These areas still need codebook mapping or expert review:

- NHANES gender codes,
- NHANES race/ethnicity codes,
- NHANES cancer type codes to NCIt concepts,
- device placement and orientation codes,
- predicted wear-state codes,
- minute quality flag labels,
- citation-level justification for valid-day protocols.

---

## Relationship to SHACL

The ontology says what the project terms mean.

The SHACL shapes say what must exist in the pilot graph for the graph to be structurally valid.

Current related files:

```text
ontology/cskg.ttl
ontology/cskg_alignment_candidates.ttl
shapes/pilot_kg_shapes.ttl
src/cskg_pipeline/validate_pilot_kg.py
reports/pilot_kg_shacl_validation_summary.json
```

Current graph validation result:

```text
passed: true
total checks: 4745
failed checks: 0
```

---

## Next Step

Use this ontology as the stable project vocabulary for the next graph iteration, then harden it by mapping source codes to external controlled vocabularies.
