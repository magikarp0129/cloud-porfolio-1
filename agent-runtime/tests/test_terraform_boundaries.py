from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TerraformBoundaryTests(unittest.TestCase):
    def test_monitoring_role_contains_deny_guardrails(self) -> None:
        policy = (
            ROOT / "terraform/modules/monitoring-agent-access/main.tf"
        ).read_text()
        for action in (
            "logs:Unmask",
            "secretsmanager:GetSecretValue",
            "ssm:StartSession",
            "ssm:SendCommand",
            "kms:Decrypt",
            "sts:AssumeRole",
            "cloudwatch:DisableAlarmActions",
            "ec2:TerminateInstances",
        ):
            self.assertIn(f'"{action}"', policy)
        self.assertNotIn("ReadOnlyAccess", policy)
        self.assertNotIn("AdministratorAccess", policy)

    def test_monitoring_kubernetes_role_has_no_sensitive_resources_or_writes(self) -> None:
        source = (
            ROOT / "terraform/modules/kubernetes-platform/main.tf"
        ).read_text()
        role = source.split(
            'resource "kubernetes_role_v1" "monitoring_agent_workload"', 1
        )[1].split(
            'resource "kubernetes_role_binding_v1" "monitoring_agent_workload"', 1
        )[0]
        for forbidden in (
            '"secrets"',
            '"configmaps"',
            '"serviceaccounts"',
            '"pods/log"',
            '"pods/exec"',
            '"create"',
            '"update"',
            '"patch"',
            '"delete"',
        ):
            self.assertNotIn(forbidden, role)
        self.assertIn('verbs      = ["get", "list"]', role)


if __name__ == "__main__":
    unittest.main()
