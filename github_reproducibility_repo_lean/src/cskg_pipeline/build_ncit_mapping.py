"""Build a conservative draft mapping from NHANES cancer type codes to NCIt.

This produces review artifacts only. The output is not used as final graph
assertions until a domain/ontology review accepts the proposed mappings.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
NCIT_BASE = "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#"
EVS_API = "https://api-evsrest.nci.nih.gov/api/v1/concept/ncit"

FIELDNAMES = [
    "source_variable",
    "nhanes_code",
    "nhanes_label",
    "observed_count",
    "ncit_code",
    "ncit_preferred_label",
    "ncit_iri",
    "mapping_relation",
    "mapping_status",
    "confidence",
    "evs_search_term",
    "review_note",
]

# Candidate NCIt mappings confirmed from NCI EVS REST API search results during
# draft creation. Conservative statuses are used where NHANES labels are broad.
CANDIDATES = {
    "10": ("C9334", "Malignant Bladder Neoplasm", "broadMatch", "draft_candidate", "medium", "Bladder cancer", "EVS search also returned Bladder Carcinoma C4912; malignant neoplasm is broader and better matches unknown histology."),
    "12": ("C4016", "Malignant Bone Neoplasm", "broadMatch", "draft_candidate", "medium", "Bone cancer", "Broad anatomic cancer label; histology unknown."),
    "13": ("C3568", "Malignant Brain Neoplasm", "broadMatch", "draft_candidate", "medium", "Brain cancer", "Broad anatomic cancer label; histology unknown."),
    "14": ("C4872", "Breast Carcinoma", "closeMatch", "draft_candidate", "high", "Breast cancer", "EVS phrase search returned Breast Carcinoma C4872 and Malignant Breast Neoplasm C9335; carcinoma is common but still needs review."),
    "15": ("C9039", "Cervical Carcinoma", "closeMatch", "draft_candidate", "high", "Cervical carcinoma", "NHANES label is cervix/cervical; candidate is carcinoma-level."),
    "16": ("C4910", "Colon Carcinoma", "closeMatch", "draft_candidate", "high", "Colon carcinoma", "Candidate returned by EVS phrase search."),
    "17": ("C3513", "Esophageal Carcinoma", "closeMatch", "draft_candidate", "high", "Esophageal carcinoma", "Candidate returned by EVS phrase search."),
    "18": ("C3844", "Gallbladder Carcinoma", "closeMatch", "draft_candidate", "high", "Gallbladder carcinoma", "Candidate returned by EVS phrase search; not observed in current cohort."),
    "19": ("C9384", "Kidney Carcinoma", "closeMatch", "draft_candidate", "high", "Kidney carcinoma", "Candidate returned by EVS phrase search."),
    "20": ("C4855", "Laryngeal Carcinoma", "closeMatch", "draft_candidate", "medium", "Laryngeal carcinoma", "NHANES label includes larynx/windpipe; laryngeal candidate needs review for windpipe/trachea ambiguity."),
    "21": ("C3161", "Leukemia", "exactMatch", "draft_candidate", "high", "Leukemia", "Candidate returned by EVS phrase search."),
    "22": ("C7927", "Liver Carcinoma", "closeMatch", "draft_candidate", "high", "Liver carcinoma", "Candidate returned by EVS phrase search."),
    "23": ("C4878", "Lung Carcinoma", "closeMatch", "draft_candidate", "high", "Lung carcinoma", "Candidate returned by EVS phrase search."),
    "24": ("C3208", "Lymphoma", "broadMatch", "draft_candidate", "medium", "Lymphoma", "NHANES label combines lymphoma/Hodgkin disease; broad lymphoma candidate needs review."),
    "25": ("C3224", "Melanoma", "exactMatch", "draft_candidate", "high", "Melanoma", "Candidate returned by EVS phrase search."),
    "26": ("C8990", "Oral Cavity Carcinoma", "broadMatch", "draft_candidate", "medium", "Oral cavity carcinoma", "NHANES label mouth/tongue/lip is broader than oral cavity carcinoma; needs review."),
    "28": ("C4908", "Ovarian Carcinoma", "closeMatch", "draft_candidate", "high", "Ovarian carcinoma", "Candidate returned by EVS phrase search."),
    "29": ("C207229", "Pancreatic Carcinoma", "closeMatch", "draft_candidate", "high", "Pancreatic carcinoma", "Candidate returned by EVS phrase search."),
    "30": ("C4863", "Prostate Carcinoma", "closeMatch", "draft_candidate", "high", "Prostate cancer", "EVS phrase search returned Prostate Carcinoma C4863."),
    "31": ("C9382", "Rectal Carcinoma", "closeMatch", "draft_candidate", "high", "Rectal carcinoma", "Candidate returned by EVS phrase search."),
    "34": ("C9306", "Soft Tissue Sarcoma", "broadMatch", "draft_candidate", "medium", "Soft tissue sarcoma", "NHANES label is soft tissue muscle/fat; sarcoma candidate likely but needs review."),
    "35": ("C4911", "Gastric Carcinoma", "closeMatch", "draft_candidate", "high", "Stomach carcinoma", "EVS phrase search returned Gastric Carcinoma C4911."),
    "37": ("C4815", "Thyroid Gland Carcinoma", "closeMatch", "draft_candidate", "high", "Thyroid carcinoma", "EVS phrase search returned Thyroid Gland Carcinoma C4815."),
    "38": ("C3552", "Malignant Uterine Neoplasm", "broadMatch", "draft_candidate", "medium", "Uterine cancer", "EVS search returned Malignant Uterine Neoplasm C3552; broad anatomic label."),
}

UNMAPPED_NOTES = {
    "11": ("manual_review_needed", "low", "Blood cancer", "NHANES label is broad. EVS returned Liquid Tumor C116915, but this is too broad to assert without review."),
    "27": ("manual_review_needed", "low", "Nervous system cancer", "Broad site/system label; needs EVS/manual review."),
    "32": ("manual_review_needed", "low", "Non-melanoma skin cancer", "Needs review: source label says non-melanoma skin, but exact NCIt concept should be selected carefully."),
    "33": ("not_mapped", "none", "Skin cancer unknown kind", "Ambiguous NHANES category; do not map to a precise cancer concept."),
    "36": ("manual_review_needed", "low", "Testicular cancer", "EVS phrase search did not return a clean general testicular carcinoma/neoplasm candidate in the first results."),
    "39": ("not_mapped", "none", "Other cancer", "Ambiguous NHANES category; do not map to a precise cancer concept."),
    "66": ("not_mapped", "none", "More than 3 kinds", "Aggregate response category; not a disease concept."),
    "77": ("not_mapped", "none", "Refused", "Response status, not a disease concept."),
    "99": ("not_mapped", "none", "Don't know", "Response status, not a disease concept."),
}


def build_rows() -> list[dict[str, object]]:
    code_mappings = pd.read_csv(PROCESSED / "code_mappings.csv")
    cancers = code_mappings[code_mappings["source_variable"].eq("cancer_type_code")].copy()
    rows = []
    for row in cancers.sort_values("code_value").itertuples(index=False):
        code = str(int(float(row.code_value)))
        label = str(row.source_label)
        observed_count = int(row.observed_count)
        if code in CANDIDATES:
            ncit_code, ncit_label, relation, status, confidence, search_term, note = CANDIDATES[code]
            iri = f"{NCIT_BASE}{ncit_code}"
        else:
            status, confidence, search_term, note = UNMAPPED_NOTES.get(
                code,
                ("manual_review_needed", "low", f"{label} cancer", "No draft mapping provided yet."),
            )
            ncit_code = ""
            ncit_label = ""
            iri = ""
            relation = "notMapped" if status == "not_mapped" else "reviewNeeded"
        rows.append(
            {
                "source_variable": "cancer_type_code",
                "nhanes_code": code,
                "nhanes_label": label,
                "observed_count": observed_count,
                "ncit_code": ncit_code,
                "ncit_preferred_label": ncit_label,
                "ncit_iri": iri,
                "mapping_relation": relation,
                "mapping_status": status,
                "confidence": confidence,
                "evs_search_term": search_term,
                "review_note": note,
            }
        )
    return rows


def write_outputs(rows: list[dict[str, object]]) -> dict[str, object]:
    out = PROCESSED / "cancer_type_ncit_mapping.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(str(r["mapping_status"]) for r in rows)
    relation_counts = Counter(str(r["mapping_relation"]) for r in rows)
    confidence_counts = Counter(str(r["confidence"]) for r in rows)
    observed_with_candidate = sum(1 for r in rows if int(r["observed_count"]) > 0 and r["ncit_code"])
    observed_without_candidate = sum(1 for r in rows if int(r["observed_count"]) > 0 and not r["ncit_code"])
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(out.relative_to(ROOT)),
        "mapping_rows": len(rows),
        "rows_with_ncit_candidate": sum(1 for r in rows if r["ncit_code"]),
        "rows_without_ncit_candidate": sum(1 for r in rows if not r["ncit_code"]),
        "observed_rows_with_ncit_candidate": observed_with_candidate,
        "observed_rows_without_ncit_candidate": observed_without_candidate,
        "status_counts": dict(sorted(status_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "evs_api": EVS_API,
        "note": "Draft review artifact only; NCIt IRIs are not yet asserted in the RDF graph.",
    }
    summary_path = REPORTS / "cancer_type_ncit_mapping_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    rows = build_rows()
    print(json.dumps(write_outputs(rows), indent=2))


if __name__ == "__main__":
    main()
