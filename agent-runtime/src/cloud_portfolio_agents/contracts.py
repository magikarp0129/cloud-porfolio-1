from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


class ContractError(ValueError):
    """Raised when an incident request or runtime config violates policy."""


_SAFE_VALUE = re.compile(r"^[A-Za-z0-9/][A-Za-z0-9_.:/=@+-]{0,255}$")
_REQUEST_ID = re.compile(r"^req-[A-Za-z0-9][A-Za-z0-9-]{5,127}$")
_INCIDENT_ID = re.compile(r"^INC-[0-9]{4}-[0-9]{4,12}$")
_ALLOWED_ENVIRONMENTS = {"dev", "stg", "prod"}
_ALLOWED_DATA_CLASSES = {"public", "internal", "confidential", "restricted"}
_REJECTED_IDENTITY_FIELDS = {
    "user_id",
    "role",
    "account_id",
    "approval",
    "approved",
    "principal",
    "principal_arn",
}
_ALLOWED_REQUEST_FIELDS = {
    "request_id",
    "agent_id",
    "task",
    "repository",
    "environment",
    "mode",
    "incident_ticket",
    "data_classification",
    "max_cost_usd",
    "timeout_seconds",
    "incident",
    "scope",
    "requested_queries",
}
_ALLOWED_INCIDENT_FIELDS = {"severity", "started_at", "ended_at"}


def load_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        if source.stat().st_size > 1_000_000:
            raise ContractError(f"JSON input {path} exceeds the 1 MB limit")
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON root in {path} must be an object")
    return value


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{key} must be a non-empty string")
    return value.strip()


