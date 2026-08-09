from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

from ..contracts import ContractError, IncidentRequest, RuntimeConfig
from .base import Evidence, HttpClient, ToolBudget, render_template


_DASHBOARD_UID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_ENV_NAME = re.compile(r"^AGENT_[A-Z0-9_]{1,64}$")


class GrafanaAdapter:
    """Reads dashboard metadata only; it never uses the data-source proxy API."""

    source_name = "grafana"

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
            return [self._error("grafana_connection", str(exc))]
        evidence = []
        for entry in self.source.get("dashboards", []):
            query_id = str(entry.get("id", ""))
            if request.requested_queries and query_id not in request.requested_queries:
                continue
            try:
                evidence.append(
                    self._dashboard(request, entry, base_url, headers, allowed_hosts)
                )
            except Exception as exc:
                evidence.append(self._error(query_id or "grafana_dashboard", str(exc)))
        return evidence

    def _connection(self) -> tuple[str, dict[str, str], list[str]]:
        base_env = self.source.get("base_url_env")
        token_env = self.source.get("token_env")
        if (
            not isinstance(base_env, str)
            or not _ENV_NAME.fullmatch(base_env)
            or not isinstance(token_env, str)
            or not _ENV_NAME.fullmatch(token_env)
        ):
            raise ContractError("Grafana base_url_env and token_env are required")
        base_url = os.environ.get(base_env, "").rstrip("/")
        token = os.environ.get(token_env, "")
        if not base_url or not token:
            raise ContractError("Grafana endpoint or Viewer token environment variable is unset")
        allowed_hosts = [str(value) for value in self.source.get("allowed_hosts", [])]
        if not allowed_hosts:
            raise ContractError("Grafana allowed_hosts is required")
        self.http.validate_base_url(base_url, allowed_hosts)
        return (
            base_url,
            {"Accept": "application/json", "Authorization": f"Bearer {token}"},
            allowed_hosts,
        )

    def _dashboard(
        self,
        request: IncidentRequest,
        entry: dict[str, Any],
        base_url: str,
        headers: dict[str, str],
        allowed_hosts: list[str],
    ) -> Evidence:
        query_id = str(entry.get("id", ""))
        uid = render_template(str(entry.get("uid", "")), request)
        if not _DASHBOARD_UID.fullmatch(uid):
            raise ContractError("Grafana dashboard UID is invalid")
        payload = self.http.get_json(
            f"{base_url}/api/dashboards/uid/{quote(uid)}",
            headers=headers,
            allowed_hosts=allowed_hosts,
        )
        dashboard = payload.get("dashboard", {})
        metadata = payload.get("meta", {})
        url = metadata.get("url")
        if isinstance(url, str) and url.startswith("/"):
            url = f"{base_url}{url}"
        data = {
            "uid": uid,
            "title": dashboard.get("title"),
            "tags": dashboard.get("tags", [])[:20],
            "version": dashboard.get("version"),
            "folder_title": metadata.get("folderTitle"),
            "dashboard_url": url,
        }
        return Evidence(
            f"ev-grafana-{query_id}",
            self.source_name,
            query_id,
            "ok",
            f"Grafana dashboard available: {data['title'] or uid}",
            data,
        )

    def _error(self, query_id: str, message: str) -> Evidence:
        return Evidence(
            f"ev-grafana-{query_id}-error",
            self.source_name,
            query_id,
            "error",
            f"Grafana metadata unavailable: {message}",
        )
