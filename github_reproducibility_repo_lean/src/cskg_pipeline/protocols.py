"""Candidate wear-time and valid-day protocol calculations.

These rules are implementation scaffolds for sensitivity analysis. They are not
clinical PA/MVPA/sedentary thresholds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class ValidDayProtocol:
    protocol_id: str
    label: str
    valid_day_expression: str
    min_valid_days: int
    metric: str
    unit: str
    notes: str


PROTOCOLS: tuple[ValidDayProtocol, ...] = (
    ValidDayProtocol(
        protocol_id="wake_wear_10h_min4",
        label="At least 10 hours valid wake wear on at least 4 days",
        valid_day_expression="PAXWWMD >= 600",
        min_valid_days=4,
        metric="valid wake wear minutes",
        unit="minute",
        notes="Candidate eligibility rule using PAXDAY valid wake wear minutes.",
    ),
    ValidDayProtocol(
        protocol_id="wake_wear_12h_min4",
        label="At least 12 hours valid wake wear on at least 4 days",
        valid_day_expression="PAXWWMD >= 720",
        min_valid_days=4,
        metric="valid wake wear minutes",
        unit="minute",
        notes="Sensitivity rule for stricter wake wear completeness.",
    ),
    ValidDayProtocol(
        protocol_id="valid_minutes_20h_min4",
        label="At least 20 hours valid data on at least 4 days",
        valid_day_expression="PAXVMD >= 1200",
        min_valid_days=4,
        metric="valid minutes",
        unit="minute",
        notes="Candidate 24-hour completeness rule using total valid minutes.",
    ),
)


def protocol_definitions_frame() -> pd.DataFrame:
    return pd.DataFrame([asdict(protocol) for protocol in PROTOCOLS])


def _valid_day_mask(pam_days: pd.DataFrame, protocol: ValidDayProtocol) -> pd.Series:
    if protocol.protocol_id == "wake_wear_10h_min4":
        return pam_days["PAXWWMD"] >= 600
    if protocol.protocol_id == "wake_wear_12h_min4":
        return pam_days["PAXWWMD"] >= 720
    if protocol.protocol_id == "valid_minutes_20h_min4":
        return pam_days["PAXVMD"] >= 1200
    raise ValueError(f"Unsupported protocol: {protocol.protocol_id}")


def apply_valid_day_protocols(pam_days: pd.DataFrame) -> pd.DataFrame:
    required = {"SEQN", "cycle", "PAXDAYD", "PAXWWMD", "PAXVMD", "PAXMTSD", "PAXQFD"}
    missing = sorted(required.difference(pam_days.columns))
    if missing:
        raise ValueError(f"pam_days is missing required columns: {missing}")

    outputs: list[pd.DataFrame] = []
    for protocol in PROTOCOLS:
        frame = pam_days.copy()
        frame["protocol_id"] = protocol.protocol_id
        frame["is_valid_day"] = _valid_day_mask(frame, protocol)
        frame["has_quality_flag"] = frame["PAXQFD"] > 0

        grouped = frame.groupby(["SEQN", "cycle", "protocol_id"], as_index=False).agg(
            observed_days=("PAXDAYD", "nunique"),
            valid_days=("is_valid_day", "sum"),
            valid_days_with_quality_flags=("has_quality_flag", lambda s: int((s & frame.loc[s.index, "is_valid_day"]).sum())),
            total_wake_wear_minutes=("PAXWWMD", "sum"),
            total_valid_minutes=("PAXVMD", "sum"),
            total_mims=("PAXMTSD", "sum"),
            mean_daily_mims=("PAXMTSD", "mean"),
        )
        grouped["min_valid_days"] = protocol.min_valid_days
        grouped["eligible_under_protocol"] = grouped["valid_days"] >= protocol.min_valid_days
        outputs.append(grouped)

    return pd.concat(outputs, ignore_index=True).sort_values(["cycle", "SEQN", "protocol_id"])

