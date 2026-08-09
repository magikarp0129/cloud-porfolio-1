from __future__ import annotations

import math
import os
import re
from typing import Any
from urllib.parse import urlencode

from ..contracts import ContractError, IncidentRequest, RuntimeConfig
from .base import Evidence, HttpClient, ToolBudget, render_template


class PrometheusAdapter:
    source_name = "prometheus"
    _SAFE_LABELS = {
        "cluster",
        "container",
        "device",
        "environment",
        "instance",
        "job",
        "mountpoint",
        "namespace",
        "node",
        "persistentvolumeclaim",
        "pod",
        "service",
        "workload",
        "status",
        "reason",
    }
    _ENV_NAME = re.compile(r"^AGENT_[A-Z0-9_]{1,64}$")

    def __init__(self, config: RuntimeConfig, budget: ToolBudget):
        self.config = config
        self.source = config.sources.get(self.source_name, {})
        self.http = HttpClient(config.limits, budget)

    def collect(self, request: IncidentRequest) -> list[Evidence]:
        if not self.source.get("enabled", False):
            return []
        try:
            base_url, headers, allowed_hosts = self._connection()
        except Exception as exc:
            return [self._error("prometheus_connection", str(exc))]

        evidence = []
        for entry in self.source.get("queries", []):
            query_id = str(entry.get("id", ""))
            if request.requested_queries and query_id not in request.requested_queries:
                continue
            try:
                evidence.append(
                    self._query(request, entry, base_url, headers, allowed_hosts)
                )
            except Exception as exc:
                evidence.append(self._error(query_id or "prometheus_query", str(exc)))
        return evidence

    def _connection(self) -> tuple[str, dict[str, str], list[str]]:
        base_env = self.source.get("base_url_env")
        if not isinstance(base_env, str) or not self._ENV_NAME.fullmatch(base_env):
            raise ContractError("Prometheus base_url_env is required")
        base_url = os.environ.get(base_env, "").rstrip("/")
        if not base_url:
            raise ContractError(f"Prometheus endpoint environment variable {base_env} is unset")
        allowed_hosts = self.source.get("allowed_hosts", [])
        if not isinstance(allowed_hosts, list) or not allowed_hosts:
            raise ContractError("Prometheus allowed_hosts is required")
        self.http.validate_base_url(base_url, [str(value) for value in allowed_hosts])
        headers = {"Accept": "application/json"}
        token_env = self.source.get("token_env")
        if token_env:
            if not isinstance(token_env, str) or not self._ENV_NAME.fullmatch(token_env):
                raise ContractError("Prometheus token_env must use an AGENT_ variable")
            token = os.environ.get(str(token_env), "")
            if not token:
                raise ContractError("Prometheus token environment variable is unset")
            headers["Authorization"] = f"Bearer {token}"
        return base_url, headers, [str(value) for value in allowed_hosts]

    def _query(
        self,
        request: IncidentRequest,
        entry: dict[str, Any],
        base_url: str,
        headers: dict[str, str],
        allowed_hosts: list[str],
    ) -> Evidence:
        query_id = str(entry.get("id", ""))
        if not query_id or not query_id.replace("_", "").replace("-", "").isalnum():
            raise ContractError("Prometheus query id is invalid")
        query = render_template(str(entry.get("query", "")), request)
        if not query or len(query) > 4096:
            raise ContractError("Prometheus query is empty or too long")
        step = int(entry.get("step_seconds", 60))
        if not 15 <= step <= 3600:
            raise ContractError("Prometheus step_seconds must be from 15 through 3600")
        params = urlencode(
            {
                "query": query,
                "start": request.start.timestamp(),
                "end": request.end.timestamp(),
                "step": step,
            }
        )
        payload = self.http.get_json(
            f"{base_url}/api/v1/query_range?{params}",
            headers=headers,
            allowed_hosts=allowed_hosts,
        )
        if payload.get("status") != "success":
            raise RuntimeError("Prometheus query did not succeed")
        result = payload.get("data", {}).get("result", [])
        max_series = min(int(entry.get("max_series", 50)), 100)
        if len(result) > max_series:
            raise RuntimeError("Prometheus result exceeded the configured series limit")
        series = []
        total_samples = 0
        for item in result:
            values = []
            for sample in item.get("values", []):
                try:
                    number = float(sample[1])
                except (IndexError, TypeError, ValueError):
                    continue
                if math.isfinite(number):
                    values.append(number)
            total_samples += len(values)
            labels = {
                key: value
                for key, value in item.get("metric", {}).items()
                if key in self._SAFE_LABELS
            }
            series.append(
                {
                    "labels": labels,
                    "sample_count": len(values),
                    "minimum": min(values) if values else None,
                    "maximum": max(values) if values else None,
                    "latest": values[-1] if values else None,
                }
            )
        return Evidence(
            f"ev-prom-{query_id}",
            self.source_name,
            query_id,
            "ok",
            f"Prometheus {query_id}: {len(series)} series, {total_samples} samples",
            {"series_count": len(series), "sample_count": total_samples, "series": series},
        )

    def _error(self, query_id: str, message: str) -> Evidence:
        return Evidence(
            f"ev-prom-{query_id}-error",
            self.source_name,
            query_id,
            "error",
            f"Prometheus evidence unavailable: {message}",
        )
