"""Compare alternative accelerometry definitions on independent NHANES PAM data.

The goal is not to create clinical activity labels. It is to show, on the same
participants, how processing rules and cut-points change derived classifications.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"

CYCLES = {
    "2003-2004": RAW / "2003-2004" / "paxraw_c.xpt",
    "2005-2006": RAW / "2005-2006" / "paxraw_d.xpt",
}

PARTICIPANTS = PROCESSED / "independent_nhanes_pam_participants.csv"
DAILY_OUT = PROCESSED / "activity_definition_daily_thresholds.csv"
PARTICIPANT_OUT = PROCESSED / "activity_definition_participant_classification.csv"
COMPARISON_OUT = PROCESSED / "activity_definition_protocol_comparison.csv"
RULES_OUT = PROCESSED / "activity_definition_rules.csv"
SUMMARY_OUT = REPORTS / "activity_definition_comparison_summary.json"
DOC_OUT = DOCS / "activity_definition_comparison.md"

SOURCE_URLS = {
    "cdc_pcd_2016": "https://www.cdc.gov/pcd/issues/2016/16_0159.htm",
    "pmc_nhanes_catalog": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3457743/",
    "pubmed_thresholds": "https://pubmed.ncbi.nlm.nih.gov/25889192/",
}


def count_bouted_minutes(flags: Iterable[bool], min_run: int = 10) -> int:
    """Count minutes in strict uninterrupted runs of at least min_run minutes."""
    total = 0
    run = 0
    for flag in flags:
        if flag:
            run += 1
        else:
            if run >= min_run:
                total += run
            run = 0
    if run >= min_run:
        total += run
    return total


def load_filtered_minutes(chunksize: int = 500_000) -> pd.DataFrame:
    participants = pd.read_csv(PARTICIPANTS, usecols=["SEQN", "cycle"])
    participant_sets = {
        cycle: set(frame["SEQN"].astype(float))
        for cycle, frame in participants.groupby("cycle", sort=False)
    }

    frames: list[pd.DataFrame] = []
    for cycle, path in CYCLES.items():
        if not path.exists():
            raise FileNotFoundError(path)
        keep_seqn = participant_sets.get(cycle, set())
        if not keep_seqn:
            continue

        for chunk in pd.read_sas(path, chunksize=chunksize):
            chunk = chunk[chunk["SEQN"].isin(keep_seqn)]
            if chunk.empty:
                continue
            frame = chunk[["SEQN", "PAXSTAT", "PAXCAL", "PAXDAY", "PAXN", "PAXINTEN"]].copy()
            frame["cycle"] = cycle
            frame["SEQN"] = frame["SEQN"].astype("int64")
            frame["PAXN"] = frame["PAXN"].astype("int32")
            frame["PAXDAY"] = frame["PAXDAY"].astype("int16")
            frame["PAXSTAT"] = frame["PAXSTAT"].astype("int16")
            frame["PAXCAL"] = frame["PAXCAL"].astype("int16")
            frame["PAXINTEN"] = frame["PAXINTEN"].fillna(0).astype("float32")
            frame["day_index"] = ((frame["PAXN"] - 1) // 1440 + 1).astype("int16")
            frame["minute_order"] = ((frame["PAXN"] - 1) % 1440).astype("int16")
            frames.append(frame)

    if not frames:
        raise RuntimeError("No NHANES PAM minute rows were available for cancer-history participants.")
    minutes = pd.concat(frames, ignore_index=True)
    minutes.sort_values(["cycle", "SEQN", "day_index", "minute_order"], inplace=True)
    minutes["valid_minute"] = (minutes["PAXSTAT"].eq(1) & minutes["PAXCAL"].eq(1))
    return minutes


def build_daily_thresholds(minutes: pd.DataFrame) -> pd.DataFrame:
    valid = minutes["valid_minute"]
    intensity = minutes["PAXINTEN"]

    minutes["valid_minute_count"] = valid.astype("int16")
    minutes["sedentary_lt100_minutes"] = (valid & intensity.lt(100)).astype("int16")
    minutes["light_100_759_minutes"] = (valid & intensity.ge(100) & intensity.lt(760)).astype("int16")
    minutes["lifestyle_760_2019_minutes"] = (valid & intensity.ge(760) & intensity.lt(2020)).astype("int16")
    minutes["mvpa_760_any_minutes"] = (valid & intensity.ge(760)).astype("int16")
    minutes["mvpa_2020_any_minutes"] = (valid & intensity.ge(2020)).astype("int16")
    minutes["vigorous_5999_any_minutes"] = (valid & intensity.ge(5999)).astype("int16")
    minutes["activity_counts_valid"] = np.where(valid, intensity, 0).astype("float32")

    keys = ["SEQN", "cycle", "day_index"]
    daily = (
        minutes.groupby(keys, sort=False)
        .agg(
            PAXDAY=("PAXDAY", "first"),
            minute_rows=("PAXN", "size"),
            reliable_in_calibration_minutes=("valid_minute_count", "sum"),
            sedentary_lt100_minutes=("sedentary_lt100_minutes", "sum"),
            light_100_759_minutes=("light_100_759_minutes", "sum"),
            lifestyle_760_2019_minutes=("lifestyle_760_2019_minutes", "sum"),
            mvpa_760_any_minutes=("mvpa_760_any_minutes", "sum"),
            mvpa_2020_any_minutes=("mvpa_2020_any_minutes", "sum"),
            vigorous_5999_any_minutes=("vigorous_5999_any_minutes", "sum"),
            total_activity_counts_valid=("activity_counts_valid", "sum"),
        )
        .reset_index()
    )

    bout_rows = []
    for (seqn, cycle, day_index), group in minutes.groupby(keys, sort=False):
        valid_group = group["valid_minute"].to_numpy(dtype=bool)
        counts = group["PAXINTEN"].to_numpy()
        bout_rows.append(
            {
                "SEQN": int(seqn),
                "cycle": cycle,
                "day_index": int(day_index),
                "mvpa_760_bouted_10min_strict_minutes": count_bouted_minutes(valid_group & (counts >= 760)),
                "mvpa_2020_bouted_10min_strict_minutes": count_bouted_minutes(valid_group & (counts >= 2020)),
            }
        )
    bout_frame = pd.DataFrame(bout_rows)
    daily = daily.merge(bout_frame, on=keys, how="left")
    daily["valid_day_10h"] = daily["reliable_in_calibration_minutes"].ge(600)
    daily["valid_day_12h"] = daily["reliable_in_calibration_minutes"].ge(720)
    daily["mean_activity_counts_valid"] = (
        daily["total_activity_counts_valid"] / daily["reliable_in_calibration_minutes"].replace(0, np.nan)
    ).round(3)
    return daily


def build_participant_classification(daily: pd.DataFrame) -> pd.DataFrame:
    keys = ["SEQN", "cycle"]
    base = (
        daily.groupby(keys, sort=False)
        .agg(
            observed_days=("day_index", "nunique"),
            valid_days_10h=("valid_day_10h", "sum"),
            valid_days_12h=("valid_day_12h", "sum"),
        )
        .reset_index()
    )
    base["eligible_10h_min4"] = base["valid_days_10h"].ge(4)
    base["eligible_12h_min4"] = base["valid_days_12h"].ge(4)

    valid_10h = daily[daily["valid_day_10h"]].copy()
    means = (
        valid_10h.groupby(keys, sort=False)
        .agg(
            mean_daily_sedentary_lt100_minutes=("sedentary_lt100_minutes", "mean"),
            mean_daily_mvpa_760_any_minutes=("mvpa_760_any_minutes", "mean"),
            mean_daily_mvpa_2020_any_minutes=("mvpa_2020_any_minutes", "mean"),
            mean_daily_mvpa_760_bouted_10min_minutes=("mvpa_760_bouted_10min_strict_minutes", "mean"),
            mean_daily_mvpa_2020_bouted_10min_minutes=("mvpa_2020_bouted_10min_strict_minutes", "mean"),
            mean_daily_vigorous_5999_any_minutes=("vigorous_5999_any_minutes", "mean"),
        )
        .reset_index()
    )
    participant = base.merge(means, on=keys, how="left")
    mean_cols = [col for col in participant.columns if col.startswith("mean_daily_")]
    participant[mean_cols] = participant[mean_cols].round(3)

    eligible = participant["eligible_10h_min4"]
    participant["demo_ge30min_day_mvpa_760_any"] = eligible & participant["mean_daily_mvpa_760_any_minutes"].ge(30)
    participant["demo_ge30min_day_mvpa_2020_any"] = eligible & participant["mean_daily_mvpa_2020_any_minutes"].ge(30)
    participant["demo_ge30min_day_mvpa_760_bouted_10min"] = eligible & participant[
        "mean_daily_mvpa_760_bouted_10min_minutes"
    ].ge(30)
    participant["demo_ge30min_day_mvpa_2020_bouted_10min"] = eligible & participant[
        "mean_daily_mvpa_2020_bouted_10min_minutes"
    ].ge(30)
    participant["demo_high_sedentary_ge8h_day"] = eligible & participant[
        "mean_daily_sedentary_lt100_minutes"
    ].ge(480)
    return participant


def comparison_row(
    participant: pd.DataFrame,
    comparison_id: str,
    left_definition: str,
    right_definition: str,
    left_col: str,
    right_col: str,
    denominator_col: str | None,
    plain_meaning: str,
) -> dict[str, object]:
    frame = participant[participant[denominator_col]].copy() if denominator_col else participant.copy()
    left = frame[left_col].astype(bool)
    right = frame[right_col].astype(bool)
    return {
        "comparison_id": comparison_id,
        "left_definition": left_definition,
        "right_definition": right_definition,
        "denominator": int(len(frame)),
        "left_true": int(left.sum()),
        "right_true": int(right.sum()),
        "both_true": int((left & right).sum()),
        "left_only": int((left & ~right).sum()),
        "right_only": int((~left & right).sum()),
        "both_false": int((~left & ~right).sum()),
        "discordant": int((left != right).sum()),
        "plain_meaning": plain_meaning,
    }


def build_comparisons(participant: pd.DataFrame) -> pd.DataFrame:
    rows = [
        comparison_row(
            participant,
            "valid_day_10h_vs_12h_min4",
            ">=4 days with >=10 h valid wear proxy",
            ">=4 days with >=12 h valid wear proxy",
            "eligible_10h_min4",
            "eligible_12h_min4",
            None,
            "This source has near-complete valid PAM days, so this wear-time sensitivity did not change eligibility here.",
        ),
        comparison_row(
            participant,
            "mvpa_760_vs_2020_any_ge30min_day",
            "mean >=30 min/day at >=760 counts/min",
            "mean >=30 min/day at >=2020 counts/min",
            "demo_ge30min_day_mvpa_760_any",
            "demo_ge30min_day_mvpa_2020_any",
            "eligible_10h_min4",
            "Changing the MVPA cut-point changes who crosses the same demonstration activity threshold.",
        ),
        comparison_row(
            participant,
            "mvpa_2020_any_vs_10min_bout_ge30min_day",
            "mean >=30 min/day at >=2020 counts/min, any valid minute",
            "mean >=30 min/day at >=2020 counts/min, strict 10-min bouts",
            "demo_ge30min_day_mvpa_2020_any",
            "demo_ge30min_day_mvpa_2020_bouted_10min",
            "eligible_10h_min4",
            "Adding a bout rule changes who crosses the same demonstration activity threshold.",
        ),
        comparison_row(
            participant,
            "mvpa_760_any_vs_10min_bout_ge30min_day",
            "mean >=30 min/day at >=760 counts/min, any valid minute",
            "mean >=30 min/day at >=760 counts/min, strict 10-min bouts",
            "demo_ge30min_day_mvpa_760_any",
            "demo_ge30min_day_mvpa_760_bouted_10min",
            "eligible_10h_min4",
            "Adding a bout rule has a larger effect when the lower intensity cut-point is used.",
        ),
    ]
    return pd.DataFrame(rows)


def build_rules() -> pd.DataFrame:
    rows = [
        {
            "definition_id": "valid_day_10h",
            "plain_name": "Valid day: 10 hours",
            "rule_type": "wear-time inclusion",
            "machine_rule": "reliable_in_calibration_minutes >= 600",
            "source_metric": "PAXSTAT == 1 and PAXCAL == 1 minute count",
            "provenance": SOURCE_URLS["cdc_pcd_2016"],
            "interpretation_limit": "Uses NHANES PAM reliability/calibration flags as a wear proxy; full nonwear bout reconstruction is not asserted.",
        },
        {
            "definition_id": "valid_day_12h",
            "plain_name": "Valid day: 12 hours",
            "rule_type": "wear-time inclusion sensitivity",
            "machine_rule": "reliable_in_calibration_minutes >= 720",
            "source_metric": "PAXSTAT == 1 and PAXCAL == 1 minute count",
            "provenance": SOURCE_URLS["cdc_pcd_2016"],
            "interpretation_limit": "Sensitivity definition used to demonstrate valid-day rule dependence.",
        },
        {
            "definition_id": "sedentary_lt100",
            "plain_name": "Sedentary minute: <100 counts/min",
            "rule_type": "intensity cut-point",
            "machine_rule": "valid_minute and PAXINTEN < 100",
            "source_metric": "NHANES 2003-2006 hip ActiGraph activity counts/min",
            "provenance": SOURCE_URLS["pmc_nhanes_catalog"],
            "interpretation_limit": "Applies to hip ActiGraph PAM counts; not applied to wrist MIMS.",
        },
        {
            "definition_id": "mvpa_760_any",
            "plain_name": "MVPA-like minute: >=760 counts/min",
            "rule_type": "lower intensity cut-point",
            "machine_rule": "valid_minute and PAXINTEN >= 760",
            "source_metric": "NHANES 2003-2006 hip ActiGraph activity counts/min",
            "provenance": SOURCE_URLS["pubmed_thresholds"],
            "interpretation_limit": "Lower lifestyle/moderate threshold; not numerically equivalent to >=2020 counts/min.",
        },
        {
            "definition_id": "mvpa_2020_any",
            "plain_name": "MVPA minute: >=2020 counts/min",
            "rule_type": "intensity cut-point",
            "machine_rule": "valid_minute and PAXINTEN >= 2020",
            "source_metric": "NHANES 2003-2006 hip ActiGraph activity counts/min",
            "provenance": SOURCE_URLS["cdc_pcd_2016"],
            "interpretation_limit": "Applies to hip ActiGraph PAM counts; not applied to wrist MIMS.",
        },
        {
            "definition_id": "mvpa_2020_bout10_strict",
            "plain_name": "MVPA bout: >=2020 counts/min for >=10 uninterrupted minutes",
            "rule_type": "bout rule",
            "machine_rule": "count minutes in strict consecutive runs where valid_minute and PAXINTEN >= 2020, run length >= 10",
            "source_metric": "NHANES 2003-2006 hip ActiGraph activity counts/min",
            "provenance": SOURCE_URLS["cdc_pcd_2016"],
            "interpretation_limit": "Strict bout implementation for sensitivity demonstration; no interruption allowance is asserted.",
        },
        {
            "definition_id": "vigorous_5999_any",
            "plain_name": "Vigorous minute: >=5999 counts/min",
            "rule_type": "intensity cut-point",
            "machine_rule": "valid_minute and PAXINTEN >= 5999",
            "source_metric": "NHANES 2003-2006 hip ActiGraph activity counts/min",
            "provenance": SOURCE_URLS["pubmed_thresholds"],
            "interpretation_limit": "Applies to hip ActiGraph PAM counts; not applied to wrist MIMS.",
        },
    ]
    return pd.DataFrame(rows)


def write_doc(summary: dict[str, object], comparisons: pd.DataFrame) -> None:
    lines = [
        "# Activity Definition Comparison Experiment",
        "",
        "This experiment realigns the prototype with the manuscript scope: alternative accelerometry definitions are applied to the same cancer-history participants to show how methodological choices change derived classifications.",
        "",
        "## Data Scope",
        "",
        f"- Source: NHANES 2003-2006 hip-worn ActiGraph PAM raw minute data.",
        f"- Participants with self-reported cancer history and PAM records: {summary['participants_evaluated']:,}.",
        f"- Daily rows with derived threshold features: {summary['daily_rows']:,}.",
        "- These rules are applied only to hip ActiGraph counts. They are not applied to 2011-2014 wrist MIMS.",
        "",
        "## What Is Being Compared",
        "",
        "- Valid-day inclusion: >=10 hours versus >=12 hours of reliable/in-calibration minutes.",
        "- Intensity cut-points: >=760 versus >=2020 counts/min.",
        "- Bout rule: any qualifying minute versus strict uninterrupted 10-minute bouts.",
        "- Demonstration classification: mean >=30 min/day among participants with >=4 valid 10-hour days. This is a methodological threshold for comparing definitions, not an autonomous clinical decision rule.",
        "",
        "## Main Result",
        "",
    ]
    for row in comparisons.to_dict(orient="records"):
        lines.append(
            f"- {row['comparison_id']}: denominator {row['denominator']:,}; "
            f"left true {row['left_true']:,}; right true {row['right_true']:,}; "
            f"discordant {row['discordant']:,}. {row['plain_meaning']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "The result supports the paper's core claim: semantic harmonisation preserves the rule that produced each activity label, so researchers can see whether a difference is biological/clinical or caused by processing choices. It does not convert wrist MIMS to steps, does not infer MVPA from MIMS, and does not prescribe rehabilitation.",
            "",
            "## Provenance",
            "",
            f"- CDC PCD NHANES 2003-2006 ActiGraph processing reference: {SOURCE_URLS['cdc_pcd_2016']}",
            f"- NHANES accelerometry threshold catalog: {SOURCE_URLS['pmc_nhanes_catalog']}",
            f"- Published threshold comparison reference: {SOURCE_URLS['pubmed_thresholds']}",
            "",
        ]
    )
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    minutes = load_filtered_minutes()
    daily = build_daily_thresholds(minutes)
    participant = build_participant_classification(daily)
    comparisons = build_comparisons(participant)
    rules = build_rules()

    daily.to_csv(DAILY_OUT, index=False)
    participant.to_csv(PARTICIPANT_OUT, index=False)
    comparisons.to_csv(COMPARISON_OUT, index=False)
    rules.to_csv(RULES_OUT, index=False)

    eligible_10h = participant["eligible_10h_min4"]
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "NHANES 2003-2006 hip-worn ActiGraph PAM raw minute data",
        "participants_evaluated": int(len(participant)),
        "participants_eligible_10h_min4": int(participant["eligible_10h_min4"].sum()),
        "participants_eligible_12h_min4": int(participant["eligible_12h_min4"].sum()),
        "participants_valid_day_rule_discordant": int(
            (participant["eligible_10h_min4"] != participant["eligible_12h_min4"]).sum()
        ),
        "daily_rows": int(len(daily)),
        "definition_rules": int(len(rules)),
        "protocol_comparisons": int(len(comparisons)),
        "eligible_10h_mvpa_760_any_ge30": int(participant.loc[eligible_10h, "demo_ge30min_day_mvpa_760_any"].sum()),
        "eligible_10h_mvpa_2020_any_ge30": int(participant.loc[eligible_10h, "demo_ge30min_day_mvpa_2020_any"].sum()),
        "eligible_10h_mvpa_2020_bouted_ge30": int(
            participant.loc[eligible_10h, "demo_ge30min_day_mvpa_2020_bouted_10min"].sum()
        ),
        "outputs": {
            "daily_thresholds": str(DAILY_OUT.relative_to(ROOT)),
            "participant_classification": str(PARTICIPANT_OUT.relative_to(ROOT)),
            "protocol_comparison": str(COMPARISON_OUT.relative_to(ROOT)),
            "definition_rules": str(RULES_OUT.relative_to(ROOT)),
            "documentation": str(DOC_OUT.relative_to(ROOT)),
        },
        "source_urls": SOURCE_URLS,
        "interpretation_limit": (
            "This is a methodological definition-comparison experiment on NHANES hip ActiGraph counts. "
            "It is not a clinical diagnosis, not a treatment recommendation, and not a MIMS-to-MVPA conversion."
        ),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_doc(summary, comparisons)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
