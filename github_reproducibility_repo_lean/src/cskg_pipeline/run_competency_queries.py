"""Run competency-question SPARQL queries against the pilot KG."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rdflib import Graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=Path("data/processed/pilot_kg.ttl"))
    parser.add_argument("--queries-dir", type=Path, default=Path("queries/competency"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--sample-size", type=int, default=5)
    return parser.parse_args()


def cell_to_json(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def run_queries(args: argparse.Namespace) -> dict[str, Any]:
    graph = Graph()
    graph.parse(args.graph, format="turtle")

    results: list[dict[str, Any]] = []
    for query_path in sorted(args.queries_dir.glob("*.rq")):
        query_text = query_path.read_text(encoding="utf-8")
        query_result = graph.query(query_text)
        variables = [str(var) for var in query_result.vars]
        rows = []
        for row in query_result:
            rows.append({var: cell_to_json(row[index]) for index, var in enumerate(variables)})
        results.append(
            {
                "query": str(query_path),
                "variables": variables,
                "row_count": len(rows),
                "sample_rows": rows[: args.sample_size],
            }
        )

    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "graph": str(args.graph),
        "queries_dir": str(args.queries_dir),
        "query_count": len(results),
        "results": results,
    }
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    (args.reports_dir / "competency_question_results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return payload


def main() -> None:
    print(json.dumps(run_queries(parse_args()), indent=2))


if __name__ == "__main__":
    main()
