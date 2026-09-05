"""Evaluate semantic compatibility of PhysioNet ActiLife steps with NHANES MIMS."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs" / "evaluation"


def build_variable_map() -> pd.DataFrame:
    rows = [
        {
            "source_id": "nhanes_2011_2014_wrist_mims",
            "source_table": "pam_days.csv",
            "source_variable": "PAXMTSD",
            "source_label": "Daily total MIMS",
            "source_device_location": "wrist",
            "source_unit": "MIMS",
            "harmonised_construct": "daily movement volume",
            "compatibility_status": "source-specific metric; not directly convertible",
            "harmonisation_action": "Preserve as wrist MIMS and align at construct level only.",
            "interpretation_limit": "Do not convert MIMS to steps, MVPA, sedentary time, or activity counts.",
        },
        {
            "source_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
            "source_table": "physionet_actisteps_daily_summary.csv",
            "source_variable": "daily_total_actilife_steps",
            "source_label": "Daily total ActiLife steps",
            "source_device_location": "wrist",
            "source_unit": "step",
            "harmonised_construct": "daily movement volume",
            "compatibility_status": "source-specific metric; not directly convertible",
            "harmonisation_action": "Preserve as real derived step-count metric and align at construct level only.",
            "interpretation_limit": "Do not treat ActiLife steps as MIMS, MVPA, sedentary time, or clinical physical-activity classification.",
        },
    ]
    return pd.DataFrame(rows)


def build_outputs() -> dict[str, Any]:
    pam_days = pd.read_csv(PROCESSED / "pam_days.csv")
    steps = pd.read_csv(PROCESSED / "physionet_actisteps_daily_summary.csv")
    pam_days["SEQN"] = pam_days["SEQN"].astype(float).astype(int)
    steps["SEQN"] = steps["SEQN"].astype(int)

    merged = pam_days[
        ["SEQN", "cycle", "PAXDAYD", "PAXMTSD", "PAXWWMD", "PAXVMD"]
    ].merge(
        steps[
            [
                "SEQN",
                "cycle",
                "measurement_day",
                "daily_total_actilife_steps",
                "nonmissing_step_minutes",
                "positive_step_minutes",
            ]
        ],
        left_on=["SEQN", "cycle", "PAXDAYD"],
        right_on=["SEQN", "cycle", "measurement_day"],
        how="inner",
    )
    merged = merged.rename(columns={"PAXDAYD": "measurement_day_project"})
    merged["naive_comparison_status"] = "same broad construct only; numeric values not equivalent"
    merged["kg_guarded_decision"] = "allow construct-level comparison; block MIMS-to-steps conversion"
    merged["interpretation_limit"] = (
        "Daily MIMS and ActiLife steps are both movement-volume summaries, but "
        "they are source-specific metrics and are not numerically interchangeable."
    )

    variable_map = build_variable_map()
    risk_register = pd.DataFrame(
        [
            {
                "risk_id": "real_source_mims_vs_actilife_steps",
                "risk_type": "real_source_construct_pair",
                "harmonised_construct": "daily movement volume",
                "left_source": "nhanes_2011_2014_wrist_mims",
                "left_variable": "PAXMTSD",
                "left_unit": "MIMS",
                "right_source": "physionet_nhanes_steps_activity_counts_v1_0_2",
                "right_variable": "daily_total_actilife_steps",
                "right_unit": "step",
                "naive_harmonisation_risk": "naive movement-volume matching could imply MIMS-to-steps numeric comparability",
                "kg_guarded_decision": "block numeric equivalence; preserve source-specific metrics",
                "risk_level": "high",
                "interpretation_limit": "ActiLife steps and MIMS are real but different source-specific metrics.",
            }
        ]
    )

    participant = (
        merged.groupby(["SEQN", "cycle"], as_index=False)
        .agg(
            paired_days=("measurement_day", "nunique"),
            mean_daily_mims=("PAXMTSD", "mean"),
            mean_daily_actilife_steps=("daily_total_actilife_steps", "mean"),
            mean_nonmissing_step_minutes=("nonmissing_step_minutes", "mean"),
            mean_positive_step_minutes=("positive_step_minutes", "mean"),
        )
    )

    pearson = float(merged["PAXMTSD"].corr(merged["daily_total_actilife_steps"], method="pearson"))
    spearman = float(merged["PAXMTSD"].corr(merged["daily_total_actilife_steps"], method="spearman"))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    paired_path = PROCESSED / "physionet_actisteps_mims_paired_daily.csv"
    participant_path = PROCESSED / "physionet_actisteps_mims_participant_comparison.csv"
    map_path = PROCESSED / "physionet_real_source_harmonisation_map.csv"
    risk_path = PROCESSED / "physionet_real_source_semantic_risk_register.csv"
    merged.to_csv(paired_path, index=False)
    participant.to_csv(participant_path, index=False)
    variable_map.to_csv(map_path, index=False)
    risk_register.to_csv(risk_path, index=False)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
        "paired_daily_rows": int(merged.shape[0]),
        "paired_participants": int(participant["SEQN"].nunique()),
        "pearson_mims_steps": round(pearson, 6),
        "spearman_mims_steps": round(spearman, 6),
        "semantic_risk_rows": int(risk_register.shape[0]),
        "high_semantic_risk_rows": int(risk_register["risk_level"].eq("high").sum()),
        "interpretation_limit": (
            "Correlation between MIMS and ActiLife steps may be descriptively "
            "reported, but it does not establish numeric conversion, MVPA, "
            "sedentary classification, or clinical physical-activity status."
        ),
        "outputs": {
            "paired_daily": str(paired_path.relative_to(ROOT)),
            "participant_comparison": str(participant_path.relative_to(ROOT)),
            "real_source_harmonisation_map": str(map_path.relative_to(ROOT)),
            "real_source_semantic_risk_register": str(risk_path.relative_to(ROOT)),
            "documentation": "docs/evaluation/physionet_real_source_semantic_evaluation.md",
        },
    }
    write_document(summary, risk_register)
    (REPORTS / "physionet_semantic_evaluation_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.itertuples(index=False):
        values = [str(value).replace("|", "/") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_document(summary: dict[str, Any], risk_register: pd.DataFrame) -> None:
    lines = [
        "# PhysioNet Real Source Semantic Evaluation",
        "",
        "**Purpose:** repeat the naive-vs-semantic harmonisation logic with a real non-synthetic derived step-count source.",
        "",
        "## Summary",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Paired daily rows | {summary['paired_daily_rows']} |",
        f"| Paired participants | {summary['paired_participants']} |",
        f"| Pearson correlation, MIMS vs ActiLife steps | {summary['pearson_mims_steps']} |",
        f"| Spearman correlation, MIMS vs ActiLife steps | {summary['spearman_mims_steps']} |",
        f"| High semantic risk rows | {summary['high_semantic_risk_rows']} |",
        "",
        "## Semantic Risk Register",
        "",
    ]
    lines.extend(markdown_table(risk_register))
    lines.extend(
        [
            "",
            "## Interpretation Limit",
            "",
            summary["interpretation_limit"],
            "",
            "## Main Meaning",
            "",
            "The project now has a real derived step-count source linked to the same cohort. The KG-compatible interpretation is construct-level alignment under daily movement volume, while explicitly blocking numeric equivalence between MIMS and steps.",
        ]
    )
    (DOCS / "physionet_real_source_semantic_evaluation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
