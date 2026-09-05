"""Import completed expert review files for NHANES cancer-code NCIt mappings."""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
REVIEW = ROOT / "docs" / "review"
EVIDENCE = REVIEW / "evidence"
NCIT_BASE = "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#"

XLSX_SOURCE = ROOT / "expert review of cancer codes 1.xlsx"
RTF_SOURCE = ROOT / "expert review of cancer codes 2.rtf"

COMPLETED_REVIEW = REVIEW / "ncit_cancer_type_review_sheet_completed.csv"
APPROVED_MAPPING = PROCESSED / "approved_cancer_type_ncit_mapping.csv"
SUMMARY_PATH = REPORTS / "ncit_expert_review_import_summary.json"
STATUS_JSON = REPORTS / "ncit_mapping_review_status.json"
STATUS_MD = REVIEW / "ncit_mapping_review_status.md"
DOMAIN_STATUS_JSON = REPORTS / "domain_ontology_review_status.json"

XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

COMPLETED_FIELDNAMES = [
    "nhanes_code",
    "nhanes_label",
    "observed_count",
    "ncit_code",
    "ncit_preferred_label",
    "ncit_iri",
    "mapping_relation",
    "mapping_status",
    "confidence",
    "review_note",
    "review_decision",
    "approved_relation",
    "approved_ncit_code",
    "approved_ncit_label",
    "requires_clinical_note",
    "reviewer_comment",
    "reviewer_name",
    "review_date",
]

APPROVED_FIELDNAMES = [
    "source_variable",
    "nhanes_code",
    "nhanes_label",
    "observed_count",
    "review_decision",
    "approved_relation",
    "approved_ncit_code",
    "approved_ncit_label",
    "approved_ncit_iri",
    "requires_clinical_note",
    "reviewer_comment",
    "reviewer_name",
    "review_date",
    "graph_assertion_allowed",
    "assertion_kind",
    "clinical_caveat_policy",
    "assertion_status",
    "evidence_files",
]

APPROVED_DECISIONS = {"accept", "accept_with_note"}
REVIEW_RELATIONS = {"exactMatch", "closeMatch", "broadMatch"}
CLINICAL_CAVEAT_POLICY = (
    "NCIt IRIs are reviewed mappings from self-reported NHANES cancer-type codes. "
    "They are not registry-confirmed diagnoses, histology confirmations, staging, "
    "treatment, recurrence, or current disease-status assertions. The second "
    "oncologist review recommends preserving source-level site information and "
    "not inferring histology from prevalence."
)
ACKNOWLEDGEMENT_REVIEWERS = [
    {
        "name": "Christos Kazazis",
        "credentials": "MD",
        "role": "Specialist doctor in Internal Medicine and Diabetology; expert reviewer of NHANES cancer-code to NCIt mapping spreadsheet",
        "affiliation": "Department of History of Medicine and Medical Ethics, National and Kapodistrian University of Athens, Athens, Greece",
        "additional_context": "Private physician, Samos, Greece; PhD candidate, Athens Medical School",
        "contact": "chrkazazis@gmail.com",
        "source_file": "expert review of cancer codes 1.xlsx",
    },
    {
        "name": "Helena Linardou",
        "credentials": "MD PhD",
        "role": "Medical Oncologist, Director, 4th Oncology Dept. & Clinical Trials Center",
        "affiliation": "Metropolitan Hospital, Athens, Greece",
        "source_file": "expert review of cancer codes 2.rtf",
    },
]


def col_index(cell_ref: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_ref)
    if not letters:
        raise ValueError(f"Cannot parse spreadsheet cell reference: {cell_ref}")
    index = 0
    for char in letters.group(1):
        index = index * 26 + ord(char) - 64
    return index - 1


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find("a:v", XLSX_NS)
    inline = cell.find("a:is", XLSX_NS)
    if cell.attrib.get("t") == "s" and value is not None:
        return shared_strings[int(value.text or "0")]
    if cell.attrib.get("t") == "inlineStr" and inline is not None:
        return "".join(t.text or "" for t in inline.findall(".//a:t", XLSX_NS))
    return value.text if value is not None and value.text is not None else ""


