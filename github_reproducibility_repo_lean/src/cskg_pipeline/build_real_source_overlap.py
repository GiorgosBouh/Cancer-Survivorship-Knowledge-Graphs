"""Check overlap between selected PhysioNet accelerometry source and cohort."""

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
RAW_SOURCE = ROOT / "data" / "raw" / "physionet-minute-level-step-count-nhanes-1.0.2"


def cycle_from_release(value: object) -> str:
    text = str(value)
    if text in {"7", "7.0"}:
        return "2011-2012"
    if text in {"8", "8.0"}:
        return "2013-2014"
    return ""


def build_outputs() -> dict[str, Any]:
    participants = pd.read_csv(PROCESSED / "participants.csv", usecols=["SEQN", "cycle", "MCQ220"])
    physionet = pd.read_csv(RAW_SOURCE / "subject-info.csv")

    participants["SEQN"] = participants["SEQN"].astype(float).astype(int)
    participants["cycle"] = participants["cycle"].astype(str)
    physionet["SEQN"] = physionet["SEQN"].astype(int)
    physionet["cycle"] = physionet["data_release_cycle"].map(cycle_from_release)

    merged = participants.merge(
        physionet,
        on=["SEQN", "cycle"],
        how="left",
        indicator=True,
        suffixes=("_project", "_physionet"),
    )
    merged["present_in_physionet"] = merged["_merge"].eq("both")

    by_cycle = (
        merged.groupby("cycle", as_index=False)
        .agg(
            project_cancer_history_participants=("SEQN", "nunique"),
            present_in_physionet=("present_in_physionet", "sum"),
        )
        .sort_values("cycle")
    )
    by_cycle["overlap_percent"] = (
        100
        * by_cycle["present_in_physionet"]
        / by_cycle["project_cancer_history_participants"]
    ).round(6)

    overlap_rows = merged[
        [
            "SEQN",
            "cycle",
            "present_in_physionet",
            "gender",
            "age_in_years_at_screening",
            "full_sample_2_year_interview_weight",
            "full_sample_2_year_mec_exam_weight",
        ]
    ].copy()
    overlap_rows.to_csv(PROCESSED / "physionet_source_cohort_overlap.csv", index=False)
    by_cycle.to_csv(PROCESSED / "physionet_source_cohort_overlap_by_cycle.csv", index=False)

    missing = merged[~merged["present_in_physionet"]][["SEQN", "cycle"]].copy()
    missing.to_csv(PROCESSED / "physionet_source_missing_project_participants.csv", index=False)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
        "selection_status": "metadata_downloaded_overlap_checked",
        "physionet_subjects_total": int(physionet["SEQN"].nunique()),
        "project_cancer_history_participants": int(participants["SEQN"].nunique()),
        "project_rows": int(participants.shape[0]),
        "project_participants_present_in_physionet": int(merged["present_in_physionet"].sum()),
        "project_participants_missing_from_physionet": int((~merged["present_in_physionet"]).sum()),
        "overall_overlap_percent": round(100 * float(merged["present_in_physionet"].mean()), 6),
        "by_cycle": by_cycle.to_dict(orient="records"),
        "outputs": {
            "participant_overlap": "data/processed/physionet_source_cohort_overlap.csv",
            "overlap_by_cycle": "data/processed/physionet_source_cohort_overlap_by_cycle.csv",
            "missing_project_participants": "data/processed/physionet_source_missing_project_participants.csv",
            "documentation": "docs/physionet_real_source_overlap.md",
        },
        "next_step": (
            "Download one compressed metric file, preferably csv/nhanes_1440_AC.csv.xz "
            "or csv/nhanes_1440_actisteps.csv.xz, and build cohort-restricted daily summaries."
        ),
    }

    write_document(summary, by_cycle)
    (REPORTS / "physionet_source_overlap_summary.json").write_text(
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
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def write_document(summary: dict[str, Any], by_cycle: pd.DataFrame) -> None:
    lines = [
        "# PhysioNet Real Source Cohort Overlap",
        "",
        "**Source:** PhysioNet minute-level step counts and physical activity data from NHANES 2011-2014, version 1.0.2.",
        "",
        "This is the first real non-synthetic source integration check. It uses downloaded PhysioNet metadata only and does not yet process the large activity-count or step-count metric files.",
        "",
        "## Summary",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| PhysioNet subjects | {summary['physionet_subjects_total']} |",
        f"| Project cancer-history participants | {summary['project_cancer_history_participants']} |",
        f"| Present in PhysioNet metadata | {summary['project_participants_present_in_physionet']} |",
        f"| Missing from PhysioNet metadata | {summary['project_participants_missing_from_physionet']} |",
        f"| Overall overlap percent | {summary['overall_overlap_percent']} |",
        "",
        "## By Cycle",
        "",
    ]
    lines.extend(markdown_table(by_cycle))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The selected PhysioNet source can be linked to the existing NHANES cancer-history cohort by `SEQN` and cycle. This supports the next experiment: add a real derived accelerometry metric such as ActiGraph activity counts or step counts and rerun semantic compatibility checks without using the synthetic hip-counts demo as the only contrasting source.",
            "",
            "## Next Step",
            "",
            summary["next_step"],
        ]
    )
    (DOCS / "physionet_real_source_overlap.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