def _parse_time(value: Any, key: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError(f"{key} must be an RFC3339 timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ContractError(f"{key} must be an RFC3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"{key} must include a timezone")
    return parsed


def safe_scope_value(value: str, key: str) -> str:
    if not _SAFE_VALUE.fullmatch(value):
        raise ContractError(f"scope.{key} contains unsupported characters")
    return value


@dataclass(frozen=True)
class IncidentRequest:
    request_id: str
    agent_id: str
    task: str
    repository: str
    environment: str
    mode: str
    incident_ticket: str
    data_classification: str
    max_cost_usd: float
    timeout_seconds: int
    severity: str
    start: datetime
    end: datetime
    scope: dict[str, str]
    requested_queries: tuple[str, ...]

    @property
    def window_seconds(self) -> int:
        return int((self.end - self.start).total_seconds())

    @property
    def template_context(self) -> dict[str, str]:
        return {
            "environment": self.environment,
            "incident_ticket": self.incident_ticket,
            **self.scope,
        }

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any], *, max_window_minutes: int = 120
    ) -> "IncidentRequest":
        rejected = sorted(_REJECTED_IDENTITY_FIELDS.intersection(data))
        if rejected:
            raise ContractError(
                "caller-supplied identity or approval fields are forbidden: "
                + ", ".join(rejected)
            )
        unknown_fields = sorted(set(data).difference(_ALLOWED_REQUEST_FIELDS))
        if unknown_fields:
            raise ContractError(
                "incident request contains unknown fields: " + ", ".join(unknown_fields)
            )

        request_id = _required_string(data, "request_id")
        if not _REQUEST_ID.fullmatch(request_id):
            raise ContractError("request_id must use the req-<opaque-id> format")

        agent_id = _required_string(data, "agent_id")
        if agent_id != "monitoring":
            raise ContractError("incident triage only supports agent_id=monitoring")
        mode = _required_string(data, "mode")
        if mode != "read":
            raise ContractError("incident triage only supports mode=read")

        incident_ticket = _required_string(data, "incident_ticket")
        if not _INCIDENT_ID.fullmatch(incident_ticket):
            raise ContractError("incident_ticket must use INC-YYYY-NNNN format")

        environment = _required_string(data, "environment")
        if environment not in _ALLOWED_ENVIRONMENTS:
            raise ContractError("environment must be dev, stg, or prod")

        data_classification = _required_string(data, "data_classification")
        if data_classification not in _ALLOWED_DATA_CLASSES:
            raise ContractError("unsupported data_classification")

        try:
            max_cost_usd = float(data.get("max_cost_usd"))
        except (TypeError, ValueError) as exc:
            raise ContractError("max_cost_usd must be a number") from exc
        if not 0 < max_cost_usd <= 25:
            raise ContractError("max_cost_usd must be greater than 0 and at most 25")

        timeout_seconds = data.get("timeout_seconds", 300)
        if not isinstance(timeout_seconds, int) or not 10 <= timeout_seconds <= 900:
            raise ContractError("timeout_seconds must be an integer from 10 through 900")

        incident = data.get("incident")
        if not isinstance(incident, Mapping):
            raise ContractError("incident must be an object")
        unknown_incident = sorted(set(incident).difference(_ALLOWED_INCIDENT_FIELDS))
        if unknown_incident:
            raise ContractError(
                "incident contains unknown fields: " + ", ".join(unknown_incident)
            )
        severity = _required_string(incident, "severity").lower()
        if severity not in {"critical", "high", "warning", "info"}:
            raise ContractError("incident.severity is unsupported")
        start = _parse_time(incident.get("started_at"), "incident.started_at")
        end = _parse_time(incident.get("ended_at"), "incident.ended_at")
        if end <= start:
            raise ContractError("incident.ended_at must be after incident.started_at")
        if (end - start).total_seconds() > max_window_minutes * 60:
            raise ContractError(
                f"incident query window exceeds {max_window_minutes} minutes"
            )

        scope_value = data.get("scope")
        if not isinstance(scope_value, Mapping):
            raise ContractError("scope must be an object")
        scope: dict[str, str] = {}
        for key, value in scope_value.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ContractError("scope keys and values must be strings")
            scope[key] = safe_scope_value(value, key)
        for key in ("region", "service"):
            if key not in scope:
                raise ContractError(f"scope.{key} is required")

        requested = data.get("requested_queries", [])
        if not isinstance(requested, list) or not all(
            isinstance(item, str) and _SAFE_VALUE.fullmatch(item) for item in requested
        ):
            raise ContractError("requested_queries must be a list of safe query IDs")
        if len(requested) != len(set(requested)):
            raise ContractError("requested_queries must not contain duplicates")

        task = _required_string(data, "task")
        if len(task) > 2000:
            raise ContractError("task must be at most 2000 characters")

        repository = _required_string(data, "repository")
        if len(repository) > 256:
            raise ContractError("repository must be at most 256 characters")

        return cls(
            request_id=request_id,
            agent_id=agent_id,
            task=task,
            repository=repository,
            environment=environment,
            mode=mode,
            incident_ticket=incident_ticket,
            data_classification=data_classification,
            max_cost_usd=max_cost_usd,
            timeout_seconds=timeout_seconds,
            severity=severity,
            start=start,
            end=end,
            scope=scope,
            requested_queries=tuple(requested),
        )


@dataclass(frozen=True)
class RuntimeLimits:
    max_window_minutes: int = 120
    max_tool_calls: int = 20
    max_log_groups: int = 5
    max_log_rows: int = 200
    max_response_bytes: int = 1_000_000
    tool_timeout_seconds: int = 30


