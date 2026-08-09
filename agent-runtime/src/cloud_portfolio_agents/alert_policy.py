from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


_DURATION = re.compile(r"^[1-9][0-9]*[smh]$")
_COMPARISONS = {"gte", "gt", "lte", "lt"}
_MISSING_DATA = {"missing", "ignore", "breaching", "notBreaching"}
_STATUSES = {"documented_target", "query_catalog_ready", "implemented"}


def load_and_validate_alert_policy(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("alert policy root must be an object")
    errors = validate_alert_policy(payload)
    if errors:
        raise ValueError("invalid alert policy:\n- " + "\n- ".join(errors))
    return payload


def validate_alert_policy(policy: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not _text(policy.get("policy_version")):
        errors.append("policy_version is required")
    if policy.get("implementation_status") not in _STATUSES:
        errors.append("implementation_status is invalid")

    defaults = policy.get("defaults")
    if not isinstance(defaults, Mapping):
        errors.append("defaults must be an object")
    else:
        _check_duration(defaults.get("evaluation_period"), "defaults.evaluation_period", errors)
        _check_duration(defaults.get("recovery_for"), "defaults.recovery_for", errors)
        if defaults.get("missing_data") not in _MISSING_DATA:
            errors.append("defaults.missing_data is invalid")
        for route_key in ("warning_routes", "critical_routes"):
            routes = defaults.get(route_key)
            if not isinstance(routes, list) or not routes or not all(_text(value) for value in routes):
                errors.append(f"defaults.{route_key} must be a non-empty string array")

    rules = policy.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty array")
        return errors

    rule_ids: set[str] = set()
    query_ids: set[str] = set()
    for index, rule in enumerate(rules):
        prefix = f"rules[{index}]"
        if not isinstance(rule, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        rule_id = rule.get("rule_id")
        query_id = rule.get("query_id")
        for key in ("rule_id", "query_id", "source", "scope", "unit", "query", "runbook"):
            if not _text(rule.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if isinstance(rule_id, str):
            if rule_id in rule_ids:
                errors.append(f"duplicate rule_id: {rule_id}")
            rule_ids.add(rule_id)
        if isinstance(query_id, str):
            if query_id in query_ids:
                errors.append(f"duplicate query_id: {query_id}")
            query_ids.add(query_id)
        if rule.get("status") not in _STATUSES:
            errors.append(f"{prefix}.status is invalid")
        if rule.get("missing_data") not in _MISSING_DATA:
            errors.append(f"{prefix}.missing_data is invalid")

        warning = _check_condition(rule.get("warning"), f"{prefix}.warning", errors)
        critical = _check_condition(rule.get("critical"), f"{prefix}.critical", errors)
        _check_condition(rule.get("recovery"), f"{prefix}.recovery", errors, require_datapoints=False)
        if warning and critical and warning[0] == critical[0]:
            comparison, warning_value = warning
            critical_value = critical[1]
            if comparison in {"gte", "gt"} and critical_value < warning_value:
                errors.append(f"{prefix}.critical threshold must be >= warning threshold")
            if comparison in {"lte", "lt"} and critical_value > warning_value:
                errors.append(f"{prefix}.critical threshold must be <= warning threshold")
    return errors


def _check_condition(
    value: Any,
    prefix: str,
    errors: list[str],
    *,
    require_datapoints: bool = True,
) -> tuple[str, float] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{prefix} must be an object")
        return None
    comparison = value.get("comparison")
    if comparison not in _COMPARISONS:
        errors.append(f"{prefix}.comparison is invalid")
    threshold = value.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        errors.append(f"{prefix}.threshold must be numeric")
        threshold_value = 0.0
    else:
        threshold_value = float(threshold)
    _check_duration(value.get("for"), f"{prefix}.for", errors)
    if require_datapoints:
        periods = value.get("evaluation_periods")
        datapoints = value.get("datapoints_to_alarm")
        if not isinstance(periods, int) or periods < 1:
            errors.append(f"{prefix}.evaluation_periods must be a positive integer")
        if not isinstance(datapoints, int) or datapoints < 1:
            errors.append(f"{prefix}.datapoints_to_alarm must be a positive integer")
        if isinstance(periods, int) and isinstance(datapoints, int) and datapoints > periods:
            errors.append(f"{prefix}.datapoints_to_alarm cannot exceed evaluation_periods")
    return (str(comparison), threshold_value)


def _check_duration(value: Any, key: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _DURATION.fullmatch(value):
        errors.append(f"{key} must use a positive duration such as 5m")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
