"""Build cohort-restricted daily summaries from PhysioNet ActiLife steps.

The input is the real non-synthetic PhysioNet NHANES-derived ActiLife step-count
metric. Outputs are daily and participant summaries for the existing project
cohort only; this avoids expanding the full 1440-minute wide source into a
large long table.
"""

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
ACTISTEPS_FILE = RAW_SOURCE / "csv" / "nhanes_1440_actisteps.csv.xz"

SOURCE_ID = "physionet_nhanes_steps_activity_counts_v1_0_2"
METRIC_ID = "actilife_steps"
MINUTE_COLS = [f"min_{index:04d}" for index in range(1, 1441)]


def load_project_participants() -> pd.DataFrame:
    participants = pd.read_csv(PROCESSED / "participants.csv", usecols=["SEQN", "cycle"])
    participants["SEQN"] = participants["SEQN"].astype(float).astype(int)
    participants["cycle"] = participants["cycle"].astype(str)
    return participants.drop_duplicates(["SEQN", "cycle"])


def top_n_sum(values: pd.Series, n: int) -> float:
    clean = values.dropna()
    if clean.empty:
        return 0.0
    return float(clean.nlargest(min(n, clean.shape[0])).sum())


def summarise_chunk(chunk: pd.DataFrame, cohort: pd.DataFrame) -> pd.DataFrame:
    chunk["SEQN"] = chunk["SEQN"].astype(int)
    filtered = chunk[chunk["SEQN"].isin(set(cohort["SEQN"]))].copy()
    if filtered.empty:
        return pd.DataFrame()

    values = filtered[MINUTE_COLS].apply(pd.to_numeric, errors="coerce")
    daily = filtered[["SEQN", "PAXDAYM", "PAXDAYWM"]].copy()
    daily["source_id"] = SOURCE_ID
    daily["metric_id"] = METRIC_ID
    daily["daily_total_actilife_steps"] = values.sum(axis=1, skipna=True).round(6)
    daily["nonmissing_step_minutes"] = values.notna().sum(axis=1).astype(int)
    daily["positive_step_minutes"] = values.gt(0).sum(axis=1).astype(int)
    daily["mean_steps_per_nonmissing_minute"] = values.mean(axis=1, skipna=True).round(6)
    daily["max_steps_per_minute"] = values.max(axis=1, skipna=True).round(6)
    daily["top30_minute_step_sum"] = values.apply(lambda row: top_n_sum(row, 30), axis=1).round(6)
    daily = daily.merge(cohort, on="SEQN", how="left")
    daily = daily.rename(columns={"PAXDAYM": "measurement_day", "PAXDAYWM": "day_of_week_code"})
    daily["interpretation_limit"] = (
        "ActiLife step counts are a real derived step-count metric; do not treat "
        "as MVPA, sedentary, MIMS, or hip-count intensity classification."
    )
    return daily[
        [
            "source_id",
            "metric_id",
            "SEQN",
            "cycle",
            "measurement_day",
            "day_of_week_code",
            "daily_total_actilife_steps",
            "nonmissing_step_minutes",
            "positive_step_minutes",
            "mean_steps_per_nonmissing_minute",
            "max_steps_per_minute",
            "top30_minute_step_sum",
            "interpretation_limit",
        ]
    ]


