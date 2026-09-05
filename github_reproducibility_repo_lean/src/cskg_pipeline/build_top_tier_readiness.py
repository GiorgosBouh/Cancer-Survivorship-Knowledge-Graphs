"""Build top-tier submission readiness and naive-vs-semantic risk outputs.

The goal is to turn the current pilot into an explicit evaluation package:
which harmonisation claims are supported, which naive comparisons would be
unsafe, and which gaps remain before a top-tier submission.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
DOCS = ROOT / "docs"
EVALUATION = DOCS / "evaluation"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fmt(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in frame.itertuples(index=False):
        values = [fmt(value).replace("|", "/") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def build_semantic_risk_register() -> pd.DataFrame:
    mapping = pd.read_csv(PROCESSED / "harmonisation_source_variable_map.csv")
    rows: list[dict[str, object]] = []

    for construct, group in mapping.groupby("harmonised_construct"):
        for left, right in combinations(group.to_dict(orient="records"), 2):
            if left["source_id"] == right["source_id"]:
                continue
            statuses = {left["compatibility_status"], right["compatibility_status"]}
            if statuses == {"compatible after protocol abstraction"}:
                kg_decision = "allow construct-level protocol abstraction only"
                risk_level = "controlled"
                naive_risk = "low if protocol and interpretation limits are retained"
            else:
                kg_decision = "block numeric equivalence; retain source-specific metrics"
                risk_level = "high"
                naive_risk = "naive construct matching could imply invalid numeric comparability"
            rows.append(
                {
                    "risk_id": f"construct_pair_{len(rows) + 1}",
                    "risk_type": "cross_source_construct_pair",
                    "harmonised_construct": construct,
                    "left_source": left["source_id"],
                    "left_variable": left["source_variable"],
                    "left_unit": left["source_unit"],
                    "left_compatibility": left["compatibility_status"],
                    "right_source": right["source_id"],
                    "right_variable": right["source_variable"],
                    "right_unit": right["source_unit"],
                    "right_compatibility": right["compatibility_status"],
                    "naive_harmonisation_risk": naive_risk,
                    "kg_guarded_decision": kg_decision,
                    "risk_level": risk_level,
                    "interpretation_limit": f"{left['interpretation_limit']} {right['interpretation_limit']}",
                }
            )

    nhanes_constructs = set(mapping[mapping["source_id"].str.contains("nhanes")]["harmonised_construct"])
    synthetic_only = mapping[
        mapping["source_id"].str.contains("synthetic")
        & ~mapping["harmonised_construct"].isin(nhanes_constructs)
    ]
    for item in synthetic_only.to_dict(orient="records"):
        rows.append(
            {
                "risk_id": f"unsupported_claim_{len(rows) + 1}",
                "risk_type": "unsupported_back_mapping",
                "harmonised_construct": item["harmonised_construct"],
                "left_source": item["source_id"],
                "left_variable": item["source_variable"],
                "left_unit": item["source_unit"],
                "left_compatibility": item["compatibility_status"],
                "right_source": "nhanes_2011_2014_wrist_mims",
                "right_variable": "no compatible NHANES wrist MIMS variable",
                "right_unit": "not applicable",
                "right_compatibility": "not supported",
                "naive_harmonisation_risk": (
                    "naive activity-label harmonisation could back-map hip-counts intensity "
                    "classification to wrist MIMS"
                ),
                "kg_guarded_decision": "block back-mapping to NHANES wrist MIMS",
                "risk_level": "high",
                "interpretation_limit": item["interpretation_limit"],
            }
        )
    return pd.DataFrame(rows)


def build_protocol_risk_register() -> pd.DataFrame:
    pairwise = pd.read_csv(PROCESSED / "protocol_pairwise_inclusion_comparison.csv")
    rows = []
    for item in pairwise.to_dict(orient="records"):
        total = int(item["both_eligible"] + item["left_only"] + item["right_only"] + item["neither"])
        discordant = int(item["discordant_participants"])
        rows.append(
            {
                "risk_id": f"{item['left_protocol']}__vs__{item['right_protocol']}",
                "left_protocol": item["left_protocol"],
                "right_protocol": item["right_protocol"],
                "participants_evaluated": total,
                "discordant_participants": discordant,
                "discordant_percent": round(100 * discordant / total, 6) if total else None,
                "naive_harmonisation_risk": "treating valid-day protocols as interchangeable changes analytic inclusion",
                "kg_guarded_decision": "represent each protocol and query discordant eligibility explicitly",
                "risk_level": "high" if discordant else "low",
            }
        )
    return pd.DataFrame(rows)


def build_dataset_candidates() -> pd.DataFrame:
    rows = [
        {
            "candidate_id": "nhanes_2003_2006_hip_actigraph_pam",
            "source": "NHANES 2003-2006 Physical Activity Monitor PAXRAW_C/PAXRAW_D",
            "url": "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&Cycle=",
            "access_status": "open integrated",
            "why_it_matters": "Adds an independent public accelerometry cohort: different participants, survey cycles, hip-worn ActiGraph AM-7164, and 1-minute activity-count/step epochs.",
            "top_tier_use": "main independent-source semantic validation case for cross-device and cross-cohort compatibility safeguards",
            "limitation": "Still NHANES and self-reported cancer history; not an independent clinical cancer-survivorship cohort.",
            "priority": 1,
        },
        {
            "candidate_id": "physionet_nhanes_steps_activity_counts_v1_0_2",
            "source": "PhysioNet minute-level step counts and physical activity data from NHANES 2011-2014, version 1.0.2",
            "url": "https://physionet.org/content/minute-level-step-count-nhanes/1.0.2/",
            "access_status": "open",
            "why_it_matters": "Adds real algorithmic step-count and ActiGraph activity-count outputs derived from NHANES raw wrist data.",
            "top_tier_use": "near-term real derived-source extension; not a fully independent cohort",
            "limitation": "Same NHANES monitoring population, so it tests metric/algorithm harmonisation more than cross-cohort generalisation.",
            "priority": 2,
        },
        {
            "candidate_id": "capture24",
            "source": "CAPTURE-24 wrist accelerometry with activity annotations",
            "url": "https://ora.ox.ac.uk/objects/uuid:99d7c092-d865-4a19-b096-cc16440cd001",
            "access_status": "open large download",
            "why_it_matters": "Adds a real external wrist accelerometry dataset with ground-truth activity labels and MET-linked annotations.",
            "top_tier_use": "strong external semantic compatibility case for activity-label and intensity-definition modelling",
            "limitation": "Not cancer-survivorship specific and full download is large.",
            "priority": 3,
        },
        {
            "candidate_id": "nci_idata_actigraph",
            "source": "NCI IDATA ActiGraph 60-second and 10-second epoch datasets",
            "url": "https://cdas.cancer.gov/datasets/idata/140/",
            "access_status": "approval required",
            "why_it_matters": "Cancer-relevant ActiGraph epoch data with public dictionaries and controlled access to records.",
            "top_tier_use": "best fit for a cancer-focused top-tier extension if access is approved",
            "limitation": "Requires CDAS project approval and data-transfer process before experiments can be run.",
            "priority": 4,
        },
    ]
    return pd.DataFrame(rows)


def build_readiness_checklist(summary: dict[str, Any]) -> pd.DataFrame:
    independent_pam = summary.get("independent_pam_summary", {})
    pilot_kg = summary.get("pilot_kg_summary", {})
    domain_review = summary.get("domain_ontology_review_status", {})
    independent_pam_evidence = (
        f"NHANES 2003-2006 PAM integrated: participants_with_paxraw="
        f"{independent_pam.get('participants_with_paxraw_total')}; "
        f"daily_rows={independent_pam.get('daily_rows_total')}; "
        f"retained_minute_rows={independent_pam.get('retained_minute_rows_total')}; "
        f"kg_nodes={pilot_kg.get('independent_pam_daily_summaries')}"
        if independent_pam
        else "independent PAM source not yet integrated"
    )
    domain_review_evidence = (
        f"review packet prepared: items={domain_review.get('review_items')}; "
        f"status={domain_review.get('status')}"
        if domain_review
        else "external review packet not prepared"
    )
    ncit_status = str(summary.get("ncit_review_status") or "")
    ncit_complete = ncit_status == "review_completed_qualified_assertions_allowed"
    ncit_evidence = (
        f"NCIt review status={summary['ncit_review_status']}; "
        f"assertion_count={summary['ncit_assertion_count']}"
    )
    ncit_action = (
        "use reviewed mappings only as qualified self-report code mappings; keep clinical caveats visible"
        if ncit_complete
        else "obtain completed expert review sheet before asserting NCIt IRIs"
    )
    rows = [
        {
            "criterion": "Reproducible NHANES data foundation",
            "status": "complete",
            "evidence": "cohort, day, minute, feature, protocol, manifest, and quality artifacts exist",
            "top_tier_action": "keep one-command rebuild documented",
        },
        {
            "criterion": "Standards-compliant KG validation",
            "status": "complete",
            "evidence": f"pySHACL conforms={summary['pyshacl_conforms']}; failed_policy_checks={summary['failed_policy_checks']}",
            "top_tier_action": "use --require-pyshacl as mandatory validation gate",
        },
        {
            "criterion": "Protocol sensitivity evaluation",
            "status": "complete",
            "evidence": "protocol-discordance risk register quantifies participant inclusion changes",
            "top_tier_action": "make protocol discordance a main result",
        },
        {
            "criterion": "Naive-vs-semantic harmonisation evaluation",
            "status": "complete",
            "evidence": "semantic risk registers and competency queries now cover synthetic, PhysioNet, and independent PAM sources; CQ9 exposes PAM source safeguards",
            "top_tier_action": "keep interpretation limits prominent in manuscript tables and figures",
        },
        {
            "criterion": "Second real accelerometry data source",
            "status": "complete",
            "evidence": "PhysioNet v1.0.2 ActiLife steps integrated for 878 participants as a real derived same-cohort source",
            "top_tier_action": "keep wording precise: real derived same-cohort source, not independent validation",
        },
        {
            "criterion": "Independent public accelerometry source",
            "status": "complete" if independent_pam else "not_started",
            "evidence": independent_pam_evidence,
            "top_tier_action": "use as the main independent-source harmonisation validation; do not claim independent clinical survivorship cohort",
        },
        {
            "criterion": "NCIt cancer-type expert review",
            "status": "complete_with_caveat" if ncit_complete else "blocking_gap",
            "evidence": ncit_evidence,
            "top_tier_action": ncit_action,
        },
        {
            "criterion": "External ontology/domain expert review",
            "status": "prepared_pending_review" if domain_review else "not_started",
            "evidence": domain_review_evidence,
            "top_tier_action": "obtain completed external reviewer decisions before claiming independent expert approval",
        },
        {
            "criterion": "Public reproducibility archive",
            "status": "prepared_pending_deposit",
            "evidence": "reproducibility archive plan generated; no DOI/archive deposit yet",
            "top_tier_action": "prepare Zenodo/OSF archive with code, generated non-sensitive outputs, and environment lock",
        },
        {
            "criterion": "Reporting checklists",
            "status": "partial_complete",
            "evidence": "STROBE-style and FAIR/resource checklist draft generated",
            "top_tier_action": "complete target-journal-specific reporting checklist during manuscript finalization",
        },
        {
            "criterion": "Journal-specific manuscript package",
            "status": "partial_complete",
            "evidence": "manuscript tables and figure inputs generated",
            "top_tier_action": "create target-journal cover story and final figures",
        },
    ]
    return pd.DataFrame(rows)


def write_outputs(
    semantic_risks: pd.DataFrame,
    protocol_risks: pd.DataFrame,
    dataset_candidates: pd.DataFrame,
    readiness: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    EVALUATION.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Naive vs Semantic Harmonisation Evaluation",
        "",
        "**Purpose:** show what a naive harmonisation would incorrectly permit and how the KG blocks or qualifies those claims.",
        "",
        "## Main Finding",
        "",
        "The current KG does not merely store activity variables. It records whether variables and definitions are compatible, source-specific, or not harmonisable with NHANES wrist MIMS. This turns hidden preprocessing and definition choices into queryable validation evidence.",
        "",
        "## Semantic Harmonisation Risk Register",
        "",
    ]
    lines.extend(markdown_table(semantic_risks))
    lines.extend(["", "## Protocol Discordance Risk Register", ""])
    lines.extend(markdown_table(protocol_risks))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A naive workflow could match variables by broad labels such as movement volume, MVPA, sedentary time, or valid wear. The KG-guarded workflow allows only reviewed construct-level abstraction and blocks numeric equivalence or back-mapping where source metrics are incompatible.",
        ]
    )
    (EVALUATION / "naive_vs_semantic_harmonisation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    plan_lines = [
        "# Top-Tier Submission Plan",
        "",
        "**Target contribution:** semantic validation framework for preventing invalid harmonisation of accelerometry-derived physical-activity definitions in cancer-survivorship research.",
        "",
        "## Recommended Scope",
        "",
        "Do not frame the paper as a completed cancer-survivorship KG. Frame it as a reproducible semantic validation and compatibility-checking framework, with NHANES cancer-history accelerometry as the primary use case.",
        "",
        "## Dataset Strategy",
        "",
    ]
    plan_lines.extend(markdown_table(dataset_candidates))
    plan_lines.extend(["", "## Readiness Checklist", ""])
    plan_lines.extend(markdown_table(readiness))
    plan_lines.extend(
        [
            "",
            "## Blocking Items Before Top-Tier Submission",
            "",
            "1. Keep reviewed NCIt mappings qualified as self-reported source-code mappings, not confirmed disease diagnoses.",
            "2. Obtain completed independent domain/ontology review of compatibility statuses and interpretation limits.",
            "3. Archive code and generated reusable artifacts with a DOI.",
            "4. Complete target-journal reporting checklist and final figure drafts.",
            "",
            "## Near-Term Experiment Order",
            "",
            "1. Use CQ9 and the IndependentPAMDailySummary SHACL shape as the KG-level evidence for the independent public accelerometry source.",
            "2. Report PhysioNet ActiLife steps as a real same-cohort derived metric source, not as independent validation.",
            "3. Send `docs/review/domain_ontology_review_sheet.csv` for external domain/ontology review.",
            "4. Deposit the reproducibility package and complete journal-specific figures/checklists.",
        ]
    )
    (DOCS / "top_tier_submission_plan.md").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    semantic_risks.to_csv(PROCESSED / "semantic_harmonisation_risk_register.csv", index=False)
    protocol_risks.to_csv(PROCESSED / "protocol_discordance_risk_register.csv", index=False)
    dataset_candidates.to_csv(PROCESSED / "top_tier_dataset_candidates.csv", index=False)
    readiness.to_csv(PROCESSED / "top_tier_readiness_checklist.csv", index=False)
    (REPORTS / "top_tier_readiness_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


def build_outputs() -> dict[str, Any]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    EVALUATION.mkdir(parents=True, exist_ok=True)

    validation = read_json(REPORTS / "pilot_kg_shacl_validation_summary.json")
    independent_pam_summary = (
        read_json(REPORTS / "independent_nhanes_pam_summary.json")
        if (REPORTS / "independent_nhanes_pam_summary.json").exists()
        else {}
    )
    pilot_kg_summary = (
        read_json(REPORTS / "pilot_kg_summary.json")
        if (REPORTS / "pilot_kg_summary.json").exists()
        else {}
    )
    domain_ontology_review_status = (
        read_json(REPORTS / "domain_ontology_review_status.json")
        if (REPORTS / "domain_ontology_review_status.json").exists()
        else {}
    )
    ncit_guard = next(
        (item for item in validation.get("policy_checks", []) if item.get("guard") == "NCItReviewPendingGuard"),
        {},
    )
    semantic_risks = build_semantic_risk_register()
    protocol_risks = build_protocol_risk_register()
    dataset_candidates = build_dataset_candidates()

    partial_summary = {
        "pyshacl_conforms": validation.get("standard_shacl", {}).get("conforms"),
        "failed_checks": validation.get("failed_checks"),
        "failed_policy_checks": validation.get("failed_policy_checks"),
        "ncit_review_status": ncit_guard.get("status"),
        "ncit_assertion_count": ncit_guard.get("assertion_count"),
        "independent_pam_summary": independent_pam_summary,
        "pilot_kg_summary": pilot_kg_summary,
        "domain_ontology_review_status": domain_ontology_review_status,
    }
    readiness = build_readiness_checklist(partial_summary)
    readiness_counts = readiness["status"].value_counts().to_dict()
    top_tier_status = (
        "not_ready_blocking_gaps_remain"
        if readiness_counts.get("blocking_gap", 0)
        else "not_ready_pending_external_review_and_archive"
    )
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "top_tier_status": top_tier_status,
        "documentation": {
            "top_tier_submission_plan": "docs/top_tier_submission_plan.md",
            "naive_vs_semantic_evaluation": "docs/evaluation/naive_vs_semantic_harmonisation.md",
        },
        "outputs": {
            "semantic_harmonisation_risk_register": "data/processed/semantic_harmonisation_risk_register.csv",
            "protocol_discordance_risk_register": "data/processed/protocol_discordance_risk_register.csv",
            "dataset_candidates": "data/processed/top_tier_dataset_candidates.csv",
            "readiness_checklist": "data/processed/top_tier_readiness_checklist.csv",
            "independent_pam_summary": "reports/independent_nhanes_pam_summary.json"
            if independent_pam_summary
            else None,
            "domain_ontology_review_status": "reports/domain_ontology_review_status.json"
            if domain_ontology_review_status
            else None,
            "reproducibility_archive_plan": "docs/reproducibility_archive_plan.md",
            "reporting_checklists": "docs/reporting_checklists.md",
        },
        "semantic_risk_rows": int(semantic_risks.shape[0]),
        "high_semantic_risk_rows": int(semantic_risks["risk_level"].eq("high").sum()),
        "protocol_risk_rows": int(protocol_risks.shape[0]),
        "max_protocol_discordant_percent": float(protocol_risks["discordant_percent"].max()),
        "readiness_counts": readiness_counts,
        **partial_summary,
    }
    write_outputs(semantic_risks, protocol_risks, dataset_candidates, readiness, summary)
    return summary


def main() -> None:
    print(json.dumps(build_outputs(), indent=2))


if __name__ == "__main__":
    main()
