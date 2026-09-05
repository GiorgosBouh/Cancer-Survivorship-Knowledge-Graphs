"""Select and document the next real accelerometry source.

This does not download multi-GB external files. It records the source decision,
why it is suitable, what files are needed, and how it will be integrated into
the semantic harmonisation evaluation.
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


SELECTED_SOURCE = {
    "source_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
    "source_name": "Minute level step counts and physical activity data from NHANES 2011-2014",
    "repository": "PhysioNet",
    "version": "1.0.2",
    "published": "2026-08-06",
    "doi": "10.13026/d7sw-f662",
    "landing_page": "https://physionet.org/content/minute-level-step-count-nhanes/1.0.2/",
    "download_root": "https://physionet.org/files/minute-level-step-count-nhanes/1.0.2/",
    "access": "open access under PhysioNet terms",
    "license": "Creative Commons Zero 1.0 Universal Public Domain Dedication",
    "size_uncompressed": "2.7 GB",
    "selection_decision": "selected_for_near_term_real_source_extension",
    "selection_reason": (
        "Real non-synthetic derived accelerometry source with step-count algorithms, "
        "ActiGraph activity counts, MIMS, wear prediction, and quality flags. It can "
        "link to the existing NHANES cohort by SEQN and day."
    ),
    "top_tier_limitation": (
        "It is not an independent external cohort; it is a real derived source from "
        "the same NHANES wrist accelerometry population. CAPTURE-24 remains the "
        "stronger external open validation candidate."
    ),
}


def build_required_files() -> pd.DataFrame:
    rows = [
        {
            "file_group": "metadata",
            "file_name": "subject-info.csv",
            "priority": "required_first",
            "purpose": "Confirm SEQN linkage and coverage against the current cancer-history cohort.",
            "expected_size": "926.3 KB",
            "integration_use": "cohort overlap and source manifest",
        },
        {
            "file_group": "documentation",
            "file_name": "data_README.md",
            "priority": "required_first",
            "purpose": "Record source-variable definitions, file layout, and version-specific notes.",
            "expected_size": "2.9 KB",
            "integration_use": "provenance and citation evidence",
        },
        {
            "file_group": "checksums",
            "file_name": "SHA256SUMS.txt",
            "priority": "required_first",
            "purpose": "Verify downloaded files and support reproducibility.",
            "expected_size": "3.0 KB",
            "integration_use": "source manifest checksums",
        },
        {
            "file_group": "activity_counts",
            "file_name": "csv/nhanes_1440_AC.csv.xz",
            "priority": "required_for_first_metric_experiment",
            "purpose": "Add ActiGraph activity counts as a real derived source variable.",
            "expected_size": "large",
            "integration_use": "daily and valid-minute activity-count summaries",
        },
        {
            "file_group": "step_counts",
            "file_name": "csv/nhanes_1440_actisteps.csv.xz",
            "priority": "required_for_first_step_experiment",
            "purpose": "Add ActiLife step-count estimates for naive-vs-semantic comparison.",
            "expected_size": "large",
            "integration_use": "daily step-count summaries",
        },
        {
            "file_group": "wear_prediction",
            "file_name": "csv/nhanes_1440_PAXPREDM.csv.xz",
            "priority": "recommended",
            "purpose": "Compare source-provided wear prediction to existing PAXMIN/PAXDAY protocol variables.",
            "expected_size": "large",
            "integration_use": "valid-day protocol compatibility checks",
        },
        {
            "file_group": "quality_flags",
            "file_name": "csv/nhanes_1440_PAXFLGSM.csv.xz",
            "priority": "recommended",
            "purpose": "Preserve data-quality context for derived metrics.",
            "expected_size": "small_to_medium",
            "integration_use": "quality/provenance safeguards",
        },
    ]
    return pd.DataFrame(rows)


def build_source_comparison() -> pd.DataFrame:
    rows = [
        {
            "candidate_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
            "decision": "selected_now",
            "is_real_source": True,
            "is_external_cohort": False,
            "access": "open",
            "linkage_to_current_cohort": "direct SEQN/day linkage",
            "primary_value": "real derived metrics: step counts, ActiGraph activity counts, Troiano wear, MIMS",
            "main_limitation": "same NHANES wrist accelerometry population",
            "next_action": "download metadata/checksums first, then selected compressed metric files",
        },
        {
            "candidate_id": "capture24",
            "decision": "external_validation_candidate",
            "is_real_source": True,
            "is_external_cohort": True,
            "access": "open large download",
            "linkage_to_current_cohort": "no participant linkage; semantic comparison only",
            "primary_value": "external free-living wrist accelerometry with activity annotations",
            "main_limitation": "not cancer-specific and large download",
            "next_action": "use after PhysioNet extension or if external-cohort validation becomes required",
        },
        {
            "candidate_id": "nci_idata_actigraph",
            "decision": "best_cancer_relevant_candidate_after_access",
            "is_real_source": True,
            "is_external_cohort": True,
            "access": "approval required",
            "linkage_to_current_cohort": "no direct linkage expected",
            "primary_value": "cancer-relevant ActiGraph epoch data",
            "main_limitation": "requires CDAS project approval and data transfer",
            "next_action": "prepare project proposal if cancer-specific external validation is required",
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


def write_document(required_files: pd.DataFrame, comparison: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Real Accelerometry Source Selection",
        "",
        "**Decision:** select PhysioNet NHANES-derived step/activity-count data version 1.0.2 as the near-term real non-synthetic source extension.",
        "",
        "This is not an NCIt task. NCIt expert review remains pending and no NCIt disease IRIs should be asserted because of this source selection.",
        "",
        "## Selected Source",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in SELECTED_SOURCE.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Why This Source",
            "",
            "The source is open, current, real, and directly linkable to the existing NHANES cancer-history cohort through `SEQN` and measurement day. It adds derived step-count and ActiGraph activity-count variables, enabling a real naive-vs-semantic harmonisation experiment without inventing a synthetic second source.",
            "",
            "It is still not the final strongest top-tier validation because it is derived from the same NHANES wrist accelerometry population. CAPTURE-24 and NCI IDATA remain external-source candidates.",
            "",
            "## Required Files",
            "",
        ]
    )
    lines.extend(markdown_table(required_files))
    lines.extend(["", "## Candidate Comparison", ""])
    lines.extend(markdown_table(comparison))
    lines.extend(
        [
            "",
            "## Integration Plan",
            "",
            "1. Download `subject-info.csv`, `data_README.md`, `SHA256SUMS.txt`, and `LICENSE.txt` first.",
            "2. Confirm overlap between PhysioNet `SEQN` values and the current cancer-history cohort.",
            "3. Download one metric file first, preferably `csv/nhanes_1440_AC.csv.xz` or `csv/nhanes_1440_actisteps.csv.xz`.",
            "4. Build daily summaries for the current cohort only to avoid unnecessary full-dataset expansion.",
            "5. Add source-variable mappings for activity counts and step-count outputs.",
            "6. Repeat naive-vs-semantic risk evaluation using this real source.",
            "",
            "## Current Status",
            "",
            f"Selection status: `{summary['selection_status']}`",
            "",
            f"Selected source id: `{summary['selected_source_id']}`",
        ]
    )
    (DOCS / "real_accelerometry_source_selection.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_outputs() -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    required_files = build_required_files()
    comparison = build_source_comparison()
    required_files.to_csv(PROCESSED / "real_source_required_files.csv", index=False)
    comparison.to_csv(PROCESSED / "real_accelerometry_source_selection.csv", index=False)

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_status": "selected_metadata_downloaded",
        "selected_source_id": SELECTED_SOURCE["source_id"],
        "selected_source_name": SELECTED_SOURCE["source_name"],
        "version": SELECTED_SOURCE["version"],
        "doi": SELECTED_SOURCE["doi"],
        "landing_page": SELECTED_SOURCE["landing_page"],
        "download_root": SELECTED_SOURCE["download_root"],
        "required_file_rows": int(required_files.shape[0]),
        "candidate_rows": int(comparison.shape[0]),
        "immediate_next_step": "metadata/checksums downloaded and verified; download one compressed metric file for cohort-overlap testing",
        "top_tier_note": SELECTED_SOURCE["top_tier_limitation"],
        "outputs": {
            "documentation": "docs/real_accelerometry_source_selection.md",
            "required_files": "data/processed/real_source_required_files.csv",
            "source_selection": "data/processed/real_accelerometry_source_selection.csv",
        },
    }
    write_document(required_files, comparison, summary)
    (REPORTS / "real_accelerometry_source_selection_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
