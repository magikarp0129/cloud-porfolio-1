from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

from ..contracts import ContractError, IncidentRequest, RuntimeLimits
from ..redaction import redact_text


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    query_id: str
    status: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    observed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "query_id": self.query_id,
            "status": self.status,
            "summary": self.summary,
            "data": self.data,
            "warnings": list(self.warnings),
            "observed_at": self.observed_at,
        }


class ToolBudget:
    def __init__(self, maximum: int, total_timeout_seconds: int | None = None):
        self.maximum = maximum
        self.used = 0
        self.actual_calls = 0
        self.deadline = (
            time.monotonic() + total_timeout_seconds
            if total_timeout_seconds is not None
            else None
        )

    def consume(self, *, logical_call: bool = True) -> None:
        if logical_call and self.used >= self.maximum:
            raise ContractError("tool-call budget exhausted")
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise ContractError("incident request timeout exhausted")
        if logical_call:
            self.used += 1
        self.actual_calls += 1

    def timeout(self, per_call_seconds: int) -> float:
        if self.deadline is None:
            return float(per_call_seconds)
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ContractError("incident request timeout exhausted")
        return max(0.1, min(float(per_call_seconds), remaining))


_PLACEHOLDER = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")


def render_template(value: str, request: IncidentRequest) -> str:
    context = request.template_context

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise ContractError(f"query template references unknown scope key: {key}")
        return context[key]

    return _PLACEHOLDER.sub(replace, value)


class CommandRunner:
    _ALLOWED_EXECUTABLES = {"aws", "kubectl"}
    _ALLOWED_AWS_OPERATIONS = {
        ("cloudwatch", "get-metric-statistics"),
        ("eks", "describe-cluster"),
        ("logs", "get-query-results"),
        ("logs", "start-query"),
        ("logs", "stop-query"),
        ("sts", "get-caller-identity"),
    }

    def __init__(self, limits: RuntimeLimits, budget: ToolBudget):
        self.limits = limits
        self.budget = budget

    def run_json(
        self, args: list[str], *, count_toward_budget: bool = True
    ) -> dict[str, Any]:
        if not args or args[0] not in self._ALLOWED_EXECUTABLES:
            raise ContractError("command executable is not allowlisted")
        if args[0] == "aws" and (
            len(args) < 3 or tuple(args[1:3]) not in self._ALLOWED_AWS_OPERATIONS
        ):
            raise ContractError("AWS operation is not allowlisted")
        if args[0] == "kubectl":
            operation_index = 1
            if len(args) > 2 and args[1] == "--context":
                operation_index = 3
            is_get = len(args) > operation_index and args[operation_index] == "get"
            is_safe_config_view = (
                len(args) > operation_index + 1
                and args[operation_index : operation_index + 2] == ["config", "view"]
                and "--minify" in args
                and "--raw" not in args
            )
            if not is_get and not is_safe_config_view:
                raise ContractError("kubectl operation is not allowlisted")
        executable = shutil.which(args[0])
        if executable is None:
            raise RuntimeError(f"required executable is not installed: {args[0]}")
        self.budget.consume(logical_call=count_toward_budget)
        try:
            completed = subprocess.run(
                [executable, *args[1:]],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.budget.timeout(self.limits.tool_timeout_seconds),
                shell=False,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{args[0]} query timed out") from exc
        if completed.returncode != 0:
            message, _ = redact_text(completed.stderr.strip()[:1000])
            raise RuntimeError(f"{args[0]} query failed: {message}")
        encoded = completed.stdout.encode("utf-8")
        if len(encoded) > self.limits.max_response_bytes:
            raise RuntimeError("tool response exceeded the configured byte limit")
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{args[0]} returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"{args[0]} response must be a JSON object")
        return value


class HttpClient:
    def __init__(self, limits: RuntimeLimits, budget: ToolBudget):
        self.limits = limits
        self.budget = budget

    @staticmethod
    def validate_base_url(base_url: str, allowed_hosts: list[str]) -> None:
        parsed = urlparse(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ContractError("HTTP adapter endpoints must use an HTTPS URL without userinfo")
        if parsed.hostname not in allowed_hosts:
            raise ContractError("HTTP adapter host is not in allowed_hosts")
        try:
            addresses = {
                ipaddress.ip_address(result[4][0])
                for result in socket.getaddrinfo(parsed.hostname, parsed.port or 443)
            }
        except socket.gaierror as exc:
            raise ContractError("HTTP adapter host cannot be resolved") from exc
        if not addresses or any(
            address.is_loopback
            or address.is_link_local
            or address.is_unspecified
            or address.is_multicast
            for address in addresses
        ):
            raise ContractError(
                "HTTP adapter host resolves to a forbidden loopback, link-local, unspecified, or multicast address"
            )

    def get_json(
        self, url: str, *, headers: Mapping[str, str], allowed_hosts: list[str]
    ) -> dict[str, Any]:
        self.validate_base_url(url, allowed_hosts)
        self.budget.consume()
        request = urllib.request.Request(url, headers=dict(headers), method="GET")
        try:
            opener = urllib.request.build_opener(_NoRedirectHandler())
            with opener.open(
                request, timeout=self.budget.timeout(self.limits.tool_timeout_seconds)
            ) as response:
                raw = response.read(self.limits.max_response_bytes + 1)
        except (urllib.error.URLError, TimeoutError) as exc:
            message, _ = redact_text(str(exc))
            raise RuntimeError(f"HTTPS query failed: {message}") from exc
        if len(raw) > self.limits.max_response_bytes:
            raise RuntimeError("HTTP response exceeded the configured byte limit")
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("HTTP adapter returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise RuntimeError("HTTP adapter response must be a JSON object")
        return value


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None
