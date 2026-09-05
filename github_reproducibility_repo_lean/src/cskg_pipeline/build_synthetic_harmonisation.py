"""Build a synthetic contrasting-source harmonisation demonstration.

The output is a review artifact. It creates a deterministic hip-worn
counts/minute source seeded from the NHANES participant-day rows so the project
can demonstrate source-level harmonisation patterns without claiming that wrist
MIMS can be converted into hip counts/minute.
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

SYNTHETIC_SOURCE_ID = "synthetic_hip_counts_demo"
NHANES_SOURCE_ID = "nhanes_2011_2014_wrist_mims"


def _cycle_index(cycle: object) -> int:
    return {"2011-2012": 0, "2013-2014": 1}.get(str(cycle), 2)


def deterministic_offset(seqn: object, cycle: object, day: object, span: int, center: int = 0) -> int:
    seed = int(float(seqn)) * 17 + _cycle_index(cycle) * 31 + int(float(day)) * 13
    return seed % span - center


def bounded(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def build_synthetic_daily(days: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    required = {"SEQN", "cycle", "PAXDAYD", "PAXWWMD", "PAXVMD", "PAXMTSD", "PAXTMD"}
    missing = sorted(required.difference(days.columns))
    if missing:
        raise ValueError(f"pam_days.csv is missing required columns: {missing}")

    for row in days.itertuples(index=False):
        wear_offset = deterministic_offset(row.SEQN, row.cycle, row.PAXDAYD, span=91, center=45)
        cpm_offset = deterministic_offset(row.SEQN, row.cycle, row.PAXDAYD, span=301, center=150)
        valid_wear_minutes = int(round(bounded(float(row.PAXWWMD) + wear_offset, 0, float(row.PAXTMD))))
        denominator = max(float(row.PAXWWMD), 1.0)
        mean_cpm = bounded((float(row.PAXMTSD) / denominator) * 80.0 + cpm_offset, 0.0, 8000.0)
        daily_counts = int(round(mean_cpm * valid_wear_minutes))
        mvpa_minutes = int(round(bounded((mean_cpm - 1200.0) / 18.0, 0.0, valid_wear_minutes)))
        sedentary_minutes = int(round(bounded(valid_wear_minutes * (0.68 - min(mean_cpm, 4000.0) / 10000.0), 0.0, valid_wear_minutes)))

        rows.append(
            {
                "source_id": SYNTHETIC_SOURCE_ID,
                "synthetic_participant_id": f"SYN-{row.cycle}-{int(float(row.SEQN))}",
                "seed_nhanes_cycle": row.cycle,
                "seed_nhanes_seqn": int(float(row.SEQN)),
                "measurement_day": int(float(row.PAXDAYD)),
                "device_location": "hip",
                "device_type": "synthetic ActiGraph-style accelerometer",
                "epoch_length_seconds": 60,
                "movement_metric": "vertical_axis_counts_per_minute",
                "valid_wear_minutes": valid_wear_minutes,
                "daily_total_vertical_axis_counts": daily_counts,
                "mean_vertical_axis_counts_per_minute": round(mean_cpm, 6),
                "mvpa_minutes_1952_cpm": mvpa_minutes,
                "sedentary_minutes_100_cpm": sedentary_minutes,
                "valid_day_10h": valid_wear_minutes >= 600,
                "synthetic_generation_note": (
                    "Deterministic synthetic source for semantic harmonisation testing only; "
                    "not measured hip accelerometry and not a conversion from wrist MIMS."
                ),
            }
        )
    return pd.DataFrame(rows)


def build_variable_map() -> pd.DataFrame:
    rows = [
        {
            "source_id": NHANES_SOURCE_ID,
            "source_table": "pam_days.csv",
            "source_variable": "PAXMTSD",
            "source_label": "Daily total MIMS",
            "source_device_location": "wrist",
            "source_unit": "MIMS",
            "harmonised_construct": "daily movement volume",
            "harmonised_property": "cskg:dailyTotalMIMS",
            "protocol_role": "movement summary",
            "compatibility_status": "source-specific metric; not directly convertible",
            "harmonisation_action": "Preserve as wrist MIMS and align at construct level only.",
            "interpretation_limit": "Do not apply hip counts/minute intensity thresholds to MIMS.",
        },
        {
            "source_id": NHANES_SOURCE_ID,
            "source_table": "pam_days.csv",
            "source_variable": "PAXWWMD",
            "source_label": "Valid wake wear minutes",
            "source_device_location": "wrist",
            "source_unit": "minute",
            "harmonised_construct": "valid wear completeness",
            "harmonised_property": "cskg:wakeWearMinutes",
            "protocol_role": "valid-day eligibility",
            "compatibility_status": "compatible after protocol abstraction",
            "harmonisation_action": "Represent as source-specific valid wear input to a reviewed completeness protocol.",
            "interpretation_limit": "Completeness rule only; not an activity classification.",
        },
        {
            "source_id": NHANES_SOURCE_ID,
            "source_table": "pam_days.csv",
            "source_variable": "PAXVMD",
            "source_label": "Valid minutes",
            "source_device_location": "wrist",
            "source_unit": "minute",
            "harmonised_construct": "valid data completeness",
            "harmonised_property": "cskg:validMinutes",
            "protocol_role": "valid-day eligibility",
            "compatibility_status": "compatible after protocol abstraction",
            "harmonisation_action": "Represent as total valid monitored minutes.",
            "interpretation_limit": "Does not encode intensity.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "source_table": "synthetic_contrasting_daily_activity.csv",
            "source_variable": "daily_total_vertical_axis_counts",
            "source_label": "Daily total vertical-axis counts",
            "source_device_location": "hip",
            "source_unit": "count",
            "harmonised_construct": "daily movement volume",
            "harmonised_property": "cskg:dailyTotalAxisCounts",
            "protocol_role": "movement summary",
            "compatibility_status": "source-specific metric; not directly convertible",
            "harmonisation_action": "Preserve as hip counts and align at construct level only.",
            "interpretation_limit": "Not comparable as a numeric equivalent of MIMS.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "source_table": "synthetic_contrasting_daily_activity.csv",
            "source_variable": "valid_wear_minutes",
            "source_label": "Valid wear minutes",
            "source_device_location": "hip",
            "source_unit": "minute",
            "harmonised_construct": "valid wear completeness",
            "harmonised_property": "cskg:validWearMinutes",
            "protocol_role": "valid-day eligibility",
            "compatibility_status": "compatible after protocol abstraction",
            "harmonisation_action": "Represent as source-specific valid wear input to a reviewed completeness protocol.",
            "interpretation_limit": "Completeness rule only; not an activity classification.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "source_table": "synthetic_contrasting_daily_activity.csv",
            "source_variable": "mvpa_minutes_1952_cpm",
            "source_label": "MVPA minutes by 1952 counts/minute cut point",
            "source_device_location": "hip",
            "source_unit": "minute",
            "harmonised_construct": "source-defined activity intensity",
            "harmonised_property": "cskg:sourceDefinedMVPAMinutes",
            "protocol_role": "intensity classification",
            "compatibility_status": "not harmonisable with NHANES wrist MIMS in current KG",
            "harmonisation_action": "Represent as source-specific classification and do not back-map to wrist MIMS.",
            "interpretation_limit": "Requires hip counts/minute protocol context.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "source_table": "synthetic_contrasting_daily_activity.csv",
            "source_variable": "sedentary_minutes_100_cpm",
            "source_label": "Sedentary minutes by 100 counts/minute cut point",
            "source_device_location": "hip",
            "source_unit": "minute",
            "harmonised_construct": "source-defined sedentary classification",
            "harmonised_property": "cskg:sourceDefinedSedentaryMinutes",
            "protocol_role": "intensity classification",
            "compatibility_status": "not harmonisable with NHANES wrist MIMS in current KG",
            "harmonisation_action": "Represent as source-specific classification and do not back-map to wrist MIMS.",
            "interpretation_limit": "Requires hip counts/minute protocol context.",
        },
    ]
    return pd.DataFrame(rows)


def build_definition_rows() -> pd.DataFrame:
    rows = [
        {
            "source_id": NHANES_SOURCE_ID,
            "definition_id": "nhanes_wrist_mims_wake_wear_10h_min4",
            "label": "NHANES wrist MIMS wake-wear completeness rule",
            "expression": "PAXWWMD >= 600 on at least 4 monitor days",
            "device_location": "wrist",
            "movement_metric": "MIMS",
            "threshold": "600 wake-wear minutes; 4 days",
            "definition_type": "valid-day completeness",
            "harmonisation_status": "compatible after protocol abstraction",
            "interpretation_limit": "No MVPA, sedentary, or clinical activity classification.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "definition_id": "synthetic_hip_counts_wear_10h_min4",
            "label": "Synthetic hip counts wear-time completeness rule",
            "expression": "valid_wear_minutes >= 600 on at least 4 monitor days",
            "device_location": "hip",
            "movement_metric": "vertical-axis counts/minute",
            "threshold": "600 valid wear minutes; 4 days",
            "definition_type": "valid-day completeness",
            "harmonisation_status": "compatible after protocol abstraction",
            "interpretation_limit": "Completeness rule only; synthetic source.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "definition_id": "synthetic_hip_counts_mvpa_1952_cpm",
            "label": "Synthetic hip counts MVPA cut point",
            "expression": "vertical_axis_counts_per_minute >= 1952",
            "device_location": "hip",
            "movement_metric": "vertical-axis counts/minute",
            "threshold": "1952 counts/minute",
            "definition_type": "activity-intensity classification",
            "harmonisation_status": "not harmonisable with NHANES wrist MIMS in current KG",
            "interpretation_limit": "Do not apply to wrist MIMS.",
        },
        {
            "source_id": SYNTHETIC_SOURCE_ID,
            "definition_id": "synthetic_hip_counts_sedentary_100_cpm",
            "label": "Synthetic hip counts sedentary cut point",
            "expression": "vertical_axis_counts_per_minute < 100",
            "device_location": "hip",
            "movement_metric": "vertical-axis counts/minute",
            "threshold": "100 counts/minute",
            "definition_type": "activity-intensity classification",
            "harmonisation_status": "not harmonisable with NHANES wrist MIMS in current KG",
            "interpretation_limit": "Do not apply to wrist MIMS.",
        },
    ]
    return pd.DataFrame(rows)


def build_protocol_results(synthetic_daily: pd.DataFrame) -> pd.DataFrame:
    grouped = synthetic_daily.groupby(["seed_nhanes_seqn", "seed_nhanes_cycle"], as_index=False).agg(
        observed_days=("measurement_day", "nunique"),
        valid_days=("valid_day_10h", "sum"),
        total_valid_wear_minutes=("valid_wear_minutes", "sum"),
        total_vertical_axis_counts=("daily_total_vertical_axis_counts", "sum"),
        mean_daily_vertical_axis_counts=("daily_total_vertical_axis_counts", "mean"),
        mean_daily_mvpa_minutes_1952_cpm=("mvpa_minutes_1952_cpm", "mean"),
        mean_daily_sedentary_minutes_100_cpm=("sedentary_minutes_100_cpm", "mean"),
    )
    grouped["source_id"] = SYNTHETIC_SOURCE_ID
    grouped["protocol_id"] = "synthetic_hip_counts_wear_10h_min4"
    grouped["min_valid_days"] = 4
    grouped["eligible_under_protocol"] = grouped["valid_days"] >= grouped["min_valid_days"]
    grouped = grouped.rename(columns={"seed_nhanes_seqn": "SEQN", "seed_nhanes_cycle": "cycle"})
    ordered = [
        "source_id",
        "protocol_id",
        "SEQN",
        "cycle",
        "observed_days",
        "valid_days",
        "min_valid_days",
        "eligible_under_protocol",
        "total_valid_wear_minutes",
        "total_vertical_axis_counts",
        "mean_daily_vertical_axis_counts",
        "mean_daily_mvpa_minutes_1952_cpm",
        "mean_daily_sedentary_minutes_100_cpm",
    ]
    return grouped[ordered].sort_values(["cycle", "SEQN"])


def build_pairwise_comparison(synthetic_results: pd.DataFrame, nhanes_results: pd.DataFrame) -> pd.DataFrame:
    nhanes = nhanes_results[nhanes_results["protocol_id"].eq("wake_wear_10h_min4")][
        ["SEQN", "cycle", "eligible_under_protocol", "valid_days", "observed_days"]
    ].rename(
        columns={
            "eligible_under_protocol": "nhanes_wrist_wake_wear_10h_min4_eligible",
            "valid_days": "nhanes_valid_days",
            "observed_days": "nhanes_observed_days",
        }
    )
    synthetic = synthetic_results[
        ["SEQN", "cycle", "eligible_under_protocol", "valid_days", "observed_days"]
    ].rename(
        columns={
            "eligible_under_protocol": "synthetic_hip_wear_10h_min4_eligible",
            "valid_days": "synthetic_valid_days",
            "observed_days": "synthetic_observed_days",
        }
    )
    comparison = nhanes.merge(synthetic, on=["SEQN", "cycle"], how="inner")
    comparison["eligibility_agreement"] = (
        comparison["nhanes_wrist_wake_wear_10h_min4_eligible"].astype(bool)
        == comparison["synthetic_hip_wear_10h_min4_eligible"].astype(bool)
    )
    comparison["comparison_limit"] = (
        "Seed-linked synthetic comparison for harmonisation testing only; not cross-device measurement validation."
    )
    return comparison.sort_values(["cycle", "SEQN"])


def write_doc(report: dict[str, Any], compatibility_counts: Counter[str]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Synthetic Contrasting-Source Harmonisation Demo",
        "",
        "**Purpose:** demonstrate semantic harmonisation across two accelerometry source patterns without overclaiming numeric equivalence.",
        "",
        "This is a synthetic review artifact. The hip counts/minute source is deterministically generated from NHANES participant-day rows only to exercise the mapping and protocol-comparison layer. It is not measured hip accelerometry, and it is not a conversion from wrist MIMS.",
        "",
        "## Generated Artifacts",
        "",
        "| Artifact | Role |",
        "|---|---|",
        "| `data/processed/synthetic_contrasting_daily_activity.csv` | Synthetic hip-counts participant-day source |",
        "| `data/processed/synthetic_harmonisation_protocol_results.csv` | Synthetic source valid-day protocol results |",
        "| `data/processed/harmonisation_source_variable_map.csv` | Source variable to harmonised construct bridge |",
        "| `data/processed/harmonised_activity_definitions.csv` | Source-specific protocol and cut-point definitions |",
        "| `data/processed/source_harmonisation_pairwise_comparison.csv` | Seed-linked NHANES versus synthetic completeness comparison |",
        "| `reports/synthetic_harmonisation_summary.json` | Machine-readable summary |",
        "",
        "## Current Counts",
        "",
        f"- Synthetic participant-day rows: {report['synthetic_daily_rows']}",
        f"- Synthetic participants: {report['synthetic_participants']}",
        f"- Source variable mappings: {report['variable_mapping_rows']}",
        f"- Activity/protocol definitions: {report['definition_rows']}",
        f"- Pairwise completeness comparison rows: {report['pairwise_comparison_rows']}",
        "",
        "## Compatibility Summary",
        "",
        "| Compatibility status | Rows |",
        "|---|---:|",
    ]
    for status, count in sorted(compatibility_counts.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation Rules",
            "",
            "- Valid-day completeness can be harmonised at the protocol abstraction level when source-specific inputs are preserved.",
            "- Wrist MIMS and hip counts/minute remain source-specific movement summaries, not interchangeable numeric units.",
            "- Hip counts/minute MVPA and sedentary cut points are represented only as source-defined classifications.",
            "- No MVPA, sedentary, active/inactive, or clinical physical-activity classification is inferred for NHANES wrist MIMS.",
        ]
    )
    (DOCS / "semantic_harmonisation_demo.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_outputs() -> dict[str, Any]:
    days = pd.read_csv(PROCESSED / "pam_days.csv")
    nhanes_protocol_results = pd.read_csv(PROCESSED / "valid_day_protocol_results.csv")

    synthetic_daily = build_synthetic_daily(days)
    variable_map = build_variable_map()
    definitions = build_definition_rows()
    synthetic_results = build_protocol_results(synthetic_daily)
    pairwise = build_pairwise_comparison(synthetic_results, nhanes_protocol_results)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    synthetic_daily_path = PROCESSED / "synthetic_contrasting_daily_activity.csv"
    synthetic_results_path = PROCESSED / "synthetic_harmonisation_protocol_results.csv"
    variable_map_path = PROCESSED / "harmonisation_source_variable_map.csv"
    definitions_path = PROCESSED / "harmonised_activity_definitions.csv"
    pairwise_path = PROCESSED / "source_harmonisation_pairwise_comparison.csv"

    synthetic_daily.to_csv(synthetic_daily_path, index=False)
    synthetic_results.to_csv(synthetic_results_path, index=False)
    variable_map.to_csv(variable_map_path, index=False)
    definitions.to_csv(definitions_path, index=False)
    pairwise.to_csv(pairwise_path, index=False)

    compatibility_counts = Counter(variable_map["compatibility_status"])
    pairwise_agreement = int(pairwise["eligibility_agreement"].sum())
    pairwise_disagreement = int((~pairwise["eligibility_agreement"]).sum())
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "synthetic_source_id": SYNTHETIC_SOURCE_ID,
        "nhanes_source_id": NHANES_SOURCE_ID,
        "synthetic_daily": str(synthetic_daily_path.relative_to(ROOT)),
        "synthetic_protocol_results": str(synthetic_results_path.relative_to(ROOT)),
        "source_variable_map": str(variable_map_path.relative_to(ROOT)),
        "activity_definitions": str(definitions_path.relative_to(ROOT)),
        "pairwise_comparison": str(pairwise_path.relative_to(ROOT)),
        "documentation": "docs/semantic_harmonisation_demo.md",
        "synthetic_daily_rows": int(synthetic_daily.shape[0]),
        "synthetic_participants": int(synthetic_daily["synthetic_participant_id"].nunique()),
        "variable_mapping_rows": int(variable_map.shape[0]),
        "definition_rows": int(definitions.shape[0]),
        "pairwise_comparison_rows": int(pairwise.shape[0]),
        "pairwise_eligibility_agreement_rows": pairwise_agreement,
        "pairwise_eligibility_disagreement_rows": pairwise_disagreement,
        "compatibility_counts": dict(sorted(compatibility_counts.items())),
        "interpretation_limit": (
            "Synthetic source is for semantic harmonisation testing only. "
            "MIMS and hip counts/minute are not asserted as convertible or numerically equivalent."
        ),
    }
    report_path = REPORTS / "synthetic_harmonisation_summary.json"
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_doc(payload, compatibility_counts)
    return payload


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
