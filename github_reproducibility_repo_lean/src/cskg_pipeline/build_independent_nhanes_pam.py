"""Build an independent NHANES 2003-2006 PAM accelerometry validation source.

This source is independent from the current NHANES 2011-2014 wrist/MIMS cohort:
different survey cycles, different participants, hip-worn ActiGraph AM-7164, and
1-minute activity-count epochs. It is still NHANES, so the claim is independent
accelerometry source/cohort, not independent health-system cancer survivorship
cohort.
"""

from __future__ import annotations

import json
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
EVALUATION = DOCS / "evaluation"

LOGGER = logging.getLogger(__name__)

CYCLES = {
    "2003-2004": {
        "suffix": "C",
        "pax_zip": RAW / "2003-2004" / "PAXRAW_C.zip",
        "pax_member": "paxraw_c.xpt",
        "pax_xpt": RAW / "2003-2004" / "paxraw_c.xpt",
        "pax_doc": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/PAXRAW_C.htm",
    },
    "2005-2006": {
        "suffix": "D",
        "pax_zip": RAW / "2005-2006" / "PAXRAW_D.zip",
        "pax_member": "paxraw_d.xpt",
        "pax_xpt": RAW / "2005-2006" / "paxraw_d.xpt",
        "pax_doc": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles/PAXRAW_D.htm",
    },
}


def read_xpt(path: Path) -> pd.DataFrame:
    return pd.read_sas(path, format="xport", encoding="latin1")


