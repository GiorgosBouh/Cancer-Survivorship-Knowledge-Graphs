# Reproduce the Paper Results

This file gives the expected rebuild order. Commands assume the repository root as the working directory.

## 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 2. Place Raw Data

Download public source files as described in `DATA_SOURCES.md`. Raw files are not included in Git.

## 3. Build the Main NHANES 2011-2014 Cohort

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_cohort
PYTHONPATH=src python3 -m cskg_pipeline.validate_paxday_paxmin
```

## 4. Build Semantic Mappings and Review Artifacts

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_code_mappings
PYTHONPATH=src python3 -m cskg_pipeline.build_ncit_mapping
PYTHONPATH=src python3 -m cskg_pipeline.import_ncit_expert_review
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_review
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_citations
```

## 5. Build Protocol and Harmonisation Analyses

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_protocol_outcome_sensitivity
PYTHONPATH=src python3 -m cskg_pipeline.build_synthetic_harmonisation
PYTHONPATH=src python3 -m cskg_pipeline.build_activity_definition_comparison
```

## 6. Build Real-Source and Independent-Source Analyses

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_real_source_selection
PYTHONPATH=src python3 -m cskg_pipeline.build_real_source_overlap
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_actisteps
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_semantic_evaluation
PYTHONPATH=src python3 -m cskg_pipeline.build_independent_nhanes_pam
```

## 7. Build and Validate the Pilot KG

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_pilot_kg --participants 20 --max-days 3 --max-minutes-per-day 5 --max-independent-pam-days 20
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg --require-pyshacl
PYTHONPATH=src python3 -m cskg_pipeline.run_competency_queries
```

## 8. Build Manuscript and Reviewer Artifacts

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_manuscript_assets
PYTHONPATH=src python3 -m cskg_pipeline.build_top_tier_readiness
PYTHONPATH=src python3 -m cskg_pipeline.build_reviewer_app_data
```

## 9. Reference Checks

The reference bundle was checked with:

```bash
python3 -m compileall src
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg --require-pyshacl
PYTHONPATH=src python3 -m cskg_pipeline.run_competency_queries
PYTHONPATH=src python3 -m cskg_pipeline.build_manuscript_assets
```

