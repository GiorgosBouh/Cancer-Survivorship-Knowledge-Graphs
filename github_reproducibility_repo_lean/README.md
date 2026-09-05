# Cancer Survivorship Accelerometry Knowledge Graph

This is the lean GitHub reproducibility package for the manuscript:

**When Definitions Change Conclusions: An Auditable Knowledge Graph for Accelerometer Use in Cancer Survivorship Research**

The repository contains the core scripts, ontology artifacts, validation shapes, competency queries, manuscript outputs, and compact derived outputs needed to inspect and reproduce the paper results. It is intentionally not a raw-data archive.

## Main Scientific Point

The same accelerometer data can lead to different conclusions when studies use different wear-time rules, valid-day rules, cut-points, bout definitions, device placements, or source metrics. This project represents those definitions as auditable semantic objects in a knowledge graph.

The project does **not** claim that wrist MIMS, hip ActiGraph counts, steps, MVPA, sedentary time, active/inactive status, or clinical activity status are numerically interchangeable.

## What Is Included

- `src/cskg_pipeline/`: all Python pipeline modules.
- `scripts/`: helper script for segmented large-file downloads.
- `ontology/`: project ontology and candidate alignment file.
- `shapes/`: SHACL shapes used to validate the pilot KG.
- `queries/competency/`: SPARQL competency queries CQ1-CQ9.
- `data/processed/`: compact processed outputs needed for manuscript tables, KG inspection, review status, semantic maps, and participant-level summaries.
- `reports/`: key summary JSON reports and validation summaries.
- `docs/`: methodology notes, review sheets, manuscript tables, protocol documentation, and evaluation notes.
- `latex_jws_elsevier/`: manuscript source package and table inputs.
- `DATA_SOURCES.md`: where to obtain raw public files.
- `REPRODUCE.md`: rebuild order.

## What Is Deliberately Excluded

The full working project contained large raw and intermediate files that are not suitable for GitHub:

- `data/raw/`: public NHANES and PhysioNet source files, about 23 GB locally.
- `data/processed/pam_minutes.csv`: large derived minute-level intermediate, about 1.4 GB.
- full row-level validation dumps such as `paxday_paxmin_validation_rows.csv`.
- `.git/` internals and Python `__pycache__/` directories.
- duplicated project-history logs and nonessential working files.

Raw data can be downloaded from the public sources listed in `DATA_SOURCES.md`.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Rebuild Order

A full rebuild requires raw data in `data/raw/`. The intended sequence is:

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_cohort
PYTHONPATH=src python3 -m cskg_pipeline.validate_paxday_paxmin
PYTHONPATH=src python3 -m cskg_pipeline.build_code_mappings
PYTHONPATH=src python3 -m cskg_pipeline.build_ncit_mapping
PYTHONPATH=src python3 -m cskg_pipeline.import_ncit_expert_review
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_review
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_citations
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_outcome_sensitivity
PYTHONPATH=src python3 -m cskg_pipeline.build_synthetic_harmonisation
PYTHONPATH=src python3 -m cskg_pipeline.build_real_source_selection
PYTHONPATH=src python3 -m cskg_pipeline.build_real_source_overlap
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_actisteps
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_semantic_evaluation
PYTHONPATH=src python3 -m cskg_pipeline.build_independent_nhanes_pam
PYTHONPATH=src python3 -m cskg_pipeline.build_activity_definition_comparison
PYTHONPATH=src python3 -m cskg_pipeline.build_pilot_kg --participants 20 --max-days 3 --max-minutes-per-day 5 --max-independent-pam-days 20
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg --require-pyshacl
PYTHONPATH=src python3 -m cskg_pipeline.run_competency_queries
PYTHONPATH=src python3 -m cskg_pipeline.build_manuscript_assets
PYTHONPATH=src python3 -m cskg_pipeline.build_top_tier_readiness
```

## Quick Verification Without Raw Data

The bundle includes compact outputs, so the KG and manuscript-facing checks can be inspected directly:

```bash
python3 -m compileall src
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg --require-pyshacl
PYTHONPATH=src python3 -m cskg_pipeline.run_competency_queries
PYTHONPATH=src python3 -m cskg_pipeline.build_manuscript_assets
```

Expected reference status:

- pilot KG triples: `9324`
- pySHACL conforms: `true`
- failed local checks: `0`
- failed policy checks: `0`
- competency queries: `9`
- manuscript asset outputs: `14`

## Key Result Files

- `docs/manuscript/manuscript_tables.md`
- `docs/manuscript/table1_cohort_construction.csv`
- `docs/manuscript/table3_protocol_outcome_sensitivity.csv`
- `docs/manuscript/table5_harmonisation_compatibility.csv`
- `docs/manuscript/table7_competency_questions.csv`
- `reports/activity_definition_comparison_summary.json`
- `reports/pilot_kg_summary.json`
- `reports/pilot_kg_shacl_validation_summary.json`
- `reports/competency_question_results.json`
- `data/processed/pilot_kg.ttl`

## Claim Boundaries

Allowed:

- self-reported NHANES cancer history cohort;
- qualified NCIt mappings from reviewed self-reported source codes;
- protocol sensitivity and definition-discordance results;
- broad construct-level comparison of movement summaries;
- KG validation, provenance, and query behavior.

Not allowed:

- registry-confirmed cancer survivorship claims;
- clinical diagnosis, stage, recurrence, treatment, or severity claims;
- converting wrist MIMS into steps, hip counts, MVPA, sedentary time, or clinical activity status;
- treating different accelerometry definitions as interchangeable without source-specific validation.