def read_first_xlsx_sheet(path: Path) -> list[dict[str, str]]:
    with ZipFile(path) as xlsx:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in xlsx.namelist():
            shared_root = ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", XLSX_NS):
                shared_strings.append("".join(t.text or "" for t in item.findall(".//a:t", XLSX_NS)))

        workbook = ET.fromstring(xlsx.read("xl/workbook.xml"))
        rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pr:Relationship", REL_NS)
        }
        first_sheet = workbook.find("a:sheets/a:sheet", XLSX_NS)
        if first_sheet is None:
            raise ValueError(f"No worksheet found in {path}")
        target = rel_map[first_sheet.attrib[RID]]
        sheet_path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
        sheet = ET.fromstring(xlsx.read(sheet_path))

        rows: list[list[str]] = []
        for row in sheet.findall("a:sheetData/a:row", XLSX_NS):
            cells: dict[int, str] = {}
            max_index = -1
            for cell in row.findall("a:c", XLSX_NS):
                index = col_index(cell.attrib["r"])
                max_index = max(max_index, index)
                cells[index] = cell_value(cell, shared_strings).strip()
            if max_index < 0:
                continue
            values = [""] * (max_index + 1)
            for index, value in cells.items():
                values[index] = value
            rows.append(values)

    if not rows:
        return []
    header = rows[0]
    out: list[dict[str, str]] = []
    for row in rows[1:]:
        row = row + [""] * (len(header) - len(row))
        out.append({str(key): str(value).strip() for key, value in zip(header, row)})
    return out


def excel_serial_to_iso(value: str) -> str:
    if not value:
        return ""
    try:
        serial = float(value)
    except ValueError:
        return value
    if serial < 30000:
        return value
    date = datetime(1899, 12, 30) + timedelta(days=serial)
    return date.date().isoformat()


def normalise_completed_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    reviewer_name = next((row.get("reviewer_name", "") for row in rows if row.get("reviewer_name")), "")
    review_date = next((row.get("review_date", "") for row in rows if row.get("review_date")), "")
    review_date = excel_serial_to_iso(review_date)
    out: list[dict[str, str]] = []
    for row in rows:
        normalised = {field: row.get(field, "") for field in COMPLETED_FIELDNAMES}
        if not normalised["reviewer_name"]:
            normalised["reviewer_name"] = reviewer_name
        normalised["review_date"] = excel_serial_to_iso(normalised["review_date"]) or review_date
        out.append(normalised)
    return out


def assertion_status(row: dict[str, str]) -> tuple[str, str]:
    decision = row["review_decision"]
    relation = row["approved_relation"]
    code = row["approved_ncit_code"]
    if decision in APPROVED_DECISIONS and code and relation in REVIEW_RELATIONS:
        return "yes", "reviewed_qualified_mapping_asserted"
    if decision in {"needs_more_information", "revise"}:
        return "no", "not_asserted_needs_more_information_or_revision"
    if decision == "reject" or relation == "notMapped":
        return "no", "not_asserted_rejected_or_not_mapped"
    return "no", "not_asserted_no_completed_approval"


def build_approved_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    approved: list[dict[str, str]] = []
    evidence_files = "docs/review/evidence/expert review of cancer codes 1.xlsx; docs/review/evidence/expert review of cancer codes 2.rtf"
    for row in rows:
        allowed, status = assertion_status(row)
        code = row["approved_ncit_code"]
        iri = f"{NCIT_BASE}{code}" if code else ""
        approved.append(
            {
                "source_variable": "cancer_type_code",
                "nhanes_code": row["nhanes_code"],
                "nhanes_label": row["nhanes_label"],
                "observed_count": row["observed_count"],
                "review_decision": row["review_decision"],
                "approved_relation": row["approved_relation"],
                "approved_ncit_code": code,
                "approved_ncit_label": row["approved_ncit_label"],
                "approved_ncit_iri": iri,
                "requires_clinical_note": row["requires_clinical_note"],
                "reviewer_comment": row["reviewer_comment"],
                "reviewer_name": row["reviewer_name"],
                "review_date": row["review_date"],
                "graph_assertion_allowed": allowed,
                "assertion_kind": "qualified_mapping_from_self_reported_source_code",
                "clinical_caveat_policy": CLINICAL_CAVEAT_POLICY,
                "assertion_status": status,
                "evidence_files": evidence_files,
            }
        )
    return approved


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_domain_status() -> None:
    if not DOMAIN_STATUS_JSON.exists():
        return
    status = json.loads(DOMAIN_STATUS_JSON.read_text(encoding="utf-8"))
    status.update(
        {
            "last_checked_after_cancer_code_review_utc": datetime.now(timezone.utc).isoformat(),
            "cancer_code_review_files_received": True,
            "cancer_code_review_files": [
                "expert review of cancer codes 1.xlsx",
                "expert review of cancer codes 2.rtf",
            ],
            "does_cancer_code_review_complete_domain_ontology_review": False,
            "domain_review_note": (
                "The received files complete cancer-code/NCIt expert review. They do not answer "
                "the separate accelerometry/domain-ontology review items on source independence, "
                "metric compatibility, valid-day interpretation, or KG modeling pattern."
            ),
        }
    )
    DOMAIN_STATUS_JSON.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


