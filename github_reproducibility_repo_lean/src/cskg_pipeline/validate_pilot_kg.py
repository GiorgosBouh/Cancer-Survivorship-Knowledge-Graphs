"""Lightweight SHACL-like validation for the generated pilot Turtle graph.

This is not a full SHACL engine. It mirrors the required-property checks in
shapes/pilot_kg_shapes.ttl so the project can validate locally without rdflib
or pyshacl installed.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TRIPLE_RE = re.compile(r"^(?P<s><[^>]+>|\w+:[^\s]+)\s+(?P<p>\w+:[^\s]+)\s+(?P<o>.+)\s+\.$")


@dataclass(frozen=True)
class Shape:
    name: str
    target_class: str
    required_properties: tuple[str, ...]


SHAPES: tuple[Shape, ...] = (
    Shape(
        "ParticipantShape",
        "cskg:Participant",
        (
            "dct:identifier",
            "cskg:nhanesCycle",
            "cskg:hasCancerHistoryCode",
            "cskg:hasCancerHistoryAssertion",
            "cskg:hasCancerDiagnosis",
            "cskg:hasDailyMovementSummary",
            "cskg:hasProtocolApplicationResult",
            "prov:wasDerivedFrom",
        ),
    ),

    Shape(
        "CancerHistoryAssertionShape",
        "cskg:CancerHistoryAssertion",
        (
            "cskg:hasCancerHistoryCode",
            "cskg:sourceQuestion",
            "cskg:assertionInterpretationLimit",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "CancerDiagnosisShape",
        "cskg:CancerDiagnosis",
        ("cskg:diagnosisSlot", "cskg:hasCancerTypeCode", "prov:wasDerivedFrom"),
    ),
    Shape(
        "SensorShape",
        "sosa:Sensor",
        ("dct:identifier", "cskg:hasDevicePlacementCode", "cskg:hasDeviceOrientationCode"),
    ),
    Shape(
        "DailyMovementSummaryShape",
        "cskg:DailyMovementSummary",
        (
            "cskg:monitorDayIndex",
            "cskg:totalRecordedMinutes",
            "cskg:validMinutes",
            "cskg:dailyTotalMIMS",
            "cskg:wakeWearMinutes",
            "cskg:sleepWearMinutes",
            "cskg:nonWearMinutes",
            "cskg:unknownStatusMinutes",
            "cskg:qualityFlagScore",
            "cskg:hasDerivedFeatureSet",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "MinuteObservationShape",
        "sosa:Observation",
        (
            "cskg:monitorDayIndex",
            "cskg:epochLengthSeconds",
            "cskg:minuteMIMS",
            "cskg:predictedWearStateCode",
            "cskg:qualityFlagScore",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "DerivedMovementFeatureSetShape",
        "cskg:DerivedMovementFeatureSet",
        (
            "cskg:validMinuteRows",
            "cskg:dailyTotalValidMIMS",
            "cskg:peak30ValidMIMS",
            "cskg:validWakeMinutes",
            "cskg:validSleepMinutes",
            "cskg:validNonWearMinutes",
            "cskg:validUnknownMinutes",
            "prov:wasGeneratedBy",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "ProcessingProtocolShape",
        "cskg:ProcessingProtocol",
        (
            "dct:identifier",
            "cskg:hasExecutableExpression",
            "cskg:minValidDays",
            "cskg:metric",
            "cskg:unit",
            "cskg:hasProtocolCitationEvidence",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "ProtocolApplicationResultShape",
        "cskg:ProtocolApplicationResult",
        (
            "cskg:appliesProtocol",
            "cskg:observedDays",
            "cskg:validDayCount",
            "cskg:minValidDays",
            "cskg:eligibleUnderProtocol",
            "cskg:totalMIMS",
            "prov:wasGeneratedBy",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "ProtocolCitationEvidenceShape",
        "cskg:ProtocolCitationEvidence",
        (
            "dct:identifier",
            "cskg:citationRole",
            "cskg:sourceType",
            "dct:title",
            "dct:bibliographicCitation",
            "cskg:sourceUrl",
            "cskg:citedClaim",
            "cskg:supportLevel",
            "cskg:interpretationLimit",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "ActivityDataSourceShape",
        "cskg:ActivityDataSource",
        (
            "dct:identifier",
            "dct:title",
            "cskg:sourceDeviceLocation",
            "cskg:sourceMovementMetric",
            "cskg:interpretationLimit",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "HarmonisedSourceVariableMappingShape",
        "cskg:HarmonisedSourceVariableMapping",
        (
            "dct:identifier",
            "cskg:mapsFromActivitySource",
            "cskg:sourceVariableName",
            "cskg:harmonisedConstruct",
            "cskg:compatibilityStatus",
            "cskg:interpretationLimit",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "HarmonisedActivityDefinitionShape",
        "cskg:HarmonisedActivityDefinition",
        (
            "dct:identifier",
            "cskg:definedForActivitySource",
            "cskg:hasExecutableExpression",
            "cskg:definitionType",
            "cskg:compatibilityStatus",
            "cskg:interpretationLimit",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "SyntheticDailyActivitySummaryShape",
        "cskg:SyntheticDailyActivitySummary",
        (
            "dct:identifier",
            "cskg:seededFromNhanesDay",
            "cskg:fromActivitySource",
            "cskg:sourceMovementMetric",
            "cskg:validWearMinutes",
            "cskg:dailyTotalAxisCounts",
            "cskg:sourceDefinedMVPAMinutes",
            "cskg:sourceDefinedSedentaryMinutes",
            "cskg:interpretationLimit",
            "prov:wasGeneratedBy",
            "prov:wasDerivedFrom",
        ),
    ),
    Shape(
        "IndependentPAMDailySummaryShape",
        "cskg:IndependentPAMDailySummary",
        (
            "dct:identifier",
            "cskg:sourceId",
            "cskg:sourceParticipantIdentifier",
            "cskg:nhanesCycle",
            "cskg:monitorDayIndex",
            "cskg:fromActivitySource",
            "cskg:sourceDeviceLocation",
            "cskg:sourceMovementMetric",
            "cskg:epochLengthSeconds",
            "cskg:minuteRowCount",
            "cskg:validWearMinutes",
            "cskg:dailyTotalAxisCounts",
            "cskg:interpretationLimit",
            "prov:wasGeneratedBy",
            "prov:wasDerivedFrom",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=Path("data/processed/pilot_kg.ttl"))
    parser.add_argument("--shapes", type=Path, default=Path("shapes/pilot_kg_shapes.ttl"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument(
        "--ncit-review-status",
        type=Path,
        default=Path("reports/ncit_mapping_review_status.json"),
        help="Review status file used to prevent unreviewed NCIt assertions from entering the graph.",
    )
    parser.add_argument(
        "--require-pyshacl",
        action="store_true",
        help="Fail validation unless the graph conforms under the standards-compliant pySHACL engine.",
    )
    return parser.parse_args()


def parse_graph(path: Path) -> tuple[dict[str, set[str]], dict[str, dict[str, list[str]]], int]:
    types: dict[str, set[str]] = defaultdict(set)
    properties: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    triple_count = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("@prefix") or line.startswith("#"):
            continue
        match = TRIPLE_RE.match(line)
        if not match:
            continue
        subject = match.group("s")
        predicate = match.group("p")
        obj = match.group("o")
        triple_count += 1
        properties[subject][predicate].append(obj)
        if predicate == "rdf:type":
            types[subject].add(obj)
    return types, properties, triple_count


def ncit_assertion_objects(properties: dict[str, dict[str, list[str]]]) -> list[dict[str, str]]:
    ncit_patterns = (
        "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
        "https://ncit.nci.nih.gov/",
        "ncit:",
    )
    hits: list[dict[str, str]] = []
    for subject, predicates in properties.items():
        for predicate, objects in predicates.items():
            for obj in objects:
                if any(pattern in obj for pattern in ncit_patterns):
                    hits.append({"subject": subject, "predicate": predicate, "object": obj})
    return hits


def validate_policy_guards(
    properties: dict[str, dict[str, list[str]]], ncit_review_status_path: Path
) -> list[dict[str, Any]]:
    if not ncit_review_status_path.exists():
        return [
            {
                "guard": "NCItReviewPendingGuard",
                "passed": True,
                "status": "status_file_missing",
                "assertion_count": 0,
                "message": "No NCIt review status file found; guard skipped.",
            }
        ]

    status_payload = json.loads(ncit_review_status_path.read_text(encoding="utf-8"))
    status = status_payload.get("status", "unknown")
    hits = ncit_assertion_objects(properties)
    pending = status == "pending_reviewer_review"
    passed = not pending or len(hits) == 0
    return [
        {
            "guard": "NCItReviewPendingGuard",
            "passed": passed,
            "status": status,
            "assertion_count": len(hits),
            "message": (
                "NCIt review is pending; RDF graph must not assert NCIt IRIs."
                if pending
                else "NCIt review is not pending; guard did not block NCIt assertions."
            ),
            "examples": hits[:10],
        }
    ]


def validate(types: dict[str, set[str]], properties: dict[str, dict[str, list[str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    for shape in SHAPES:
        targets = sorted(subject for subject, classes in types.items() if shape.target_class in classes)
        shape_failures = 0
        for subject in targets:
            for required_property in shape.required_properties:
                count = len(properties.get(subject, {}).get(required_property, []))
                passed = count >= 1
                if not passed:
                    shape_failures += 1
                rows.append(
                    {
                        "shape": shape.name,
                        "target_class": shape.target_class,
                        "focus_node": subject,
                        "required_property": required_property,
                        "value_count": count,
                        "passed": passed,
                    }
                )
        summary.append(
            {
                "shape": shape.name,
                "target_class": shape.target_class,
                "target_nodes": len(targets),
                "required_properties": len(shape.required_properties),
                "checks": len(targets) * len(shape.required_properties),
                "failures": shape_failures,
            }
        )
    return rows, summary


def run_pyshacl(graph_path: Path, shapes_path: Path) -> dict[str, Any]:
    try:
        from pyshacl import validate as pyshacl_validate
    except ModuleNotFoundError as exc:
        return {
            "engine": "pyshacl",
            "available": False,
            "conforms": None,
            "message": f"pySHACL is not installed: {exc}",
        }

    conforms, _results_graph, results_text = pyshacl_validate(
        data_graph=str(graph_path),
        shacl_graph=str(shapes_path),
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
    )
    return {
        "engine": "pyshacl",
        "available": True,
        "conforms": bool(conforms),
        "message": results_text,
    }


def main() -> None:
    args = parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    types, properties, triple_count = parse_graph(args.graph)
    rows, shape_summary = validate(types, properties)
    failures = [row for row in rows if not row["passed"]]
    policy_checks = validate_policy_guards(properties, args.ncit_review_status)
    policy_failures = [check for check in policy_checks if not check["passed"]]
    standard_shacl = run_pyshacl(args.graph, args.shapes)
    pyshacl_failure = args.require_pyshacl and (not standard_shacl.get("available") or not standard_shacl.get("conforms"))
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "graph": str(args.graph),
        "shapes": str(args.shapes),
        "engine": "local-required-property-validator-with-optional-pyshacl",
        "note": "The local validator mirrors required-property checks. Use --require-pyshacl for standards-compliant SHACL gating.",
        "standard_shacl": standard_shacl,
        "require_pyshacl": bool(args.require_pyshacl),
        "passed": len(failures) == 0,
        "triple_count": triple_count,
        "shape_summary": shape_summary,
        "policy_checks": policy_checks,
        "total_checks": len(rows),
        "failed_checks": len(failures),
        "failed_policy_checks": len(policy_failures),
    }
    payload["passed"] = len(failures) == 0 and len(policy_failures) == 0 and not pyshacl_failure

    (args.reports_dir / "pilot_kg_shacl_validation_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    with (args.reports_dir / "pilot_kg_shacl_validation_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["shape", "target_class", "focus_node", "required_property", "value_count", "passed"],
        )
        writer.writeheader()
        writer.writerows(rows)

    pyshacl_report = args.reports_dir / "pilot_kg_pyshacl_validation_summary.json"
    pyshacl_report.write_text(json.dumps(standard_shacl, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    if failures or policy_failures or pyshacl_failure:
        raise SystemExit("Pilot KG validation failed. See reports/pilot_kg_shacl_validation_summary.json")


if __name__ == "__main__":
    main()
