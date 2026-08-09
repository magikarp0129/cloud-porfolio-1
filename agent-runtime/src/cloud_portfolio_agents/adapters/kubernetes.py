from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Callable

from ..contracts import ContractError, IncidentRequest, RuntimeConfig
from .base import CommandRunner, Evidence, ToolBudget, render_template


class KubernetesAdapter:
    source_name = "kubernetes"

    def __init__(self, config: RuntimeConfig, budget: ToolBudget):
        self.config = config
        self.source = config.sources.get(self.source_name, {})
        self.runner = CommandRunner(config.limits, budget)

    def collect(self, request: IncidentRequest) -> list[Evidence]:
        if not self.source.get("enabled", False):
            return []
        namespace = request.scope.get("namespace")
        if not namespace:
            return [self._error("k8s_scope", "scope.namespace is required")]

        contexts = self.source.get("context_by_environment", {})
        context = contexts.get(request.environment)
        prefix = ["kubectl"]
        if context:
            prefix.extend(["--context", str(context)])
        try:
            self._verify_cluster_binding(request, prefix)
        except Exception as exc:
            return [self._error("k8s_cluster_binding", str(exc))]
        selector_template = str(
            self.source.get("workload_selector", "app.kubernetes.io/name={service}")
        )
        selector = render_template(selector_template, request)

        calls: list[tuple[str, list[str], Callable[[dict[str, Any]], Evidence]]] = [
            (
                "k8s_nodes",
                [*prefix, "get", "nodes", "-o", "json"],
                self._summarize_nodes,
            ),
            (
                "k8s_workload_pods",
                [
                    *prefix,
                    "get",
                    "pods",
                    "--namespace",
                    namespace,
                    "--selector",
                    selector,
                    "-o",
                    "json",
                ],
                self._summarize_pods,
            ),
            (
                "k8s_workload_controllers",
                [
                    *prefix,
                    "get",
                    "deployments,replicasets,statefulsets,daemonsets",
                    "--namespace",
                    namespace,
                    "--selector",
                    selector,
                    "-o",
                    "json",
                ],
                self._summarize_controllers,
            ),
            (
                "k8s_workload_resilience",
                [
                    *prefix,
                    "get",
                    "horizontalpodautoscalers,poddisruptionbudgets",
                    "--namespace",
                    namespace,
                    "-o",
                    "json",
                ],
                self._summarize_controllers,
            ),
            (
                "k8s_namespace_events",
                [
                    *prefix,
                    "get",
                    "events",
                    "--namespace",
                    namespace,
                    "-o",
                    "json",
                ],
                self._summarize_events,
            ),
        ]

        evidence: list[Evidence] = []
        for query_id, args, summarizer in calls:
            if request.requested_queries and query_id not in request.requested_queries:
                continue
            try:
                evidence.append(summarizer(self.runner.run_json(args)))
            except Exception as exc:  # errors become explicit evidence gaps
                evidence.append(self._error(query_id, str(exc)))
        return evidence

    def _verify_cluster_binding(
        self, request: IncidentRequest, prefix: list[str]
    ) -> None:
        environment = self.config.environments[request.environment]
        service = environment["services"][request.scope["service"]]
        expected_cluster_arn = service.get("cluster_arn")
        expected_role_arn = environment.get("diagnostic_role_arn")
        if not isinstance(expected_cluster_arn, str) or not isinstance(
            expected_role_arn, str
        ):
            raise ContractError("service registry lacks cluster_arn or diagnostic_role_arn")
        cluster = self.runner.run_json(
            [
                "aws",
                "eks",
                "describe-cluster",
                "--name",
                request.scope["cluster"],
                "--region",
                request.scope["region"],
                "--query",
                "cluster.{arn:arn,endpoint:endpoint}",
                "--output",
                "json",
            ]
        )
        if cluster.get("arn") != expected_cluster_arn:
            raise ContractError("EKS cluster ARN does not match the service registry")
        endpoint = cluster.get("endpoint")
        if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
            raise ContractError("EKS cluster endpoint is invalid")

        kubeconfig = self.runner.run_json(
            [*prefix, "config", "view", "--minify", "-o", "json"]
        )
        clusters = kubeconfig.get("clusters", [])
        contexts = kubeconfig.get("contexts", [])
        users = kubeconfig.get("users", [])
        if len(clusters) != 1 or len(contexts) != 1 or len(users) != 1:
            raise ContractError("kubeconfig context did not resolve to one cluster and user")
        if clusters[0].get("cluster", {}).get("server") != endpoint:
            raise ContractError("kubeconfig endpoint does not match EKS DescribeCluster")
        selected_user = contexts[0].get("context", {}).get("user")
        if users[0].get("name") != selected_user:
            raise ContractError("kubeconfig selected user is ambiguous")
        exec_config = users[0].get("user", {}).get("exec", {})
        if Path(str(exec_config.get("command", ""))).name != "aws":
            raise ContractError("kubeconfig must use AWS exec authentication")
        exec_args = [str(value) for value in exec_config.get("args", [])]
        required = ["eks", "get-token", "--cluster-name", request.scope["cluster"]]
        if not all(value in exec_args for value in required):
            raise ContractError("kubeconfig AWS exec arguments do not match the cluster")
        if "--role-arn" in exec_args:
            index = exec_args.index("--role-arn")
            if index + 1 >= len(exec_args) or exec_args[index + 1] != expected_role_arn:
                raise ContractError("kubeconfig role does not match the diagnostic role")

    @staticmethod
    def _ready_condition(item: dict[str, Any]) -> bool:
        return any(
            condition.get("type") == "Ready" and condition.get("status") == "True"
            for condition in item.get("status", {}).get("conditions", [])
        )

    def _summarize_nodes(self, payload: dict[str, Any]) -> Evidence:
        items = payload.get("items", [])
        not_ready = [
            item.get("metadata", {}).get("name", "unknown")
            for item in items
            if not self._ready_condition(item)
        ]
        data = {
            "total": len(items),
            "ready": len(items) - len(not_ready),
            "not_ready": not_ready,
        }
        return Evidence(
            "ev-k8s-nodes",
            self.source_name,
            "k8s_nodes",
            "ok",
            f"Kubernetes nodes: {data['ready']}/{data['total']} Ready",
            data,
        )

    def _summarize_pods(self, payload: dict[str, Any]) -> Evidence:
        items = payload.get("items", [])
        phases: Counter[str] = Counter()
        waiting: Counter[str] = Counter()
        terminated: Counter[str] = Counter()
        restarts = 0
        unready: list[str] = []
        for item in items:
            name = item.get("metadata", {}).get("name", "unknown")
            status = item.get("status", {})
            phases[str(status.get("phase", "Unknown"))] += 1
            if not self._ready_condition(item):
                unready.append(name)
            statuses = status.get("initContainerStatuses", []) + status.get(
                "containerStatuses", []
            )
            for container in statuses:
                restarts += int(container.get("restartCount", 0))
                state = container.get("state", {})
                last_state = container.get("lastState", {})
                if state.get("waiting", {}).get("reason"):
                    waiting[state["waiting"]["reason"]] += 1
                if last_state.get("terminated", {}).get("reason"):
                    terminated[last_state["terminated"]["reason"]] += 1
        data = {
            "total": len(items),
            "ready": len(items) - len(unready),
            "unready": unready[:50],
            "phases": dict(phases),
            "restart_count": restarts,
            "waiting_reasons": dict(waiting),
            "last_termination_reasons": dict(terminated),
        }
        return Evidence(
            "ev-k8s-pods",
            self.source_name,
            "k8s_workload_pods",
            "ok",
            f"Workload pods: {data['ready']}/{data['total']} Ready, {restarts} restarts",
            data,
        )

    def _summarize_controllers(self, payload: dict[str, Any]) -> Evidence:
        controllers = []
        for item in payload.get("items", []):
            metadata = item.get("metadata", {})
            spec = item.get("spec", {})
            status = item.get("status", {})
            controllers.append(
                {
                    "kind": item.get("kind", "Unknown"),
                    "name": metadata.get("name", "unknown"),
                    "generation": metadata.get("generation"),
                    "desired": spec.get("replicas"),
                    "ready": status.get("readyReplicas"),
                    "available": status.get("availableReplicas"),
                    "current": status.get("currentReplicas"),
                }
            )
        return Evidence(
            "ev-k8s-controllers",
            self.source_name,
            "k8s_workload_controllers",
            "ok",
            f"Collected status for {len(controllers)} workload controllers",
            {"controllers": controllers[:100]},
        )

    def _summarize_events(self, payload: dict[str, Any]) -> Evidence:
        reasons: Counter[str] = Counter()
        warnings = []
        for item in payload.get("items", []):
            reason = str(item.get("reason", "Unknown"))
            reasons[reason] += int(item.get("count", 1) or 1)
            if item.get("type") == "Warning":
                involved = item.get("involvedObject", {})
                warnings.append(
                    {
                        "reason": reason,
                        "kind": involved.get("kind"),
                        "name": involved.get("name"),
                        "last_seen": item.get("eventTime")
                        or item.get("lastTimestamp")
                        or item.get("metadata", {}).get("creationTimestamp"),
                    }
                )
        warnings.sort(key=lambda item: item.get("last_seen") or "", reverse=True)
        return Evidence(
            "ev-k8s-events",
            self.source_name,
            "k8s_namespace_events",
            "ok",
            f"Kubernetes events include {len(warnings)} Warning entries",
            {"reason_counts": dict(reasons), "recent_warnings": warnings[:20]},
        )

    def _error(self, query_id: str, message: str) -> Evidence:
        return Evidence(
            f"ev-{query_id}-error",
            self.source_name,
            query_id,
            "error",
            f"Kubernetes evidence unavailable: {message}",
        )