def write_status(summary: dict[str, object]) -> None:
    status = {
        "status": "review_completed_qualified_assertions_allowed",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_target": "NHANES cancer_type_code to NCIt mapping",
        "draft_mapping": "data/processed/cancer_type_ncit_mapping.csv",
        "completed_review_sheet": "docs/review/ncit_cancer_type_review_sheet_completed.csv",
        "approved_mapping": "data/processed/approved_cancer_type_ncit_mapping.csv",
        "review_evidence_files": [
            "docs/review/evidence/expert review of cancer codes 1.xlsx",
            "docs/review/evidence/expert review of cancer codes 2.rtf",
        ],
        "policy": CLINICAL_CAVEAT_POLICY,
        "acknowledgement_reviewers": ACKNOWLEDGEMENT_REVIEWERS,
        "graph_assertion_policy": (
            "Rows with graph_assertion_allowed=yes may be asserted as qualified NCIt mapping metadata "
            "on self-reported NHANES cancer-type codes. They must not be interpreted as confirmed "
            "histology, registry diagnosis, stage, treatment, recurrence, or current disease status."
        ),
        "summary": summary,
        "next_action": "Regenerate pilot KG and validation reports so reviewed NCIt mapping assertions are visible.",
    }
    STATUS_JSON.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# NCIt Mapping Review Status",
        "",
        "**Status:** review completed; qualified NCIt mapping assertions allowed",
        "",
        "## Scope",
        "",
        "This status applies to NHANES `cancer_type_code` values mapped to NCI Thesaurus candidates.",
        "",
        "## Evidence Received",
        "",
        "- `docs/review/evidence/expert review of cancer codes 1.xlsx`",
        "- `docs/review/evidence/expert review of cancer codes 2.rtf`",
        "",
        "## Current Decision",
        "",
        "The review is no longer pending. Reviewed NCIt IRIs may be asserted only as qualified mapping metadata from self-reported NHANES source codes.",
        "",
        "They must not be interpreted as registry-confirmed diagnoses, histology confirmations, stage, treatment, recurrence, or current disease status.",
        "",
        "## Generated Files",
        "",
        "- `docs/review/ncit_cancer_type_review_sheet_completed.csv`",
        "- `data/processed/approved_cancer_type_ncit_mapping.csv`",
        "- `reports/ncit_expert_review_import_summary.json`",
        "",
        "## Import Summary",
        "",
        f"- Review rows: `{summary['review_rows']}`",
        f"- Graph-assertable qualified mappings: `{summary['graph_assertion_allowed_rows']}`",
        f"- Not asserted rows: `{summary['not_asserted_rows']}`",
        "",
        "## Policy",
        "",
        CLINICAL_CAVEAT_POLICY,
        "",
        "## Acknowledgement Names",
        "",
        "- Christos Kazazis, MD, specialist doctor in Internal Medicine and Diabetology, Department of History of Medicine and Medical Ethics, National and Kapodistrian University of Athens, Athens, Greece.",
        "- Helena Linardou, MD PhD, Medical Oncologist, Director, 4th Oncology Dept. & Clinical Trials Center, Metropolitan Hospital, Athens, Greece.",
    ]
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_evidence() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for source in (XLSX_SOURCE, RTF_SOURCE):
        if source.exists():
            shutil.copy2(source, EVIDENCE / source.name)


def main() -> None:
    if not XLSX_SOURCE.exists():
        raise FileNotFoundError(XLSX_SOURCE)
    if not RTF_SOURCE.exists():
        raise FileNotFoundError(RTF_SOURCE)

    copy_evidence()
    completed_rows = normalise_completed_rows(read_first_xlsx_sheet(XLSX_SOURCE))
    approved_rows = build_approved_rows(completed_rows)

    write_csv(COMPLETED_REVIEW, COMPLETED_FIELDNAMES, completed_rows)
    write_csv(APPROVED_MAPPING, APPROVED_FIELDNAMES, approved_rows)

    decision_counts = Counter(row["review_decision"] or "<blank>" for row in completed_rows)
    relation_counts = Counter(row["approved_relation"] or "<blank>" for row in completed_rows)
    assertion_counts = Counter(row["assertion_status"] for row in approved_rows)
    summary: dict[str, object] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_rows": len(completed_rows),
        "decision_counts": dict(sorted(decision_counts.items())),
        "approved_relation_counts": dict(sorted(relation_counts.items())),
        "assertion_status_counts": dict(sorted(assertion_counts.items())),
        "graph_assertion_allowed_rows": sum(row["graph_assertion_allowed"] == "yes" for row in approved_rows),
        "not_asserted_rows": sum(row["graph_assertion_allowed"] != "yes" for row in approved_rows),
        "completed_review_sheet": str(COMPLETED_REVIEW.relative_to(ROOT)),
        "approved_mapping": str(APPROVED_MAPPING.relative_to(ROOT)),
        "evidence_dir": str(EVIDENCE.relative_to(ROOT)),
        "domain_ontology_review_completed_by_these_files": False,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_status(summary)
    update_domain_status()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
