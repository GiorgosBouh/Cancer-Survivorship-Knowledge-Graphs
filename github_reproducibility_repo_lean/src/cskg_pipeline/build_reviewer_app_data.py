"""Build static data payload for the reviewer-facing GitHub Pages app."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
APP_DIR = DOCS / "reviewer_app"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    return json.loads(frame.fillna("").to_json(orient="records"))


def compact_competency(results: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    labels = {
        "cq1_protocol_discordance.rq": "Protocol discordance",
        "cq2_protocol_review_status.rq": "Protocol review status",
        "cq3_pending_cancer_type_mappings.rq": "NCIt pending mappings",
        "cq4_daily_feature_provenance.rq": "Daily feature provenance",
        "cq5_minute_measurement_context.rq": "Minute context",
        "cq6_self_reported_cancer_history.rq": "Self-reported cancer history",
        "cq7_harmonisation_compatibility.rq": "Harmonisation compatibility",
        "cq8_protocol_citation_provenance.rq": "Protocol citation provenance",
        "cq9_independent_pam_source_validation.rq": "Independent PAM validation",
    }
    for result in results.get("results", []):
        query_name = Path(result.get("query", "")).name
        out.append(
            {
                "id": query_name.replace(".rq", "").upper(),
                "name": labels.get(query_name, query_name),
                "query": result.get("query"),
                "rowCount": result.get("row_count", 0),
                "variables": result.get("variables", []),
                "sampleRows": result.get("sample_rows", []),
            }
        )
    return out


def combined_harmonisation() -> list[dict[str, Any]]:
    rows = read_csv_records(PROCESSED / "harmonisation_source_variable_map.csv")
    independent = read_csv_records(PROCESSED / "independent_nhanes_pam_semantic_map.csv")
    for row in independent:
        row.setdefault("source_table", "independent_nhanes_pam_daily_summary.csv")
        row.setdefault("source_device_location", "hip")
        row.setdefault("harmonised_property", "source-specific property")
        row.setdefault("protocol_role", "source metric")
        row.setdefault("harmonisation_action", "retain source-specific metric and block numeric equivalence")
    return rows + independent


def source_cards(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    independent = payloads.get("independent_pam", {})
    physionet = payloads.get("physionet_actisteps", {})
    pilot = payloads.get("pilot_kg", {})
    return [
        {
            "id": "nhanes_2011_2014_wrist_mims",
            "name": "Main data: wrist movement score",
            "role": "Main KG use case",
            "independence": "primary cohort",
            "device": "wrist accelerometry",
            "metric": "wrist movement score (MIMS)",
            "participants": 1035,
            "kgNodes": pilot.get("days"),
            "allowed": "Source-specific movement summaries and protocol sensitivity analysis.",
            "blocked": "No hip-count thresholds, MVPA, sedentary, active/inactive, or clinical PA status.",
        },
        {
            "id": "physionet_nhanes_steps_activity_counts_v1_0_2",
            "name": "Same people: steps estimate",
            "role": "Real same-cohort derived metric source",
            "independence": "same NHANES 2011-2014 participants/raw source",
            "device": "derived from same NHANES wrist accelerometry source",
            "metric": "steps estimate",
            "participants": physionet.get("participants_with_actilife_steps"),
            "kgNodes": "CSV/report-level semantic evaluation",
            "allowed": "Descriptive MIMS-step correlation and broad movement-volume grouping.",
            "blocked": "No MIMS-to-steps conversion or intensity classification.",
        },
        {
            "id": "nhanes_2003_2006_hip_actigraph_pam",
            "name": "Independent data: hip activity tracker",
            "role": "Independent public accelerometry validation source",
            "independence": "different participants, cycles, placement, metric family",
            "device": "hip-worn ActiGraph AM-7164",
            "metric": "hip tracker counts; steps in 2005-2006",
            "participants": independent.get("participants_with_paxraw_total"),
            "kgNodes": pilot.get("independent_pam_daily_summaries"),
            "allowed": "Independent cross-device semantic validation under broad constructs.",
            "blocked": "No identity linkage to 2011-2014 participants and no conversion to wrist MIMS/MVPA/sedentary.",
        },
    ]


def build_payload() -> dict[str, Any]:
    payloads = {
        "pilot_kg": read_json(REPORTS / "pilot_kg_summary.json"),
        "validation": read_json(REPORTS / "pilot_kg_shacl_validation_summary.json"),
        "top_tier": read_json(REPORTS / "top_tier_readiness_summary.json"),
        "independent_pam": read_json(REPORTS / "independent_nhanes_pam_summary.json"),
        "physionet_actisteps": read_json(REPORTS / "physionet_actisteps_summary.json"),
        "physionet_semantic": read_json(REPORTS / "physionet_semantic_evaluation_summary.json"),
        "domain_review": read_json(REPORTS / "domain_ontology_review_status.json"),
        "ncit_review": read_json(REPORTS / "ncit_mapping_review_status.json"),
        "definition_comparison": read_json(REPORTS / "activity_definition_comparison_summary.json"),
    }
    competency = compact_competency(read_json(REPORTS / "competency_question_results.json"))
    harmonisation = combined_harmonisation()
    return {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "projectTitle": "Accelerometry Definition Comparison",
        "sources": source_cards(payloads),
        "definitionComparison": {
            "summary": payloads["definition_comparison"],
            "rules": read_csv_records(PROCESSED / "activity_definition_rules.csv"),
            "comparisons": read_csv_records(PROCESSED / "activity_definition_protocol_comparison.csv"),
            "participants": read_csv_records(PROCESSED / "activity_definition_participant_classification.csv"),
        },
        "harmonisation": harmonisation,
        "competencyQueries": competency,
        "readiness": read_csv_records(PROCESSED / "top_tier_readiness_checklist.csv"),
        "datasetCandidates": read_csv_records(PROCESSED / "top_tier_dataset_candidates.csv"),
        "riskRegisters": {
            "semantic": read_csv_records(PROCESSED / "semantic_harmonisation_risk_register.csv"),
            "protocol": read_csv_records(PROCESSED / "protocol_discordance_risk_register.csv"),
            "independentPam": read_csv_records(PROCESSED / "independent_nhanes_pam_semantic_risk_register.csv"),
            "physionet": read_csv_records(PROCESSED / "physionet_real_source_semantic_risk_register.csv"),
        },
        "summaries": payloads,
        "clinicianScenarios": [
            {
                "question": "Two studies both say activity is low. Can I treat them as the same?",
                "shortAnswer": "No. You can compare the idea, not the numbers.",
                "whatItMeans": "One study may use a wrist movement score. Another may use steps. They both describe movement, but they are not the same measurement.",
                "allowed": "Say both suggest lower movement.",
                "blocked": "Do not say the numbers mean the same thing.",
                "clinicalUse": "Useful when reading papers that used different activity trackers.",
                "status": "qualified"
            },
            {
                "question": "Can I call someone sedentary from this wrist activity score?",
                "shortAnswer": "No.",
                "whatItMeans": "This project has movement scores. It does not have a validated rule that turns those scores into sedentary time.",
                "allowed": "Say the wrist movement score is lower or higher.",
                "blocked": "Do not call the person sedentary, inactive, or guideline-adherent from this score alone.",
                "clinicalUse": "Prevents a number from becoming an unsupported clinical label.",
                "status": "blocked"
            },
            {
                "question": "Can I mix wrist scores with hip tracker counts in one analysis?",
                "shortAnswer": "No, not as one numeric outcome.",
                "whatItMeans": "Wrist and hip trackers count movement differently. They can support the same broad story, but they should not be pooled as the same variable.",
                "allowed": "Use them side by side and state that the devices differ.",
                "blocked": "Do not average or convert wrist scores and hip counts as if they are the same.",
                "clinicalUse": "Useful for reviews or studies that combine evidence from older and newer trackers.",
                "status": "qualified"
            },
            {
                "question": "I am planning a study. What must I write down?",
                "shortAnswer": "Write down how activity was measured and what claim you want to make.",
                "whatItMeans": "The tracker, where it is worn, the activity number, and the valid-day rule all affect what can be concluded later.",
                "allowed": "Record device, wrist/hip placement, activity metric, valid-day rule, and allowed clinical claim.",
                "blocked": "Do not decide later that a movement score means MVPA or sedentary time unless that rule is validated.",
                "clinicalUse": "Helps design a study that other clinicians can interpret safely.",
                "status": "supported"
            }
        ],
        "claims": [
            {
                "claim": "Second independent public accelerometry source is integrated.",
                "status": "supported",
                "evidence": "NHANES 2003-2006 PAM: 768 participants with PAM records; 20 KG summary nodes; CQ9 returns 20 rows.",
                "limit": "Not an independent clinical cancer-survivorship cohort.",
            },
            {
                "claim": "MIMS and ActiLife steps can be compared descriptively.",
                "status": "qualified",
                "evidence": "PhysioNet same-cohort paired daily evaluation exists.",
                "limit": "Correlation does not imply conversion, MVPA, sedentary, or clinical status.",
            },
            {
                "claim": "Reviewed NCIt cancer-type mappings are asserted.",
                "status": "qualified",
                "evidence": "Completed cancer-code expert review imported; validation guard allows qualified NCIt mapping assertions.",
                "limit": "Treat NCIt IRIs as reviewed mappings from self-reported NHANES source codes, not confirmed diagnoses or histology.",
            },
            {
                "claim": "External domain/ontology review is complete.",
                "status": "pending",
                "evidence": "Review packet prepared.",
                "limit": "Do not claim external expert approval yet.",
            },
        ],
        "artifacts": [
            {"label": "Pilot KG Turtle", "path": "../../data/processed/pilot_kg.ttl"},
            {"label": "Activity definition comparison", "path": "../activity_definition_comparison.md"},
            {"label": "Top-tier submission plan", "path": "../top_tier_submission_plan.md"},
            {"label": "Paper package", "path": "../paper_package.md"},
            {"label": "Domain/ontology review sheet", "path": "../review/domain_ontology_review_sheet.csv"},
            {"label": "Reproducibility archive plan", "path": "../reproducibility_archive_plan.md"},
            {"label": "Reporting checklists", "path": "../reporting_checklists.md"},
        ],
    }


def write_app_data(payload: dict[str, Any]) -> dict[str, Any]:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data_path = APP_DIR / "data.js"
    json_text = json.dumps(payload, indent=2).replace("</", "<\\/")
    data_path.write_text(f"window.CSKG_APP_DATA = {json_text};\n", encoding="utf-8")
    return {
        "created_at_utc": payload["generatedAtUtc"],
        "app_data": str(data_path.relative_to(ROOT)),
        "sources": len(payload["sources"]),
        "harmonisation_rows": len(payload["harmonisation"]),
        "competency_queries": len(payload["competencyQueries"]),
        "readiness_rows": len(payload["readiness"]),
    }


def main() -> None:
    summary = write_app_data(build_payload())
    (REPORTS / "reviewer_app_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
