from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import ContractError, RuntimeConfig, build_request, load_json
from .triage import (
    build_report,
    collect_evidence,
    load_fixture,
    render_markdown,
    validate_requested_queries,
)


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    os.replace(temporary, path)
    os.chmod(path, 0o600, follow_symlinks=False)


def _write_audit(path: Path, event: dict[str, Any]) -> None:
    line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, 0o600, follow_symlinks=False)


def _policy_digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _verify_live_policy(path: str) -> str:
    approved_root = os.environ.get("AGENT_CONFIG_ROOT")
    expected_digest = os.environ.get("AGENT_POLICY_SHA256")
    if not approved_root or not expected_digest:
        raise ContractError(
            "live runs require server-owned AGENT_CONFIG_ROOT and AGENT_POLICY_SHA256"
        )
    root = Path(approved_root).resolve(strict=True)
    candidate = Path(path)
    if candidate.is_symlink():
        raise ContractError("runtime config must not be a symbolic link")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_file() or root not in resolved.parents:
        raise ContractError("runtime config is outside the approved config root")
    digest = _policy_digest(str(resolved))
    if not hashlib.compare_digest(digest, expected_digest.lower()):
        raise ContractError("runtime config integrity check failed")
    return digest


def _load_contracts(
    request_path: str, config_path: str
) -> tuple[Any, RuntimeConfig]:
    config = RuntimeConfig.from_dict(load_json(config_path))
    request = build_request(load_json(request_path), config)
    validate_requested_queries(request, config)
    return request, config


def _validate(args: argparse.Namespace) -> int:
    request, config = _load_contracts(args.request, args.config)
    print(
        json.dumps(
            {
                "status": "valid",
                "request_id": request.request_id,
                "incident_ticket": request.incident_ticket,
                "environment": request.environment,
                "window_seconds": request.window_seconds,
                "policy_version": config.policy_version,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _run(args: argparse.Namespace) -> int:
    request, config = _load_contracts(args.request, args.config)
    if args.agent_id != "monitoring":
        raise ContractError("only the monitoring agent is implemented")

    if args.fixture and not args.simulation:
        raise ContractError("--fixture requires --simulation")
    if args.simulation and not args.fixture:
        raise ContractError("--simulation requires --fixture")
    policy_sha256 = _policy_digest(args.config) if args.simulation else _verify_live_policy(args.config)

    output_dir = Path(args.output_dir or f"artifacts/incidents/{request.incident_ticket}")
    if output_dir.is_symlink():
        raise ContractError("output directory must not be a symbolic link")
    output_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(output_dir, 0o700, follow_symlinks=False)
    audit_path = output_dir / "audit.jsonl"
    _write_audit(
        audit_path,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "incident_triage_started",
            "request_id": request.request_id,
            "incident_ticket": request.incident_ticket,
            "agent_id": request.agent_id,
            "environment": request.environment,
            "mode": request.mode,
            "policy_version": config.policy_version,
            "policy_sha256": policy_sha256,
            "simulation": args.simulation,
        },
    )

    if args.fixture:
        evidence = load_fixture(args.fixture)
        tool_calls = 0
    else:
        evidence, tool_calls = collect_evidence(request, config)
    report = build_report(
        request,
        config,
        evidence,
        tool_calls=tool_calls,
        simulation=args.simulation,
        policy_sha256=policy_sha256,
    )
    report_path = output_dir / "report.json"
    markdown_path = output_dir / "report.md"
    _atomic_write(
        report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    _atomic_write(markdown_path, render_markdown(report))
    _write_audit(
        audit_path,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "incident_triage_finished",
            "request_id": request.request_id,
            "trace_id": report["trace_id"],
            "incident_ticket": request.incident_ticket,
            "status": report["status"],
            "simulation": args.simulation,
            "tool_calls": tool_calls,
            "successful_evidence_items": report["summary"]["successful_evidence_items"],
            "failed_evidence_items": report["summary"]["failed_evidence_items"],
            "redaction_count": report["summary"]["redaction_count"],
        },
    )
    print(str(markdown_path))
    return 0 if report["status"] in {"complete", "simulation"} else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentctl", description="Cloud portfolio Agent operator CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate request and policy")
    validate.add_argument("--request", required=True)
    validate.add_argument("--config", required=True)
    validate.set_defaults(handler=_validate)

    run = subparsers.add_parser("run", help="run an Agent profile")
    run.add_argument("agent_id", choices=["monitoring"])
    run.add_argument("--request", required=True)
    run.add_argument("--config", required=True)
    run.add_argument("--fixture", help="offline evidence fixture; no external tools run")
    run.add_argument(
        "--simulation",
        action="store_true",
        help="mark an offline fixture run as non-operational simulation",
    )
    run.add_argument("--output-dir")
    run.set_defaults(handler=_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ContractError as exc:
        print(f"policy validation failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"runtime I/O failed: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
