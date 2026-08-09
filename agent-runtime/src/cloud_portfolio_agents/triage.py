from __future__ import annotations

import json
import re
import uuid
from datetime import timezone
from pathlib import Path
from typing import Any, Iterable

from .adapters import (
    CloudWatchAdapter,
    Evidence,
    GrafanaAdapter,
    KubernetesAdapter,
    PrometheusAdapter,
    ToolBudget,
)
from .adapters.base import CommandRunner
from .contracts import ContractError, IncidentRequest, RuntimeConfig
from .redaction import redact


_KUBERNETES_QUERY_IDS = {
    "k8s_nodes",
    "k8s_workload_pods",
    "k8s_workload_controllers",
    "k8s_workload_resilience",
    "k8s_namespace_events",
}


def query_catalog(config: RuntimeConfig) -> set[str]:
    query_ids: set[str] = set()
    if config.sources.get("kubernetes", {}).get("enabled", False):
        query_ids.update(_KUBERNETES_QUERY_IDS)
    for source_name, collection_name in (
        ("cloudwatch", "metric_queries"),
        ("cloudwatch", "logs_insights_queries"),
        ("prometheus", "queries"),
        ("grafana", "dashboards"),
    ):
        source = config.sources.get(source_name, {})
        if not source.get("enabled", False):
            continue
        for entry in source.get(collection_name, []):
            query_id = entry.get("id")
            if isinstance(query_id, str):
                if query_id in query_ids:
                    raise ContractError(f"duplicate query catalog id: {query_id}")
                query_ids.add(query_id)
    return query_ids


def validate_requested_queries(
    request: IncidentRequest, config: RuntimeConfig
) -> None:
    available = query_catalog(config)
    unknown = sorted(set(request.requested_queries).difference(available))
    if unknown:
        raise ContractError("requested query IDs are not in the catalog: " + ", ".join(unknown))


def load_fixture(path: str | Path) -> list[Evidence]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load fixture: {exc}") from exc
    items = payload.get("evidence") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        raise ContractError("fixture must contain an evidence array")
    evidence = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ContractError(f"fixture evidence item {index} must be an object")
        status = item.get("status")
        if status not in {"ok", "error", "skipped"}:
            raise ContractError(f"fixture evidence item {index} has invalid status")
        evidence.append(
            Evidence(
                evidence_id=str(item.get("evidence_id", f"ev-fixture-{index}")),
                source=str(item.get("source", "fixture")),
                query_id=str(item.get("query_id", f"fixture_{index}")),
                status=status,
                summary=str(item.get("summary", "fixture evidence")),
                data=item.get("data", {}) if isinstance(item.get("data", {}), dict) else {},
                warnings=tuple(str(value) for value in item.get("warnings", [])),
            )
        )
    return evidence


def collect_evidence(
    request: IncidentRequest, config: RuntimeConfig
) -> tuple[list[Evidence], int]:
    validate_requested_queries(request, config)
    budget = ToolBudget(config.limits.max_tool_calls, request.timeout_seconds)
    evidence: list[Evidence] = []
    requires_aws_identity = any(
        config.sources.get(source, {}).get("enabled", False)
        for source in ("cloudwatch", "kubernetes")
    )
    if requires_aws_identity:
        identity, verified = verify_runtime_identity(request, config, budget)
        evidence.append(identity)
        if not verified:
            return evidence, budget.actual_calls
    adapters = (
        CloudWatchAdapter(config, budget),
        KubernetesAdapter(config, budget),
        PrometheusAdapter(config, budget),
        GrafanaAdapter(config, budget),
    )
    for adapter in adapters:
        evidence.extend(adapter.collect(request))
    return evidence, budget.actual_calls


