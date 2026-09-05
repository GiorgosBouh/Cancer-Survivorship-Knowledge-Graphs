# Competency Questions

**Purpose:** show what the pilot knowledge graph should answer beyond a flat CSV export.

The current KG is still a pilot representation of one NHANES use case. These questions define the query behavior needed before claiming broader semantic harmonisation.

## CQ1: Which participants are included by one valid-day protocol but excluded by another?

Reviewer risk addressed: protocol choice must have demonstrable consequences.

SPARQL: `queries/competency/cq1_protocol_discordance.rq`

## CQ2: What are the protocol definitions, review decisions, and interpretation limits?

Reviewer risk addressed: protocols must be represented as reviewed completeness/sensitivity rules, not activity classifications.

SPARQL: `queries/competency/cq2_protocol_review_status.rq`

## CQ3: Which cancer type labels remain source-coded or candidate-only rather than approved NCIt assertions?

Reviewer risk addressed: NCIt candidate mappings must not be treated as approved medical semantics.

SPARQL: `queries/competency/cq3_pending_cancer_type_mappings.rq`

## CQ4: For each participant-day, what source table and software activity generated the movement features?

Reviewer risk addressed: the KG must expose provenance, not only joined values.

SPARQL: `queries/competency/cq4_daily_feature_provenance.rq`

## CQ5: Which minute observations carry MIMS values, wear-state source labels, and quality-flag information?

Reviewer risk addressed: MIMS and wear state remain measurement summaries/source labels, not behavioral classes.

SPARQL: `queries/competency/cq5_minute_measurement_context.rq`

## CQ6: Which participants are explicitly represented as self-reported cancer-history cases?

Reviewer risk addressed: the cohort must not be overclaimed as clinically verified survivorship.

SPARQL: `queries/competency/cq6_self_reported_cancer_history.rq`

## CQ7: Which harmonisation mappings and definitions are compatible, source-specific, or not harmonisable?

Reviewer risk addressed: harmonisation must preserve metric incompatibility rather than hiding it.

SPARQL: `queries/competency/cq7_harmonisation_compatibility.rq`

## CQ8: What citation evidence supports each valid-day protocol, and what is the support level?

Reviewer risk addressed: protocol citations must show scoped evidence, not broad clinical validation.

SPARQL: `queries/competency/cq8_protocol_citation_provenance.rq`

## Current Status

The SPARQL files are query-ready artifacts. They should be executed against `data/processed/pilot_kg.ttl` with a standards-compliant RDF engine as the next validation step.

## Executed Results

The queries were executed against `data/processed/pilot_kg.ttl` after review-oriented sampling and synthetic harmonisation enrichment were added. Results are stored in:

```text
reports/competency_question_results.json
```

| Query | Rows returned |
|---|---:|
| CQ1 protocol discordance | 40 |
| CQ2 protocol review status | 3 |
| CQ3 pending cancer type mappings | 25 |
| CQ4 daily feature provenance | 60 |
| CQ5 minute measurement context | 300 |
| CQ6 self-reported cancer history | 20 |
| CQ7 harmonisation compatibility | 11 |
| CQ8 protocol citation provenance | 12 |
