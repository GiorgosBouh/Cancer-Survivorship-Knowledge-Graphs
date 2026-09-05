"""Build the initial NHANES cancer-survivor accelerometry cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from cskg_pipeline.nhanes_files import NhanesFile, get_file_registry
from cskg_pipeline.protocols import apply_valid_day_protocols, protocol_definitions_frame
from cskg_pipeline.quality import run_quality_checks, write_quality_report

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--include-minutes", action="store_true")
    parser.add_argument("--minute-chunksize", type=int, default=250_000)
    parser.add_argument("--refresh", action="store_true", help="Redownload source files.")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_file(source: NhanesFile, raw_dir: Path, refresh: bool = False) -> dict[str, str]:
    cycle_dir = raw_dir / source.cycle
    cycle_dir.mkdir(parents=True, exist_ok=True)
    output_path = cycle_dir / source.filename
    if refresh or not output_path.exists():
        partial_path = output_path.with_suffix(output_path.suffix + ".partial")
        LOGGER.info("Downloading %s %s from %s", source.cycle, source.component, source.url)
        urlretrieve(source.url, partial_path)
        partial_path.replace(output_path)
    checksum = sha256_file(output_path)
    return {
        "cycle": source.cycle,
        "component": source.component,
        "url": source.url,
        "path": str(output_path),
        "sha256": checksum,
    }


def read_xpt(path: Path) -> pd.DataFrame:
    LOGGER.info("Reading %s", path)
    return pd.read_sas(path, format="xport", encoding="latin1")


def load_cycle_tables(manifest_rows: list[dict[str, str]]) -> dict[str, dict[str, pd.DataFrame]]:
    tables: dict[str, dict[str, pd.DataFrame]] = {}
    for row in manifest_rows:
        cycle = row["cycle"]
        component = row["component"]
        frame = read_xpt(Path(row["path"]))
        frame["cycle"] = cycle
        tables.setdefault(cycle, {})[component] = frame
    return tables


def _first_existing_columns(frame: pd.DataFrame, prefixes: tuple[str, ...]) -> list[str]:
    return [column for column in frame.columns if column.startswith(prefixes)]


def build_participants(demo: pd.DataFrame, mcq: pd.DataFrame, paxhd: pd.DataFrame | None) -> pd.DataFrame:
    merged = demo.merge(mcq, on=["SEQN", "cycle"], how="inner", suffixes=("", "_mcq"))
    if "RIDAGEYR" in merged.columns:
        merged = merged.loc[merged["RIDAGEYR"] >= 20].copy()
    if "MCQ220" in merged.columns:
        merged = merged.loc[merged["MCQ220"] == 1].copy()

    if paxhd is not None:
        paxhd_one_row = paxhd.drop_duplicates(subset=["SEQN", "cycle"])
        merged = merged.merge(paxhd_one_row, on=["SEQN", "cycle"], how="left", suffixes=("", "_paxhd"))

    preferred = [
        "SEQN",
        "cycle",
        "RIDAGEYR",
        "RIAGENDR",
        "RIDRETH1",
        "RIDRETH3",
        "DMDEDUC2",
        "DMDMARTL",
        "INDFMPIR",
        "MCQ220",
    ]
    paxhd_columns = _first_existing_columns(merged, ("PAX",))
    ordered = [column for column in preferred + paxhd_columns if column in merged.columns]
    remaining = [column for column in merged.columns if column not in ordered]
    return merged[ordered + remaining].sort_values(["cycle", "SEQN"]).reset_index(drop=True)


def build_cancer_diagnoses(participants: pd.DataFrame) -> pd.DataFrame:
    diagnosis_columns = [column for column in participants.columns if column.startswith("MCQ230")]
    rows: list[dict[str, object]] = []
    for _, participant in participants.iterrows():
        for diagnosis_column in diagnosis_columns:
            value = participant.get(diagnosis_column)
            if pd.isna(value) or value in {77, 99}:
                continue
            suffix = diagnosis_column.replace("MCQ230", "", 1)
            age_column = f"MCQ240{suffix}"
            age_value = participant.get(age_column) if age_column in participants.columns else pd.NA
            rows.append(
                {
                    "SEQN": participant["SEQN"],
                    "cycle": participant["cycle"],
                    "diagnosis_slot": suffix or "primary",
                    "cancer_type_code": value,
                    "age_at_diagnosis": age_value,
                    "source_type_variable": diagnosis_column,
                    "source_age_variable": age_column if age_column in participants.columns else None,
                }
            )
    return pd.DataFrame(rows)


def filter_to_participants(frame: pd.DataFrame, participants: pd.DataFrame) -> pd.DataFrame:
    keys = participants[["SEQN", "cycle"]].drop_duplicates()
    return frame.merge(keys, on=["SEQN", "cycle"], how="inner")


def build_cohort_flow(
    cycle_tables: dict[str, dict[str, pd.DataFrame]],
    minute_seqn_by_cycle: dict[str, set[float]] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    stages = [
        "all_nhanes_participants",
        "age_20_or_older",
        "mcq220_cancer_history",
        "available_paxhd",
        "available_paxday",
        "available_paxmin",
    ]
    minute_seqn_by_cycle = minute_seqn_by_cycle or {}
    for cycle, tables in cycle_tables.items():
        demo = tables["DEMO"]
        mcq = tables["MCQ"]
        demo_mcq = demo.merge(mcq, on=["SEQN", "cycle"], how="inner")
        adult = demo_mcq.loc[demo_mcq["RIDAGEYR"] >= 20] if "RIDAGEYR" in demo_mcq else demo_mcq.iloc[0:0]
        cancer = adult.loc[adult["MCQ220"] == 1] if "MCQ220" in adult else adult.iloc[0:0]
        cancer_keys = set(cancer["SEQN"])
        counts = {
            "all_nhanes_participants": int(demo["SEQN"].nunique()),
            "age_20_or_older": int(adult["SEQN"].nunique()),
            "mcq220_cancer_history": int(cancer["SEQN"].nunique()),
            "available_paxhd": int(len(cancer_keys.intersection(set(tables.get("PAXHD", pd.DataFrame()).get("SEQN", []))))),
            "available_paxday": int(len(cancer_keys.intersection(set(tables.get("PAXDAY", pd.DataFrame()).get("SEQN", []))))),
            "available_paxmin": int(len(cancer_keys.intersection(minute_seqn_by_cycle.get(cycle, set()))))
            if cycle in minute_seqn_by_cycle
            else None,
        }
        for stage in stages:
            rows.append({"stage": stage, "cycle": cycle, "n": counts[stage]})

    flow = pd.DataFrame(rows)
    totals = flow.dropna(subset=["n"]).groupby("stage", as_index=False)["n"].sum()
    totals["cycle"] = "total"
    output = pd.concat([flow, totals[["stage", "cycle", "n"]]], ignore_index=True)
    output["n"] = output["n"].astype("Int64")
    return output


def filter_paxmin_to_participants(
    minute_manifest_rows: list[dict[str, str]],
    participants: pd.DataFrame,
    output_path: Path,
    chunksize: int,
) -> tuple[dict[str, set[float]], dict[str, int]]:
    if output_path.exists():
        output_path.unlink()

    minute_seqn_by_cycle: dict[str, set[float]] = {}
    row_counts: dict[str, int] = {}
    wrote_header = False

    for row in minute_manifest_rows:
        cycle = row["cycle"]
        participant_seqn = set(participants.loc[participants["cycle"] == cycle, "SEQN"])
        minute_seqn_by_cycle.setdefault(cycle, set())
        row_counts.setdefault(cycle, 0)
        LOGGER.info("Filtering %s PAXMIN in chunks of %s rows", cycle, chunksize)

        iterator = pd.read_sas(Path(row["path"]), format="xport", encoding="latin1", chunksize=chunksize)
        for chunk_index, chunk in enumerate(iterator, start=1):
            filtered = chunk.loc[chunk["SEQN"].isin(participant_seqn)].copy()
            if filtered.empty:
                continue
            filtered["cycle"] = cycle
            filtered.to_csv(output_path, mode="a", header=not wrote_header, index=False)
            wrote_header = True
            minute_seqn_by_cycle[cycle].update(filtered["SEQN"].dropna().unique())
            row_counts[cycle] += len(filtered)
            if chunk_index % 20 == 0:
                LOGGER.info("%s PAXMIN chunk %s retained rows so far: %s", cycle, chunk_index, row_counts[cycle])

    return minute_seqn_by_cycle, row_counts


def _minute_day_column(columns: pd.Index) -> str:
    if "PAXDAYM" in columns:
        return "PAXDAYM"
    if "PAXDAYD" in columns:
        return "PAXDAYD"
    raise ValueError("PAXMIN output does not contain PAXDAYM or PAXDAYD")


def build_minute_movement_features(pam_minutes_path: Path, output_path: Path) -> pd.DataFrame:
    LOGGER.info("Building minute-level movement features from %s", pam_minutes_path)
    pam_minutes = pd.read_csv(pam_minutes_path, low_memory=False)
    day_column = _minute_day_column(pam_minutes.columns)
    if "PAXMTSM" not in pam_minutes.columns:
        raise ValueError("PAXMIN output does not contain PAXMTSM")

    sort_columns = ["SEQN", "cycle", day_column]
    if "PAXSSNMP" in pam_minutes.columns:
        sort_columns.append("PAXSSNMP")
    pam_minutes = pam_minutes.sort_values(sort_columns)

    group_columns = ["SEQN", "cycle", day_column]
    pam_minutes["valid_mims_minute"] = pam_minutes["PAXMTSM"].where(pam_minutes["PAXMTSM"] > 1e-50, 0)
    if "PAXQFM" in pam_minutes.columns:
        pam_minutes["quality_flag_score"] = pam_minutes["PAXQFM"].where(pam_minutes["PAXQFM"] > 1e-50, 0)
        pam_minutes["is_quality_flagged_minute"] = pam_minutes["quality_flag_score"] > 0.5
    else:
        pam_minutes["quality_flag_score"] = 0
        pam_minutes["is_quality_flagged_minute"] = False
    pam_minutes["valid_analysis_mims_minute"] = pam_minutes["valid_mims_minute"].where(
        ~pam_minutes["is_quality_flagged_minute"], 0
    )
    pam_minutes["is_valid_analysis_minute"] = ~pam_minutes["is_quality_flagged_minute"]
    pam_minutes["rolling_30_mims"] = pam_minutes.groupby(group_columns)["valid_mims_minute"].transform(
        lambda s: s.rolling(window=30, min_periods=1).sum()
    )
    pam_minutes["rolling_30_valid_mims"] = pam_minutes.groupby(group_columns)["valid_analysis_mims_minute"].transform(
        lambda s: s.rolling(window=30, min_periods=1).sum()
    )

    aggregations = {
        "minute_rows": ("PAXMTSM", "size"),
        "valid_minute_rows": ("is_valid_analysis_minute", "sum"),
        "quality_flagged_minutes": ("is_quality_flagged_minute", "sum"),
        "quality_flag_score_sum": ("quality_flag_score", "sum"),
        "daily_total_mims_from_minutes": ("valid_mims_minute", "sum"),
        "daily_total_valid_mims_from_minutes": ("valid_analysis_mims_minute", "sum"),
        "peak_30_mims": ("rolling_30_mims", "max"),
        "peak_30_valid_mims": ("rolling_30_valid_mims", "max"),
        "mean_minute_mims": ("valid_mims_minute", "mean"),
    }
    if "PAXPREDM" in pam_minutes.columns:
        pam_minutes["is_wake_minute"] = pam_minutes["PAXPREDM"] == 1
        pam_minutes["is_sleep_minute"] = pam_minutes["PAXPREDM"] == 2
        pam_minutes["is_nonwear_minute"] = pam_minutes["PAXPREDM"] == 3
        pam_minutes["is_unknown_minute"] = pam_minutes["PAXPREDM"] == 4
        pam_minutes["is_valid_wake_minute"] = pam_minutes["is_wake_minute"] & pam_minutes["is_valid_analysis_minute"]
        pam_minutes["is_valid_sleep_minute"] = pam_minutes["is_sleep_minute"] & pam_minutes["is_valid_analysis_minute"]
        pam_minutes["is_valid_nonwear_minute"] = pam_minutes["is_nonwear_minute"] & pam_minutes["is_valid_analysis_minute"]
        pam_minutes["is_valid_unknown_minute"] = pam_minutes["is_unknown_minute"] & pam_minutes["is_valid_analysis_minute"]
        aggregations["wake_minutes"] = ("is_wake_minute", "sum")
        aggregations["sleep_minutes"] = ("is_sleep_minute", "sum")
        aggregations["nonwear_minutes"] = ("is_nonwear_minute", "sum")
        aggregations["unknown_minutes"] = ("is_unknown_minute", "sum")
        aggregations["valid_wake_minutes"] = ("is_valid_wake_minute", "sum")
        aggregations["valid_sleep_minutes"] = ("is_valid_sleep_minute", "sum")
        aggregations["valid_nonwear_minutes"] = ("is_valid_nonwear_minute", "sum")
        aggregations["valid_unknown_minutes"] = ("is_valid_unknown_minute", "sum")

    features = pam_minutes.groupby(group_columns, as_index=False).agg(**aggregations)
    features = features.rename(columns={day_column: "PAXDAYM"})
    features.to_csv(output_path, index=False)
    return features


def write_manifest(manifest_rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": manifest_rows,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(message)s")

    raw_dir = args.data_dir / "raw"
    processed_dir = args.data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    registry = get_file_registry(include_minutes=args.include_minutes)
    standard_registry = [source for source in registry if source.component != "PAXMIN"]
    minute_registry = [source for source in registry if source.component == "PAXMIN"]

    standard_manifest_rows = [download_file(source, raw_dir, refresh=args.refresh) for source in standard_registry]
    cycle_tables = load_cycle_tables(standard_manifest_rows)

    participant_frames: list[pd.DataFrame] = []
    diagnosis_frames: list[pd.DataFrame] = []
    day_frames: list[pd.DataFrame] = []

    for cycle, tables in cycle_tables.items():
        participants = build_participants(tables["DEMO"], tables["MCQ"], tables.get("PAXHD"))
        participant_frames.append(participants)
        diagnosis_frames.append(build_cancer_diagnoses(participants))
        day_frames.append(filter_to_participants(tables["PAXDAY"], participants))
        LOGGER.info("%s: retained %s adult cancer survivors", cycle, len(participants))

    participants = pd.concat(participant_frames, ignore_index=True)
    cancer_diagnoses = pd.concat(diagnosis_frames, ignore_index=True) if diagnosis_frames else pd.DataFrame()
    pam_days = pd.concat(day_frames, ignore_index=True) if day_frames else pd.DataFrame()

    minute_manifest_rows: list[dict[str, str]] = []
    minute_seqn_by_cycle: dict[str, set[float]] = {}
    minute_row_counts: dict[str, int] = {}
    pam_minute_features: pd.DataFrame | None = None
    pam_minutes_path = processed_dir / "pam_minutes.csv"
    pam_minute_features_path = processed_dir / "pam_minute_features.csv"

    if args.include_minutes:
        minute_manifest_rows = [download_file(source, raw_dir, refresh=args.refresh) for source in minute_registry]
        minute_seqn_by_cycle, minute_row_counts = filter_paxmin_to_participants(
            minute_manifest_rows,
            participants,
            pam_minutes_path,
            args.minute_chunksize,
        )
        if pam_minutes_path.exists():
            pam_minute_features = build_minute_movement_features(pam_minutes_path, pam_minute_features_path)
            LOGGER.info("Minute-level retained rows by cycle: %s", minute_row_counts)

    cohort_flow = build_cohort_flow(cycle_tables, minute_seqn_by_cycle)
    protocol_definitions = protocol_definitions_frame()
    valid_day_protocol_results = apply_valid_day_protocols(pam_days)

    participants.to_csv(processed_dir / "participants.csv", index=False)
    cancer_diagnoses.to_csv(processed_dir / "cancer_diagnoses.csv", index=False)
    pam_days.to_csv(processed_dir / "pam_days.csv", index=False)
    protocol_definitions.to_csv(processed_dir / "protocol_definitions.csv", index=False)
    valid_day_protocol_results.to_csv(processed_dir / "valid_day_protocol_results.csv", index=False)
    cohort_flow.to_csv(processed_dir / "cohort_flow.csv", index=False)
    write_manifest(standard_manifest_rows + minute_manifest_rows, processed_dir / "source_manifest.json")

    checks = run_quality_checks(participants, cancer_diagnoses, pam_days, None)
    write_quality_report(checks, args.reports_dir / "data_quality_report.json")
    if not all(check.passed for check in checks):
        raise SystemExit("One or more data-quality checks failed. See reports/data_quality_report.json")

    if pam_minute_features is not None:
        LOGGER.info("Wrote %s minute-derived daily feature rows", len(pam_minute_features))
    LOGGER.info("Wrote processed outputs to %s", processed_dir)


if __name__ == "__main__":
    main()