def extract_paxraw_if_needed(cycle: str, meta: dict[str, Any]) -> dict[str, Any]:
    zip_path = meta["pax_zip"]
    output_path = meta["pax_xpt"]
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing required PAM ZIP for {cycle}: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        info = archive.getinfo(meta["pax_member"])
        if output_path.exists() and output_path.stat().st_size == info.file_size:
            return {
                "cycle": cycle,
                "zip_path": str(zip_path),
                "xpt_path": str(output_path),
                "xpt_size_bytes": output_path.stat().st_size,
                "extracted": False,
            }
        LOGGER.info("Extracting %s to %s", meta["pax_member"], output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, output_path.open("wb") as target:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                target.write(block)

    return {
        "cycle": cycle,
        "zip_path": str(zip_path),
        "xpt_path": str(output_path),
        "xpt_size_bytes": output_path.stat().st_size,
        "extracted": True,
    }


def build_participants() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for cycle, meta in CYCLES.items():
        suffix = meta["suffix"]
        demo = read_xpt(RAW / cycle / f"DEMO_{suffix}.XPT")
        mcq = read_xpt(RAW / cycle / f"MCQ_{suffix}.XPT")
        merged = demo.merge(mcq, on="SEQN", how="inner", suffixes=("", "_mcq"))
        merged["cycle"] = cycle
        if "RIDAGEYR" in merged.columns:
            merged = merged.loc[merged["RIDAGEYR"] >= 20].copy()
        if "MCQ220" in merged.columns:
            merged = merged.loc[merged["MCQ220"] == 1].copy()

        preferred = [
            "SEQN",
            "cycle",
            "RIDAGEYR",
            "RIAGENDR",
            "RIDRETH1",
            "DMDEDUC2",
            "DMDMARTL",
            "INDFMPIR",
            "MCQ220",
        ]
        cancer_columns = [column for column in merged.columns if column.startswith(("MCQ230", "MCQ240"))]
        ordered = [column for column in preferred + cancer_columns if column in merged.columns]
        frames.append(merged[ordered].copy())
    return pd.concat(frames, ignore_index=True).sort_values(["cycle", "SEQN"]).reset_index(drop=True)


def process_paxraw_cycle(
    cycle: str,
    xpt_path: Path,
    participant_seqn: set[float],
    chunksize: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    daily_parts: list[pd.DataFrame] = []
    rows_scanned = 0
    retained_rows = 0
    chunks_scanned = 0
    has_step_column = False

    iterator = pd.read_sas(xpt_path, format="xport", encoding="latin1", chunksize=chunksize)
    for chunk in iterator:
        chunks_scanned += 1
        rows_scanned += len(chunk)
        filtered = chunk.loc[chunk["SEQN"].isin(participant_seqn)].copy()
        if filtered.empty:
            continue
        retained_rows += len(filtered)
        filtered["cycle"] = cycle
        filtered["day_index"] = ((filtered["PAXN"] - 1) // 1440 + 1).astype("Int64")
        filtered["is_reliable"] = filtered["PAXSTAT"] == 1
        filtered["is_in_calibration"] = filtered["PAXCAL"] == 1
        filtered["is_reliable_in_calibration"] = filtered["is_reliable"] & filtered["is_in_calibration"]
        filtered["valid_activity_count"] = filtered["PAXINTEN"].where(filtered["is_reliable_in_calibration"], 0)
        filtered["is_nonzero_activity_count_minute"] = filtered["valid_activity_count"] > 0
        aggregations: dict[str, tuple[str, str]] = {
            "minute_rows": ("PAXINTEN", "size"),
            "reliable_minutes": ("is_reliable", "sum"),
            "in_calibration_minutes": ("is_in_calibration", "sum"),
            "reliable_in_calibration_minutes": ("is_reliable_in_calibration", "sum"),
            "nonzero_activity_count_minutes": ("is_nonzero_activity_count_minute", "sum"),
            "total_activity_counts_all_minutes": ("PAXINTEN", "sum"),
            "total_activity_counts_reliable_in_calibration": ("valid_activity_count", "sum"),
            "mean_activity_counts_reliable_in_calibration": ("valid_activity_count", "mean"),
            "max_activity_counts": ("PAXINTEN", "max"),
        }
        if "PAXSTEP" in filtered.columns:
            has_step_column = True
            filtered["valid_step_count"] = filtered["PAXSTEP"].where(filtered["is_reliable_in_calibration"], 0)
            aggregations["total_steps_reliable_in_calibration"] = ("valid_step_count", "sum")
            aggregations["max_steps_per_minute"] = ("PAXSTEP", "max")

        grouped = (
            filtered.groupby(["SEQN", "cycle", "day_index", "PAXDAY"], dropna=False)
            .agg(**aggregations)
            .reset_index()
        )
        daily_parts.append(grouped)
        if chunks_scanned % 25 == 0:
            LOGGER.info("%s chunks=%s retained_rows=%s", cycle, chunks_scanned, retained_rows)

    if daily_parts:
        daily = pd.concat(daily_parts, ignore_index=True)
        sum_columns = [
            "minute_rows",
            "reliable_minutes",
            "in_calibration_minutes",
            "reliable_in_calibration_minutes",
            "nonzero_activity_count_minutes",
            "total_activity_counts_all_minutes",
            "total_activity_counts_reliable_in_calibration",
        ]
        if "total_steps_reliable_in_calibration" in daily.columns:
            sum_columns.append("total_steps_reliable_in_calibration")
        max_columns = ["max_activity_counts"]
        if "max_steps_per_minute" in daily.columns:
            max_columns.append("max_steps_per_minute")
        daily = (
            daily.groupby(["SEQN", "cycle", "day_index", "PAXDAY"], as_index=False)
            .agg(
                **{column: (column, "sum") for column in sum_columns},
                **{column: (column, "max") for column in max_columns},
            )
            .sort_values(["cycle", "SEQN", "day_index"])
        )
        daily["mean_activity_counts_reliable_in_calibration"] = (
            daily["total_activity_counts_reliable_in_calibration"]
            / daily["reliable_in_calibration_minutes"].replace({0: pd.NA})
        )
    else:
        daily = pd.DataFrame()

    stats = {
        "cycle": cycle,
        "rows_scanned": int(rows_scanned),
        "chunks_scanned": int(chunks_scanned),
        "retained_minute_rows": int(retained_rows),
        "participants_requested": int(len(participant_seqn)),
        "participants_with_paxraw": int(daily["SEQN"].nunique()) if not daily.empty else 0,
        "daily_rows": int(len(daily)),
        "has_step_column": bool(has_step_column),
    }
    return daily, stats


def build_participant_summary(daily: pd.DataFrame) -> pd.DataFrame:
    aggregations: dict[str, tuple[str, str]] = {
        "observed_days": ("day_index", "nunique"),
        "mean_reliable_in_calibration_minutes_per_day": ("reliable_in_calibration_minutes", "mean"),
        "mean_daily_activity_counts": ("total_activity_counts_reliable_in_calibration", "mean"),
        "median_daily_activity_counts": ("total_activity_counts_reliable_in_calibration", "median"),
        "mean_nonzero_activity_count_minutes": ("nonzero_activity_count_minutes", "mean"),
    }
    if "total_steps_reliable_in_calibration" in daily.columns:
        aggregations["mean_daily_steps"] = ("total_steps_reliable_in_calibration", "mean")
    return (
        daily.groupby(["SEQN", "cycle"], as_index=False)
        .agg(**aggregations)
        .sort_values(["cycle", "SEQN"])
    )


def build_semantic_map() -> pd.DataFrame:
    rows = [
        {
            "source_id": "nhanes_2003_2006_hip_actigraph_pam",
            "source_variable": "PAXINTEN",
            "source_label": "ActiGraph AM-7164 hip-worn activity counts per 1-minute epoch",
            "source_unit": "device-specific activity counts/minute",
            "harmonised_construct": "daily movement volume",
            "compatibility_status": "broad construct only; numeric equivalence blocked",
            "compatible_with_current_mims": False,
            "interpretation_limit": (
                "Do not convert hip ActiGraph counts to wrist MIMS. Do not treat cut-points, MVPA, "
                "sedentary time, or total volume as numerically equivalent without protocol-specific validation."
            ),
        },
        {
            "source_id": "nhanes_2005_2006_hip_actigraph_pam",
            "source_variable": "PAXSTEP",
            "source_label": "ActiGraph AM-7164 hip-worn step count per 1-minute epoch",
            "source_unit": "steps/minute",
            "harmonised_construct": "daily ambulatory volume",
            "compatibility_status": "source-specific step metric; no conversion from/to MIMS",
            "compatible_with_current_mims": False,
            "interpretation_limit": (
                "Steps can be summarized as a real ambulatory metric, but cannot be inferred from "
                "NHANES 2011-2014 wrist MIMS and cannot validate MIMS-to-steps conversion."
            ),
        },
    ]
    return pd.DataFrame(rows)


def build_risk_register() -> pd.DataFrame:
    rows = [
        {
            "risk_id": "independent_pam_vs_wrist_mims_numeric_equivalence",
            "risk_type": "cross_cohort_cross_device_metric",
            "risk_level": "high",
            "naive_claim": "Treat NHANES 2003-2006 hip ActiGraph counts and NHANES 2011-2014 wrist MIMS as the same physical activity variable.",
            "kg_guarded_decision": "Permit only broad construct-level grouping under movement volume; block numeric conversion/equivalence.",
            "why_it_matters": "The source differs by participants, cycle, device placement, device generation, and metric definition.",
        },
        {
            "risk_id": "independent_pam_cutpoint_back_mapping",
            "risk_type": "unsupported_threshold_transfer",
            "risk_level": "high",
            "naive_claim": "Apply hip-count cut-points or step cadence interpretations to wrist MIMS outputs.",
            "kg_guarded_decision": "Require source-specific protocol nodes and explicit validation before threshold transfer.",
            "why_it_matters": "A semantic match on activity labels is not enough to support MVPA/sedentary claims across devices.",
        },
    ]
    return pd.DataFrame(rows)


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


def write_doc(summary: dict[str, Any], semantic_map: pd.DataFrame, risks: pd.DataFrame) -> None:
    lines = [
        "# Independent NHANES 2003-2006 PAM Integration",
        "",
        "**Decision:** use NHANES 2003-2006 Physical Activity Monitor data as the first independent public accelerometry validation source.",
        "",
        "This source is independent from the existing NHANES 2011-2014 wrist/MIMS source at the participant, survey-cycle, device-placement, and metric level. It is still from the NHANES program, so it should not be described as an independent clinical cancer-survivorship cohort.",
        "",
        "## Source",
        "",
        "- 2003-2004 PAXRAW_C: hip-worn ActiGraph AM-7164, 1-minute `PAXINTEN` activity-count epochs.",
        "- 2005-2006 PAXRAW_D: hip-worn ActiGraph AM-7164, 1-minute `PAXINTEN` and `PAXSTEP` epochs.",
        "- Cancer-history cohort definition is the same conservative survey definition used in the main pipeline: adults aged 20+ with `MCQ220=1`.",
        "",
        "## Current Counts",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| cancer-history adults before PAM filtering | {summary['cancer_history_adults_total']} |",
        f"| participants with PAM minute records | {summary['participants_with_paxraw_total']} |",
        f"| daily PAM summary rows | {summary['daily_rows_total']} |",
        f"| retained PAM minute rows | {summary['retained_minute_rows_total']} |",
        "",
        "## Per-Cycle Processing",
        "",
    ]
    lines.extend(markdown_table(pd.DataFrame(summary["cycle_stats"])))
    lines.extend(
        [
            "",
            "## Semantic Map",
            "",
        ]
    )
    lines.extend(markdown_table(semantic_map))
    lines.extend(["", "## Risk Register", ""])
    lines.extend(markdown_table(risks))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This closes the practical independent-dataset gap better than PhysioNet because the participants and raw accelerometry collection are not the same as the 2011-2014 wrist/MIMS source.",
            "",
            "It does not permit conversion between hip ActiGraph counts, steps, and wrist MIMS. The KG should represent these as source-specific metrics that can be grouped only under broad constructs unless a validated conversion or protocol-specific threshold mapping is provided.",
        ]
    )
    (DOCS / "independent_nhanes_pam_integration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_outputs(chunksize: int = 500_000) -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    EVALUATION.mkdir(parents=True, exist_ok=True)

    extraction_rows = [extract_paxraw_if_needed(cycle, meta) for cycle, meta in CYCLES.items()]
    participants = build_participants()
    participants.to_csv(PROCESSED / "independent_nhanes_pam_participants.csv", index=False)

    daily_parts: list[pd.DataFrame] = []
    cycle_stats: list[dict[str, Any]] = []
    for cycle, meta in CYCLES.items():
        participant_seqn = set(participants.loc[participants["cycle"] == cycle, "SEQN"])
        daily, stats = process_paxraw_cycle(cycle, meta["pax_xpt"], participant_seqn, chunksize)
        if not daily.empty:
            daily_parts.append(daily)
        cycle_stats.append(stats)

    daily_all = pd.concat(daily_parts, ignore_index=True) if daily_parts else pd.DataFrame()
    if not daily_all.empty:
        daily_all.to_csv(PROCESSED / "independent_nhanes_pam_daily_summary.csv", index=False)
        participant_summary = build_participant_summary(daily_all)
    else:
        participant_summary = pd.DataFrame()
    participant_summary.to_csv(PROCESSED / "independent_nhanes_pam_participant_summary.csv", index=False)

    semantic_map = build_semantic_map()
    risks = build_risk_register()
    semantic_map.to_csv(PROCESSED / "independent_nhanes_pam_semantic_map.csv", index=False)
    risks.to_csv(PROCESSED / "independent_nhanes_pam_semantic_risk_register.csv", index=False)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_id": "nhanes_2003_2006_hip_actigraph_pam",
        "source_status": "independent_public_accelerometry_source_integrated",
        "independence_claim": (
            "Independent from NHANES 2011-2014 wrist/MIMS at participant, cycle, device-placement, "
            "and source-metric level; not an independent clinical cancer-survivorship cohort."
        ),
        "cancer_history_adults_total": int(participants["SEQN"].nunique()),
        "participants_with_paxraw_total": int(participant_summary["SEQN"].nunique()) if not participant_summary.empty else 0,
        "daily_rows_total": int(len(daily_all)),
        "retained_minute_rows_total": int(sum(item["retained_minute_rows"] for item in cycle_stats)),
        "semantic_risk_rows": int(len(risks)),
        "high_semantic_risk_rows": int((risks["risk_level"] == "high").sum()),
        "cycle_stats": cycle_stats,
        "extraction": extraction_rows,
        "outputs": {
            "participants": "data/processed/independent_nhanes_pam_participants.csv",
            "daily_summary": "data/processed/independent_nhanes_pam_daily_summary.csv",
            "participant_summary": "data/processed/independent_nhanes_pam_participant_summary.csv",
            "semantic_map": "data/processed/independent_nhanes_pam_semantic_map.csv",
            "semantic_risk_register": "data/processed/independent_nhanes_pam_semantic_risk_register.csv",
            "documentation": "docs/independent_nhanes_pam_integration.md",
        },
    }
    write_doc(summary, semantic_map, risks)
    (REPORTS / "independent_nhanes_pam_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
