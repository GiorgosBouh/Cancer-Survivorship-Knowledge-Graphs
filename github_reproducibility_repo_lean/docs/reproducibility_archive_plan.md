# Reproducibility Archive Plan

Purpose: prepare a DOI-ready archive package for the top-tier submission.

## Include

- `src/cskg_pipeline/` pipeline source code.
- `ontology/cskg.ttl` and `shapes/pilot_kg_shapes.ttl`.
- `queries/competency/` SPARQL competency queries.
- Generated non-sensitive processed summaries under `data/processed/`.
- Reports under `reports/`.
- Documentation under `docs/`, including review sheets and interpretation limits.
- `requirements.txt`, `pyproject.toml`, and README instructions.

## Exclude Or Handle Separately

- Large raw NHANES XPT/ZIP files should not be duplicated in the DOI archive if source URLs are stable and licensing/repository norms favor scripted re-download.
- If raw files are excluded, include checksums, source URLs, and exact commands used to rebuild derived artifacts.
- Do not include any private reviewer notes beyond completed review sheets approved for release.

## Rebuild Commands

```bash
PYTHONPATH=src python3 -m cskg_pipeline.build_cohort --include-minutes --minute-chunksize 250000
PYTHONPATH=src python3 -m cskg_pipeline.build_synthetic_harmonisation
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_actisteps
PYTHONPATH=src python3 -m cskg_pipeline.build_physionet_semantic_evaluation
PYTHONPATH=src python3 -m cskg_pipeline.build_independent_nhanes_pam
PYTHONPATH=src python3 -m cskg_pipeline.build_pilot_kg --participants 20 --max-days 3 --max-minutes-per-day 5 --max-independent-pam-days 20
PYTHONPATH=src python3 -m cskg_pipeline.validate_pilot_kg --require-pyshacl
PYTHONPATH=src python3 -m cskg_pipeline.run_competency_queries
PYTHONPATH=src python3 -m cskg_pipeline.build_top_tier_readiness
```

## Archive Status

Prepared, not yet deposited. A Zenodo/OSF DOI is still required before final top-tier submission.
