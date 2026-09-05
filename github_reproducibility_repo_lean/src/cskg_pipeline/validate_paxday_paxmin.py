"""Validate PAXDAY summaries against minute-derived PAXMIN features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ZERO_EPSILON = 1e-50


COMPARISONS = (
    {
        "name": "total_recorded_minutes",
        "paxday_column": "PAXTMD",
        "paxmin_column": "minute_rows",
        "tolerance": 0.0,
        "description": "PAXDAY total minutes should equal the number of retained PAXMIN minute rows.",
    },
    {
        "name": "valid_minutes",
        "paxday_column": "PAXVMD",
        "paxmin_column": "valid_minute_rows",
        "tolerance": 0.0,
        "description": "PAXDAY valid minutes should equal PAXMIN rows after excluding quality-flagged minutes.",
    },
    {
        "name": "daily_total_mims",
        "paxday_column": "PAXMTSD",
        "paxmin_column": "daily_total_valid_mims_from_minutes",
        "tolerance": 0.001,
        "description": "PAXDAY daily MIMS should match the sum of non-quality-flagged PAXMIN MIMS.",
    },
    {
        "name": "wake_wear_minutes",
        "paxday_column": "PAXWWMD",
        "paxmin_column": "valid_wake_minutes",
        "tolerance": 0.0,
        "description": "PAXDAY wake wear minutes should match non-quality-flagged PAXMIN wake minutes.",
    },
    {
        "name": "sleep_wear_minutes",
        "paxday_column": "PAXSWMD",
        "paxmin_column": "valid_sleep_minutes",
        "tolerance": 0.0,
        "description": "PAXDAY sleep wear minutes should match non-quality-flagged PAXMIN sleep minutes.",
    },
    {
        "name": "nonwear_minutes",
        "paxday_column": "PAXNWMD",
        "paxmin_column": "valid_nonwear_minutes",
        "tolerance": 0.0,
        "description": "PAXDAY non-wear minutes should match non-quality-flagged PAXMIN non-wear minutes.",
    },
    {
        "name": "unknown_minutes",
        "paxday_column": "PAXUMD",
        "paxmin_column": "valid_unknown_minutes",
        "tolerance": 0.0,
        "description": "PAXDAY unknown minutes should match non-quality-flagged PAXMIN unknown minutes.",
    },
    {
        "name": "quality_flag_score_sum",
        "paxday_column": "PAXQFD",
        "paxmin_column": "quality_flag_score_sum",
        "tolerance": 0.0,
        "description": "PAXDAY quality flag score should match the sum of PAXMIN PAXQFM values.",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser.parse_args()


def _clean_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.mask(numeric.abs() < ZERO_EPSILON, 0)


def _json_number(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def build_validation_rows(pam_days: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    merged = pam_days.merge(
        features,
        left_on=["SEQN", "cycle", "PAXDAYD"],
        right_on=["SEQN", "cycle", "PAXDAYM"],
        how="outer",
        indicator=True,
        suffixes=("_paxday", "_paxmin"),
    )

    rows: list[pd.DataFrame] = []
    base_columns = ["SEQN", "cycle", "PAXDAYD", "PAXDAYM", "_merge"]
    for comparison in COMPARISONS:
        paxday_column = comparison["paxday_column"]
        paxmin_column = comparison["paxmin_column"]
        if paxday_column not in merged.columns or paxmin_column not in merged.columns:
            continue

        frame = merged[base_columns + [paxday_column, paxmin_column]].copy()
        frame["comparison"] = comparison["name"]
        frame["paxday_column"] = paxday_column
        frame["paxmin_column"] = paxmin_column
        frame["paxday_value"] = _clean_numeric(frame[paxday_column])
        frame["paxmin_value"] = _clean_numeric(frame[paxmin_column])
        frame["difference"] = frame["paxday_value"] - frame["paxmin_value"]
        frame["absolute_difference"] = frame["difference"].abs()
        frame["tolerance"] = comparison["tolerance"]
        frame["passes"] = (frame["_merge"] == "both") & (frame["absolute_difference"] <= comparison["tolerance"])
        rows.append(
            frame[
                [
                    "SEQN",
                    "cycle",
                    "PAXDAYD",
                    "PAXDAYM",
                    "_merge",
                    "comparison",
                    "paxday_column",
                    "paxmin_column",
                    "paxday_value",
                    "paxmin_value",
                    "difference",
                    "absolute_difference",
                    "tolerance",
                    "passes",
                ]
            ]
        )

    return pd.concat(rows, ignore_index=True)


def summarize(validation_rows: pd.DataFrame, pam_days: pd.DataFrame, features: pd.DataFrame) -> dict[str, Any]:
    matched_days = pam_days.merge(
        features,
        left_on=["SEQN", "cycle", "PAXDAYD"],
        right_on=["SEQN", "cycle", "PAXDAYM"],
        how="inner",
    )
    summary: dict[str, Any] = {
        "paxday_rows": int(len(pam_days)),
        "paxmin_feature_rows": int(len(features)),
        "matched_participant_days": int(len(matched_days)),
        "paxday_only_rows": int(len(pam_days) - len(matched_days)),
        "paxmin_only_rows": int(len(features) - len(matched_days)),
        "comparisons": [],
    }

    for comparison in COMPARISONS:
        subset = validation_rows.loc[validation_rows["comparison"] == comparison["name"]]
        if subset.empty:
            continue
        failed = subset.loc[~subset["passes"]]
        matched_subset = subset.loc[subset["_merge"] == "both"]
        summary["comparisons"].append(
            {
                "name": comparison["name"],
                "description": comparison["description"],
                "paxday_column": comparison["paxday_column"],
                "paxmin_column": comparison["paxmin_column"],
                "tolerance": comparison["tolerance"],
                "matched_rows": int(len(matched_subset)),
                "passed_rows": int(subset["passes"].sum()),
                "failed_rows": int(len(failed)),
                "max_absolute_difference": _json_number(matched_subset["absolute_difference"].max()),
                "mean_absolute_difference": _json_number(matched_subset["absolute_difference"].mean()),
                "p95_absolute_difference": _json_number(matched_subset["absolute_difference"].quantile(0.95)),
            }
        )

    summary["passed"] = all(item["failed_rows"] == 0 for item in summary["comparisons"])
    return summary


def main() -> None:
    args = parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    pam_days = pd.read_csv(args.processed_dir / "pam_days.csv")
    features = pd.read_csv(args.processed_dir / "pam_minute_features.csv")
    validation_rows = build_validation_rows(pam_days, features)
    summary = summarize(validation_rows, pam_days, features)

    validation_rows.to_csv(args.reports_dir / "paxday_paxmin_validation_rows.csv", index=False)
    (args.reports_dir / "paxday_paxmin_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit("PAXDAY/PAXMIN validation found mismatches. See reports/paxday_paxmin_validation_summary.json")


if __name__ == "__main__":
    main()
