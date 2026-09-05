"""Build a small pilot RDF/Turtle graph from the processed NHANES data layer."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

BASE_RESOURCE = "https://w3id.org/cskg/resource/"
BASE_ONTOLOGY = "https://w3id.org/cskg/ontology/"
PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dct": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "sosa": "http://www.w3.org/ns/sosa/",
    "time": "http://www.w3.org/2006/time#",
    "qudt": "http://qudt.org/schema/qudt/",
    "cskg": BASE_ONTOLOGY,
    "res": BASE_RESOURCE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/pilot_kg.ttl"))
    parser.add_argument("--participants", type=int, default=20)
    parser.add_argument("--max-days", type=int, default=3)
    parser.add_argument("--max-minutes-per-day", type=int, default=5)
    parser.add_argument("--max-independent-pam-days", type=int, default=20)
    parser.add_argument(
        "--approved-ncit-mapping",
        type=Path,
        default=Path("data/processed/approved_cancer_type_ncit_mapping.csv"),
    )
    return parser.parse_args()


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass
    return False


def slug(value: Any) -> str:
    text = str(value)
    text = re.sub(r"\.0$", "", text)
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")
    return text or "unknown"


def iri(local: str) -> str:
    safe_local = str(local).replace(" ", "%20")
    return f"<{BASE_RESOURCE}{safe_local}>"


def literal(value: Any, datatype: str | None = None) -> str:
    if is_missing(value):
        raise ValueError("Cannot serialize missing literal")
    if isinstance(value, bool):
        return f'"{str(value).lower()}"^^xsd:boolean'
    if isinstance(value, float) and abs(value) < 1e-50:
        value = 0.0
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer() and not math.isnan(value)):
        if datatype is None:
            datatype = "xsd:integer"
        return f'"{int(value)}"^^{datatype}'
    if isinstance(value, float):
        if datatype is None:
            datatype = "xsd:decimal"
        return f'"{value:.12g}"^^{datatype}'
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"' + (f"^^{datatype}" if datatype else "")


def add(triples: list[str], subject: str, predicate: str, obj: str) -> None:
    triples.append(f"{subject} {predicate} {obj} .")


def add_literal(triples: list[str], subject: str, predicate: str, value: Any, datatype: str | None = None) -> None:
    if not is_missing(value):
        add(triples, subject, predicate, literal(value, datatype))


def participant_uri(cycle: Any, seqn: Any) -> str:
    return iri(f"participant/{slug(cycle)}/{slug(seqn)}")


def sensor_uri(cycle: Any, seqn: Any, sensor_id: Any) -> str:
    sid = slug(sensor_id) if not is_missing(sensor_id) else "unknown-sensor"
    return iri(f"sensor/{slug(cycle)}/{slug(seqn)}/{sid}")


def day_uri(cycle: Any, seqn: Any, day: Any) -> str:
    return iri(f"pam-day/{slug(cycle)}/{slug(seqn)}/{slug(day)}")


def feature_uri(cycle: Any, seqn: Any, day: Any) -> str:
    return iri(f"feature-set/{slug(cycle)}/{slug(seqn)}/{slug(day)}")


def diagnosis_uri(cycle: Any, seqn: Any, slot: Any) -> str:
    return iri(f"cancer-diagnosis/{slug(cycle)}/{slug(seqn)}/{slug(slot)}")


def cancer_history_uri(cycle: Any, seqn: Any) -> str:
    return iri(f"cancer-history-assertion/{slug(cycle)}/{slug(seqn)}/MCQ220")


def protocol_uri(protocol_id: Any) -> str:
    return iri(f"protocol/{slug(protocol_id)}")


def protocol_citation_uri(protocol_id: Any, citation_id: Any) -> str:
    return iri(f"protocol-citation/{slug(protocol_id)}/{slug(citation_id)}")


def protocol_result_uri(cycle: Any, seqn: Any, protocol_id: Any) -> str:
    return iri(f"protocol-result/{slug(cycle)}/{slug(seqn)}/{slug(protocol_id)}")


def minute_uri(cycle: Any, seqn: Any, day: Any, second_marker: Any) -> str:
    return iri(f"pam-minute/{slug(cycle)}/{slug(seqn)}/{slug(day)}/{slug(second_marker)}")


def source_table_uri(table_name: str) -> str:
    return iri(f"source-table/{slug(table_name)}")


def activity_source_uri(source_id: Any) -> str:
    return iri(f"activity-source/{slug(source_id)}")


def harmonisation_mapping_uri(source_id: Any, source_variable: Any) -> str:
    return iri(f"harmonisation-mapping/{slug(source_id)}/{slug(source_variable)}")


def harmonised_definition_uri(definition_id: Any) -> str:
    return iri(f"harmonised-definition/{slug(definition_id)}")


def synthetic_day_uri(cycle: Any, seqn: Any, day: Any) -> str:
    return iri(f"synthetic-activity-day/{slug(cycle)}/{slug(seqn)}/{slug(day)}")


def independent_pam_day_uri(cycle: Any, seqn: Any, day: Any) -> str:
    return iri(f"independent-pam-day/{slug(cycle)}/{slug(seqn)}/{slug(day)}")


def synthetic_protocol_result_uri(cycle: Any, seqn: Any, protocol_id: Any) -> str:
    return iri(f"synthetic-protocol-result/{slug(cycle)}/{slug(seqn)}/{slug(protocol_id)}")


def code_value(value: Any, source_variable: str | None = None) -> str:
    if is_missing(value):
        return "<blank>"
    if source_variable == "PAXQFM":
        numeric = float(value)
        return "0" if abs(numeric) < 1e-12 else ">0"
    if isinstance(value, str):
        return value.strip() or "<blank>"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(value)


def load_code_mappings(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    mappings = pd.read_csv(path, dtype=str).fillna("")
    return {
        (str(row.source_variable), str(row.code_value)): row._asdict()
        for row in mappings.itertuples(index=False)
    }


def mapping_row(mappings: dict[tuple[str, str], dict[str, str]], source_variable: str, value: Any) -> dict[str, str] | None:
    return mappings.get((source_variable, code_value(value, source_variable)))


def mapping_label(mappings: dict[tuple[str, str], dict[str, str]], source_variable: str, value: Any) -> str | None:
    row = mapping_row(mappings, source_variable, value)
    if not row:
        return None
    return row.get("source_label") or None


def add_mapping_label(
    triples: list[str],
    subject: str,
    predicate: str,
    mappings: dict[tuple[str, str], dict[str, str]],
    source_variable: str,
    value: Any,
) -> None:
    label = mapping_label(mappings, source_variable, value)
    if label:
        add_literal(triples, subject, predicate, label)


def add_cancer_mapping_metadata(
    triples: list[str],
    subject: str,
    mappings: dict[tuple[str, str], dict[str, str]],
    value: Any,
) -> None:
    row = mapping_row(mappings, "cancer_type_code", value)
    if not row:
        return
    for predicate, column in [
        ("cskg:cancerTypeLabel", "source_label"),
        ("cskg:cancerTypeMappingStatus", "mapping_status"),
        ("cskg:cancerTypeExternalVocabulary", "external_vocabulary"),
        ("cskg:cancerTypeExternalCandidateLabel", "external_candidate_label"),
    ]:
        value = row.get(column)
        if value:
            add_literal(triples, subject, predicate, value)


def load_approved_ncit_mappings(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows = pd.read_csv(path, dtype=str).fillna("")
    return {
        str(row.nhanes_code): row._asdict()
        for row in rows.itertuples(index=False)
        if str(row.graph_assertion_allowed).lower() == "yes"
    }


def add_reviewed_ncit_mapping(
    triples: list[str],
    subject: str,
    reviewed_mappings: dict[str, dict[str, str]],
    value: Any,
) -> bool:
    row = reviewed_mappings.get(code_value(value))
    if not row:
        return False
    ncit_iri = row.get("approved_ncit_iri")
    if ncit_iri:
        add(triples, subject, "cskg:reviewedNCItConcept", f"<{ncit_iri}>")
    for predicate, column in [
        ("cskg:reviewedNCItCode", "approved_ncit_code"),
        ("cskg:reviewedNCItLabel", "approved_ncit_label"),
        ("cskg:ncitMappingRelation", "approved_relation"),
        ("cskg:ncitReviewDecision", "review_decision"),
        ("cskg:ncitClinicalNoteRequired", "requires_clinical_note"),
        ("cskg:ncitReviewerComment", "reviewer_comment"),
        ("cskg:ncitMappingInterpretationLimit", "clinical_caveat_policy"),
    ]:
        item = row.get(column)
        if item:
            add_literal(triples, subject, predicate, item)
    return bool(ncit_iri)


def add_quality_flag_label_descriptions(
    triples: list[str],
    subject: str,
    mappings: dict[tuple[str, str], dict[str, str]],
    labels: Any,
) -> None:
    if is_missing(labels):
        label = mapping_label(mappings, "PAXFLGSM", "<blank>")
        if label:
            add_literal(triples, subject, "cskg:qualityFlagLabelDescription", label)
        return
    for letter in sorted(set(str(labels).strip())):
        label = mapping_label(mappings, "PAXFLGSM", letter)
        if label:
            add_literal(triples, subject, "cskg:qualityFlagLabelDescription", label)




def load_protocol_review(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    review = pd.read_csv(path, dtype=str).fillna("")
    return {str(row.protocol_id): row._asdict() for row in review.itertuples(index=False)}


def load_protocol_citations(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        return {}
    citations = pd.read_csv(path, dtype=str).fillna("")
    out: dict[str, list[dict[str, str]]] = {}
    for row in citations.itertuples(index=False):
        out.setdefault(str(row.protocol_id), []).append(row._asdict())
    return out


def add_protocol_citation_metadata(
    triples: list[str], protocol: str, citation_rows: dict[str, list[dict[str, str]]], protocol_id: str
) -> int:
    rows = citation_rows.get(str(protocol_id), [])
    for row in rows:
        citation = protocol_citation_uri(protocol_id, row["citation_id"])
        add(triples, citation, "rdf:type", "cskg:ProtocolCitationEvidence")
        add(triples, protocol, "cskg:hasProtocolCitationEvidence", citation)
        add_literal(triples, citation, "dct:identifier", row["citation_id"])
        add_literal(triples, citation, "cskg:citationRole", row["citation_role"])
        add_literal(triples, citation, "cskg:sourceType", row["source_type"])
        add_literal(triples, citation, "dct:title", row["title"])
        add_literal(triples, citation, "dct:bibliographicCitation", row["citation_text"])
        add_literal(triples, citation, "cskg:sourceUrl", row["source_url"])
        add_literal(triples, citation, "cskg:citedClaim", row["cited_claim"])
        add_literal(triples, citation, "cskg:supportsProtocolComponent", row["supports_protocol_component"])
        add_literal(triples, citation, "cskg:supportLevel", row["support_level"])
        add_literal(triples, citation, "cskg:evidenceStatus", row["evidence_status"])
        add_literal(triples, citation, "cskg:protocolCompatibilityWarning", row["compatibility_warning"])
        add_literal(triples, citation, "cskg:interpretationLimit", row["interpretation_limit"])
        add(triples, citation, "prov:wasDerivedFrom", source_table_uri("protocol_citation_evidence.csv"))
    return len(rows)


def add_protocol_review_metadata(
    triples: list[str], protocol: str, review_rows: dict[str, dict[str, str]], protocol_id: str
) -> None:
    row = review_rows.get(str(protocol_id))
    if not row:
        return
    for predicate, column in [
        ("cskg:protocolReviewDecision", "review_decision"),
        ("cskg:protocolApprovedLabel", "approved_label"),
        ("cskg:protocolApprovedExpression", "approved_expression"),
        ("cskg:protocolApprovedStatus", "approved_status"),
        ("cskg:protocolReviewerComment", "reviewer_comment"),
        ("cskg:protocolReviewerName", "reviewer_name"),
        ("cskg:protocolReviewDate", "review_date"),
        ("cskg:protocolClassificationType", "classification_type"),
        ("cskg:protocolCompatibilityWarning", "compatibility_warning"),
    ]:
        value = row.get(column)
        if value:
            add_literal(triples, protocol, predicate, value)
    min_days = row.get("approved_min_valid_days")
    if min_days:
        add_literal(triples, protocol, "cskg:protocolApprovedMinValidDays", int(float(min_days)), "xsd:integer")
    if row.get("review_decision"):
        add_literal(
            triples,
            protocol,
            "cskg:protocolInterpretationLimit",
            "Approved as a data completeness/sensitivity rule only; not an active/inactive, MVPA, sedentary, or clinical physical activity classification.",
        )


def load_selected_minutes(path: Path, selected_days: pd.DataFrame, max_minutes_per_day: int) -> pd.DataFrame:
    wanted = {
        (float(row.SEQN), str(row.cycle), int(row.PAXDAYD))
        for row in selected_days[["SEQN", "cycle", "PAXDAYD"]].itertuples(index=False)
    }
    counts: dict[tuple[float, str, int], int] = {key: 0 for key in wanted}
    chunks: list[pd.DataFrame] = []
    usecols = ["SEQN", "cycle", "PAXDAYM", "PAXSSNMP", "PAXTSM", "PAXMTSM", "PAXPREDM", "PAXQFM", "PAXFLGSM"]
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=250_000, low_memory=False):
        mask = chunk.apply(lambda row: (float(row.SEQN), str(row.cycle), int(row.PAXDAYM)) in wanted, axis=1)
        if not mask.any():
            continue
        filtered = chunk.loc[mask].sort_values(["cycle", "SEQN", "PAXDAYM", "PAXSSNMP"])
        selected_rows = []
        for row in filtered.itertuples(index=False):
            key = (float(row.SEQN), str(row.cycle), int(row.PAXDAYM))
            if counts[key] >= max_minutes_per_day:
                continue
            selected_rows.append(row._asdict())
            counts[key] += 1
        if selected_rows:
            chunks.append(pd.DataFrame(selected_rows))
        if all(count >= max_minutes_per_day for count in counts.values()):
            break
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols)


def add_source_tables(triples: list[str], table_names: Iterable[str]) -> None:
    for table_name in table_names:
        table = source_table_uri(table_name)
        add(triples, table, "rdf:type", "prov:Entity")
        add_literal(triples, table, "dct:title", table_name)


def load_optional_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def add_activity_sources(triples: list[str]) -> None:
    sources = [
        {
            "source_id": "nhanes_2011_2014_wrist_mims",
            "title": "NHANES 2011-2014 wrist MIMS source",
            "device_location": "wrist",
            "movement_metric": "MIMS",
            "source_table": "pam_days.csv",
            "limit": "Source-specific wrist MIMS movement summaries; do not apply hip counts/minute thresholds.",
        },
        {
            "source_id": "synthetic_hip_counts_demo",
            "title": "Synthetic hip counts/minute demonstration source",
            "device_location": "hip",
            "movement_metric": "vertical-axis counts/minute",
            "source_table": "synthetic_contrasting_daily_activity.csv",
            "limit": "Synthetic review/demo artifact only; not measured hip accelerometry and not a conversion from wrist MIMS.",
        },
        {
            "source_id": "nhanes_2003_2006_hip_actigraph_pam",
            "title": "NHANES 2003-2006 independent hip-worn ActiGraph PAM source",
            "device_location": "hip",
            "movement_metric": "ActiGraph activity counts/minute",
            "source_table": "independent_nhanes_pam_daily_summary.csv",
            "limit": "Independent public accelerometry source; do not convert hip ActiGraph counts or steps to NHANES 2011-2014 wrist MIMS, MVPA, sedentary, or clinical activity status.",
        },
        {
            "source_id": "nhanes_2005_2006_hip_actigraph_pam",
            "title": "NHANES 2005-2006 independent hip-worn ActiGraph PAM step source",
            "device_location": "hip",
            "movement_metric": "ActiGraph steps/minute",
            "source_table": "independent_nhanes_pam_daily_summary.csv",
            "limit": "Source-specific hip-worn step metric available in 2005-2006 only; no MIMS-to-steps or steps-to-MIMS conversion is asserted.",
        },
    ]
    for row in sources:
        source = activity_source_uri(row["source_id"])
        add(triples, source, "rdf:type", "cskg:ActivityDataSource")
        add_literal(triples, source, "dct:identifier", row["source_id"])
        add_literal(triples, source, "dct:title", row["title"])
        add_literal(triples, source, "cskg:sourceDeviceLocation", row["device_location"])
        add_literal(triples, source, "cskg:sourceMovementMetric", row["movement_metric"])
        add_literal(triples, source, "cskg:interpretationLimit", row["limit"])
        add(triples, source, "prov:wasDerivedFrom", source_table_uri(row["source_table"]))


def add_harmonisation_mappings(
    triples: list[str], variable_map: pd.DataFrame, provenance_table: str = "harmonisation_source_variable_map.csv"
) -> None:
    if variable_map.empty:
        return

    def row_value(row: Any, column: str, default: Any = None) -> Any:
        value = getattr(row, column, default)
        return default if is_missing(value) else value

    for row in variable_map.itertuples(index=False):
        mapping = harmonisation_mapping_uri(row.source_id, row.source_variable)
        source = activity_source_uri(row.source_id)
        source_variable = row_value(row, "source_variable", "unknown")
        add(triples, mapping, "rdf:type", "cskg:HarmonisedSourceVariableMapping")
        add_literal(triples, mapping, "dct:identifier", f"{row.source_id}:{source_variable}")
        add(triples, mapping, "cskg:mapsFromActivitySource", source)
        add_literal(triples, mapping, "cskg:sourceId", row.source_id)
        add_literal(triples, mapping, "cskg:sourceTable", row_value(row, "source_table", provenance_table))
        add_literal(triples, mapping, "cskg:sourceVariableName", source_variable)
        add_literal(triples, mapping, "cskg:sourceLabel", row_value(row, "source_label", source_variable))
        add_literal(triples, mapping, "cskg:sourceDeviceLocation", row_value(row, "source_device_location", "hip"))
        add_literal(triples, mapping, "cskg:sourceUnit", row_value(row, "source_unit", "source-specific unit"))
        add_literal(triples, mapping, "cskg:harmonisedConstruct", row_value(row, "harmonised_construct", "source-specific movement construct"))
        add_literal(triples, mapping, "cskg:harmonisedProperty", row_value(row, "harmonised_property", "source-specific property"))
        add_literal(triples, mapping, "cskg:protocolRole", row_value(row, "protocol_role", "source metric"))
        add_literal(triples, mapping, "cskg:compatibilityStatus", row_value(row, "compatibility_status", "source-specific metric; not directly convertible"))
        add_literal(triples, mapping, "cskg:harmonisationAction", row_value(row, "harmonisation_action", "retain source-specific metric and block numeric equivalence"))
        add_literal(triples, mapping, "cskg:interpretationLimit", row_value(row, "interpretation_limit", "No numeric conversion or activity-status classification is asserted."))
        add(triples, mapping, "prov:wasDerivedFrom", source_table_uri(provenance_table))


def add_harmonised_definitions(triples: list[str], definitions: pd.DataFrame) -> None:
    if definitions.empty:
        return
    for row in definitions.itertuples(index=False):
        definition = harmonised_definition_uri(row.definition_id)
        source = activity_source_uri(row.source_id)
        add(triples, definition, "rdf:type", "cskg:HarmonisedActivityDefinition")
        add_literal(triples, definition, "dct:identifier", row.definition_id)
        add_literal(triples, definition, "rdfs:label", row.label)
        add(triples, definition, "cskg:definedForActivitySource", source)
        add_literal(triples, definition, "cskg:sourceId", row.source_id)
        add_literal(triples, definition, "cskg:hasExecutableExpression", row.expression)
        add_literal(triples, definition, "cskg:sourceDeviceLocation", row.device_location)
        add_literal(triples, definition, "cskg:sourceMovementMetric", row.movement_metric)
        add_literal(triples, definition, "cskg:threshold", row.threshold)
        add_literal(triples, definition, "cskg:definitionType", row.definition_type)
        add_literal(triples, definition, "cskg:compatibilityStatus", row.harmonisation_status)
        add_literal(triples, definition, "cskg:interpretationLimit", row.interpretation_limit)
        add(triples, definition, "prov:wasDerivedFrom", source_table_uri("harmonised_activity_definitions.csv"))


def add_synthetic_daily_summaries(
    triples: list[str], selected_days: pd.DataFrame, synthetic_daily: pd.DataFrame, execution: str
) -> pd.DataFrame:
    if synthetic_daily.empty:
        return synthetic_daily
    selected = synthetic_daily.merge(
        selected_days[["SEQN", "cycle", "PAXDAYD"]],
        left_on=["seed_nhanes_seqn", "seed_nhanes_cycle", "measurement_day"],
        right_on=["SEQN", "cycle", "PAXDAYD"],
        how="inner",
    ).sort_values(["cycle", "SEQN", "measurement_day"])
    synthetic_source = activity_source_uri("synthetic_hip_counts_demo")
    for row in selected.itertuples(index=False):
        summary = synthetic_day_uri(row.seed_nhanes_cycle, row.seed_nhanes_seqn, row.measurement_day)
        participant = participant_uri(row.seed_nhanes_cycle, row.seed_nhanes_seqn)
        nhanes_day = day_uri(row.seed_nhanes_cycle, row.seed_nhanes_seqn, row.measurement_day)
        add(triples, summary, "rdf:type", "cskg:SyntheticDailyActivitySummary")
        add(triples, participant, "cskg:hasSyntheticDailyActivitySummary", summary)
        add(triples, summary, "cskg:seededFromNhanesDay", nhanes_day)
        add(triples, summary, "cskg:fromActivitySource", synthetic_source)
        add_literal(triples, summary, "dct:identifier", f"{row.source_id}:{row.seed_nhanes_cycle}:{int(row.seed_nhanes_seqn)}:{int(row.measurement_day)}")
        add_literal(triples, summary, "cskg:sourceId", row.source_id)
        add_literal(triples, summary, "cskg:monitorDayIndex", row.measurement_day, "xsd:integer")
        add_literal(triples, summary, "cskg:sourceDeviceLocation", row.device_location)
        add_literal(triples, summary, "cskg:sourceDeviceType", row.device_type)
        add_literal(triples, summary, "cskg:epochLengthSeconds", row.epoch_length_seconds, "xsd:integer")
        add_literal(triples, summary, "cskg:sourceMovementMetric", row.movement_metric)
        add_literal(triples, summary, "cskg:validWearMinutes", row.valid_wear_minutes, "xsd:integer")
        add_literal(triples, summary, "cskg:dailyTotalAxisCounts", row.daily_total_vertical_axis_counts, "xsd:integer")
        add_literal(triples, summary, "cskg:meanAxisCountsPerMinute", row.mean_vertical_axis_counts_per_minute, "xsd:decimal")
        add_literal(triples, summary, "cskg:sourceDefinedMVPAMinutes", row.mvpa_minutes_1952_cpm, "xsd:integer")
        add_literal(triples, summary, "cskg:sourceDefinedSedentaryMinutes", row.sedentary_minutes_100_cpm, "xsd:integer")
        add_literal(triples, summary, "cskg:validDayUnderSourceProtocol", bool(row.valid_day_10h), "xsd:boolean")
        add_literal(triples, summary, "cskg:interpretationLimit", row.synthetic_generation_note)
        add(triples, summary, "prov:wasGeneratedBy", execution)
        add(triples, summary, "prov:wasDerivedFrom", source_table_uri("synthetic_contrasting_daily_activity.csv"))
    return selected


def add_independent_pam_daily_summaries(
    triples: list[str], independent_daily: pd.DataFrame, execution: str, max_days: int
) -> pd.DataFrame:
    if independent_daily.empty:
        return independent_daily
    selected = (
        independent_daily.sort_values(["cycle", "SEQN", "day_index"])
        .groupby("cycle", as_index=False)
        .head(max(1, max_days // max(1, independent_daily["cycle"].nunique())))
    )
    if len(selected) < max_days:
        selected = independent_daily.sort_values(["cycle", "SEQN", "day_index"]).head(max_days)
    for row in selected.itertuples(index=False):
        summary = independent_pam_day_uri(row.cycle, row.SEQN, row.day_index)
        source_id = "nhanes_2003_2006_hip_actigraph_pam"
        source = activity_source_uri(source_id)
        add(triples, summary, "rdf:type", "cskg:IndependentPAMDailySummary")
        add_literal(triples, summary, "dct:identifier", f"{source_id}:{row.cycle}:{int(row.SEQN)}:{int(row.day_index)}")
        add_literal(triples, summary, "cskg:sourceId", source_id)
        add_literal(triples, summary, "cskg:sourceParticipantIdentifier", int(row.SEQN), "xsd:integer")
        add_literal(triples, summary, "cskg:nhanesCycle", row.cycle)
        add_literal(triples, summary, "cskg:monitorDayIndex", row.day_index, "xsd:integer")
        add_literal(triples, summary, "cskg:dayOfWeekCode", row.PAXDAY, "xsd:integer")
        add(triples, summary, "cskg:fromActivitySource", source)
        add_literal(triples, summary, "cskg:sourceDeviceLocation", "hip")
        add_literal(triples, summary, "cskg:sourceDeviceType", "ActiGraph AM-7164")
        add_literal(triples, summary, "cskg:sourceMovementMetric", "ActiGraph activity counts/minute")
        add_literal(triples, summary, "cskg:epochLengthSeconds", 60, "xsd:integer")
        add_literal(triples, summary, "cskg:minuteRowCount", row.minute_rows, "xsd:integer")
        add_literal(triples, summary, "cskg:reliableMinutes", row.reliable_minutes, "xsd:integer")
        add_literal(triples, summary, "cskg:inCalibrationMinutes", row.in_calibration_minutes, "xsd:integer")
        add_literal(triples, summary, "cskg:validWearMinutes", row.reliable_in_calibration_minutes, "xsd:integer")
        add_literal(triples, summary, "cskg:nonzeroActivityCountMinutes", row.nonzero_activity_count_minutes, "xsd:integer")
        add_literal(triples, summary, "cskg:dailyTotalAxisCounts", row.total_activity_counts_reliable_in_calibration, "xsd:decimal")
        add_literal(triples, summary, "cskg:meanAxisCountsPerMinute", row.mean_activity_counts_reliable_in_calibration, "xsd:decimal")
        add_literal(triples, summary, "cskg:maxAxisCountsPerMinute", row.max_activity_counts, "xsd:decimal")
        if hasattr(row, "total_steps_reliable_in_calibration") and not is_missing(row.total_steps_reliable_in_calibration):
            add_literal(triples, summary, "cskg:dailyTotalSteps", row.total_steps_reliable_in_calibration, "xsd:decimal")
            add_literal(triples, summary, "cskg:maxStepsPerMinute", row.max_steps_per_minute, "xsd:decimal")
        add_literal(
            triples,
            summary,
            "cskg:interpretationLimit",
            "Independent hip-worn ActiGraph PAM source. Counts/minute and steps are source-specific metrics; do not convert to wrist MIMS, MVPA, sedentary time, active/inactive status, or clinical physical-activity status.",
        )
        add(triples, summary, "prov:wasGeneratedBy", execution)
        add(triples, summary, "prov:wasDerivedFrom", source_table_uri("independent_nhanes_pam_daily_summary.csv"))
    return selected


def build_graph(args: argparse.Namespace) -> dict[str, Any]:
    processed = args.processed_dir
    participants = pd.read_csv(processed / "participants.csv")
    diagnoses = pd.read_csv(processed / "cancer_diagnoses.csv")
    days = pd.read_csv(processed / "pam_days.csv")
    features = pd.read_csv(processed / "pam_minute_features.csv")
    protocols = pd.read_csv(processed / "protocol_definitions.csv")
    protocol_results = pd.read_csv(processed / "valid_day_protocol_results.csv")
    code_mappings = load_code_mappings(processed / "code_mappings.csv")
    reviewed_ncit_mappings = load_approved_ncit_mappings(args.approved_ncit_mapping)
    protocol_review = load_protocol_review(Path("docs/protocols/protocol_review_sheet.csv"))
    protocol_citations = load_protocol_citations(Path("docs/protocols/protocol_citation_evidence.csv"))
    harmonisation_map = load_optional_csv(processed / "harmonisation_source_variable_map.csv")
    harmonised_definitions = load_optional_csv(processed / "harmonised_activity_definitions.csv")
    synthetic_daily = load_optional_csv(processed / "synthetic_contrasting_daily_activity.csv")
    independent_pam_daily = load_optional_csv(processed / "independent_nhanes_pam_daily_summary.csv")
    independent_pam_map = load_optional_csv(processed / "independent_nhanes_pam_semantic_map.csv")

    candidate_seqn = (
        features[["SEQN", "cycle"]]
        .drop_duplicates()
        .merge(diagnoses[["SEQN", "cycle"]].drop_duplicates(), on=["SEQN", "cycle"], how="inner")
    )
    inclusion_wide = (
        protocol_results.merge(candidate_seqn, on=["SEQN", "cycle"], how="inner")
        .pivot_table(
            index=["SEQN", "cycle"],
            columns="protocol_id",
            values="eligible_under_protocol",
            aggfunc="first",
            fill_value=False,
        )
        .reset_index()
    )
    protocol_columns = [column for column in inclusion_wide.columns if column not in {"SEQN", "cycle"}]
    inclusion_wide["_discordant_protocol_result"] = (
        inclusion_wide[protocol_columns].astype(bool).nunique(axis=1) > 1 if protocol_columns else False
    )
    eligible_seqn = (
        inclusion_wide.sort_values(["_discordant_protocol_result", "cycle", "SEQN"], ascending=[False, True, True])
        .head(args.participants)[["SEQN", "cycle"]]
    )
    selected_participants = participants.merge(eligible_seqn, on=["SEQN", "cycle"], how="inner")
    selected_days = (
        days.merge(eligible_seqn, on=["SEQN", "cycle"], how="inner")
        .sort_values(["cycle", "SEQN", "PAXDAYD"])
        .groupby(["SEQN", "cycle"], as_index=False)
        .head(args.max_days)
    )
    selected_features = features.merge(
        selected_days[["SEQN", "cycle", "PAXDAYD"]],
        left_on=["SEQN", "cycle", "PAXDAYM"],
        right_on=["SEQN", "cycle", "PAXDAYD"],
        how="inner",
    )
    selected_diagnoses = diagnoses.merge(eligible_seqn, on=["SEQN", "cycle"], how="inner")
    selected_protocol_results = protocol_results.merge(eligible_seqn, on=["SEQN", "cycle"], how="inner")
    selected_minutes = load_selected_minutes(processed / "pam_minutes.csv", selected_days, args.max_minutes_per_day)

    triples: list[str] = []
    add_source_tables(
        triples,
        [
            "participants.csv",
            "cancer_diagnoses.csv",
            "pam_days.csv",
            "pam_minutes.csv",
            "pam_minute_features.csv",
            "protocol_definitions.csv",
            "valid_day_protocol_results.csv",
            "semantic_mapping.csv",
            "code_mappings.csv",
            "approved_cancer_type_ncit_mapping.csv",
            "protocol_review_sheet.csv",
            "protocol_citation_evidence.csv",
            "synthetic_contrasting_daily_activity.csv",
            "harmonisation_source_variable_map.csv",
            "harmonised_activity_definitions.csv",
            "source_harmonisation_pairwise_comparison.csv",
            "independent_nhanes_pam_daily_summary.csv",
            "independent_nhanes_pam_semantic_map.csv",
            "independent_nhanes_pam_semantic_risk_register.csv",
        ],
    )

    add(triples, "cskg:MIMSUnit", "rdf:type", "qudt:Unit")
    add_literal(triples, "cskg:MIMSUnit", "rdfs:label", "MIMS unit")
    add_literal(
        triples,
        "cskg:MIMSUnit",
        "rdfs:comment",
        "Monitor-Independent Movement Summary algorithmic movement-summary unit; not counts/minute and not an activity-intensity category.",
    )

    add(triples, "cskg:CountsPerMinuteUnit", "rdf:type", "qudt:Unit")
    add_literal(triples, "cskg:CountsPerMinuteUnit", "rdfs:label", "counts per minute")
    add_literal(
        triples,
        "cskg:CountsPerMinuteUnit",
        "rdfs:comment",
        "Source-specific hip-worn vertical-axis counts/minute unit used by synthetic and independent PAM source summaries.",
    )
    add(triples, "cskg:StepsPerMinuteUnit", "rdf:type", "qudt:Unit")
    add_literal(triples, "cskg:StepsPerMinuteUnit", "rdfs:label", "steps per minute")
    add_literal(
        triples,
        "cskg:StepsPerMinuteUnit",
        "rdfs:comment",
        "Source-specific step-count unit. It is not numerically equivalent to wrist MIMS.",
    )
    add_activity_sources(triples)
    add_harmonisation_mappings(triples, harmonisation_map)
    add_harmonisation_mappings(triples, independent_pam_map, "independent_nhanes_pam_semantic_map.csv")
    add_harmonised_definitions(triples, harmonised_definitions)

    nhanes_processing_plan = iri("processing-plan/nhanes-2011-2014-wrist-accelerometry")
    add(triples, nhanes_processing_plan, "rdf:type", "prov:Plan")
    add_literal(triples, nhanes_processing_plan, "dct:title", "NHANES 2011-2014 wrist accelerometry processing plan")
    add_literal(
        triples,
        nhanes_processing_plan,
        "dct:description",
        "CDC/NHANES-provided wrist accelerometry processing outputs used here as source data: PAXHD, PAXDAY, and PAXMIN. The local KG does not reconstruct the raw acceleration processing algorithm.",
    )

    execution = iri("software-execution/build-pilot-kg")
    add(triples, execution, "rdf:type", "prov:Activity")
    add_literal(triples, execution, "dct:title", "Build pilot RDF knowledge graph")
    add_literal(triples, execution, "prov:startedAtTime", datetime.now(timezone.utc).isoformat(), "xsd:dateTime")
    add(triples, execution, "prov:used", source_table_uri("semantic_mapping.csv"))
    add(triples, execution, "prov:used", source_table_uri("code_mappings.csv"))
    add(triples, execution, "prov:used", source_table_uri("approved_cancer_type_ncit_mapping.csv"))
    add(triples, execution, "prov:used", source_table_uri("protocol_review_sheet.csv"))
    add(triples, execution, "prov:used", source_table_uri("protocol_citation_evidence.csv"))
    add(triples, execution, "prov:used", source_table_uri("synthetic_contrasting_daily_activity.csv"))
    add(triples, execution, "prov:used", source_table_uri("harmonisation_source_variable_map.csv"))
    add(triples, execution, "prov:used", source_table_uri("harmonised_activity_definitions.csv"))
    add(triples, execution, "prov:used", source_table_uri("independent_nhanes_pam_daily_summary.csv"))
    add(triples, execution, "prov:used", source_table_uri("independent_nhanes_pam_semantic_map.csv"))
    add(triples, execution, "prov:used", nhanes_processing_plan)

    for row in selected_participants.itertuples(index=False):
        p = participant_uri(row.cycle, row.SEQN)
        add(triples, p, "rdf:type", "cskg:Participant")
        add_literal(triples, p, "dct:identifier", int(row.SEQN))
        add_literal(triples, p, "cskg:nhanesCycle", row.cycle)
        add_literal(triples, p, "cskg:ageInYears", row.RIDAGEYR, "xsd:decimal")
        add_literal(triples, p, "cskg:hasGenderCode", row.RIAGENDR, "xsd:decimal")
        add_mapping_label(triples, p, "cskg:genderLabel", code_mappings, "RIAGENDR", row.RIAGENDR)
        add_literal(triples, p, "cskg:hasRaceEthnicityCode", row.RIDRETH3, "xsd:decimal")
        add_mapping_label(triples, p, "cskg:raceEthnicityLabel", code_mappings, "RIDRETH3", row.RIDRETH3)
        add_literal(triples, p, "cskg:hasCancerHistoryCode", row.MCQ220, "xsd:decimal")
        add_mapping_label(triples, p, "cskg:cancerHistoryLabel", code_mappings, "MCQ220", row.MCQ220)
        cancer_history = cancer_history_uri(row.cycle, row.SEQN)
        add(triples, cancer_history, "rdf:type", "cskg:CancerHistoryAssertion")
        add(triples, cancer_history, "rdf:type", "cskg:SelfReportedCancerHistory")
        add(triples, p, "cskg:hasCancerHistoryAssertion", cancer_history)
        add_literal(triples, cancer_history, "cskg:hasCancerHistoryCode", row.MCQ220, "xsd:decimal")
        add_mapping_label(triples, cancer_history, "cskg:cancerHistoryLabel", code_mappings, "MCQ220", row.MCQ220)
        add_literal(triples, cancer_history, "cskg:sourceQuestion", "Ever told by a doctor or other health professional that you had cancer or a malignancy")
        add_literal(triples, cancer_history, "cskg:assertionInterpretationLimit", "Self-reported NHANES MCQ220 history only; no registry, EHR, stage, treatment, recurrence, or current disease status validation.")
        add(triples, cancer_history, "prov:wasDerivedFrom", source_table_uri("participants.csv"))
        add(triples, p, "prov:wasDerivedFrom", source_table_uri("participants.csv"))
        if hasattr(row, "PAXSENID") and not is_missing(row.PAXSENID):
            sensor = sensor_uri(row.cycle, row.SEQN, row.PAXSENID)
            add(triples, sensor, "rdf:type", "sosa:Sensor")
            add_literal(triples, sensor, "dct:identifier", row.PAXSENID)
            add(triples, p, "cskg:hadAccelerometerSensor", sensor)
            add_literal(triples, sensor, "cskg:hasDevicePlacementCode", getattr(row, "PAXHAND", None), "xsd:decimal")
            add_mapping_label(triples, sensor, "cskg:devicePlacementLabel", code_mappings, "PAXHAND", getattr(row, "PAXHAND", None))
            add_literal(triples, sensor, "cskg:hasDeviceOrientationCode", getattr(row, "PAXORENT", None), "xsd:decimal")
            add_mapping_label(triples, sensor, "cskg:deviceOrientationLabel", code_mappings, "PAXORENT", getattr(row, "PAXORENT", None))

    for row in selected_diagnoses.itertuples(index=False):
        d = diagnosis_uri(row.cycle, row.SEQN, row.diagnosis_slot)
        p = participant_uri(row.cycle, row.SEQN)
        add(triples, d, "rdf:type", "cskg:CancerDiagnosis")
        add(triples, p, "cskg:hasCancerDiagnosis", d)
        add_literal(triples, d, "cskg:diagnosisSlot", row.diagnosis_slot)
        add_literal(triples, d, "cskg:hasCancerTypeCode", row.cancer_type_code, "xsd:decimal")
        add_cancer_mapping_metadata(triples, d, code_mappings, row.cancer_type_code)
        add_reviewed_ncit_mapping(triples, d, reviewed_ncit_mappings, row.cancer_type_code)
        add_literal(triples, d, "cskg:ageAtDiagnosis", row.age_at_diagnosis, "xsd:decimal")
        add_literal(triples, d, "cskg:sourceTypeVariable", row.source_type_variable)
        add_literal(triples, d, "cskg:sourceAgeVariable", row.source_age_variable)
        add(triples, d, "prov:wasDerivedFrom", source_table_uri("cancer_diagnoses.csv"))

    for row in selected_days.itertuples(index=False):
        day = day_uri(row.cycle, row.SEQN, row.PAXDAYD)
        p = participant_uri(row.cycle, row.SEQN)
        add(triples, day, "rdf:type", "cskg:DailyMovementSummary")
        add(triples, p, "cskg:hasDailyMovementSummary", day)
        add_literal(triples, day, "cskg:monitorDayIndex", row.PAXDAYD, "xsd:integer")
        add_literal(triples, day, "cskg:dayOfWeekCode", row.PAXDAYWD, "xsd:integer")
        add_mapping_label(triples, day, "cskg:dayOfWeekLabel", code_mappings, "PAXDAYWD", row.PAXDAYWD)
        add_literal(triples, day, "cskg:totalRecordedMinutes", row.PAXTMD, "xsd:decimal")
        add_literal(triples, day, "cskg:validMinutes", row.PAXVMD, "xsd:decimal")
        add_literal(triples, day, "cskg:dailyTotalMIMS", row.PAXMTSD, "xsd:decimal")
        add(triples, day, "cskg:hasMeasurementUnit", "cskg:MIMSUnit")
        add_literal(triples, day, "cskg:wakeWearMinutes", row.PAXWWMD, "xsd:decimal")
        add_literal(triples, day, "cskg:sleepWearMinutes", row.PAXSWMD, "xsd:decimal")
        add_literal(triples, day, "cskg:nonWearMinutes", row.PAXNWMD, "xsd:decimal")
        add_literal(triples, day, "cskg:unknownStatusMinutes", row.PAXUMD, "xsd:decimal")
        add_literal(triples, day, "cskg:qualityFlagScore", row.PAXQFD, "xsd:decimal")
        add(triples, day, "prov:wasDerivedFrom", source_table_uri("pam_days.csv"))

    for row in selected_features.itertuples(index=False):
        feature = feature_uri(row.cycle, row.SEQN, row.PAXDAYM)
        day = day_uri(row.cycle, row.SEQN, row.PAXDAYM)
        add(triples, feature, "rdf:type", "cskg:DerivedMovementFeatureSet")
        add(triples, day, "cskg:hasDerivedFeatureSet", feature)
        add_literal(triples, feature, "cskg:validMinuteRows", row.valid_minute_rows, "xsd:integer")
        add_literal(triples, feature, "cskg:dailyTotalValidMIMS", row.daily_total_valid_mims_from_minutes, "xsd:decimal")
        add_literal(triples, feature, "cskg:peak30ValidMIMS", row.peak_30_valid_mims, "xsd:decimal")
        add(triples, feature, "cskg:hasMeasurementUnit", "cskg:MIMSUnit")
        add_literal(triples, feature, "cskg:validWakeMinutes", row.valid_wake_minutes, "xsd:integer")
        add_literal(triples, feature, "cskg:validSleepMinutes", row.valid_sleep_minutes, "xsd:integer")
        add_literal(triples, feature, "cskg:validNonWearMinutes", row.valid_nonwear_minutes, "xsd:integer")
        add_literal(triples, feature, "cskg:validUnknownMinutes", row.valid_unknown_minutes, "xsd:integer")
        add(triples, feature, "prov:wasGeneratedBy", execution)
        add(triples, feature, "prov:wasDerivedFrom", source_table_uri("pam_minutes.csv"))

    for row in selected_minutes.itertuples(index=False):
        obs = minute_uri(row.cycle, row.SEQN, row.PAXDAYM, row.PAXSSNMP)
        day = day_uri(row.cycle, row.SEQN, row.PAXDAYM)
        add(triples, obs, "rdf:type", "sosa:Observation")
        add(triples, day, "cskg:hasMinuteObservation", obs)
        add_literal(triples, obs, "cskg:monitorDayIndex", row.PAXDAYM, "xsd:integer")
        add_literal(triples, obs, "time:numericPosition", row.PAXSSNMP, "xsd:decimal")
        add_literal(triples, obs, "cskg:epochLengthSeconds", row.PAXTSM, "xsd:decimal")
        add_literal(triples, obs, "cskg:minuteMIMS", row.PAXMTSM, "xsd:decimal")
        add(triples, obs, "cskg:hasMeasurementUnit", "cskg:MIMSUnit")
        add_literal(triples, obs, "cskg:predictedWearStateCode", row.PAXPREDM, "xsd:integer")
        add_mapping_label(triples, obs, "cskg:predictedWearStateLabel", code_mappings, "PAXPREDM", row.PAXPREDM)
        add_literal(triples, obs, "cskg:qualityFlagScore", row.PAXQFM, "xsd:decimal")
        add_mapping_label(triples, obs, "cskg:qualityFlagScoreLabel", code_mappings, "PAXQFM", row.PAXQFM)
        add_literal(triples, obs, "cskg:qualityFlagLabels", row.PAXFLGSM)
        add_quality_flag_label_descriptions(triples, obs, code_mappings, row.PAXFLGSM)
        add(triples, obs, "prov:wasDerivedFrom", source_table_uri("pam_minutes.csv"))

    protocol_citation_triples = 0
    for row in protocols.itertuples(index=False):
        protocol = protocol_uri(row.protocol_id)
        add(triples, protocol, "rdf:type", "cskg:ProcessingProtocol")
        add_literal(triples, protocol, "dct:identifier", row.protocol_id)
        add_literal(triples, protocol, "rdfs:label", row.label)
        add_literal(triples, protocol, "cskg:hasExecutableExpression", row.valid_day_expression)
        add_literal(triples, protocol, "cskg:minValidDays", row.min_valid_days, "xsd:integer")
        add_literal(triples, protocol, "cskg:metric", row.metric)
        add_literal(triples, protocol, "cskg:unit", row.unit)
        if str(row.unit).strip().lower() == "mims":
            add(triples, protocol, "cskg:hasMeasurementUnit", "cskg:MIMSUnit")
        add_literal(triples, protocol, "dct:description", row.notes)
        add_protocol_review_metadata(triples, protocol, protocol_review, row.protocol_id)
        protocol_citation_triples += add_protocol_citation_metadata(triples, protocol, protocol_citations, row.protocol_id)
        add(triples, protocol, "prov:wasDerivedFrom", source_table_uri("protocol_definitions.csv"))
        if protocol_review:
            add(triples, protocol, "prov:wasDerivedFrom", source_table_uri("protocol_review_sheet.csv"))
        if protocol_citations:
            add(triples, protocol, "prov:wasDerivedFrom", source_table_uri("protocol_citation_evidence.csv"))

    for row in selected_protocol_results.itertuples(index=False):
        result = protocol_result_uri(row.cycle, row.SEQN, row.protocol_id)
        p = participant_uri(row.cycle, row.SEQN)
        protocol = protocol_uri(row.protocol_id)
        add(triples, result, "rdf:type", "cskg:ProtocolApplicationResult")
        add(triples, p, "cskg:hasProtocolApplicationResult", result)
        add(triples, result, "cskg:appliesProtocol", protocol)
        add_literal(triples, result, "cskg:observedDays", row.observed_days, "xsd:integer")
        add_literal(triples, result, "cskg:validDayCount", row.valid_days, "xsd:integer")
        add_literal(triples, result, "cskg:minValidDays", row.min_valid_days, "xsd:integer")
        add_literal(triples, result, "cskg:eligibleUnderProtocol", bool(row.eligible_under_protocol), "xsd:boolean")
        add_literal(triples, result, "cskg:totalMIMS", row.total_mims, "xsd:decimal")
        add(triples, result, "cskg:hasMeasurementUnit", "cskg:MIMSUnit")
        add(triples, result, "prov:wasGeneratedBy", execution)
        add(triples, result, "prov:wasDerivedFrom", source_table_uri("valid_day_protocol_results.csv"))

    selected_synthetic_days = add_synthetic_daily_summaries(triples, selected_days, synthetic_daily, execution)
    selected_independent_pam_days = add_independent_pam_daily_summaries(
        triples, independent_pam_daily, execution, args.max_independent_pam_days
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for prefix, namespace in PREFIXES.items():
            handle.write(f"@prefix {prefix}: <{namespace}> .\n")
        handle.write("\n")
        handle.write("\n".join(triples))
        handle.write("\n")

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(args.output),
        "participants": int(len(selected_participants)),
        "diagnoses": int(len(selected_diagnoses)),
        "days": int(len(selected_days)),
        "feature_sets": int(len(selected_features)),
        "cancer_history_assertions": int(len(selected_participants)),
        "minute_observations": int(len(selected_minutes)),
        "protocols": int(len(protocols)),
        "protocol_results": int(len(selected_protocol_results)),
        "triples": int(len(triples)),
        "code_mapping_rows_loaded": int(len(code_mappings)),
        "code_labels_enriched": bool(code_mappings),
        "reviewed_ncit_mapping_rows_loaded": int(len(reviewed_ncit_mappings)),
        "reviewed_ncit_assertions_enabled": bool(reviewed_ncit_mappings),
        "protocol_review_rows_loaded": int(len(protocol_review)),
        "protocol_review_enriched": bool(protocol_review),
        "protocol_citation_rows_loaded": int(sum(len(rows) for rows in protocol_citations.values())),
        "protocol_citation_enriched": bool(protocol_citations),
        "harmonisation_mapping_rows_loaded": int(len(harmonisation_map)),
        "harmonised_activity_definitions_loaded": int(len(harmonised_definitions)),
        "synthetic_daily_activity_summaries": int(len(selected_synthetic_days)),
        "independent_pam_daily_summaries": int(len(selected_independent_pam_days)),
        "independent_pam_harmonisation_mapping_rows_loaded": int(len(independent_pam_map)),
        "synthetic_harmonisation_enriched": bool(len(harmonisation_map) and len(harmonised_definitions) and len(selected_synthetic_days)),
        "independent_pam_kg_enriched": bool(len(independent_pam_map) and len(selected_independent_pam_days)),
        "selection_strategy": "participants with protocol-discordant inclusion results first, then cycle and SEQN order",
        "limits": {
            "participants": args.participants,
            "max_days_per_participant": args.max_days,
            "max_minutes_per_day": args.max_minutes_per_day,
        },
    }
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    (args.reports_dir / "pilot_kg_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build_graph(parse_args()), indent=2))


if __name__ == "__main__":
    main()
