"""Build manuscript-ready tables and figure data from pipeline artifacts.

This package layer is deliberately downstream of the reviewed/generated CSV and
JSON artifacts. It does not create new scientific claims, assert NCIt mappings,
or reinterpret wrist MIMS as MVPA/sedentary classification.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
MANUSCRIPT = DOCS / "manuscript"

INTERPRETATION_LIMIT = (
    "MIMS values are movement-summary metrics only; no MVPA, sedentary, "
    "active/inactive, or clinical physical activity classification is made."
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def short_name(value: object) -> str:
    text = str(value)
    if "/" in text:
        return text.rsplit("/", 1)[-1]
    return text


def fmt(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.itertuples(index=False):
        values = [fmt(value).replace("|", "/") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_table(name: str, frame: pd.DataFrame) -> str:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    path = MANUSCRIPT / f"{name}.csv"
    frame.to_csv(path, index=False)
    return str(path.relative_to(ROOT))


def build_table1_cohort() -> pd.DataFrame:
    cohort = pd.read_csv(PROCESSED / "cohort_flow.csv")
    stage_labels = {
        "all_nhanes_participants": "All NHANES participants",
        "age_20_or_older": "Age 20 or older",
        "mcq220_cancer_history": "Self-reported cancer history, MCQ220 = 1",
        "available_paxhd": "Physical activity monitor header available",
        "available_paxday": "Daily physical activity monitor summary available",
        "available_paxmin": "Minute-level physical activity monitor data available",
    }
    order = list(stage_labels)
    frame = cohort[cohort["stage"].isin(order)].copy()
    frame["stage_order"] = frame["stage"].map({stage: index for index, stage in enumerate(order)})
    frame["Stage"] = frame["stage"].map(stage_labels)
    pivot = (
        frame.pivot_table(index=["stage_order", "Stage"], columns="cycle", values="n", aggfunc="sum")
        .reset_index()
        .sort_values("stage_order")
    )
    for column in ["2011-2012", "2013-2014", "total"]:
        if column not in pivot.columns:
            pivot[column] = 0
    pivot = pivot.rename(
        columns={
            "2011-2012": "NHANES 2011-2012",
            "2013-2014": "NHANES 2013-2014",
            "total": "Total",
        }
    )
    return pivot[["Stage", "NHANES 2011-2012", "NHANES 2013-2014", "Total"]]


def build_table2_protocols() -> pd.DataFrame:
    protocols = pd.read_csv(PROCESSED / "protocol_definitions.csv")
    review = pd.read_csv(DOCS / "protocols" / "protocol_review_sheet.csv", dtype=str).fillna("")
    merged = protocols.merge(review, on="protocol_id", how="left", suffixes=("", "_review"))
    frame = pd.DataFrame(
        {
            "Protocol": merged["protocol_id"],
            "Definition": merged["label"],
            "Expression": merged["valid_day_expression"],
            "Minimum valid days": merged["min_valid_days"],
            "Review status": merged.get("approved_status", ""),
            "Classification type": merged.get("classification_type", ""),
            "Interpretation limit": merged.get(
                "interpretation_limit",
                "Completeness/sensitivity rule only; not an activity classification.",
            ),
        }
    )
    return frame


def build_table3_protocol_sensitivity() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = pd.read_csv(PROCESSED / "protocol_outcome_sensitivity_summary.csv")
    table = summary[
        [
            "protocol_id",
            "eligible_participants",
            "eligible_percent",
            "valid_day_rows",
            "participant_mean_daily_mims_mean",
            "participant_mean_peak30_valid_mims_mean",
            "interpretation_limit",
        ]
    ].copy()
    table = table.rename(
        columns={
            "protocol_id": "Protocol",
            "eligible_participants": "Eligible participants",
            "eligible_percent": "Eligible %",
            "valid_day_rows": "Valid day rows",
            "participant_mean_daily_mims_mean": "Mean participant daily MIMS",
            "participant_mean_peak30_valid_mims_mean": "Mean participant peak-30 valid MIMS",
            "interpretation_limit": "Interpretation limit",
        }
    )

    pairwise = pd.read_csv(PROCESSED / "protocol_pairwise_inclusion_comparison.csv")
    pairwise_table = pairwise.rename(
        columns={
            "left_protocol": "Left protocol",
            "right_protocol": "Right protocol",
            "both_eligible": "Both eligible",
            "left_only": "Left only",
            "right_only": "Right only",
            "neither": "Neither",
            "discordant_participants": "Discordant participants",
        }
    )
    return table, pairwise_table


def load_combined_harmonisation_map() -> pd.DataFrame:
    base = pd.read_csv(PROCESSED / "harmonisation_source_variable_map.csv")
    independent_path = PROCESSED / "independent_nhanes_pam_semantic_map.csv"
    if not independent_path.exists():
        return base
    independent = pd.read_csv(independent_path)
    for column, default in {
        "source_table": "independent_nhanes_pam_daily_summary.csv",
        "source_device_location": "hip",
        "harmonised_property": "source-specific property",
        "protocol_role": "source metric",
        "harmonisation_action": "retain source-specific metric and block numeric equivalence",
    }.items():
        if column not in independent.columns:
            independent[column] = default
    for column in base.columns:
        if column not in independent.columns:
            independent[column] = ""
    return pd.concat([base, independent[base.columns]], ignore_index=True)


def build_table4_kg_validation() -> pd.DataFrame:
    kg = read_json(REPORTS / "pilot_kg_summary.json")
    validation = read_json(REPORTS / "pilot_kg_shacl_validation_summary.json")
    harmonisation = load_combined_harmonisation_map()
    ncit_guard = next(
        (item for item in validation.get("policy_checks", []) if item.get("guard") == "NCItReviewPendingGuard"),
        {},
    )
    rows = [
        {"Measure": "Participants", "Value": kg.get("participants")},
        {"Measure": "Cancer diagnoses", "Value": kg.get("diagnoses")},
        {"Measure": "Cancer history assertions", "Value": kg.get("cancer_history_assertions")},
        {"Measure": "Daily movement summaries", "Value": kg.get("days")},
        {"Measure": "Minute observations", "Value": kg.get("minute_observations")},
        {"Measure": "Derived feature sets", "Value": kg.get("feature_sets")},
        {"Measure": "Processing protocols", "Value": kg.get("protocols")},
        {"Measure": "Protocol application results", "Value": kg.get("protocol_results")},
        {"Measure": "Protocol citation evidence nodes", "Value": kg.get("protocol_citation_rows_loaded")},
        {"Measure": "Activity data sources", "Value": int(harmonisation["source_id"].nunique())},
        {"Measure": "Harmonisation source-variable mappings", "Value": int(len(harmonisation))},
        {"Measure": "Independent PAM daily summaries", "Value": kg.get("independent_pam_daily_summaries")},
        {"Measure": "Harmonised activity definitions", "Value": kg.get("harmonised_activity_definitions_loaded")},
        {"Measure": "Synthetic daily activity summaries", "Value": kg.get("synthetic_daily_activity_summaries")},
        {"Measure": "RDF triples", "Value": kg.get("triples")},
        {"Measure": "pySHACL conforms", "Value": validation.get("standard_shacl", {}).get("conforms")},
        {"Measure": "Validation failed checks", "Value": validation.get("failed_checks")},
        {"Measure": "Failed policy checks", "Value": validation.get("failed_policy_checks")},
        {"Measure": "NCIt review status", "Value": ncit_guard.get("status")},
        {"Measure": "NCIt assertion count while pending", "Value": ncit_guard.get("assertion_count")},
    ]
    return pd.DataFrame(rows)


def build_table5_harmonisation() -> tuple[pd.DataFrame, pd.DataFrame]:
    mapping = load_combined_harmonisation_map()
    table = mapping[
        [
            "source_id",
            "source_variable",
            "source_label",
            "source_device_location",
            "source_unit",
            "harmonised_construct",
            "compatibility_status",
            "interpretation_limit",
        ]
    ].copy()
    table = table.rename(
        columns={
            "source_id": "Source",
            "source_variable": "Variable",
            "source_label": "Label",
            "source_device_location": "Device location",
            "source_unit": "Unit",
            "harmonised_construct": "Harmonised construct",
            "compatibility_status": "Compatibility status",
            "interpretation_limit": "Interpretation limit",
        }
    )
    counts = (
        mapping.groupby(["source_id", "compatibility_status"], as_index=False)
        .size()
        .rename(
            columns={
                "source_id": "Source",
                "compatibility_status": "Compatibility status",
                "size": "Rows",
            }
        )
    )
    return table, counts


def build_table6_citations() -> tuple[pd.DataFrame, pd.DataFrame]:
    citations = pd.read_csv(DOCS / "protocols" / "protocol_citation_evidence.csv")
    table = citations[
        [
            "protocol_id",
            "citation_role",
            "support_level",
            "title",
            "supports_protocol_component",
            "interpretation_limit",
        ]
    ].copy()
    table = table.rename(
        columns={
            "protocol_id": "Protocol",
            "citation_role": "Evidence role",
            "support_level": "Support level",
            "title": "Source title",
            "supports_protocol_component": "Supported component",
            "interpretation_limit": "Interpretation limit",
        }
    )
    counts = (
        citations.groupby(["citation_role", "support_level"], as_index=False)
        .size()
        .rename(columns={"citation_role": "Evidence role", "support_level": "Support level", "size": "Rows"})
    )
    return table, counts


def build_table7_competency() -> pd.DataFrame:
    results = read_json(REPORTS / "competency_question_results.json")
    risk_labels = {
        "cq1_protocol_discordance.rq": "Protocol choice changes inclusion",
        "cq2_protocol_review_status.rq": "Protocols are reviewed completeness/sensitivity rules",
        "cq3_pending_cancer_type_mappings.rq": "NCIt candidates are not overasserted",
        "cq4_daily_feature_provenance.rq": "Movement features expose provenance",
        "cq5_minute_measurement_context.rq": "MIMS/wear-state/quality context is queryable",
        "cq6_self_reported_cancer_history.rq": "Cohort is not overclaimed as clinically verified survivorship",
        "cq7_harmonisation_compatibility.rq": "Compatibility and incompatibility are queryable",
        "cq8_protocol_citation_provenance.rq": "Protocol evidence and support levels are queryable",
        "cq9_independent_pam_source_validation.rq": "Independent PAM source evidence and non-conversion limits are queryable",
    }
    rows = []
    for result in results.get("results", []):
        query_name = Path(result["query"]).name
        rows.append(
            {
                "Query": query_name.replace(".rq", "").upper(),
                "Rows returned": result["row_count"],
                "Reviewer risk addressed": risk_labels.get(query_name, ""),
                "Source query": result["query"],
            }
        )
    return pd.DataFrame(rows)


def build_figure1_pipeline_counts(table1: pd.DataFrame) -> pd.DataFrame:
    return table1.rename(columns={"Stage": "Pipeline stage"})


def build_figure2_harmonisation_counts(harmonisation_counts: pd.DataFrame) -> pd.DataFrame:
    return harmonisation_counts.copy()


def build_figure3_protocol_sensitivity(table3: pd.DataFrame) -> pd.DataFrame:
    return table3[
        [
            "Protocol",
            "Eligible participants",
            "Eligible %",
            "Valid day rows",
            "Mean participant daily MIMS",
        ]
    ].copy()


def write_markdown_document(tables: dict[str, pd.DataFrame], outputs: dict[str, str], summary: dict[str, Any]) -> None:
    lines = [
        "# Manuscript Tables and Figure Data",
        "",
        "**Purpose:** deterministic manuscript/proposal assets generated from the current pipeline outputs.",
        "",
        "These tables are downstream summaries. Reviewed NCIt mappings are qualified self-reported source-code mappings only; the tables do not reinterpret wrist MIMS as MVPA, sedentary, active/inactive, or clinical physical-activity classification.",
        "",
        "## Generated Artifacts",
        "",
        "| Artifact | Role |",
        "|---|---|",
    ]
    for label, path in outputs.items():
        lines.append(f"| `{path}` | {label} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            INTERPRETATION_LIMIT,
            "",
            f"NCIt review status: `{summary['ncit_review_status']}`; qualified NCIt assertion count: `{summary['ncit_assertion_count']}`.",
            "",
        ]
    )

    section_titles = {
        "table1_cohort_construction": "Table 1. Cohort Construction",
        "table2_protocol_definitions": "Table 2. Protocol Definitions and Interpretation Limits",
        "table3_protocol_outcome_sensitivity": "Table 3. Protocol Outcome Sensitivity",
        "table3_pairwise_protocol_discordance": "Table 3b. Pairwise Protocol Discordance",
        "table4_kg_validation": "Table 4. Pilot KG Summary and Validation",
        "table5_harmonisation_compatibility": "Table 5. Harmonisation Compatibility",
        "table5_harmonisation_status_counts": "Table 5b. Harmonisation Compatibility Counts",
        "table6_protocol_citation_evidence": "Table 6. Protocol Citation Evidence",
        "table6_protocol_citation_counts": "Table 6b. Protocol Citation Evidence Counts",
        "table7_competency_questions": "Table 7. Competency Questions",
        "figure1_pipeline_counts": "Figure Data 1. Pipeline Counts",
        "figure2_harmonisation_status_counts": "Figure Data 2. Harmonisation Status Counts",
        "figure3_protocol_sensitivity": "Figure Data 3. Protocol Sensitivity",
    }
    for key, frame in tables.items():
        lines.extend(["", f"## {section_titles[key]}", ""])
        lines.extend(markdown_table(frame))

    lines.extend(
        [
            "",
            "## Recommended Use",
            "",
            "- Use the CSV files for manuscript tables, plotting, and supervisor review.",
            "- Use `figure*_*.csv` as plotting inputs for the three figure concepts in `docs/paper_package.md`.",
            "- Keep reviewed NCIt mappings qualified as source-code mappings, not confirmed disease or histology assertions.",
        ]
    )
    (MANUSCRIPT / "manuscript_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_outputs() -> dict[str, Any]:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    table1 = build_table1_cohort()
    table2 = build_table2_protocols()
    table3, table3_pairwise = build_table3_protocol_sensitivity()
    table4 = build_table4_kg_validation()
    table5, table5_counts = build_table5_harmonisation()
    table6, table6_counts = build_table6_citations()
    table7 = build_table7_competency()
    figure1 = build_figure1_pipeline_counts(table1)
    figure2 = build_figure2_harmonisation_counts(table5_counts)
    figure3 = build_figure3_protocol_sensitivity(table3)

    tables = {
        "table1_cohort_construction": table1,
        "table2_protocol_definitions": table2,
        "table3_protocol_outcome_sensitivity": table3,
        "table3_pairwise_protocol_discordance": table3_pairwise,
        "table4_kg_validation": table4,
        "table5_harmonisation_compatibility": table5,
        "table5_harmonisation_status_counts": table5_counts,
        "table6_protocol_citation_evidence": table6,
        "table6_protocol_citation_counts": table6_counts,
        "table7_competency_questions": table7,
        "figure1_pipeline_counts": figure1,
        "figure2_harmonisation_status_counts": figure2,
        "figure3_protocol_sensitivity": figure3,
    }

    outputs: dict[str, str] = {}
    for key, frame in tables.items():
        label = "Figure data" if key.startswith("figure") else "Manuscript table"
        outputs[f"{label}: {key}"] = write_table(key, frame)
    outputs["Human-readable manuscript table package"] = str((MANUSCRIPT / "manuscript_tables.md").relative_to(ROOT))

    validation = read_json(REPORTS / "pilot_kg_shacl_validation_summary.json")
    ncit_guard = next(
        (item for item in validation.get("policy_checks", []) if item.get("guard") == "NCItReviewPendingGuard"),
        {},
    )
    compatibility_counts = Counter(table5["Compatibility status"])
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "documentation": outputs["Human-readable manuscript table package"],
        "output_count": len(outputs),
        "outputs": outputs,
        "tables": {
            key: {
                "path": outputs[("Figure data: " if key.startswith("figure") else "Manuscript table: ") + key],
                "rows": int(frame.shape[0]),
                "columns": int(frame.shape[1]),
            }
            for key, frame in tables.items()
        },
        "claim_boundary": INTERPRETATION_LIMIT,
        "pyshacl_conforms": validation.get("standard_shacl", {}).get("conforms"),
        "failed_checks": validation.get("failed_checks"),
        "failed_policy_checks": validation.get("failed_policy_checks"),
        "ncit_review_status": ncit_guard.get("status"),
        "ncit_assertion_count": ncit_guard.get("assertion_count"),
        "harmonisation_compatibility_counts": dict(compatibility_counts),
    }
    write_markdown_document(tables, outputs, summary)
    report_path = REPORTS / "manuscript_assets_summary.json"
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
