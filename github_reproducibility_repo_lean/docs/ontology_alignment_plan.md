# Ontology Alignment Plan

**Status:** candidate alignment scaffold, pending ontology review.

The core ontology remains project-local because the first pilot graph is still a single NHANES representation. To avoid creating an isolated vocabulary, the project now has a separate candidate alignment module:

```text
ontology/cskg_alignment_candidates.ttl
```

## Decision

The alignment module uses weak mappings and notes, not `owl:equivalentClass`.

Reason: several local classes are evidence-specific roles or survey-derived entities. For example, `cskg:Participant` is a de-identified NHANES participant role, and `cskg:SelfReportedCancerHistory` is based on a single survey item. Treating those as exact external biomedical classes would overclaim the evidence.

## Current Candidate Alignments

| Local term | Candidate relation | External term or pattern | Status |
|---|---|---|---|
| `cskg:Participant` | `skos:closeMatch` | `foaf:Person` | candidate only |
| `cskg:CancerHistoryAssertion` | `rdfs:subClassOf` | `prov:Entity` | accepted provenance pattern |
| `cskg:SelfReportedCancerHistory` | subclass | `cskg:CancerHistoryAssertion` | accepted local safeguard |
| `cskg:CancerDiagnosis` | `rdfs:subClassOf` | `prov:Entity` | accepted provenance pattern; biomedical mapping pending |
| `cskg:DailyMovementSummary` | `skos:relatedMatch` | `sosa:Observation` | candidate only |
| `cskg:ProcessingProtocol` | `rdfs:subClassOf` | `prov:Plan` | accepted provenance pattern |
| `cskg:MIMSUnit` | `rdfs:subClassOf` | `qudt:Unit` | accepted custom unit pattern |

## Pending Review

Do not add exact biomedical class equivalences until these questions are reviewed:

- Should reported cancer diagnosis slots align to OGMS diagnosis, NCIt disease concepts, or remain survey assertions only?
- Should device placement use UBERON wrist terms or a local NHANES placement code system?
- Should MIMS be modeled as a QUDT unit, a quantity kind, or a custom project metric with unitless values?
- Which match predicate should be used for approved cancer type mappings: exact match, close match, broad match, or narrow match?