@dataclass(frozen=True)
class RuntimeConfig:
    policy_version: str
    limits: RuntimeLimits
    environments: dict[str, dict[str, Any]]
    sources: dict[str, dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RuntimeConfig":
        if data.get("schema_version") != "1.0":
            raise ContractError("runtime config schema_version must be 1.0")
        policy_version = _required_string(data, "policy_version")
        limits_data = data.get("limits", {})
        if not isinstance(limits_data, Mapping):
            raise ContractError("limits must be an object")
        try:
            limits = RuntimeLimits(
                max_window_minutes=int(limits_data.get("max_window_minutes", 120)),
                max_tool_calls=int(limits_data.get("max_tool_calls", 20)),
                max_log_groups=int(limits_data.get("max_log_groups", 5)),
                max_log_rows=int(limits_data.get("max_log_rows", 200)),
                max_response_bytes=int(limits_data.get("max_response_bytes", 1_000_000)),
                tool_timeout_seconds=int(limits_data.get("tool_timeout_seconds", 30)),
            )
        except (TypeError, ValueError) as exc:
            raise ContractError("runtime limits must be integers") from exc
        if not 1 <= limits.max_window_minutes <= 360:
            raise ContractError("max_window_minutes must be from 1 through 360")
        if not 1 <= limits.max_tool_calls <= 50:
            raise ContractError("max_tool_calls must be from 1 through 50")
        if not 1 <= limits.max_log_groups <= 10:
            raise ContractError("max_log_groups must be from 1 through 10")
        if not 1 <= limits.max_log_rows <= 1000:
            raise ContractError("max_log_rows must be from 1 through 1000")
        if not 10_000 <= limits.max_response_bytes <= 5_000_000:
            raise ContractError("max_response_bytes is outside the safe range")
        if not 5 <= limits.tool_timeout_seconds <= 60:
            raise ContractError("tool_timeout_seconds must be from 5 through 60")

        environments = data.get("environments")
        sources = data.get("sources")
        if not isinstance(environments, dict) or not isinstance(sources, dict):
            raise ContractError("environments and sources must be objects")
        if not all(isinstance(value, dict) for value in environments.values()):
            raise ContractError("each environment registry entry must be an object")
        if not all(isinstance(value, dict) for value in sources.values()):
            raise ContractError("each source configuration must be an object")
        return cls(policy_version, limits, environments, sources)

    def validate_request_scope(self, request: IncidentRequest) -> None:
        environment = self.environments.get(request.environment)
        if not isinstance(environment, Mapping):
            raise ContractError(
                f"environment {request.environment} is not registered in runtime config"
            )
        expected_region = environment.get("region")
        if expected_region and request.scope["region"] != expected_region:
            raise ContractError("request region does not match the environment registry")
        services = environment.get("services")
        if not isinstance(services, Mapping) or request.scope["service"] not in services:
            raise ContractError("service is not registered for the requested environment")
        service = services[request.scope["service"]]
        if not isinstance(service, Mapping):
            raise ContractError("registered service definition must be an object")
        registered_scope = service.get("scope", {})
        if not isinstance(registered_scope, Mapping):
            raise ContractError("registered service scope must be an object")
        allowed_scope_keys = {"region", "service", *registered_scope.keys()}
        unexpected_scope = sorted(set(request.scope).difference(allowed_scope_keys))
        if unexpected_scope:
            raise ContractError(
                "request scope contains keys not present in the service registry: "
                + ", ".join(unexpected_scope)
            )
        for key, expected in registered_scope.items():
            if request.scope.get(key) != expected:
                raise ContractError(
                    f"scope.{key} does not match the registered service inventory"
                )
        allowed_classes = environment.get(
            "allowed_data_classifications", ["internal"]
        )
        if request.data_classification not in allowed_classes:
            raise ContractError(
                "data classification is not permitted by the environment registry"
            )
        try:
            environment_window = int(
                environment.get("max_window_minutes", self.limits.max_window_minutes)
            )
        except (TypeError, ValueError) as exc:
            raise ContractError("environment max_window_minutes must be an integer") from exc
        if request.window_seconds > environment_window * 60:
            raise ContractError(
                "incident query window exceeds the environment-specific policy"
            )


def build_request(data: Mapping[str, Any], config: RuntimeConfig) -> IncidentRequest:
    request = IncidentRequest.from_dict(
        data, max_window_minutes=config.limits.max_window_minutes
    )
    config.validate_request_scope(request)
    return request