def build_outputs(chunksize: int = 750) -> dict[str, Any]:
    cohort = load_project_participants()
    daily_frames: list[pd.DataFrame] = []
    rows_scanned = 0
    chunks_scanned = 0

    for chunk in pd.read_csv(ACTISTEPS_FILE, compression="xz", chunksize=chunksize, na_values=["NA"]):
        chunks_scanned += 1
        rows_scanned += int(chunk.shape[0])
        daily = summarise_chunk(chunk, cohort)
        if not daily.empty:
            daily_frames.append(daily)

    if daily_frames:
        daily_summary = pd.concat(daily_frames, ignore_index=True)
    else:
        daily_summary = pd.DataFrame()

    participant_summary = (
        daily_summary.groupby(["SEQN", "cycle"], as_index=False)
        .agg(
            observed_physionet_days=("measurement_day", "nunique"),
            total_actilife_steps=("daily_total_actilife_steps", "sum"),
            mean_daily_actilife_steps=("daily_total_actilife_steps", "mean"),
            median_daily_actilife_steps=("daily_total_actilife_steps", "median"),
            mean_nonmissing_step_minutes=("nonmissing_step_minutes", "mean"),
            mean_positive_step_minutes=("positive_step_minutes", "mean"),
            mean_top30_minute_step_sum=("top30_minute_step_sum", "mean"),
        )
        if not daily_summary.empty
        else pd.DataFrame()
    )

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    daily_path = PROCESSED / "physionet_actisteps_daily_summary.csv"
    participant_path = PROCESSED / "physionet_actisteps_participant_summary.csv"
    daily_summary.to_csv(daily_path, index=False)
    participant_summary.to_csv(participant_path, index=False)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_id": SOURCE_ID,
        "metric_id": METRIC_ID,
        "input": str(ACTISTEPS_FILE.relative_to(ROOT)),
        "rows_scanned": rows_scanned,
        "chunks_scanned": chunks_scanned,
        "project_participants": int(cohort["SEQN"].nunique()),
        "daily_summary_rows": int(daily_summary.shape[0]),
        "participant_summary_rows": int(participant_summary.shape[0]),
        "participants_with_actisteps": int(participant_summary["SEQN"].nunique()) if not participant_summary.empty else 0,
        "mean_daily_actilife_steps_over_participants": round(
            float(participant_summary["mean_daily_actilife_steps"].mean()), 6
        )
        if not participant_summary.empty
        else None,
        "interpretation_limit": (
            "ActiLife step counts are real derived step-count metrics from the "
            "PhysioNet NHANES source. They are not MIMS, MVPA, sedentary, or "
            "clinical physical-activity classifications."
        ),
        "outputs": {
            "daily_summary": str(daily_path.relative_to(ROOT)),
            "participant_summary": str(participant_path.relative_to(ROOT)),
            "documentation": "docs/physionet_actisteps_integration.md",
        },
    }
    write_document(summary)
    (REPORTS / "physionet_actisteps_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def write_document(summary: dict[str, Any]) -> None:
    lines = [
        "# PhysioNet ActiLife Steps Integration",
        "",
        "**Purpose:** integrate one real non-synthetic PhysioNet accelerometry-derived metric for the current cancer-history cohort.",
        "",
        "## Source",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| source_id | {summary['source_id']} |",
        f"| metric_id | {summary['metric_id']} |",
        f"| input | `{summary['input']}` |",
        "",
        "## Generated Outputs",
        "",
        "| Artifact | Role |",
        "|---|---|",
        f"| `{summary['outputs']['daily_summary']}` | Cohort-restricted day-level ActiLife step summaries |",
        f"| `{summary['outputs']['participant_summary']}` | Participant-level ActiLife step summaries |",
        "| `reports/physionet_actisteps_summary.json` | Machine-readable integration summary |",
        "",
        "## Summary",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Rows scanned from source | {summary['rows_scanned']} |",
        f"| Project participants | {summary['project_participants']} |",
        f"| Daily summary rows | {summary['daily_summary_rows']} |",
        f"| Participant summary rows | {summary['participant_summary_rows']} |",
        f"| Participants with ActiLife steps | {summary['participants_with_actisteps']} |",
        f"| Mean daily ActiLife steps over participants | {summary['mean_daily_actilife_steps_over_participants']} |",
        "",
        "## Interpretation Limit",
        "",
        summary["interpretation_limit"],
        "",
        "## Next Step",
        "",
        "Add this real source to the harmonisation source-variable map and rerun the naive-vs-semantic risk evaluation using real ActiLife step counts rather than relying only on the synthetic hip-counts demonstration.",
    ]
    (DOCS / "physionet_actisteps_integration.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
