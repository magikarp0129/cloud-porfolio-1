from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent-runtime" / "src"))

from cloud_portfolio_agents.contracts import (  # noqa: E402
    ContractError,
    RuntimeConfig,
    build_request,
)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_data = json.loads(
            (ROOT / "config/monitoring/runtime.example.json").read_text()
        )
        cls.request_data = json.loads(
            (ROOT / "examples/incidents/prod-api-5xx-request.json").read_text()
        )
        cls.request_schema = json.loads(
            (ROOT / "schemas/incident-request.schema.json").read_text()
        )

    def build(self, request_data=None):
        config = RuntimeConfig.from_dict(copy.deepcopy(self.config_data))
        return build_request(request_data or copy.deepcopy(self.request_data), config)

    def test_valid_request(self) -> None:
        request = self.build()
        self.assertEqual(request.mode, "read")
        self.assertEqual(request.environment, "prod")
        self.assertEqual(request.window_seconds, 3600)

    def test_example_matches_request_schema_smoke_contract(self) -> None:
        schema = self.request_schema
        request = self.request_data

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue(set(schema["required"]).issubset(request))
        self.assertEqual(set(request).difference(schema["properties"]), set())
        self.assertFalse(schema["additionalProperties"])

        for key in ("agent_id", "mode"):
            self.assertEqual(request[key], schema["properties"][key]["const"])
        for key in ("environment", "data_classification"):
            self.assertIn(request[key], schema["properties"][key]["enum"])
        for key in ("request_id", "incident_ticket"):
            self.assertRegex(request[key], schema["properties"][key]["pattern"])

        incident_schema = schema["properties"]["incident"]
        self.assertTrue(set(incident_schema["required"]).issubset(request["incident"]))
        self.assertIn(
            request["incident"]["severity"],
            incident_schema["properties"]["severity"]["enum"],
        )
        scope_schema = schema["properties"]["scope"]
        self.assertTrue(set(scope_schema["required"]).issubset(request["scope"]))

    def test_rejects_mutating_mode(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["mode"] = "plan"
        with self.assertRaisesRegex(ContractError, "mode=read"):
            self.build(request)

    def test_rejects_caller_identity_and_approval(self) -> None:
        for field in ("user_id", "role", "account_id", "approval"):
            with self.subTest(field=field):
                request = copy.deepcopy(self.request_data)
                request[field] = "injected"
                with self.assertRaisesRegex(ContractError, "forbidden"):
                    self.build(request)

    def test_rejects_cross_environment_region(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["scope"]["region"] = "us-east-1"
        with self.assertRaisesRegex(ContractError, "does not match"):
            self.build(request)

    def test_rejects_excessive_window(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["incident"]["ended_at"] = "2026-08-08T06:10:00Z"
        with self.assertRaisesRegex(ContractError, "exceeds"):
            self.build(request)

    def test_rejects_restricted_data_without_jit_policy(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["data_classification"] = "restricted"
        with self.assertRaisesRegex(ContractError, "not permitted"):
            self.build(request)

    def test_rejects_resource_outside_service_inventory(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["scope"]["workload_log_group"] = "/workload/prod/other/service"
        with self.assertRaisesRegex(ContractError, "service inventory"):
            self.build(request)

    def test_rejects_unregistered_scope_key(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["scope"]["arbitrary_target"] = "other-system"
        with self.assertRaisesRegex(ContractError, "not present"):
            self.build(request)

    def test_rejects_unknown_contract_field(self) -> None:
        request = copy.deepcopy(self.request_data)
        request["unexpected"] = "value"
        with self.assertRaisesRegex(ContractError, "unknown fields"):
            self.build(request)


if __name__ == "__main__":
    unittest.main()
