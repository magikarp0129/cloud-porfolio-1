#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "agent-runtime" / "src"))

from cloud_portfolio_agents.alert_policy import (  # noqa: E402
    load_and_validate_alert_policy,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Monitoring Agent의 versioned alert policy를 검증합니다."
    )
    parser.add_argument(
        "policy",
        nargs="?",
        default=str(REPOSITORY_ROOT / "config/monitoring/alert-policy.example.json"),
    )
    args = parser.parse_args()
    try:
        policy = load_and_validate_alert_policy(args.policy)
    except (OSError, ValueError) as exc:
        print(f"monitoring alert policy validation: FAIL\n{exc}", file=sys.stderr)
        return 1
    status_counts: dict[str, int] = {}
    for rule in policy["rules"]:
        status = str(rule["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    counts = ", ".join(
        f"{key}={value}" for key, value in sorted(status_counts.items())
    )
    print(
        "monitoring alert policy validation: PASS "
        f"policy={policy['policy_version']} rules={len(policy['rules'])} {counts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
