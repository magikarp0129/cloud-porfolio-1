from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent-runtime" / "src"))

from cloud_portfolio_agents.cli import main  # noqa: E402
from cloud_portfolio_agents.contracts import RuntimeConfig, build_request  # noqa: E402
from cloud_portfolio_agents.triage import build_report  # noqa: E402


class TriageTests(unittest.TestCase):
    def test_fixture_run_writes_safe_report_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = main(
                [
                    "run",
                    "monitoring",
                    "--request",
                    str(ROOT / "examples/incidents/prod-api-5xx-request.json"),
                    "--config",
                    str(ROOT / "config/monitoring/runtime.example.json"),
                    "--fixture",
                    str(ROOT / "examples/incidents/prod-api-5xx-evidence.json"),
                    "--simulation",
                    "--output-dir",
                    directory,
                ]
            )
            self.assertEqual(result, 0)
            report = json.loads((Path(directory) / "report.json").read_text())
            report_schema = json.loads(
                (ROOT / "schemas/incident-report.schema.json").read_text()
            )
            encoded = json.dumps(report)
            self.assertEqual(report["status"], "simulation")
            self.assertTrue(report["simulation"])
            self.assertEqual(report["executed_mutations"], [])
            self.assertTrue(set(report_schema["required"]).issubset(report))
            self.assertIn(report["status"], report_schema["properties"]["status"]["enum"])
            self.assertLessEqual(
                len(report["executed_mutations"]),
                report_schema["properties"]["executed_mutations"]["maxItems"],
            )
            self.assertGreaterEqual(len(report["hypotheses"]), 2)
            self.assertNotIn("fake-test-token", encoded)
            self.assertNotIn("user@example.com", encoded)
            audit_lines = (Path(directory) / "audit.jsonl").read_text().splitlines()
            self.assertEqual(len(audit_lines), 2)
            mode = stat.S_IMODE((Path(directory) / "report.json").stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_fixture_requires_explicit_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = main(
                [
                    "run",
                    "monitoring",
                    "--request",
                    str(ROOT / "examples/incidents/prod-api-5xx-request.json"),
                    "--config",
                    str(ROOT / "config/monitoring/runtime.example.json"),
                    "--fixture",
                    str(ROOT / "examples/incidents/prod-api-5xx-evidence.json"),
                    "--output-dir",
                    directory,
                ]
            )
            self.assertEqual(result, 2)

    def test_validate_command(self) -> None:
        result = main(
            [
                "validate",
                "--request",
                str(ROOT / "examples/incidents/prod-api-5xx-request.json"),
                "--config",
                str(ROOT / "config/monitoring/runtime.example.json"),
            ]
        )
        self.assertEqual(result, 0)

    def test_zero_diagnostic_evidence_is_blocked(self) -> None:
        config = RuntimeConfig.from_dict(
            json.loads((ROOT / "config/monitoring/runtime.example.json").read_text())
        )
        request = build_request(
            json.loads(
                (ROOT / "examples/incidents/prod-api-5xx-request.json").read_text()
            ),
            config,
        )
        report = build_report(request, config, [], tool_calls=0)
        self.assertEqual(report["status"], "blocked")

    def test_live_run_requires_server_owned_policy_pin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                "os.environ",
                {"AGENT_CONFIG_ROOT": "", "AGENT_POLICY_SHA256": ""},
                clear=False,
            ):
                result = main(
                    [
                        "run",
                        "monitoring",
                        "--request",
                        str(ROOT / "examples/incidents/prod-api-5xx-request.json"),
                        "--config",
                        str(ROOT / "config/monitoring/runtime.example.json"),
                        "--output-dir",
                        directory,
                    ]
                )
        self.assertEqual(result, 2)



if __name__ == "__main__":
    unittest.main()