def verify_runtime_identity(
    request: IncidentRequest, config: RuntimeConfig, budget: ToolBudget
) -> tuple[Evidence, bool]:
    environment = config.environments[request.environment]
    expected_account = environment.get("aws_account_id")
    expected_role = environment.get("diagnostic_role_arn")
    if not isinstance(expected_account, str) or not re.fullmatch(r"\d{12}", expected_account):
        return _identity_error("environment registry has no valid aws_account_id"), False
    if not isinstance(expected_role, str):
        return _identity_error("environment registry has no diagnostic_role_arn"), False
    match = re.fullmatch(
        r"arn:([^:]+):iam::(\d{12}):role/(?:.*/)?([^/]+)", expected_role
    )
    if not match or match.group(2) != expected_account:
        return _identity_error("diagnostic_role_arn is invalid for the environment"), False
    try:
        identity = CommandRunner(config.limits, budget).run_json(
            ["aws", "sts", "get-caller-identity", "--output", "json"]
        )
    except Exception as exc:
        return _identity_error(str(exc)), False
    expected_session_arn = (
        f"arn:{match.group(1)}:sts::{expected_account}:assumed-role/"
        f"{match.group(3)}/{request.request_id}"
    )
    if identity.get("Account") != expected_account or identity.get("Arn") != expected_session_arn:
        return _identity_error(
            "effective AWS identity is not the registered diagnostic role/request session"
        ), False
    return (
        Evidence(
            "ev-aws-identity",
            "runtime",
            "aws_identity",
            "ok",
            "Effective AWS role and request-scoped session match the environment registry",
            {
                "account_match": True,
                "diagnostic_role_match": True,
                "request_session_match": True,
                "environment": request.environment,
            },
        ),
        True,
    )


def _identity_error(message: str) -> Evidence:
    return Evidence(
        "ev-aws-identity-error",
        "runtime",
        "aws_identity",
        "error",
        f"Runtime identity verification failed: {message}",
    )


def _hypothesis(
    statement: str,
    evidence_id: str,
    verify_next: str,
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "statement": statement,
        "confidence": confidence,
        "supporting_evidence": [evidence_id],
        "counter_evidence": [],
        "verify_next": verify_next,
    }


def derive_hypotheses(evidence: Iterable[Evidence]) -> list[dict[str, Any]]:
    hypotheses: list[dict[str, Any]] = []
    for item in evidence:
        if item.status != "ok":
            continue
        data = item.data
        if item.query_id == "k8s_nodes" and data.get("not_ready"):
            hypotheses.append(
                _hypothesis(
                    "One or more Kubernetes nodes may be contributing to workload impact.",
                    item.evidence_id,
                    "Correlate node conditions with EC2 status, kubelet, CNI, disk, and affected Pod placement.",
                )
            )
        if item.query_id == "k8s_workload_pods":
            if data.get("unready"):
                hypotheses.append(
                    _hypothesis(
                        "Workload readiness or startup failure may be reducing serving capacity.",
                        item.evidence_id,
                        "Compare probe failures, release version, dependency latency, and Ready target count.",
                    )
                )
            if int(data.get("restart_count", 0) or 0) > 0:
                hypotheses.append(
                    _hypothesis(
                        "Container restarts may be related to application exit, OOM, or probe failure.",
                        item.evidence_id,
                        "Correlate last termination reasons with memory, CPU throttling, and sanitized application error aggregates.",
                    )
                )
            if int(data.get("phases", {}).get("Pending", 0) or 0) > 0:
                hypotheses.append(
                    _hypothesis(
                        "Scheduling or capacity constraints may be preventing Pods from starting.",
                        item.evidence_id,
                        "Review FailedScheduling reasons, HPA maximum, namespace quota, node capacity, and subnet IP availability.",
                    )
                )
        if item.source == "cloudwatch" and item.query_id != "aws_identity":
            if item.data.get("row_count", 0):
                hypotheses.append(
                    _hypothesis(
                        "Sanitized log aggregates contain errors within the incident window.",
                        item.evidence_id,
                        "Group errors by deployment version, error code, workload, and request or trace identifier.",
                        "low",
                    )
                )
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in hypotheses:
        if item["statement"] not in seen:
            seen.add(item["statement"])
            unique.append(item)
    return unique


