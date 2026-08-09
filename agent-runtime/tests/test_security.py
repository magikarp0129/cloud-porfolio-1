from __future__ import annotations

import json
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent-runtime" / "src"))

from cloud_portfolio_agents.adapters.base import (  # noqa: E402
    CommandRunner,
    HttpClient,
    ToolBudget,
)
from cloud_portfolio_agents.adapters.cloudwatch import CloudWatchAdapter  # noqa: E402
from cloud_portfolio_agents.adapters.kubernetes import KubernetesAdapter  # noqa: E402
from cloud_portfolio_agents.contracts import (  # noqa: E402
    ContractError,
    RuntimeConfig,
    build_request,
)
from cloud_portfolio_agents.redaction import redact  # noqa: E402
from cloud_portfolio_agents.triage import verify_runtime_identity  # noqa: E402


class SecurityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = RuntimeConfig.from_dict(
            json.loads((ROOT / "config/monitoring/runtime.example.json").read_text())
        )
        cls.request = build_request(
            json.loads(
                (ROOT / "examples/incidents/prod-api-5xx-request.json").read_text()
            ),
            cls.config,
        )

    def test_redacts_credentials_and_pii(self) -> None:
        payload = {
            "Authorization": "Bearer abcdefghijklmnop",
            "line": "AKIAABCDEFGHIJKLMNOP user@example.com 010-1234-5678",
        }
        cleaned, count = redact(payload)
        encoded = json.dumps(cleaned)
        self.assertGreaterEqual(count, 4)
        self.assertNotIn("abcdefghijklmnop", encoded)
        self.assertNotIn("AKIAABCDEFGHIJKLMNOP", encoded)
        self.assertNotIn("user@example.com", encoded)
        self.assertNotIn("010-1234-5678", encoded)

    def test_command_runner_rejects_shell(self) -> None:
        runner = CommandRunner(self.config.limits, ToolBudget(1))
        with self.assertRaisesRegex(ContractError, "not allowlisted"):
            runner.run_json(["sh", "-c", "id"])

    def test_command_runner_rejects_cloud_and_kubernetes_mutations(self) -> None:
        runner = CommandRunner(self.config.limits, ToolBudget(2))
        with self.assertRaisesRegex(ContractError, "AWS operation"):
            runner.run_json(["aws", "ec2", "terminate-instances"])
        with self.assertRaisesRegex(ContractError, "kubectl operation"):
            runner.run_json(["kubectl", "delete", "pod", "example"])

    def test_http_client_rejects_localhost_and_unlisted_host(self) -> None:
        with self.assertRaises(ContractError):
            HttpClient.validate_base_url("https://127.0.0.1/api", ["127.0.0.1"])
        with self.assertRaises(ContractError):
            HttpClient.validate_base_url(
                "https://attacker.example/api", ["prometheus.example.internal"]
            )

    @patch("cloud_portfolio_agents.adapters.base.socket.getaddrinfo")
    def test_http_client_rejects_dns_to_link_local(self, getaddrinfo) -> None:
        getaddrinfo.return_value = [(2, 1, 6, "", ("169.254.169.254", 443))]
        with self.assertRaisesRegex(ContractError, "forbidden"):
            HttpClient.validate_base_url(
                "https://prometheus.example.internal/api",
                ["prometheus.example.internal"],
            )

    def test_logs_insights_rejects_unmask_before_execution(self) -> None:
        adapter = CloudWatchAdapter(self.config, ToolBudget(2))
        with self.assertRaisesRegex(ContractError, "forbidden"):
            adapter._logs_insights(
                self.request,
                {
                    "id": "unsafe",
                    "query": "fields @message | unmask @message",
                    "log_groups": ["/aws/example"],
                    "allowed_fields": ["@message"],
                },
            )

    @patch("cloud_portfolio_agents.triage.CommandRunner.run_json")
    def test_runtime_identity_is_bound_to_role_and_request(self, run_json) -> None:
        run_json.return_value = {
            "Account": "333333333333",
            "Arn": "arn:aws:sts::333333333333:assumed-role/portfolio-prod-monitoring-diagnostic/req-01JEXAMPLE142",
        }
        evidence, verified = verify_runtime_identity(
            self.request, self.config, ToolBudget(2)
        )
        self.assertTrue(verified)
        self.assertEqual(evidence.status, "ok")

        run_json.return_value["Arn"] = (
            "arn:aws:sts::333333333333:assumed-role/other-role/req-01JEXAMPLE142"
        )
        evidence, verified = verify_runtime_identity(
            self.request, self.config, ToolBudget(2)
        )
        self.assertFalse(verified)
        self.assertEqual(evidence.status, "error")

    def test_kubernetes_context_is_bound_to_registered_eks_endpoint(self) -> None:
        adapter = KubernetesAdapter(self.config, ToolBudget(4))
        adapter.runner.run_json = Mock(
            side_effect=[
                {
                    "arn": "arn:aws:eks:ap-northeast-2:333333333333:cluster/portfolio-prod-eks",
                    "endpoint": "https://expected.eks.example",
                },
                {
                    "clusters": [
                        {"cluster": {"server": "https://expected.eks.example"}}
                    ],
                    "contexts": [{"context": {"user": "diagnostic"}}],
                    "users": [
                        {
                            "name": "diagnostic",
                            "user": {
                                "exec": {
                                    "command": "aws",
                                    "args": [
                                        "eks",
                                        "get-token",
                                        "--cluster-name",
                                        "portfolio-prod-eks",
                                    ],
                                }
                            },
                        }
                    ],
                },
            ]
        )
        adapter._verify_cluster_binding(
            self.request, ["kubectl", "--context", "portfolio-prod-eks-readonly"]
        )

        adapter.runner.run_json = Mock(
            side_effect=[
                {
                    "arn": "arn:aws:eks:ap-northeast-2:333333333333:cluster/portfolio-prod-eks",
                    "endpoint": "https://expected.eks.example",
                },
                {
                    "clusters": [{"cluster": {"server": "https://other.example"}}],
                    "contexts": [{"context": {"user": "diagnostic"}}],
                    "users": [{"name": "diagnostic", "user": {}}],
                },
            ]
        )
        with self.assertRaisesRegex(ContractError, "endpoint"):
            adapter._verify_cluster_binding(
                self.request,
                ["kubectl", "--context", "portfolio-prod-eks-readonly"],
            )


if __name__ == "__main__":
    unittest.main()
