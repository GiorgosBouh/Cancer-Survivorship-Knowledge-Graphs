"""Build review artifacts for candidate valid-day protocols."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs" / "protocols"

FIELDNAMES = [
    "protocol_id",
    "label",
    "valid_day_expression",
    "min_valid_days",
    "metric",
    "unit",
    "observed_participants",
    "eligible_participants",
    "eligibility_percent",
    "classification_type",
    "current_status",
    "recommended_review_decision",
    "evidence_basis",
    "primary_source_url",
    "supporting_source_url",
    "compatibility_warning",
    "review_question",
    "review_decision",
    "approved_label",
    "approved_expression",
    "approved_min_valid_days",
    "approved_status",
    "reviewer_comment",
    "reviewer_name",
    "review_date",
]

SOURCE_NHANES_PAXMIN = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXMIN_G.htm"
SOURCE_NHANES_PAXHR = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXHR_G.htm"
SOURCE_CDC_CATALOG = "https://www.cdc.gov/pcd/issues/2012/11_0332.htm"
SOURCE_CHOI = "https://pubmed.ncbi.nlm.nih.gov/20581716/"
SOURCE_WEAR_12H = "https://pubmed.ncbi.nlm.nih.gov/22936409/"


def protocol_result_counts(results: pd.DataFrame) -> dict[str, dict[str, float]]:
    out = {}
    for protocol_id, group in results.groupby("protocol_id"):
        observed = len(group)
        eligible = int(group["eligible_under_protocol"].sum())
        out[protocol_id] = {
            "observed_participants": observed,
            "eligible_participants": eligible,
            "eligibility_percent": round(100 * eligible / observed, 2) if observed else 0.0,
        }
    return out


def evidence_for(protocol_id: str) -> dict[str, str]:
    if protocol_id == "wake_wear_10h_min4":
        return {
            "classification_type": "candidate completeness rule",
            "current_status": "implemented_candidate_needs_review",
            "recommended_review_decision": "keep_as_candidate_until_expert_review",
            "evidence_basis": "10-hour valid-day thresholds and four-day inclusion rules are common in accelerometer studies, but this implementation uses NHANES wrist/PAM PAXWWMD valid wake-wear minutes and is not an MVPA or sedentary classification.",
            "primary_source_url": SOURCE_NHANES_PAXMIN,
            "supporting_source_url": SOURCE_CDC_CATALOG,
            "compatibility_warning": "Uses NHANES wrist/PAM valid wake-wear minutes; do not interpret as hip-count MVPA/sedentary threshold.",
            "review_question": "Is PAXWWMD >= 600 on at least 4 days acceptable as a baseline completeness/sensitivity rule for this cancer survivorship KG?",
        }
    if protocol_id == "wake_wear_12h_min4":
        return {
            "classification_type": "sensitivity completeness rule",
            "current_status": "implemented_candidate_needs_review",
            "recommended_review_decision": "keep_as_sensitivity_rule_until_expert_review",
            "evidence_basis": "A stricter 12-hour day threshold can be useful for sensitivity analysis because shorter wear criteria may affect physical activity estimates; this is not a universal standard and needs explicit justification.",
            "primary_source_url": SOURCE_NHANES_PAXMIN,
            "supporting_source_url": SOURCE_WEAR_12H,
            "compatibility_warning": "Sensitivity rule only; not a clinical physical-activity definition and not validated as a cancer-specific threshold.",
            "review_question": "Should PAXWWMD >= 720 on at least 4 days remain as a stricter sensitivity rule, or should it be removed/replaced?",
        }
    if protocol_id == "valid_minutes_20h_min4":
        return {
            "classification_type": "24-hour completeness rule",
            "current_status": "implemented_candidate_needs_review",
            "recommended_review_decision": "keep_as_candidate_24h_completeness_rule_until_review",
            "evidence_basis": "NHANES provides PAXVMD total valid minutes in the day and status-specific valid minute variables whose sum equals PAXVMD; the 20-hour threshold is a candidate 24-hour completeness rule and requires study-specific justification.",
            "primary_source_url": SOURCE_NHANES_PAXMIN,
            "supporting_source_url": SOURCE_NHANES_PAXHR,
            "compatibility_warning": "Completeness rule only; not an activity-intensity or cancer survivorship clinical threshold.",
            "review_question": "Is PAXVMD >= 1200 on at least 4 days a defensible 24-hour completeness rule for this KG, or should another threshold be used?",
        }
    raise ValueError(f"Unknown protocol: {protocol_id}")


def build_rows() -> list[dict[str, object]]:
    protocols = pd.read_csv(PROCESSED / "protocol_definitions.csv")
    results = pd.read_csv(PROCESSED / "valid_day_protocol_results.csv")
    counts = protocol_result_counts(results)
    rows: list[dict[str, object]] = []
    for row in protocols.itertuples(index=False):
        ev = evidence_for(row.protocol_id)
        cnt = counts.get(row.protocol_id, {})
        rows.append(
            {
                "protocol_id": row.protocol_id,
                "label": row.label,
                "valid_day_expression": row.valid_day_expression,
                "min_valid_days": row.min_valid_days,
                "metric": row.metric,
                "unit": row.unit,
                "observed_participants": cnt.get("observed_participants", 0),
                "eligible_participants": cnt.get("eligible_participants", 0),
                "eligibility_percent": cnt.get("eligibility_percent", 0),
                **ev,
                "review_decision": "",
                "approved_label": "",
                "approved_expression": "",
                "approved_min_valid_days": "",
                "approved_status": "",
                "reviewer_comment": "",
                "reviewer_name": "",
                "review_date": "",
            }
        )
    return rows


def write_outputs(rows: list[dict[str, object]]) -> dict[str, object]:
    DOCS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    csv_path = DOCS / "protocol_review_sheet.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(str(row["current_status"]) for row in rows)
    type_counts = Counter(str(row["classification_type"]) for row in rows)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_sheet": str(csv_path.relative_to(ROOT)),
        "protocol_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "classification_type_counts": dict(sorted(type_counts.items())),
        "review_status": "pending_protocol_expert_review",
        "policy": "Treat all protocols as candidate completeness/sensitivity rules; do not claim MVPA or sedentary classification.",
    }
    (REPORTS / "protocol_review_status.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    print(json.dumps(write_outputs(build_rows()), indent=2))


if __name__ == "__main__":
    main()
