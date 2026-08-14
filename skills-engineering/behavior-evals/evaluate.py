#!/usr/bin/env python3
"""Score captured Agent outputs against the behavior-eval contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, help="JSONL: id, output, task_success, token_count, latency_ms")
    parser.add_argument("--scenarios", type=Path, default=Path(__file__).with_name("scenarios.json"))
    args = parser.parse_args()

    scenarios = {item["id"]: item for item in json.loads(args.scenarios.read_text())["scenarios"]}
    results = [json.loads(line) for line in args.results.read_text().splitlines() if line.strip()]
    unknown = sorted({item.get("id") for item in results} - scenarios.keys())
    if unknown:
        raise SystemExit(f"unknown scenario ids: {', '.join(unknown)}")

    rows = []
    infrastructure_failures = []
    for result in results:
        if result.get("exit_code", 0) != 0:
            infrastructure_failures.append({"id": result["id"], "agent": result.get("agent"), "exit_code": result["exit_code"]})
            continue
        scenario = scenarios[result["id"]]
        output = result.get("output", "")
        contract = scenario["contract"]
        success = scenario["success"]
        missing = [anchor for anchor in contract["required"] if anchor not in output]
        forbidden = [anchor for anchor in contract["forbidden"] if anchor in output]
        success_missing = [anchor for anchor in success["required"] if anchor not in output]
        success_forbidden = [anchor for anchor in success["forbidden"] if anchor in output]
        contract_pass = not missing and not forbidden
        task_success = not success_missing and not success_forbidden
        rows.append({
            "id": result["id"],
            "category": scenario["category"],
            "contract_pass": contract_pass,
            "task_success": task_success,
            "missing": missing,
            "forbidden_hits": forbidden,
            "success_missing": success_missing,
            "success_forbidden_hits": success_forbidden,
            "token_count": result.get("token_count"),
            "latency_ms": result.get("latency_ms"),
        })

    total = len(rows)
    report = {
        "schema_version": 1,
        "evaluated": total,
        "infrastructure_failures": infrastructure_failures,
        "coverage": total / len(scenarios) if scenarios else 1.0,
        "contract_pass_rate": sum(row["contract_pass"] for row in rows) / total if total else 0.0,
        "task_success_rate": sum(row["task_success"] for row in rows) / total if total else 0.0,
        "rows": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if total and not infrastructure_failures and all(row["contract_pass"] and row["task_success"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
