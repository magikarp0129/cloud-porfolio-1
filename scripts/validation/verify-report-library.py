#!/usr/bin/env python3
"""Verify report templates, sanitized examples, fixtures and schema boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TEXT = {
    "reports/README.md": [
        "Evidence Boundary",
        "reports/templates/",
        "reports/examples/",
        "examples/incidents/*.json",
    ],
    "reports/templates/monthly-platform-report.md": [
        "Report Metadata",
        "Evidence Coverage",
        "Reliability and Incidents",
        "FinOps",
        "Sign-off",
    ],
    "reports/templates/incident-report.md": [
        "Incident Metadata",
        "Confirmed Facts",
        "Hypotheses and Evidence Gaps",
        "Executed actions",
        "Corrective and Preventive Actions",
    ],
    "reports/examples/monthly/2026-07-platform-monthly.example.md": [
        "simulation",
        "not_available",
        "production KPI",
        "Evidence Register",
    ],
    "reports/examples/incidents/INC-2026-0142.example.md": [
        "simulation",
        "not_confirmed",
        "executed_mutations=[]",
        "ev-fixture-alb-5xx",
        "ev-fixture-pods",
        "ev-fixture-errors",
    ],
    "examples/README.md": [
        "sanitized fixture",
        "CI validate",
        "reports/examples/",
    ],
    "schemas/README.md": [
        "Draft 2020-12",
        "contracts.py",
        "executed_mutations.maxItems=0",
    ],
}

FORBIDDEN_IN_REPORT_EXAMPLES = [
    "fake-test-token",
    "user@example.com",
    "AKIAIOSFODNN7EXAMPLE",
]


def main() -> int:
    errors: list[str] = []

    for relative, tokens in REQUIRED_TEXT.items():
        path = REPO_ROOT / relative
        if not path.is_file():
            errors.append(f"missing required report artifact: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"{relative}: missing required text: {token}")

    for relative in (
        "reports/examples/monthly/2026-07-platform-monthly.example.md",
        "reports/examples/incidents/INC-2026-0142.example.md",
    ):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        if "<...>" in text:
            errors.append(f"{relative}: unresolved generic placeholder")
        for secret in FORBIDDEN_IN_REPORT_EXAMPLES:
            if secret in text:
                errors.append(f"{relative}: forbidden synthetic secret/PII canary leaked")

    request_schema = json.loads(
        (REPO_ROOT / "schemas/incident-request.schema.json").read_text(encoding="utf-8")
    )
    report_schema = json.loads(
        (REPO_ROOT / "schemas/incident-report.schema.json").read_text(encoding="utf-8")
    )
    request = json.loads(
        (REPO_ROOT / "examples/incidents/prod-api-5xx-request.json").read_text(encoding="utf-8")
    )

    if request_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("incident request schema must use JSON Schema Draft 2020-12")
    if report_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("incident report schema must use JSON Schema Draft 2020-12")

    missing = set(request_schema.get("required", [])) - set(request)
    if missing:
        errors.append(f"incident request fixture is missing schema fields: {sorted(missing)}")
    if request_schema.get("additionalProperties") is False:
        unknown = set(request) - set(request_schema.get("properties", {}))
        if unknown:
            errors.append(f"incident request fixture has unknown fields: {sorted(unknown)}")

    mutation_schema = report_schema.get("properties", {}).get("executed_mutations", {})
    if mutation_schema.get("maxItems") != 0:
        errors.append("incident report schema must keep executed_mutations.maxItems=0")

    if errors:
        print("Report library verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Report library verification complete")
    print(f"- templates: 2")
    print(f"- sanitized report examples: 2")
    print("- request/report schema boundary: aligned smoke checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
