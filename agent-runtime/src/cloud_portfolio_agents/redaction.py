from __future__ import annotations

import re
from typing import Any


_SENSITIVE_KEY = re.compile(
    r"(?:authorization|cookie|password|passwd|secret|token|api[_-]?key|session)",
    re.IGNORECASE,
)
_PATTERNS = (
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?:\.[A-Za-z0-9_-]+)?\b"),
    re.compile(r"(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[=:]\s*[^\s,;]+"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\d)(?:01[016789])[- ]?\d{3,4}[- ]?\d{4}(?!\d)"),
)


def redact_text(value: str) -> tuple[str, int]:
    redacted = value
    count = 0
    for pattern in _PATTERNS:
        redacted, replacements = pattern.subn("[REDACTED]", redacted)
        count += replacements
    return redacted, count


def redact(value: Any) -> tuple[Any, int]:
    if isinstance(value, dict):
        result: dict[Any, Any] = {}
        count = 0
        for key, child in value.items():
            if isinstance(key, str) and _SENSITIVE_KEY.search(key):
                result[key] = "[REDACTED]"
                count += 1
            else:
                result[key], child_count = redact(child)
                count += child_count
        return result, count
    if isinstance(value, list):
        result_list = []
        count = 0
        for child in value:
            cleaned, child_count = redact(child)
            result_list.append(cleaned)
            count += child_count
        return result_list, count
    if isinstance(value, tuple):
        cleaned, count = redact(list(value))
        return tuple(cleaned), count
    if isinstance(value, str):
        return redact_text(value)
    return value, 0