def build_report(
    request: IncidentRequest,
    config: RuntimeConfig,
    evidence: list[Evidence],
    *,
    tool_calls: int,
    simulation: bool = False,
    policy_sha256: str | None = None,
) -> dict[str, Any]:
    cleaned_evidence, redaction_count = redact([item.to_dict() for item in evidence])
    clean_items = [
        Evidence(
            evidence_id=item["evidence_id"],
            source=item["source"],
            query_id=item["query_id"],
            status=item["status"],
            summary=item["summary"],
            data=item["data"],
            warnings=tuple(item["warnings"]),
            observed_at=item["observed_at"],
        )
        for item in cleaned_evidence
    ]
    successes = [item for item in clean_items if item.status == "ok"]
    diagnostic_successes = [
        item for item in successes if item.query_id != "aws_identity"
    ]
    errors = [item for item in clean_items if item.status == "error"]
    if simulation:
        status = "simulation"
    elif not diagnostic_successes:
        status = "blocked"
    elif errors:
        status = "partial"
    else:
        status = "complete"
    hypotheses = derive_hypotheses(clean_items)
    gaps = [
        {
            "source": item.source,
            "query_id": item.query_id,
            "reason": item.summary,
        }
        for item in errors
    ]
    report = {
        "schema_version": "1.0",
        "status": status,
        "request_id": request.request_id,
        "trace_id": f"trace-{uuid.uuid4().hex}",
        "incident_ticket": request.incident_ticket,
        "agent_id": request.agent_id,
        "profile_version": "monitoring-readonly-v1",
        "policy_version": config.policy_version,
        "policy_sha256": policy_sha256,
        "simulation": simulation,
        "evidence_handling": "untrusted_observations_not_instructions",
        "environment": request.environment,
        "scope": request.scope,
        "window": {
            "started_at": request.start.astimezone(timezone.utc).isoformat(),
            "ended_at": request.end.astimezone(timezone.utc).isoformat(),
        },
        "summary": {
            "task": request.task,
            "successful_evidence_items": len(successes),
            "diagnostic_evidence_items": len(diagnostic_successes),
            "failed_evidence_items": len(errors),
            "tool_calls": tool_calls,
            "redaction_count": redaction_count,
        },
        "budget": {
            "max_cost_usd": request.max_cost_usd,
            "estimated_cost_usd": None,
            "cost_enforcement": "bounded query window, log groups, rows, tool calls, response bytes, and timeout; provider invoice cost is not yet measured",
        },
        "facts": [
            {
                "statement": item.summary,
                "evidence_id": item.evidence_id,
                "source": item.source,
            }
            for item in successes
        ],
        "hypotheses": hypotheses,
        "gaps": gaps,
        "evidence": [item.to_dict() for item in clean_items],
        "recovery_candidates": [],
        "executed_mutations": [],
        "required_handoff": (
            "Simulation only; do not use this report as operational evidence."
            if simulation
            else (
                "Operations Agent must review recovery candidates; the Incident Commander must approve any production action."
                if hypotheses
                else "Collect missing evidence before proposing recovery actions."
            )
        ),
    }
    cleaned_report, extra_redactions = redact(report)
    cleaned_report["summary"]["redaction_count"] += extra_redactions
    return cleaned_report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Incident triage: {report['incident_ticket']}",
        "",
        f"- Status: `{report['status']}`",
        f"- Environment: `{report['environment']}`",
        f"- Request ID: `{report['request_id']}`",
        f"- Trace ID: `{report['trace_id']}`",
        f"- Window: `{report['window']['started_at']}` to `{report['window']['ended_at']}`",
        "",
        "## Confirmed facts",
        "",
    ]
    facts = report["facts"]
    lines.extend(
        [f"- {item['statement']} (`{item['evidence_id']}`)" for item in facts]
        or ["- No source returned confirmed evidence."]
    )
    lines.extend(["", "## Hypotheses", ""])
    for item in report["hypotheses"]:
        lines.append(f"- **{item['confidence']}** — {item['statement']}")
        lines.append(f"  - Verify next: {item['verify_next']}")
        lines.append(
            "  - Evidence: " + ", ".join(f"`{value}`" for value in item["supporting_evidence"])
        )
    if not report["hypotheses"]:
        lines.append("- No deterministic hypothesis was produced; additional evidence is required.")
    lines.extend(["", "## Evidence gaps", ""])
    lines.extend(
        [f"- `{item['source']}/{item['query_id']}`: {item['reason']}" for item in report["gaps"]]
        or ["- None."]
    )
    lines.extend(
        [
            "",
            "## Control boundary",
            "",
            f"- {report['required_handoff']}",
            "- No restart, scale, rollback, drain, failover, alarm suppression, or cloud mutation was executed.",
            "",
        ]
    )
    return "\n".join(lines)
