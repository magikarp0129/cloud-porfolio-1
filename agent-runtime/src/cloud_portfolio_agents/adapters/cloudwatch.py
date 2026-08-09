from __future__ import annotations

import re
import time
from datetime import timezone
from typing import Any

from ..contracts import ContractError, IncidentRequest, RuntimeConfig
from ..redaction import redact
from .base import CommandRunner, Evidence, ToolBudget, render_template


_QUERY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_AWS_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./:#=-]{0,511}$")


class CloudWatchAdapter:
    source_name = "cloudwatch"

    def __init__(self, config: RuntimeConfig, budget: ToolBudget):
        self.config = config
        self.source = config.sources.get(self.source_name, {})
        self.runner = CommandRunner(config.limits, budget)

    def collect(self, request: IncidentRequest) -> list[Evidence]:
        if not self.source.get("enabled", False):
            return []
        evidence: list[Evidence] = []

        for query in self.source.get("metric_queries", []):
            query_id = str(query.get("id", ""))
            if request.requested_queries and query_id not in request.requested_queries:
                continue
            try:
                evidence.append(self._metric(request, query))
            except Exception as exc:
                evidence.append(self._error(query_id or "cloudwatch_metric", str(exc)))

        for query in self.source.get("logs_insights_queries", []):
            query_id = str(query.get("id", ""))
            if request.requested_queries and query_id not in request.requested_queries:
                continue
            try:
                evidence.append(self._logs_insights(request, query))
            except Exception as exc:
                evidence.append(self._error(query_id or "logs_insights", str(exc)))
        return evidence

    def _metric(self, request: IncidentRequest, query: dict[str, Any]) -> Evidence:
        query_id = self._query_id(query)
        namespace = self._aws_name(str(query.get("namespace", "")), "namespace")
        metric_name = self._aws_name(str(query.get("metric_name", "")), "metric_name")
        statistic = str(query.get("statistic", "Average"))
        if statistic not in {"Average", "Sum", "Minimum", "Maximum", "SampleCount"}:
            raise ContractError("CloudWatch statistic is not allowlisted")
        period = int(query.get("period_seconds", 60))
        if period < 60 or period > 3600 or period % 60:
            raise ContractError("CloudWatch period must be a 60-second multiple")

        args = [
            "aws",
            "cloudwatch",
            "get-metric-statistics",
            "--region",
            request.scope["region"],
            "--namespace",
            namespace,
            "--metric-name",
            metric_name,
            "--start-time",
            request.start.astimezone(timezone.utc).isoformat(),
            "--end-time",
            request.end.astimezone(timezone.utc).isoformat(),
            "--period",
            str(period),
            "--statistics",
            statistic,
        ]
        dimensions = query.get("dimensions", {})
        if dimensions:
            if not isinstance(dimensions, dict) or len(dimensions) > 10:
                raise ContractError("CloudWatch dimensions must be an object of at most 10 items")
            args.append("--dimensions")
            for name, value in dimensions.items():
                safe_name = self._aws_name(str(name), "dimension name")
                rendered = render_template(str(value), request)
                if not _AWS_NAME.fullmatch(rendered):
                    raise ContractError("CloudWatch dimension value is unsafe")
                args.append(f"Name={safe_name},Value={rendered}")
        args.extend(["--output", "json"])
        payload = self.runner.run_json(args)
        points = sorted(payload.get("Datapoints", []), key=lambda item: item["Timestamp"])
        values = [float(item[statistic]) for item in points if statistic in item]
        data = {
            "namespace": namespace,
            "metric_name": metric_name,
            "statistic": statistic,
            "unit": points[-1].get("Unit") if points else None,
            "datapoint_count": len(values),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "latest": values[-1] if values else None,
        }
        return Evidence(
            f"ev-cw-{query_id}",
            self.source_name,
            query_id,
            "ok",
            f"CloudWatch {metric_name}: {len(values)} datapoints, max={data['maximum']}",
            data,
        )

    def _logs_insights(
        self, request: IncidentRequest, query: dict[str, Any]
    ) -> Evidence:
        query_id = self._query_id(query)
        query_text = str(query.get("query", ""))
        if not query_text or len(query_text) > 4096:
            raise ContractError("Logs Insights query is empty or too long")
        if re.search(r"(?i)\b(?:unmask|source)\b", query_text):
            raise ContractError("Logs Insights unmask and SOURCE commands are forbidden")
        log_groups_raw = query.get("log_groups", [])
        if not isinstance(log_groups_raw, list) or not log_groups_raw:
            raise ContractError("Logs Insights query must declare log_groups")
        if len(log_groups_raw) > self.config.limits.max_log_groups:
            raise ContractError("Logs Insights log group count exceeds policy")
        log_groups = []
        for value in log_groups_raw:
            rendered = render_template(str(value), request)
            if not rendered.startswith("/") or not _AWS_NAME.fullmatch(rendered):
                raise ContractError("Logs Insights log group name is unsafe")
            log_groups.append(rendered)
        limit = min(int(query.get("limit", 100)), self.config.limits.max_log_rows)
        args = [
            "aws",
            "logs",
            "start-query",
            "--region",
            request.scope["region"],
            "--log-group-names",
            *log_groups,
            "--start-time",
            str(int(request.start.timestamp())),
            "--end-time",
            str(int(request.end.timestamp())),
            "--query-string",
            query_text,
            "--limit",
            str(limit),
            "--output",
            "json",
        ]
        started = self.runner.run_json(args)
        query_token = started.get("queryId")
        if not isinstance(query_token, str):
            raise RuntimeError("CloudWatch Logs did not return a query ID")

        deadline = time.monotonic() + self.runner.budget.timeout(
            self.config.limits.tool_timeout_seconds
        )
        payload: dict[str, Any] = {}
        while time.monotonic() < deadline:
            payload = self.runner.run_json(
                [
                    "aws",
                    "logs",
                    "get-query-results",
                    "--region",
                    request.scope["region"],
                    "--query-id",
                    query_token,
                    "--output",
                    "json",
                ],
                count_toward_budget=False,
            )
            status = payload.get("status")
            if status == "Complete":
                break
            if status in {"Failed", "Cancelled", "Timeout", "Unknown"}:
                raise RuntimeError(f"Logs Insights query ended with status {status}")
            time.sleep(1.0)
        else:
            try:
                self.runner.run_json(
                    [
                        "aws",
                        "logs",
                        "stop-query",
                        "--region",
                        request.scope["region"],
                        "--query-id",
                        query_token,
                        "--output",
                        "json",
                    ],
                    count_toward_budget=False,
                )
            finally:
                raise RuntimeError("Logs Insights query timed out and was cancelled")

        allowed_fields = query.get("allowed_fields", [])
        if not isinstance(allowed_fields, list) or not allowed_fields:
            raise ContractError("Logs Insights query must define allowed_fields")
        allowed = {str(field) for field in allowed_fields}
        rows = []
        for row in payload.get("results", [])[:limit]:
            selected = {
                str(cell.get("field")): cell.get("value")
                for cell in row
                if str(cell.get("field")) in allowed
            }
            cleaned, _ = redact(selected)
            rows.append(cleaned)
        statistics = payload.get("statistics", {})
        data = {
            "row_count": len(rows),
            "rows": rows,
            "records_matched": statistics.get("recordsMatched"),
            "records_scanned": statistics.get("recordsScanned"),
            "bytes_scanned": statistics.get("bytesScanned"),
            "log_group_count": len(log_groups),
        }
        return Evidence(
            f"ev-logs-{query_id}",
            self.source_name,
            query_id,
            "ok",
            f"Logs Insights {query_id}: {len(rows)} sanitized rows",
            data,
        )

    @staticmethod
    def _query_id(query: dict[str, Any]) -> str:
        query_id = str(query.get("id", ""))
        if not _QUERY_ID.fullmatch(query_id):
            raise ContractError("query catalog entry has an invalid id")
        return query_id

    @staticmethod
    def _aws_name(value: str, label: str) -> str:
        if not _AWS_NAME.fullmatch(value):
            raise ContractError(f"CloudWatch {label} is invalid")
        return value

    def _error(self, query_id: str, message: str) -> Evidence:
        cleaned, _ = redact(message)
        return Evidence(
            f"ev-cw-{query_id}-error",
            self.source_name,
            query_id,
            "error",
            f"CloudWatch evidence unavailable: {cleaned}",
        )
