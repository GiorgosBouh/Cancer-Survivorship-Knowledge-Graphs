"""Outcome-sensitivity analysis for approved valid-day protocols.

This analysis quantifies how protocol choice changes participant inclusion and
movement summaries. It deliberately reports MIMS as movement-summary values, not
as MVPA, sedentary, active/inactive, or clinical physical activity categories.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs" / "protocols"


def protocol_mask(days: pd.DataFrame, protocol_id: str) -> pd.Series:
    if protocol_id == "wake_wear_10h_min4":
        return days["PAXWWMD"] >= 600
    if protocol_id == "wake_wear_12h_min4":
        return days["PAXWWMD"] >= 720
    if protocol_id == "valid_minutes_20h_min4":
        return days["PAXVMD"] >= 1200
    raise ValueError(f"Unsupported protocol: {protocol_id}")


def describe(values: pd.Series, prefix: str) -> dict[str, float | int]:
    clean = values.dropna()
    if clean.empty:
        return {
            f"{prefix}_n": 0,
            f"{prefix}_mean": None,
            f"{prefix}_median": None,
            f"{prefix}_q1": None,
            f"{prefix}_q3": None,
            f"{prefix}_min": None,
            f"{prefix}_max": None,
        }
    return {
        f"{prefix}_n": int(clean.shape[0]),
        f"{prefix}_mean": round(float(clean.mean()), 6),
        f"{prefix}_median": round(float(clean.median()), 6),
        f"{prefix}_q1": round(float(clean.quantile(0.25)), 6),
        f"{prefix}_q3": round(float(clean.quantile(0.75)), 6),
        f"{prefix}_min": round(float(clean.min()), 6),
        f"{prefix}_max": round(float(clean.max()), 6),
    }


def build_outputs() -> dict[str, object]:
    protocols = pd.read_csv(PROCESSED / "protocol_definitions.csv")
    review = pd.read_csv(ROOT / "docs" / "protocols" / "protocol_review_sheet.csv", dtype=str).fillna("")
    results = pd.read_csv(PROCESSED / "valid_day_protocol_results.csv")
    days = pd.read_csv(PROCESSED / "pam_days.csv")
    features = pd.read_csv(PROCESSED / "pam_minute_features.csv")

    days = days.merge(
        features[["SEQN", "cycle", "PAXDAYM", "peak_30_valid_mims", "daily_total_valid_mims_from_minutes"]],
        left_on=["SEQN", "cycle", "PAXDAYD"],
        right_on=["SEQN", "cycle", "PAXDAYM"],
        how="left",
    )

    summary_rows: list[dict[str, object]] = []
    participant_metric_rows: list[dict[str, object]] = []
    inclusion_frames: list[pd.DataFrame] = []

    for protocol in protocols.itertuples(index=False):
        protocol_id = protocol.protocol_id
        reviewed = review[review["protocol_id"].eq(protocol_id)].iloc[0].to_dict()
        frame = days.copy()
        frame["is_valid_day_under_protocol"] = protocol_mask(frame, protocol_id)
        valid_days = frame[frame["is_valid_day_under_protocol"]].copy()

        participant = valid_days.groupby(["SEQN", "cycle"], as_index=False).agg(
            valid_day_count=("PAXDAYD", "nunique"),
            mean_daily_mims_valid_days=("PAXMTSD", "mean"),
            median_daily_mims_valid_days=("PAXMTSD", "median"),
            total_mims_valid_days=("PAXMTSD", "sum"),
            mean_valid_minutes_valid_days=("PAXVMD", "mean"),
            mean_wake_wear_minutes_valid_days=("PAXWWMD", "mean"),
            mean_peak30_valid_mims=("peak_30_valid_mims", "mean"),
        )
        participant["protocol_id"] = protocol_id
        participant["eligible_under_protocol"] = participant["valid_day_count"] >= int(protocol.min_valid_days)
        participant_metric_rows.append(participant)

        all_participants = results[results["protocol_id"].eq(protocol_id)][["SEQN", "cycle", "eligible_under_protocol"]].copy()
        all_participants = all_participants.rename(columns={"eligible_under_protocol": protocol_id})
        inclusion_frames.append(all_participants)

        eligible_participant = participant[participant["eligible_under_protocol"]]
        result_rows = results[results["protocol_id"].eq(protocol_id)]
        row = {
            "protocol_id": protocol_id,
            "approved_status": reviewed.get("approved_status", ""),
            "classification_type": reviewed.get("classification_type", ""),
            "valid_day_expression": protocol.valid_day_expression,
            "min_valid_days": int(protocol.min_valid_days),
            "observed_participants": int(result_rows.shape[0]),
            "eligible_participants": int(result_rows["eligible_under_protocol"].sum()),
            "eligible_percent": round(100 * float(result_rows["eligible_under_protocol"].mean()), 6),
            "valid_day_rows": int(valid_days.shape[0]),
            "interpretation_limit": "Movement-summary sensitivity only; not MVPA, sedentary, active/inactive, or clinical physical activity classification.",
        }
        row.update(describe(valid_days["PAXMTSD"], "daily_mims_valid_day"))
        row.update(describe(eligible_participant["mean_daily_mims_valid_days"], "participant_mean_daily_mims"))
        row.update(describe(eligible_participant["mean_peak30_valid_mims"], "participant_mean_peak30_valid_mims"))
        row.update(describe(eligible_participant["mean_valid_minutes_valid_days"], "participant_mean_valid_minutes"))
        row.update(describe(eligible_participant["mean_wake_wear_minutes_valid_days"], "participant_mean_wake_wear_minutes"))
        summary_rows.append(row)

    sensitivity_summary = pd.DataFrame(summary_rows)
    participant_metrics = pd.concat(participant_metric_rows, ignore_index=True)

    inclusion = inclusion_frames[0]
    for frame in inclusion_frames[1:]:
        inclusion = inclusion.merge(frame, on=["SEQN", "cycle"], how="outer")
    for protocol_id in protocols["protocol_id"]:
        inclusion[protocol_id] = inclusion[protocol_id].fillna(False).astype(bool)

    pairwise_rows = []
    protocol_ids = list(protocols["protocol_id"])
    for i, left in enumerate(protocol_ids):
        for right in protocol_ids[i + 1 :]:
            left_only = int((inclusion[left] & ~inclusion[right]).sum())
            right_only = int((~inclusion[left] & inclusion[right]).sum())
            both = int((inclusion[left] & inclusion[right]).sum())
            neither = int((~inclusion[left] & ~inclusion[right]).sum())
            pairwise_rows.append(
                {
                    "left_protocol": left,
                    "right_protocol": right,
                    "both_eligible": both,
                    "left_only": left_only,
                    "right_only": right_only,
                    "neither": neither,
                    "discordant_participants": left_only + right_only,
                }
            )
    pairwise = pd.DataFrame(pairwise_rows)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    summary_path = PROCESSED / "protocol_outcome_sensitivity_summary.csv"
    participant_path = PROCESSED / "protocol_outcome_sensitivity_participants.csv"
    pairwise_path = PROCESSED / "protocol_pairwise_inclusion_comparison.csv"
    sensitivity_summary.to_csv(summary_path, index=False)
    participant_metrics.to_csv(participant_path, index=False)
    pairwise.to_csv(pairwise_path, index=False)

    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": str(summary_path.relative_to(ROOT)),
        "participant_metrics": str(participant_path.relative_to(ROOT)),
        "pairwise_inclusion": str(pairwise_path.relative_to(ROOT)),
        "protocols": protocol_ids,
        "protocol_count": len(protocol_ids),
        "interpretation_limit": "MIMS values are movement-summary metrics only; no MVPA, sedentary, active/inactive, or clinical physical activity classification is made.",
        "headline": {
            row["protocol_id"]: {
                "eligible_participants": int(row["eligible_participants"]),
                "eligible_percent": float(row["eligible_percent"]),
                "participant_mean_daily_mims_mean": row["participant_mean_daily_mims_mean"],
                "valid_day_rows": int(row["valid_day_rows"]),
            }
            for row in summary_rows
        },
        "pairwise_discordance": pairwise.to_dict(orient="records"),
    }
    report_path = REPORTS / "protocol_outcome_sensitivity_summary.json"
    report_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
