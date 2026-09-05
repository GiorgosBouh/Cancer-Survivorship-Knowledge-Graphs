"""Build citation/provenance evidence for valid-day protocols.

The citation layer records source-variable evidence, literature context, and
local review decisions separately. It does not upgrade completeness rules into
MVPA, sedentary, active/inactive, or clinical physical-activity definitions.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs" / "protocols"

NHANES_PAXMIN_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXMIN_G.htm"
NHANES_PAXMIN_H = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/PAXMIN_H.htm"
CDC_CATALOG = "https://www.cdc.gov/pcd/issues/2012/11_0332.htm"
PHYSIONET_NHANES = "https://physionet.org/content/minute-level-step-count-nhanes/1.0.0/"

FIELDNAMES = [
    "citation_id",
    "protocol_id",
    "citation_role",
    "source_type",
    "title",
    "citation_text",
    "source_url",
    "cited_claim",
    "supports_protocol_component",
    "support_level",
    "evidence_status",
    "compatibility_warning",
    "interpretation_limit",
]


def row(
    citation_id: str,
    protocol_id: str,
    citation_role: str,
    source_type: str,
    title: str,
    citation_text: str,
    source_url: str,
    cited_claim: str,
    supports_protocol_component: str,
    support_level: str,
    evidence_status: str,
    compatibility_warning: str,
    interpretation_limit: str,
) -> dict[str, str]:
    return {
        "citation_id": citation_id,
        "protocol_id": protocol_id,
        "citation_role": citation_role,
        "source_type": source_type,
        "title": title,
        "citation_text": citation_text,
        "source_url": source_url,
        "cited_claim": cited_claim,
        "supports_protocol_component": supports_protocol_component,
        "support_level": support_level,
        "evidence_status": evidence_status,
        "compatibility_warning": compatibility_warning,
        "interpretation_limit": interpretation_limit,
    }


def source_variable_rows(protocol_id: str, expression: str, metric: str) -> list[dict[str, str]]:
    variable = "PAXWWMD" if "PAXWWMD" in expression else "PAXVMD"
    if variable == "PAXWWMD":
        claim = "NHANES day summary variable PAXWWMD represents valid wake wear minutes in the day."
        component = "source variable PAXWWMD"
    else:
        claim = "NHANES day summary variable PAXVMD represents total valid minutes in the day."
        component = "source variable PAXVMD"
    return [
        row(
            f"{protocol_id}_nhanes_2011_2012_{variable.lower()}",
            protocol_id,
            "source_variable_definition",
            "official_data_documentation",
            "NHANES 2011-2012 Physical Activity Monitor documentation",
            "National Center for Health Statistics. NHANES 2011-2012 Physical Activity Monitor documentation and codebook.",
            NHANES_PAXMIN_G,
            claim,
            component,
            "direct_source_variable_support",
            "ready",
            "Supports the source variable meaning only; does not validate the threshold as a clinical or activity-intensity definition.",
            f"Use {variable} only as a {metric} completeness input in this project.",
        ),
        row(
            f"{protocol_id}_nhanes_2013_2014_{variable.lower()}",
            protocol_id,
            "source_variable_definition",
            "official_data_documentation",
            "NHANES 2013-2014 Physical Activity Monitor documentation",
            "National Center for Health Statistics. NHANES 2013-2014 Physical Activity Monitor documentation and codebook.",
            NHANES_PAXMIN_H,
            claim.replace("NHANES day", "NHANES day"),
            component,
            "direct_source_variable_support",
            "ready",
            "Supports the source variable meaning only; does not validate the threshold as a clinical or activity-intensity definition.",
            f"Use {variable} only as a {metric} completeness input in this project.",
        ),
    ]


def literature_context_row(protocol_id: str) -> dict[str, str]:
    if protocol_id == "wake_wear_10h_min4":
        return row(
            "wake_wear_10h_min4_cdc_catalog_context",
            protocol_id,
            "literature_context",
            "review_article",
            "Catalog of NHANES accelerometer rules, variables, and definitions",
            "Tudor-Locke C, Camhi SM, Troiano RP. A Catalog of Rules, Variables, and Definitions Applied to Accelerometer Data in NHANES, 2003-2006. Preventing Chronic Disease. 2012;9:110332.",
            CDC_CATALOG,
            "The review reports that 10 or more hours of wear time and four or more valid days were commonly used in NHANES 2003-2006 accelerometer analyses.",
            "10h/day and min4-days context",
            "context_only_not_wrist_mims_validation",
            "ready",
            "This source concerns earlier hip-worn activity-count NHANES accelerometry and does not validate wrist MIMS thresholds.",
            "Use only to justify why 10h/min4 is a reasonable sensitivity/completeness candidate to represent and test.",
        )
    if protocol_id == "wake_wear_12h_min4":
        return row(
            "wake_wear_12h_min4_cdc_catalog_context",
            protocol_id,
            "literature_context",
            "review_article",
            "Catalog of NHANES accelerometer rules, variables, and definitions",
            "Tudor-Locke C, Camhi SM, Troiano RP. A Catalog of Rules, Variables, and Definitions Applied to Accelerometer Data in NHANES, 2003-2006. Preventing Chronic Disease. 2012;9:110332.",
            CDC_CATALOG,
            "The review discusses that stricter wear-time requirements such as 12 hours can affect sample size and activity distributions.",
            "12h/day sensitivity context",
            "context_only_not_wrist_mims_validation",
            "ready",
            "This source provides sensitivity-analysis context, not a universal standard for NHANES wrist MIMS or cancer survivorship.",
            "Use only as rationale for retaining a stricter sensitivity rule.",
        )
    if protocol_id == "valid_minutes_20h_min4":
        return row(
            "valid_minutes_20h_min4_physionet_context",
            protocol_id,
            "literature_context",
            "derived_dataset_documentation",
            "Minute-level step counts and physical activity data from NHANES 2011-2014",
            "Karas M, et al. Minute-level step counts and physical activity data from NHANES 2011-2014. PhysioNet.",
            PHYSIONET_NHANES,
            "The derived dataset documentation summarizes NHANES 2011-2014 wrist accelerometry as non-dominant wrist GT3X+ data with MIMS, wear predictions, and quality flags.",
            "24-hour wrist accelerometry context",
            "context_only_not_threshold_validation",
            "ready",
            "This source supports source context, not the 20-hour threshold as a clinical rule.",
            "Use only as context for representing a 24-hour completeness sensitivity rule.",
        )
    raise ValueError(f"Unsupported protocol: {protocol_id}")


def review_decision_row(protocol: Any, review_row: dict[str, str]) -> dict[str, str]:
    status = review_row.get("approved_status") or "approved_as_project_completeness_rule"
    return row(
        f"{protocol.protocol_id}_project_review_decision",
        protocol.protocol_id,
        "project_review_decision",
        "local_review_artifact",
        "Project protocol review sheet",
        "Cancer Survivorship Knowledge Graphs project. Protocol review sheet generated by build_protocol_review.py.",
        "docs/protocols/protocol_review_sheet.csv",
        f"Protocol status: {status}. Reviewer comment: {review_row.get('reviewer_comment', '')}",
        "project approval status",
        "local_project_review_support",
        "ready",
        "Local review approval is limited to completeness/sensitivity analysis and is not external clinical validation.",
        "Do not interpret as MVPA, sedentary, active/inactive, or clinical physical-activity classification.",
    )


def build_rows() -> list[dict[str, str]]:
    protocols = pd.read_csv(PROCESSED / "protocol_definitions.csv")
    review = pd.read_csv(DOCS / "protocol_review_sheet.csv", dtype=str).fillna("")
    review_by_protocol = {str(r.protocol_id): r._asdict() for r in review.itertuples(index=False)}

    rows: list[dict[str, str]] = []
    for protocol in protocols.itertuples(index=False):
        rows.extend(source_variable_rows(protocol.protocol_id, protocol.valid_day_expression, protocol.metric))
        rows.append(literature_context_row(protocol.protocol_id))
        rows.append(review_decision_row(protocol, review_by_protocol.get(str(protocol.protocol_id), {})))
    return rows


def write_markdown(rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    lines = [
        "# Protocol Citation Evidence",
        "",
        "**Purpose:** record citation-level provenance for valid-day completeness/sensitivity protocols.",
        "",
        "This layer separates source-variable evidence, literature context, and local review decisions. It does not convert completeness rules into MVPA, sedentary, active/inactive, or clinical physical-activity definitions.",
        "",
        "## Generated Artifacts",
        "",
        "| Artifact | Role |",
        "|---|---|",
        "| `docs/protocols/protocol_citation_evidence.csv` | Machine-readable citation evidence rows |",
        "| `reports/protocol_citation_summary.json` | Citation summary report |",
        "| `docs/protocols/protocol_citations.md` | Human-readable citation summary |",
        "",
        "## Summary",
        "",
        f"- Protocols covered: {summary['protocol_count']}",
        f"- Citation evidence rows: {summary['citation_rows']}",
        "",
        "## Evidence Roles",
        "",
        "| Role | Rows |",
        "|---|---:|",
    ]
    for role, count in summary["citation_role_counts"].items():
        lines.append(f"| {role} | {count} |")
    lines.extend([
        "",
        "## Protocol Evidence",
        "",
        "| Protocol | Role | Support level | Source | Interpretation limit |",
        "|---|---|---|---|---|",
    ])
    for item in rows:
        lines.append(
            f"| `{item['protocol_id']}` | {item['citation_role']} | {item['support_level']} | {item['title']} | {item['interpretation_limit']} |"
        )
    lines.extend([
        "",
        "## Guardrail",
        "",
        "Citation support is intentionally scoped. Official NHANES documentation supports the meaning of source variables such as `PAXWWMD` and `PAXVMD`; literature-context rows support why these candidate completeness thresholds are worth representing and testing. None of these rows validates wrist MIMS MVPA or sedentary classification.",
    ])
    (DOCS / "protocol_citations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(rows: list[dict[str, str]]) -> dict[str, Any]:
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    csv_path = DOCS / "protocol_citation_evidence.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    role_counts = Counter(row["citation_role"] for row in rows)
    support_counts = Counter(row["support_level"] for row in rows)
    protocols = sorted({row["protocol_id"] for row in rows})
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "citation_evidence": str(csv_path.relative_to(ROOT)),
        "documentation": "docs/protocols/protocol_citations.md",
        "protocol_count": len(protocols),
        "protocols": protocols,
        "citation_rows": len(rows),
        "citation_role_counts": dict(sorted(role_counts.items())),
        "support_level_counts": dict(sorted(support_counts.items())),
        "policy": "Citation evidence supports source variables, literature context, and local review status only; no MVPA/sedentary/classification claim is approved for NHANES wrist MIMS.",
    }
    (REPORTS / "protocol_citation_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(rows, payload)
    return payload


def main() -> None:
    print(json.dumps(write_outputs(build_rows()), indent=2))


if __name__ == "__main__":
    main()
