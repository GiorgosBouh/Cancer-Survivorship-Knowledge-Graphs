"""Build source-code mappings for NHANES values used in the pilot KG.

The mappings in this module are intentionally conservative: they attach CDC/NHANES
source labels to observed codes and mark external ontology alignment that still
needs controlled-vocabulary review.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

DEMO_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/demo_g.htm"
DEMO_H = "https://wwwn.cdc.gov/nchs/Data/Nhanes/Public/2013/DataFiles/DEMO_H.htm"
MCQ_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/MCQ_G.htm"
MCQ_H = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/MCQ_H.htm"
PAXHD_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXHD_G.htm"
PAXDAY_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXDAY_G.htm"
PAXMIN_G = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/PAXMIN_G.htm"

FIELDNAMES = [
    "source_table",
    "source_variable",
    "code_value",
    "source_label",
    "normalized_label",
    "kg_property",
    "kg_class",
    "mapping_status",
    "external_vocabulary",
    "external_candidate_id",
    "external_candidate_label",
    "observed_count",
    "source_url",
    "notes",
]


def as_code(value: object) -> str:
    if pd.isna(value):
        return "<blank>"
    if isinstance(value, str):
        return value.strip() or "<blank>"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(value)


def counts_for_csv(path: Path, column: str) -> Counter[str]:
    if not path.exists():
        return Counter()
    series = pd.read_csv(path, usecols=[column], low_memory=False)[column]
    return Counter(as_code(value) for value in series)


def quality_score_counts(path: Path) -> Counter[str]:
    if not path.exists():
        return Counter()
    series = pd.read_csv(path, usecols=["PAXQFM"], low_memory=False)["PAXQFM"]
    counts: Counter[str] = Counter()
    for value in series:
        if pd.isna(value):
            counts["<blank>"] += 1
            continue
        numeric = float(value)
        if abs(numeric) < 1e-12:
            counts["0"] += 1
        elif numeric > 0:
            counts[">0"] += 1
    return counts


def quality_flag_letter_counts(path: Path) -> Counter[str]:
    if not path.exists():
        return Counter()
    series = pd.read_csv(path, usecols=["PAXFLGSM"], low_memory=False)["PAXFLGSM"]
    counts: Counter[str] = Counter()
    blank = 0
    for value in series:
        if pd.isna(value) or str(value).strip() == "":
            blank += 1
            continue
        for letter in sorted(set(str(value).strip())):
            counts[letter] += 1
    counts["<blank>"] = blank
    return counts


def row(
    source_table: str,
    source_variable: str,
    code_value: str,
    source_label: str,
    normalized_label: str,
    kg_property: str,
    kg_class: str,
    mapping_status: str,
    external_vocabulary: str = "",
    external_candidate_id: str = "",
    external_candidate_label: str = "",
    observed_count: int = 0,
    source_url: str = "",
    notes: str = "",
) -> dict[str, object]:
    return {
        "source_table": source_table,
        "source_variable": source_variable,
        "code_value": code_value,
        "source_label": source_label,
        "normalized_label": normalized_label,
        "kg_property": kg_property,
        "kg_class": kg_class,
        "mapping_status": mapping_status,
        "external_vocabulary": external_vocabulary,
        "external_candidate_id": external_candidate_id,
        "external_candidate_label": external_candidate_label,
        "observed_count": observed_count,
        "source_url": source_url,
        "notes": notes,
    }


def build_rows() -> list[dict[str, object]]:
    participants = PROCESSED / "participants.csv"
    diagnoses = PROCESSED / "cancer_diagnoses.csv"
    days = PROCESSED / "pam_days.csv"
    minutes = PROCESSED / "pam_minutes.csv"

    counts = {
        "RIAGENDR": counts_for_csv(participants, "RIAGENDR"),
        "RIDRETH1": counts_for_csv(participants, "RIDRETH1"),
        "RIDRETH3": counts_for_csv(participants, "RIDRETH3"),
        "MCQ220": counts_for_csv(participants, "MCQ220"),
        "PAXHAND": counts_for_csv(participants, "PAXHAND"),
        "PAXORENT": counts_for_csv(participants, "PAXORENT"),
        "cancer_type_code": counts_for_csv(diagnoses, "cancer_type_code"),
        "PAXDAYWD": counts_for_csv(days, "PAXDAYWD"),
        "PAXPREDM": counts_for_csv(minutes, "PAXPREDM"),
        "PAXQFM": quality_score_counts(minutes),
        "PAXFLGSM": quality_flag_letter_counts(minutes),
    }

    rows: list[dict[str, object]] = []

    for code_value, label in [("1", "Male"), ("2", "Female")]:
        rows.append(row("participants.csv", "RIAGENDR", code_value, label, label.lower(), "cskg:hasGenderCode", "cskg:Participant", "source label ready", observed_count=counts["RIAGENDR"][code_value], source_url=f"{DEMO_G}; {DEMO_H}"))

    ridreth1 = [
        ("1", "Mexican American"),
        ("2", "Other Hispanic"),
        ("3", "Non-Hispanic White"),
        ("4", "Non-Hispanic Black"),
        ("5", "Other Race - Including Multi-Racial"),
    ]
    for code_value, label in ridreth1:
        rows.append(row("participants.csv", "RIDRETH1", code_value, label, label, "cskg:hasRaceEthnicityCode", "cskg:Participant", "source label ready", observed_count=counts["RIDRETH1"][code_value], source_url=f"{DEMO_G}; {DEMO_H}"))

    ridreth3 = [
        ("1", "Mexican American"),
        ("2", "Other Hispanic"),
        ("3", "Non-Hispanic White"),
        ("4", "Non-Hispanic Black"),
        ("6", "Non-Hispanic Asian"),
        ("7", "Other Race - Including Multi-Racial"),
    ]
    for code_value, label in ridreth3:
        rows.append(row("participants.csv", "RIDRETH3", code_value, label, label, "cskg:hasRaceEthnicityCode", "cskg:Participant", "source label ready", observed_count=counts["RIDRETH3"][code_value], source_url=f"{DEMO_G}; {DEMO_H}"))

    for code_value, label in [("1", "Yes"), ("2", "No"), ("7", "Refused"), ("9", "Don't know")]:
        rows.append(row("participants.csv", "MCQ220", code_value, label, label.lower(), "cskg:hasCancerHistoryCode", "cskg:Participant", "source label ready", observed_count=counts["MCQ220"][code_value], source_url=f"{MCQ_G}; {MCQ_H}", notes="Cancer history is self-reported; not registry-confirmed."))

    cancer_labels = [
        ("10", "Bladder"), ("11", "Blood"), ("12", "Bone"), ("13", "Brain"),
        ("14", "Breast"), ("15", "Cervix (cervical)"), ("16", "Colon"),
        ("17", "Esophagus (esophageal)"), ("18", "Gallbladder"), ("19", "Kidney"),
        ("20", "Larynx/ windpipe"), ("21", "Leukemia"), ("22", "Liver"),
        ("23", "Lung"), ("24", "Lymphoma/ Hodgkin's disease"), ("25", "Melanoma"),
        ("26", "Mouth/tongue/lip"), ("27", "Nervous system"), ("28", "Ovary (ovarian)"),
        ("29", "Pancreas (pancreatic)"), ("30", "Prostate"), ("31", "Rectum (rectal)"),
        ("32", "Skin (non-melanoma)"), ("33", "Skin (don't know what kind)"),
        ("34", "Soft tissue (muscle or fat)"), ("35", "Stomach"),
        ("36", "Testis (testicular)"), ("37", "Thyroid"), ("38", "Uterus (uterine)"),
        ("39", "Other"), ("66", "More than 3 kinds"), ("77", "Refused"), ("99", "Don't know"),
    ]
    ambiguous_cancer_codes = {"33", "39", "66", "77", "99"}
    exact_label_candidates = {
        "21": "Leukemia",
        "24": "Lymphoma or Hodgkin disease",
        "25": "Melanoma",
    }
    for code_value, label in cancer_labels:
        normalized = label.lower().replace("/", " or ")
        ambiguous = code_value in ambiguous_cancer_codes
        status = "source label ready; needs expert/ontology review" if ambiguous else "source label ready; NCIt pending"
        ext_label = "" if ambiguous else exact_label_candidates.get(code_value, f"{label} cancer")
        notes = "NHANES source label is ambiguous and should not be mapped to a precise cancer concept without review." if ambiguous else "NHANES source label mapped; exact NCIt concept ID still requires ontology review."
        rows.append(row("cancer_diagnoses.csv", "cancer_type_code", code_value, label, normalized, "cskg:hasCancerTypeCode", "cskg:CancerDiagnosis", status, external_vocabulary="NCIt", external_candidate_label=ext_label, observed_count=counts["cancer_type_code"][code_value], source_url=f"{MCQ_G}; {MCQ_H}", notes=notes))

    for code_value, label in [("1", "Yes (non-dominant hand)"), ("2", "No (dominant hand)"), ("9", "Unknown"), ("<blank>", "Missing")]:
        rows.append(row("participants.csv", "PAXHAND", code_value, label, label, "cskg:hasDevicePlacementCode", "sosa:Sensor", "source label ready", observed_count=counts["PAXHAND"][code_value], source_url=PAXHD_G, notes="Default placement was non-dominant wrist when identifiable."))

    for code_value, label in [("1", "Dorsal"), ("2", "Palmar"), ("<blank>", "Missing")]:
        rows.append(row("participants.csv", "PAXORENT", code_value, label, label, "cskg:hasDeviceOrientationCode", "sosa:Sensor", "source label ready", observed_count=counts["PAXORENT"][code_value], source_url=PAXHD_G, notes="Surface orientation of the wrist PAM."))

    days_of_week = [("1", "Sunday"), ("2", "Monday"), ("3", "Tuesday"), ("4", "Wednesday"), ("5", "Thursday"), ("6", "Friday"), ("7", "Saturday")]
    for code_value, label in days_of_week:
        rows.append(row("pam_days.csv", "PAXDAYWD", code_value, label, label, "cskg:dayOfWeekCode", "cskg:DailyMovementSummary", "source label ready", observed_count=counts["PAXDAYWD"][code_value], source_url=PAXDAY_G))

    wear_states = [("1", "Wake wear"), ("2", "Sleep wear"), ("3", "Non wear"), ("4", "Unknown")]
    for code_value, label in wear_states:
        rows.append(row("pam_minutes.csv", "PAXPREDM", code_value, label, label, "cskg:predictedWearStateCode", "sosa:Observation", "source label ready", observed_count=counts["PAXPREDM"][code_value], source_url=PAXMIN_G, notes="Machine-learning estimated wake/sleep/non-wear state during the minute."))

    for code_value, label, note in [
        ("0", "No data quality flags occurred", "Zero-like NHANES floating values are normalized to 0 in this mapping."),
        (">0", "One or more data quality flags occurred", "Values greater than zero indicate invalid minute under QC review; this is a score, not simply invalid-minute count at day level."),
    ]:
        rows.append(row("pam_minutes.csv", "PAXQFM", code_value, label, label, "cskg:qualityFlagScore", "cskg:QualityFlagScore", "source label ready", observed_count=counts["PAXQFM"][code_value], source_url=PAXMIN_G, notes=note))

    flag_labels = [
        ("A", "Occurrence of spikes on x-axis"),
        ("B", "Occurrence of spikes on y-axis"),
        ("C", "Occurrence of spikes on z-axis"),
        ("D", "Occurrence of maximum g_values on the x-axis"),
        ("E", "Occurrence of maximum g_values on the y-axis"),
        ("F", "Occurrence of maximum g_values on the z-axis"),
        ("G", "Occurrence of minimum g_values on the x-axis"),
        ("H", "Occurrence of minimum g_values on the y-axis"),
        ("I", "Occurrence of minimum g_values on the z-axis"),
        ("J", "Occurrence of contiguous maximum g_values on the x-axis"),
        ("K", "Occurrence of contiguous maximum g_values on the y-axis"),
        ("L", "Occurrence of contiguous maximum g_values on the z-axis"),
        ("M", "Occurrence of contiguous minimum g_values on the x-axis"),
        ("N", "Occurrence of contiguous minimum g_values on the y-axis"),
        ("O", "Occurrence of contiguous minimum g_values on the z-axis"),
        ("P", "Occurrence of contiguous impossible g_values for gravity"),
        ("Q", "Occurrence of contiguous adjacent zero values on the x-, y-, or z-axis"),
        ("R", "Occurrence of contiguous adjacent identical non-zero values on the x-, y-, or z-axis"),
        ("S", "Occurrence of spikes on the x-axis in 1-second intervals"),
        ("T", "Occurrence of spikes on the y-axis in 1-second intervals"),
        ("U", "Occurrence of spikes on the z-axis in 1-second intervals"),
        ("V", "Adjacent measures to periods of invalid data"),
        ("W", "Interval jump in measurements on the x-axis"),
        ("X", "Interval jump in measurements on the y-axis"),
        ("Y", "Interval jump in measurements on the z-axis"),
        ("<blank>", "No quality flag label recorded"),
    ]
    for code_value, label in flag_labels:
        rows.append(row("pam_minutes.csv", "PAXFLGSM", code_value, label, label, "cskg:qualityFlagLabels", "cskg:QualityFlagLabelSet", "source label ready", observed_count=counts["PAXFLGSM"][code_value], source_url=PAXMIN_G, notes="PAXFLGSM can contain multiple letters in one minute; observed_count counts rows containing this letter." if code_value != "<blank>" else "Blank minutes have no quality flag label string."))

    return rows


def write_outputs(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    output = PROCESSED / "code_mappings.csv"
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    by_status = Counter(str(r["mapping_status"]) for r in rows)
    by_variable = Counter(str(r["source_variable"]) for r in rows)
    observed_rows = sum(1 for r in rows if int(r["observed_count"]) > 0)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(output.relative_to(ROOT)),
        "mapping_rows": len(rows),
        "rows_observed_in_current_processed_data": observed_rows,
        "status_counts": dict(sorted(by_status.items())),
        "variable_counts": dict(sorted(by_variable.items())),
        "sources": {
            "DEMO_G": DEMO_G,
            "DEMO_H": DEMO_H,
            "MCQ_G": MCQ_G,
            "MCQ_H": MCQ_H,
            "PAXHD_G": PAXHD_G,
            "PAXDAY_G": PAXDAY_G,
            "PAXMIN_G": PAXMIN_G,
        },
    }
    summary_path = REPORTS / "code_mapping_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    summary = write_outputs(build_rows())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
