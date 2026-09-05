"""Data-quality checks for generated cohort tables."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    details: dict[str, Any]


def _missing_columns(frame: pd.DataFrame, columns: set[str]) -> list[str]:
    return sorted(columns.difference(frame.columns))


def run_quality_checks(
    participants: pd.DataFrame,
    cancer_diagnoses: pd.DataFrame,
    pam_days: pd.DataFrame,
    pam_minutes: pd.DataFrame | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []

    missing_participant_columns = _missing_columns(participants, {"SEQN", "cycle"})
    checks.append(
        CheckResult(
            "participants_required_columns",
            not missing_participant_columns,
            {"missing_columns": missing_participant_columns},
        )
    )

    duplicate_seqn = int(participants["SEQN"].duplicated().sum()) if "SEQN" in participants else -1
    checks.append(
        CheckResult(
            "participants_unique_seqn",
            duplicate_seqn == 0,
            {"duplicate_seqn_rows": duplicate_seqn},
        )
    )

    participant_seqn = set(participants["SEQN"]) if "SEQN" in participants else set()
    for name, frame in (("cancer_diagnoses", cancer_diagnoses), ("pam_days", pam_days)):
        missing_seqn = _missing_columns(frame, {"SEQN"})
        orphan_rows = 0
        if "SEQN" in frame:
            orphan_rows = int((~frame["SEQN"].isin(participant_seqn)).sum())
        checks.append(
            CheckResult(
                f"{name}_referential_integrity",
                not missing_seqn and orphan_rows == 0,
                {"missing_columns": missing_seqn, "orphan_rows": orphan_rows},
            )
        )

    if pam_minutes is not None:
        missing_seqn = _missing_columns(pam_minutes, {"SEQN"})
        orphan_rows = 0
        if "SEQN" in pam_minutes:
            orphan_rows = int((~pam_minutes["SEQN"].isin(participant_seqn)).sum())
        checks.append(
            CheckResult(
                "pam_minutes_referential_integrity",
                not missing_seqn and orphan_rows == 0,
                {"missing_columns": missing_seqn, "orphan_rows": orphan_rows},
            )
        )

    return checks


def write_quality_report(checks: list[CheckResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "passed": all(check.passed for check in checks),
        "checks": [
            {"name": check.name, "passed": check.passed, "details": check.details}
            for check in checks
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

